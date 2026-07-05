"""Search expansion phase execution and diagnostics for candidate discovery."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarPipelineEvent,
    RadarExecutionTask,
    WebSearchProviderResult,
)
from power_web_os.application.radar.candidate_discovery.search_expansion.payloads import benchmark_target_probe_minimums, merge_selection_summary
from power_web_os.application.radar.candidate_discovery.search_expansion.models import RadarSearchExpansionPlan
from power_web_os.application.radar.candidate_discovery.search_expansion.scheduler import schedule_guaranteed_expansion_variants
from power_web_os.application.radar.candidate_discovery.search_expansion.work_scheduler_metadata import merge_work_scheduler_metadata
from power_web_os.application.radar.candidate_discovery.execution.context import (
    CandidateDiscoveryExecutionContext,
    PhaseResult,
)
from power_web_os.application.radar.candidate_discovery.execution.state import (
    CandidateDiscoveryExecutionState,
    SmokeLimitPolicy,
)
from power_web_os.application.radar.candidate_discovery.execution.task_runner import TaskExecutionService
from power_web_os.application.live_radar_universe import (
    dict_list,
    gap_items,
    gap_observations,
    gap_payloads,
)


class ExpansionPhaseExecutor:
    """Runs target-aware recall expansion through scheduler/admission guards.

    Owns:
    - Expansion planning diagnostics, guaranteed target scheduling, scheduler
      portfolio execution, skip records, result merge, and expansion events.

    Does not own:
    - Source strategy generation, scheduler admission policy internals, final
      evaluation, or provider adapter implementation.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#expansionphaseexecutor
    """

    phase_name = "search_expansion"

    def __init__(
        self,
        task_service: TaskExecutionService | None = None,
        smoke_policy: SmokeLimitPolicy | None = None,
    ) -> None:
        self._task_service = task_service or TaskExecutionService()
        self._smoke_policy = smoke_policy or SmokeLimitPolicy()

    def run(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        base_tasks: list[RadarExecutionTask],
    ) -> PhaseResult:
        expansion_plan = self._plan_expansion(context, state)
        expansion_payload = expansion_plan.to_payload()
        self._persist_plan_diagnostics(context, state, expansion_payload)
        if not expansion_plan.should_expand:
            return PhaseResult(phase_name="search_expansion")

        schedule, scheduled_plan = self._schedule_expansion(context, state, expansion_plan, expansion_payload)
        tasks = self._build_expansion_tasks(context, state, scheduled_plan, base_tasks)
        portfolio = self._build_work_portfolio(context, state, tasks, schedule)
        self._execute_portfolio(context, state, portfolio)
        state.candidate_scope = self._candidate_scope(context, state)
        return PhaseResult(phase_name="search_expansion")

    def _plan_expansion(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> RadarSearchExpansionPlan:
        return context.search_expansion_service.plan_expansion(
            radar=context.radar,
            candidate_scope=state.candidate_scope,
            provider_metadata=state.provider_metadata,
            coverage_checks=state.coverage_checks,
            unresolved_candidate_gaps=state.unresolved_candidate_gaps,
        )

    def _persist_plan_diagnostics(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        expansion_payload: dict[str, Any],
    ) -> None:
        state.provider_metadata = {
            **state.provider_metadata,
            "expansion_target_queue": [
                *dict_list(state.provider_metadata.get("expansion_target_queue")),
                *expansion_payload.get("targets", []),
            ],
            "expansion_target_summary_by_type": _merge_int_dicts(
                state.provider_metadata.get("expansion_target_summary_by_type"),
                expansion_payload.get("targets_by_type"),
            ),
            "search_expansion_query_variants_by_target": {
                **(
                    state.provider_metadata.get("search_expansion_query_variants_by_target")
                    if isinstance(state.provider_metadata.get("search_expansion_query_variants_by_target"), dict)
                    else {}
                ),
                **expansion_payload.get("variants_by_target", {}),
            },
            "search_expansion_query_variants_by_target_type": {
                **(
                    state.provider_metadata.get("search_expansion_query_variants_by_target_type")
                    if isinstance(state.provider_metadata.get("search_expansion_query_variants_by_target_type"), dict)
                    else {}
                ),
                **expansion_payload.get("variants_by_target_type", {}),
            },
            "targets_not_searched": _dedupe_target_records([
                *dict_list(state.provider_metadata.get("targets_not_searched")),
                *dict_list(expansion_payload.get("targets_not_selected")),
            ]),
            "search_expansion_selection_summary": merge_selection_summary(
                state.provider_metadata.get("search_expansion_selection_summary"),
                expansion_payload.get("selection_summary"),
            ),
            "search_expansion_selection_diagnostics": [
                *dict_list(state.provider_metadata.get("search_expansion_selection_diagnostics")),
                *dict_list(expansion_payload.get("selection_diagnostics")),
            ],
            "source_capability_strategy_summary": _source_capability_strategy_summary(
                radar=context.radar,
                expansion_plan=expansion_payload,
            ),
            "search_expansion_query_variants": [
                *dict_list(state.provider_metadata.get("search_expansion_query_variants")),
                *expansion_payload.get("variants", []),
            ],
        }

    def _schedule_expansion(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        expansion_plan: RadarSearchExpansionPlan,
        expansion_payload: dict[str, Any],
    ) -> tuple[Any, RadarSearchExpansionPlan]:
        schedule = schedule_guaranteed_expansion_variants(
            variants=list(expansion_plan.variants),
            targets=expansion_payload.get("targets", []),
            minimums=benchmark_target_probe_minimums(context.radar),
        )
        state.provider_metadata = {
            **state.provider_metadata,
            **schedule.to_metadata(),
            "targets_not_searched": _dedupe_target_records([
                *dict_list(state.provider_metadata.get("targets_not_searched")),
                *schedule.unscheduled_targets,
            ]),
        }
        return schedule, RadarSearchExpansionPlan(
            should_expand=expansion_plan.should_expand,
            variants=schedule.variants,
            targets=expansion_plan.targets,
            reason=expansion_plan.reason,
        )

    def _build_expansion_tasks(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        scheduled_plan: RadarSearchExpansionPlan,
        base_tasks: list[RadarExecutionTask],
    ) -> list[RadarExecutionTask]:
        tasks = context.search_expansion_service.tasks_from_plan(
            plan=scheduled_plan,
            base_task=base_tasks[0] if base_tasks else None,
        )
        state.provider_metadata = {
            **state.provider_metadata,
            "search_expansion_tasks": [
                *dict_list(state.provider_metadata.get("search_expansion_tasks")),
                *[
                    {
                        "task_id": task.task_id,
                        "query": task.query,
                        "source_ids": list(task.source_ids),
                        "source_scope": task.source_scope,
                        "reason": scheduled_plan.reason,
                    }
                    for task in tasks
                ],
            ],
        }
        return tasks

    def _build_work_portfolio(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        tasks: list[RadarExecutionTask],
        schedule: Any,
    ) -> Any:
        portfolio = context.work_scheduler.build_recall_expansion_portfolio(
            tasks=tasks,
            scheduled_variants=list(schedule.scheduled_variants),
            external_budget=context.external_budget,
        )
        state.provider_metadata = merge_work_scheduler_metadata(state.provider_metadata, portfolio.to_metadata())
        return portfolio

    def _execute_portfolio(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        portfolio: Any,
    ) -> None:
        decisions_by_work_id = {decision.work_id: decision for decision in portfolio.ledger.decisions}
        for work_item in portfolio.work_items:
            self._execute_work_item(context, state, work_item, decisions_by_work_id)

    def _execute_work_item(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        work_item: Any,
        decisions_by_work_id: dict[str, Any],
    ) -> None:
        task = work_item.task
        scheduled_variant = work_item.scheduled_variant
        if scheduled_variant is None:
            return
        variant = scheduled_variant.variant
        admission_decision = decisions_by_work_id.get(work_item.work_id)
        if admission_decision is not None and not admission_decision.accepted:
            self._record_admission_rejection(state, work_item, task, variant, admission_decision)
            return
        result = self._task_service.run_task(
            provider=context.provider,
            radar=context.radar,
            task=task,
            radar_id=context.execution_plan.radar_id,
            budget=context.task_budget,
            external_budget=context.external_budget,
            semantic_reserve_key=variant.budget_reserve_key,
        )
        result_payload = _expansion_result_payload(
            task=task,
            variant=variant,
            result=result,
            budget_decision=result.provider_metadata.get("budget_decision", {}),
        )
        if result_payload["execution_status"] == "not_executed":
            self._record_not_executed(state, task, result_payload)
            return
        self._merge_executed_result(state, task, variant, result, result_payload)

    def _record_admission_rejection(
        self,
        state: CandidateDiscoveryExecutionState,
        work_item: Any,
        task: RadarExecutionTask,
        variant: Any,
        admission_decision: Any,
    ) -> None:
        skipped = {
            "task_id": task.task_id,
            "query": task.query,
            "source_ids": list(task.source_ids),
            "target_id": variant.target_id,
            "target_type": variant.target_type,
            "budget_reserve_key": variant.budget_reserve_key,
            "execution_status": "work_admission_rejected",
            "not_searched_reason": admission_decision.reason,
            "budget_decision": admission_decision.budget_decision,
            "work_id": work_item.work_id,
            "lane": work_item.lane,
        }
        state.provider_metadata = {
            **state.provider_metadata,
            "targets_not_searched": [
                *dict_list(state.provider_metadata.get("targets_not_searched")),
                skipped,
            ],
        }
        state.events.append(LiveRadarPipelineEvent(
            event_type="search_expansion_skipped_budget_reserve",
            phase="collection",
            actor="application",
            node_name="search_expansion",
            visibility="operator",
            summary=f"Skipped recall expansion task {task.task_id}: {admission_decision.message}",
            payload=skipped,
        ))

    def _record_not_executed(
        self,
        state: CandidateDiscoveryExecutionState,
        task: RadarExecutionTask,
        result_payload: dict[str, Any],
    ) -> None:
        not_executed = {
            **result_payload,
            "execution_status": "not_searched",
        }
        state.provider_metadata = {
            **state.provider_metadata,
            "targets_not_searched": [
                *dict_list(state.provider_metadata.get("targets_not_searched")),
                not_executed,
            ],
            "search_expansion_results": [
                *dict_list(state.provider_metadata.get("search_expansion_results")),
                result_payload,
            ],
        }
        state.events.append(LiveRadarPipelineEvent(
            event_type="search_expansion_skipped_external_budget",
            phase="collection",
            actor="application",
            node_name="search_expansion",
            visibility="operator",
            summary=f"Skipped recall expansion task {task.task_id}: external provider budget was exhausted.",
            payload=not_executed,
        ))

    def _merge_executed_result(
        self,
        state: CandidateDiscoveryExecutionState,
        task: RadarExecutionTask,
        variant: Any,
        result: WebSearchProviderResult,
        result_payload: dict[str, Any],
    ) -> None:
        gaps = gap_items(result)
        result = result.model_copy(update={
            "candidate_observations": [
                *result.candidate_observations,
                *gap_observations(gaps, origin_task_id=task.task_id),
            ],
        })
        state.sources, state.observations, state.provider_metadata = self._task_service.merger.merge_result(
            state.sources,
            state.observations,
            state.provider_metadata,
            result,
        )
        state.executed_task_ids.append(f"{task.task_id}:search_expansion")
        state.unresolved_candidate_gaps.extend(gap_payloads(gaps, origin_task_id=task.task_id))
        state.provider_metadata = {
            **state.provider_metadata,
            "search_expansion_results": [
                *dict_list(state.provider_metadata.get("search_expansion_results")),
                {
                    **result_payload,
                },
            ],
        }
        state.events.append(LiveRadarPipelineEvent(
            event_type="search_expansion_executed",
            phase="collection",
            actor="application",
            node_name="search_expansion",
            visibility="operator",
            summary=f"Executed recall-first search expansion task {task.task_id}.",
            payload={
                "task_id": task.task_id,
                "query": task.query,
                "source_ids": list(task.source_ids),
                "target_id": variant.target_id,
                "target_type": variant.target_type,
                "budget_reserve_key": variant.budget_reserve_key,
                "source_count": len(result.sources),
                "candidate_observation_count": len(result.candidate_observations),
            },
            source_refs=[source.evidence_ref for source in result.sources if source.evidence_ref],
        ))

    def _candidate_scope(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> list[str]:
        scope = self._task_service.eligible_candidate_names(
            radar=context.radar,
            sources=state.sources,
            observations=state.observations,
            completed_qualification_ids=state.completed_qualification_ids,
        )
        return self._smoke_policy.limit_candidates(
            scope,
            context.external_budget.settings.smoke_max_candidates,
        )

def _source_capability_strategy_summary(*, radar: dict[str, Any], expansion_plan: dict[str, Any]) -> dict[str, Any]:
    policy = radar.get("global_search_policy") if isinstance(radar.get("global_search_policy"), dict) else {}
    configured_sources = [
        str(item.get("source_id") or item.get("reference") or "")
        for item in dict_list(policy.get("sources"))
        if str(item.get("source_id") or item.get("reference") or "").strip()
    ]
    variants = dict_list(expansion_plan.get("variants"))
    return {
        "configured_source_count": len(configured_sources),
        "target_count": len(dict_list(expansion_plan.get("targets"))),
        "variant_count": len(variants),
        "official_probe_count": sum(1 for item in variants if item.get("budget_reserve_key") == "official_coverage_probe"),
        "open_web_probe_count": sum(1 for item in variants if item.get("budget_reserve_key") == "open_web_coverage_probe"),
        "production_site_probe_count": sum(1 for item in variants if item.get("budget_reserve_key") == "production_site_coverage_probe"),
        "target_count_by_type": dict(expansion_plan.get("targets_by_type") or {}),
        "variant_count_by_target_type": {
            key: len(value)
            for key, value in (
                expansion_plan.get("variants_by_target_type")
                if isinstance(expansion_plan.get("variants_by_target_type"), dict)
                else {}
            ).items()
            if isinstance(value, list)
        },
        "uses_profile_driven_sources": bool(configured_sources and variants),
    }

def _expansion_result_payload(
    *,
    task: RadarExecutionTask,
    variant: Any,
    result: WebSearchProviderResult,
    budget_decision: dict[str, Any],
) -> dict[str, Any]:
    status, reason = _expansion_execution_status(result=result, budget_decision=budget_decision)
    return {
        "task_id": task.task_id,
        "query": task.query,
        "source_ids": list(task.source_ids),
        "target_id": variant.target_id,
        "target_type": variant.target_type,
        "budget_reserve_key": variant.budget_reserve_key,
        "execution_status": status,
        "not_searched_reason": reason if status == "not_executed" else "",
        "source_count": len(result.sources),
        "candidate_observation_count": len(result.candidate_observations),
        "budget_decision": budget_decision,
    }

def _expansion_execution_status(*, result: WebSearchProviderResult, budget_decision: dict[str, Any]) -> tuple[str, str]:
    if isinstance(budget_decision, dict) and budget_decision.get("accepted") is False:
        kind = str(budget_decision.get("kind") or "")
        reason = str(budget_decision.get("reason") or "")
        if kind == "budget_reserve":
            return "not_executed", "not_executed_reserve_limited"
        if reason == "semantic_task_reserve_exhausted":
            return "not_executed", "semantic_task_budget_limited"
        return "not_executed", "not_executed_global_budget_limited"
    if result.sources:
        return "executed_source_found", ""
    return "executed_no_support", ""

def _merge_int_dicts(left: object, right: object) -> dict[str, int]:
    result: dict[str, int] = {}
    for source in (left, right):
        if not isinstance(source, dict):
            continue
        for key, value in source.items():
            try:
                result[str(key)] = result.get(str(key), 0) + int(value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
    return result

def _dedupe_target_records(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        key = (
            str(item.get("target_id") or ""),
            str(item.get("task_id") or ""),
            str(item.get("not_searched_reason") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
