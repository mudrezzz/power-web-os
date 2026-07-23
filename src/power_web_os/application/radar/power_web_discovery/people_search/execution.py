"""Bounded retrieval, receipt projection and coverage checkpoints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import re

from .contracts import (
    AcceptedAccountRoleTitleHypothesis,
    AccountRoleTitleHypothesisProposal,
    PeopleSearchBudgetReport,
    PeopleSearchBudgetSettings,
    PeopleSearchExecutionReceipt,
    PeopleSearchProviderAttempt,
    PeopleSearchStageArtifact,
    PeopleSearchTask,
    PeopleSourceLaneDecision,
    PeopleSourceLead,
    PowerWebPeopleSearchPlanningInput,
    RoleCoverageCheckpoint,
    TitleHypothesisAcceptanceDecision,
)
from .ports import PeopleSearchProvider
from .planning import PeopleSearchQueryRevisionService


def _id(prefix: str, *parts: str) -> str:
    return f"{prefix}-{sha256(chr(31).join(parts).encode('utf-8')).hexdigest()[:20]}"


@dataclass
class _Budget:
    settings: PeopleSearchBudgetSettings
    hypothesis_provider_calls: int = 0
    people_search_tasks: int = 0
    provider_calls: int = 0
    source_verifications: int = 0
    retries: int = 0
    query_revisions: int = 0
    exhaustion_events: list[str] | None = None

    def __post_init__(self) -> None:
        self.exhaustion_events = []

    def allow_task(self, task_id: str) -> bool:
        if self.people_search_tasks >= self.settings.max_people_search_tasks:
            self.exhaustion_events.append(f"people_search_tasks:{task_id}")
            return False
        self.people_search_tasks += 1
        return True

    def allow_call(self, task_id: str, *, retry: bool) -> bool:
        if self.provider_calls >= self.settings.max_provider_calls:
            self.exhaustion_events.append(f"provider_calls:{task_id}")
            return False
        self.provider_calls += 1
        if retry:
            self.retries += 1
        return True

    def report(self) -> PeopleSearchBudgetReport:
        return PeopleSearchBudgetReport(
            settings=self.settings,
            hypothesis_provider_calls=self.hypothesis_provider_calls,
            people_search_tasks=self.people_search_tasks,
            provider_calls=self.provider_calls,
            source_verifications=self.source_verifications,
            retries=self.retries,
            query_revisions=self.query_revisions,
            exhaustion_events=tuple(self.exhaustion_events or ()),
        )

    def allow_revision(self) -> bool:
        maximum = min(self.settings.recovery_reserve, self.settings.max_people_search_tasks - self.settings.max_initial_tasks)
        if self.query_revisions >= maximum:
            return False
        self.query_revisions += 1
        return True

    def verification_capacity(self, task_id: str, requested: int) -> int:
        remaining = self.settings.max_source_verifications - self.source_verifications
        allowed = max(0, min(remaining, requested))
        self.source_verifications += allowed
        if allowed < requested:
            self.exhaustion_events.append(f"source_verifications:{task_id}")
        return allowed


class PeopleSearchStageExecutor:
    def __init__(self, provider: PeopleSearchProvider, *, settings: PeopleSearchBudgetSettings) -> None:
        self._provider = provider
        self._settings = settings

    def execute(
        self,
        *,
        planning_input: PowerWebPeopleSearchPlanningInput,
        proposals: tuple[AccountRoleTitleHypothesisProposal, ...],
        accepted_hypotheses: tuple[AcceptedAccountRoleTitleHypothesis, ...],
        acceptance: tuple[TitleHypothesisAcceptanceDecision, ...],
        lane_decisions: tuple[PeopleSourceLaneDecision, ...],
        tasks: tuple[PeopleSearchTask, ...],
        hypothesis_provider_calls: int,
        model_profile_id: str,
    ) -> PeopleSearchStageArtifact:
        budget = _Budget(self._settings, hypothesis_provider_calls=hypothesis_provider_calls)
        receipts: list[PeopleSearchExecutionReceipt] = []
        leads: list[PeopleSourceLead] = []
        executed_tasks: list[PeopleSearchTask] = []
        final_decisions = {item.decision_id: item for item in lane_decisions}
        for task in tasks:
            if not budget.allow_task(task.task_id):
                final_decisions[task.decision_id] = final_decisions[task.decision_id].model_copy(
                    update={"status": "budget_limited", "reason_code": "task_budget_exhausted"}
                )
                continue
            executed_tasks.append(task)
            receipt, task_leads = self._execute_task(task, planning_input, accepted_hypotheses, budget)
            receipts.append(receipt)
            leads.extend(task_leads)
            final_decisions[task.decision_id] = final_decisions[task.decision_id].model_copy(
                update={"status": "executed", "reason_code": receipt.terminal_outcome}
            )
        revision_service = PeopleSearchQueryRevisionService()
        initial_receipts = {item.task_id: item for item in receipts}
        for task in tasks:
            receipt = initial_receipts.get(task.task_id)
            if receipt is None or receipt.terminal_outcome != "searched_no_results":
                continue
            if self._settings.max_query_revisions_per_role_lane < 1 or not budget.allow_revision():
                continue
            revised_task = revision_service.revise(task, planning_input, accepted_hypotheses)
            if not budget.allow_task(revised_task.task_id):
                break
            executed_tasks.append(revised_task)
            revised_receipt, revised_leads = self._execute_task(
                revised_task, planning_input, accepted_hypotheses, budget
            )
            receipts.append(revised_receipt)
            leads.extend(revised_leads)
            if revised_receipt.terminal_outcome == "searched_results":
                final_decisions[task.decision_id] = final_decisions[task.decision_id].model_copy(
                    update={"reason_code": "searched_results_after_query_revision"}
                )
        checkpoints = self._checkpoints(
            planning_input,
            tuple(final_decisions.values()),
            tuple(receipts),
            tuple(leads),
        )
        budget_report = budget.report()
        limited = bool(budget_report.exhaustion_events) or any(
            item.state.startswith("incomplete_") for item in checkpoints
        )
        return PeopleSearchStageArtifact(
            stage_id=_id("people-search-stage", planning_input.handoff_id, planning_input.as_of.isoformat()),
            handoff_id=planning_input.handoff_id,
            account_id=planning_input.account_id,
            source_candidate_run_id=planning_input.source_candidate_run_id,
            source_signal_run_id=planning_input.source_signal_run_id,
            model_profile_id=model_profile_id,
            provider_runtime=self._provider.runtime_name,
            planning_input=planning_input,
            proposed_hypotheses=proposals,
            accepted_hypotheses=accepted_hypotheses,
            hypothesis_acceptance=acceptance,
            lane_decisions=tuple(final_decisions.values()),
            tasks=tuple(executed_tasks),
            receipts=tuple(receipts),
            source_leads=tuple(leads),
            checkpoints=checkpoints,
            budgets=budget_report,
            completion_state="completed_with_limits" if limited else "completed",
            diagnostics=tuple(budget_report.exhaustion_events),
        )

    def _execute_task(self, task, planning_input, hypotheses, budget):
        attempts: list[PeopleSearchProviderAttempt] = []
        started = datetime.now(UTC)
        result = None
        for attempt_number in range(1, self._settings.max_provider_retries_per_task + 2):
            if not budget.allow_call(task.task_id, retry=attempt_number > 1):
                break
            attempt_started = datetime.now(UTC)
            try:
                result = self._provider.search(task)
                outcome = result.outcome
                error_code = None
                engine = result.engine
                model_id = result.model_id
                server_tool_searches = result.server_tool_searches
            except ValueError:
                outcome, error_code = "schema_error", "provider_schema_error"
                engine, model_id, server_tool_searches = "unknown", self._provider.model_id, 0
            except Exception:
                outcome, error_code = "provider_error", "provider_transport_error"
                engine, model_id, server_tool_searches = "unknown", self._provider.model_id, 0
            attempts.append(PeopleSearchProviderAttempt(
                attempt_id=_id("people-attempt", task.task_id, str(attempt_number)),
                task_id=task.task_id,
                attempt_number=attempt_number,
                started_at=attempt_started,
                completed_at=datetime.now(UTC),
                outcome=outcome,
                engine=engine,
                model_id=model_id,
                error_code=error_code,
                server_tool_searches=server_tool_searches,
            ))
            if result is not None:
                break
        terminal = attempts[-1].outcome if attempts else "provider_error"
        sources = result.sources if result is not None else ()
        receipt_id = _id("people-receipt", task.task_id)
        receipt = PeopleSearchExecutionReceipt(
            receipt_id=receipt_id,
            task_id=task.task_id,
            decision_id=task.decision_id,
            demand_id=task.demand_id,
            account_id=task.account_id,
            product_id=task.product_id,
            semantic_role_code=task.semantic_role_code,
            lane=task.lane,
            query=task.query,
            domain_restrictions=task.domain_restrictions,
            started_at=started,
            completed_at=datetime.now(UTC),
            terminal_outcome=terminal,
            result_count=len(sources),
            source_refs=tuple(item.source_ref for item in sources),
            attempts=tuple(attempts),
        )
        role_titles = tuple(
            item.title_or_function for item in hypotheses if item.demand_id == task.demand_id
        )
        allowed_sources = sources[:budget.verification_capacity(task.task_id, len(sources))]
        leads = tuple(
            self._lead(task, receipt_id, item, planning_input.account_aliases, role_titles)
            for item in allowed_sources
        )
        return receipt, leads

    @staticmethod
    def _lead(task, receipt_id, source, account_aliases, role_titles):
        haystack = f"{source.title} {source.excerpt} {source.url}".casefold()
        account_match = any(_tokens(alias) <= _tokens(haystack) for alias in account_aliases if alias)
        role_match = any(bool(_tokens(title) & _tokens(haystack)) for title in role_titles)
        relevance = (
            "account_role_relevant" if account_match and role_match
            else "account_only" if account_match
            else "role_only" if role_match
            else "unclear"
        )
        return PeopleSourceLead(
            lead_id=_id("people-lead", task.task_id, source.url),
            source_ref=source.source_ref,
            task_id=task.task_id,
            receipt_id=receipt_id,
            demand_id=task.demand_id,
            account_id=task.account_id,
            product_id=task.product_id,
            semantic_role_code=task.semantic_role_code,
            lane=task.lane,
            url=source.url,
            title=source.title,
            excerpt=source.excerpt,
            page_access_limited=source.page_access_limited,
            relevance=relevance,
            retained_reason="public_search_citation_retained_for_next_stage",
        )

    @staticmethod
    def _checkpoints(planning_input, decisions, receipts, leads):
        receipt_by_decision = {item.decision_id: item for item in receipts}
        checkpoints: list[RoleCoverageCheckpoint] = []
        for demand in planning_input.role_demands:
            role_decisions = [item for item in decisions if item.demand_id == demand.demand_id]
            role_leads = [item for item in leads if item.demand_id == demand.demand_id]
            completed = tuple(
                item.lane for item in role_decisions
                if item.status == "executed"
                and receipt_by_decision[item.decision_id].terminal_outcome in {"searched_results", "searched_no_results"}
            )
            statuses = {item.status for item in role_decisions}
            outcomes = {
                receipt_by_decision[item.decision_id].terminal_outcome
                for item in role_decisions if item.decision_id in receipt_by_decision
            }
            if "budget_limited" in statuses:
                state, reason = "incomplete_budget", "mandatory_lane_budget_limited"
            elif statuses & {"not_executable", "unsupported"}:
                state, reason = "incomplete_capability", "mandatory_lane_not_executable"
            elif "policy_limited" in statuses:
                state, reason = "incomplete_policy", "mandatory_lane_policy_limited"
            elif outcomes & {"provider_error", "schema_error"}:
                state, reason = "incomplete_provider", "mandatory_lane_provider_failure"
            elif role_leads:
                state, reason = "complete_with_leads", "all_mandatory_lanes_searched"
            else:
                state, reason = "complete_no_leads", "all_mandatory_lanes_searched_no_leads"
            checkpoints.append(RoleCoverageCheckpoint(
                checkpoint_id=_id("people-checkpoint", demand.demand_id),
                demand_id=demand.demand_id,
                account_id=planning_input.account_id,
                product_id=demand.product_id,
                semantic_role_code=demand.semantic_role_code,
                required_lanes=("official_company", "hh_public_web", "generic_web"),
                completed_lanes=completed,
                lead_ids=tuple(item.lead_id for item in role_leads),
                state=state,
                reason_code=reason,
            ))
        return tuple(checkpoints)


def _tokens(value: str) -> set[str]:
    return {item for item in re.findall(r"[\w-]+", value.casefold()) if len(item) >= 3}
