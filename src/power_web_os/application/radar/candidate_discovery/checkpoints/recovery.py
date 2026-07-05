"""Apply bounded checkpoint recovery actions for candidate discovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .models import RadarExecutionCheckpointDecision
from .policy import RadarExecutionCheckpointService
from .recording import record_execution_checkpoint
from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarPipelineEvent,
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
    WebSearchProvider,
)
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget
from power_web_os.application.live_radar_external_budget import RadarExternalCallBudget
from power_web_os.application.radar.candidate_discovery.execution.task_runner import TaskExecutionService
from power_web_os.application.live_radar_search_expansion_execution import execute_targeted_search_expansion
from power_web_os.application.radar_search_expansion import RadarSearchExpansionService
from power_web_os.application.radar_work_scheduler import RadarWorkScheduler


@dataclass
class RadarCheckpointRecoveryState:
    sources: list[RadarSourceEvidence]
    observations: list[dict[str, Any]]
    provider_metadata: dict[str, Any]
    candidate_scope: list[str]
    stopped_for_review_reason: str = ""


@dataclass
class RadarCheckpointRecoveryContext:
    radar: dict[str, Any]
    execution_plan: RadarExecutionPlan
    provider: WebSearchProvider
    service: RadarExecutionCheckpointService
    budget: RadarExecutionBudget
    completed_qualification_ids: list[str]
    checkpoint_decisions: list[dict[str, Any]]
    adaptive_actions: list[dict[str, Any]]
    checkpoint_warnings: list[str]
    events: list[LiveRadarPipelineEvent]
    executed_task_ids: list[str]
    coverage_checks: list[dict[str, Any]] = field(default_factory=list)
    coverage_warnings: list[str] = field(default_factory=list)
    unresolved_candidate_gaps: list[dict[str, Any]] = field(default_factory=list)
    useful_result_retry_records: list[dict[str, Any]] = field(default_factory=list)
    source_obligation_decisions: list[dict[str, Any]] = field(default_factory=list)
    external_budget: RadarExternalCallBudget | None = None
    search_expansion_service: RadarSearchExpansionService | None = None
    work_scheduler: RadarWorkScheduler | None = None
    smoke_candidate_limit: int | None = None


class RadarExecutionPlanReviser(Protocol):
    """Build bounded recovery tasks from product-safe checkpoint facts."""

    def revise(
        self,
        *,
        base_task: RadarExecutionTask,
        checkpoint_id: str,
        phase: str,
        attempt: int,
        state: RadarCheckpointRecoveryState,
    ) -> list[RadarExecutionTask]:
        """Return executable revised tasks or an empty list when no safe revision exists."""


class DefaultRadarExecutionPlanReviser:
    """First revision adapter: keep recovery bounded to the current failed task."""

    def revise(
        self,
        *,
        base_task: RadarExecutionTask,
        checkpoint_id: str,
        phase: str,
        attempt: int,
        state: RadarCheckpointRecoveryState,
    ) -> list[RadarExecutionTask]:
        _ = checkpoint_id, phase, state
        return [_adaptive_task(base_task, action="revise_plan", attempt=attempt)]


class RadarCheckpointActionExecutor:
    """Execute bounded adaptive actions selected by checkpoint review.

    Owns:
        Bounded retry, repair, expansion, and revision loops selected by checkpoint policy.
    Does not own:
        Checkpoint action selection, provider implementation, persistence, or API projection.
    Architecture:
        See docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md.
    """

    def __init__(self, plan_reviser: RadarExecutionPlanReviser | None = None) -> None:
        self._plan_reviser = plan_reviser or DefaultRadarExecutionPlanReviser()
        self._task_service = TaskExecutionService()

    def recover(
        self,
        *,
        checkpoint_id: str,
        phase: str,
        tasks: list[RadarExecutionTask],
        state: RadarCheckpointRecoveryState,
        context: RadarCheckpointRecoveryContext,
    ) -> tuple[RadarCheckpointRecoveryState, RadarExecutionCheckpointDecision]:
        decision = self._record(checkpoint_id=checkpoint_id, phase=phase, state=state, context=context)
        retry_attempts = 0
        repair_attempts = 0
        revision_attempts = 0
        while decision.action in {"retry_same_source", "expand_sources", "repair_extraction", "retry_extraction", "revise_plan"} and tasks:
            base_task = tasks[0]
            action = _effective_action(decision.action, base_task, context.radar)
            if action in {"retry_same_source", "expand_sources"}:
                if retry_attempts >= context.service.policy.max_retries_per_stage:
                    state.stopped_for_review_reason = "Checkpoint retry limit reached before discovery recovered."
                    _record_terminal_stop(checkpoint_id, phase, state.stopped_for_review_reason, context, reason_code="weak_candidate_coverage")
                    break
                retry_attempts += 1
                attempt = retry_attempts
            elif action in {"repair_extraction", "retry_extraction"}:
                if repair_attempts >= context.service.policy.max_retries_per_stage:
                    detail = _extraction_recovery_stop_reason(state.provider_metadata)
                    state.stopped_for_review_reason = (
                        "Extraction repair limit reached before extraction recovered."
                        if not detail
                        else f"Extraction repair limit reached before extraction recovered: {detail}."
                    )
                    _record_terminal_stop(
                        checkpoint_id,
                        phase,
                        state.stopped_for_review_reason,
                        context,
                        reason_code="extraction_repair_exhausted",
                        details={"extraction_failure_detail": detail} if detail else {},
                    )
                    break
                repair_attempts += 1
                attempt = repair_attempts
            else:
                if revision_attempts >= context.service.policy.max_revisions_per_run:
                    state.stopped_for_review_reason = "Checkpoint revision limit reached before discovery recovered."
                    _record_terminal_stop(checkpoint_id, phase, state.stopped_for_review_reason, context, reason_code="extraction_schema_failed")
                    break
                revision_attempts += 1
                attempt = revision_attempts
            task = self._task_for_action(
                base_task=base_task,
                action=action,
                attempt=attempt,
                checkpoint_id=checkpoint_id,
                phase=phase,
                state=state,
            )
            if task is None:
                state.stopped_for_review_reason = "Checkpoint revision did not produce an executable recovery task."
                _record_terminal_stop(checkpoint_id, phase, state.stopped_for_review_reason, context, reason_code="extraction_schema_failed")
                break
            if decision.action == "expand_sources" and action == "expand_sources" and context.search_expansion_service is not None:
                expansion = execute_targeted_search_expansion(
                    base_task=base_task,
                    checkpoint_id=checkpoint_id,
                    phase=phase,
                    attempt=attempt,
                    radar=context.radar,
                    execution_plan=context.execution_plan,
                    provider=context.provider,
                    service=context.search_expansion_service,
                    sources=state.sources,
                    observations=state.observations,
                    provider_metadata=state.provider_metadata,
                    candidate_scope=state.candidate_scope,
                    completed_qualification_ids=context.completed_qualification_ids,
                    coverage_checks=context.coverage_checks,
                    unresolved_candidate_gaps=context.unresolved_candidate_gaps,
                    events=context.events,
                    executed_task_ids=context.executed_task_ids,
                    budget=context.budget,
                    external_budget=context.external_budget,
                    work_scheduler=context.work_scheduler,
                    smoke_candidate_limit=context.smoke_candidate_limit,
                )
                state = RadarCheckpointRecoveryState(
                    expansion.sources,
                    expansion.observations,
                    expansion.provider_metadata,
                    expansion.candidate_scope,
                    expansion.stopped_for_review_reason,
                )
                context.adaptive_actions.append(expansion.adaptive_action)
                if expansion.stopped_for_review_reason:
                    _record_terminal_stop(
                        checkpoint_id,
                        phase,
                        expansion.stopped_for_review_reason,
                        context,
                        reason_code=expansion.stop_reason_code or "weak_candidate_coverage",
                        details=expansion.stop_details or {},
                    )
                decision = self._record(checkpoint_id=checkpoint_id, phase=phase, state=state, context=context)
                if state.stopped_for_review_reason or decision.action == "continue":
                    break
                continue
            result = self._task_service.run_task(
                provider=context.provider,
                radar=context.radar,
                task=task,
                radar_id=context.execution_plan.radar_id,
                budget=context.budget,
                external_budget=context.external_budget,
            )
            state.sources, state.observations, state.provider_metadata = self._task_service.merger.merge_result(
                state.sources,
                state.observations,
                state.provider_metadata,
                result,
            )
            if action in {"repair_extraction", "retry_extraction"}:
                recovered = not _has_extraction_issues(result.provider_metadata)
                state.provider_metadata = _with_extraction_recovery_record(
                    state.provider_metadata,
                    checkpoint_id=checkpoint_id,
                    phase=phase,
                    action=action,
                    attempt=attempt,
                    task_id=task.task_id,
                    outcome="recovered" if recovered else "schema_failed",
                    message=(
                        "Extraction retry returned schema-valid observations."
                        if recovered
                        else "Extraction retry still returned schema-invalid output."
                    ),
                )
            if action in {"revise_plan", "repair_extraction", "retry_extraction"} and not _has_extraction_issues(result.provider_metadata):
                state.provider_metadata = _without_extraction_issues(state.provider_metadata)
            context.executed_task_ids.append(f"{task.task_id}:adaptive-{action}-{attempt}")
            state.candidate_scope = self._task_service.eligible_candidate_names(
                radar=context.radar,
                sources=state.sources,
                observations=state.observations,
                completed_qualification_ids=context.completed_qualification_ids,
            )
            context.adaptive_actions.append({
                "checkpoint_id": checkpoint_id,
                "phase": phase,
                "action": action,
                "attempt": attempt,
                "task_id": task.task_id,
                "source_scope": task.source_scope,
                "source_ids": list(task.source_ids),
                "outcome": "executed",
                "message": f"Executed adaptive {action} for {base_task.task_id}.",
                "budget_key": context.budget.last_decision.key if context.budget.last_decision else "",
            })
            decision = self._record(checkpoint_id=checkpoint_id, phase=phase, state=state, context=context)
            if decision.action == "continue":
                state.stopped_for_review_reason = ""
                break
        return state, decision

    def _task_for_action(
        self,
        *,
        base_task: RadarExecutionTask,
        action: str,
        attempt: int,
        checkpoint_id: str,
        phase: str,
        state: RadarCheckpointRecoveryState,
    ) -> RadarExecutionTask | None:
        if action == "revise_plan":
            revised_tasks = self._plan_reviser.revise(
                base_task=base_task,
                checkpoint_id=checkpoint_id,
                phase=phase,
                attempt=attempt,
                state=state,
            )
            return revised_tasks[0] if revised_tasks else None
        return _adaptive_task(base_task, action=action, attempt=attempt)

    def _record(
        self,
        *,
        checkpoint_id: str,
        phase: str,
        state: RadarCheckpointRecoveryState,
        context: RadarCheckpointRecoveryContext,
    ) -> RadarExecutionCheckpointDecision:
        return record_execution_checkpoint(
            checkpoint_id=checkpoint_id,
            phase=phase,
            service=context.service,
            candidate_count=len(state.observations),
            sources=state.sources,
            observations=state.observations,
            provider_metadata=state.provider_metadata,
            candidate_scope=state.candidate_scope,
            coverage_checks=context.coverage_checks,
            coverage_warnings=context.coverage_warnings,
            unresolved_candidate_gaps=context.unresolved_candidate_gaps,
            budget=context.budget,
            useful_result_retry_records=context.useful_result_retry_records,
            source_obligation_decisions=context.source_obligation_decisions,
            checkpoint_decisions=context.checkpoint_decisions,
            adaptive_actions=context.adaptive_actions,
            checkpoint_warnings=context.checkpoint_warnings,
            events=context.events,
        )


def _effective_action(action: str, task: RadarExecutionTask, radar: dict[str, Any]) -> str:
    if action == "retry_same_source" and task.source_scope == "global" and _additional_sources_allowed(radar):
        return "expand_sources"
    return action


def _adaptive_task(task: RadarExecutionTask, *, action: str, attempt: int) -> RadarExecutionTask:
    if action in {"repair_extraction", "retry_extraction"}:
        suffix = (
            "Previous extraction response failed the strict schema gate. "
            "Retry the same bounded task and return only strict task-specific JSON with list fields."
        )
    else:
        suffix = "Previous attempt was weak; return source-linked candidates only."
    updates: dict[str, Any] = {
        "task_id": f"{task.task_id}:{action}-{attempt}",
        "query": f"{task.query} {suffix}",
    }
    if action == "expand_sources":
        updates.update({"source_scope": "additional", "source_ids": []})
    return task.model_copy(update=updates)


def _additional_sources_allowed(radar: dict[str, Any]) -> bool:
    policy = radar.get("global_search_policy")
    if not isinstance(policy, dict):
        return True
    return bool(policy.get("allow_additional_sources", policy.get("allow_open_web", policy.get("allow_system_sources", True))))


def _has_extraction_issues(metadata: dict[str, Any]) -> bool:
    for result in metadata.get("extraction_validation_results", []):
        if isinstance(result, dict) and str(result.get("state")) in {"extraction_schema_invalid", "evidence_linking_failed"}:
            return True
    for issue in metadata.get("extraction_validation_issues", []):
        if isinstance(issue, dict) and str(issue.get("severity")) == "error":
            return True
    return False


def _without_extraction_issues(metadata: dict[str, Any]) -> dict[str, Any]:
    result = dict(metadata)
    result["extraction_validation_results"] = []
    result["extraction_validation_issues"] = []
    result["extraction_repair_results"] = []
    return result


def _with_extraction_recovery_record(
    metadata: dict[str, Any],
    *,
    checkpoint_id: str,
    phase: str,
    action: str,
    attempt: int,
    task_id: str,
    outcome: str,
    message: str,
) -> dict[str, Any]:
    records = [
        *[dict(item) for item in metadata.get("extraction_recovery_records", []) if isinstance(item, dict)],
        {
            "checkpoint_id": checkpoint_id,
            "phase": phase,
            "action": action,
            "attempt": attempt,
            "task_id": task_id,
            "outcome": outcome,
            "message": message,
        },
    ]
    return {
        **metadata,
        "extraction_recovery_records": records,
        "extraction_repair_attempt_count": sum(1 for item in records if str(item.get("action")) == "repair_extraction"),
        "extraction_retry_attempt_count": sum(1 for item in records if str(item.get("action")) == "retry_extraction"),
        "extraction_recovery_outcome": records[-1]["outcome"] if records else "",
    }


def _record_terminal_stop(
    checkpoint_id: str,
    phase: str,
    message: str,
    context: RadarCheckpointRecoveryContext,
    *,
    reason_code: str,
    details: dict[str, Any] | None = None,
) -> None:
    payload = {
        "checkpoint_id": checkpoint_id,
        "phase": phase,
        "action": "stop_review_needed",
        "reason_code": reason_code,
        "severity": "warning",
        "message": message,
        "should_continue": False,
        "should_run_signal_search": False,
        "details": details or {},
    }
    context.checkpoint_decisions.append(payload)
    context.checkpoint_warnings.append(message)
    context.adaptive_actions.append({
        "checkpoint_id": checkpoint_id,
        "phase": phase,
        "action": "stop_review_needed",
        "reason_code": reason_code,
        "outcome": "limit_exhausted",
        "message": message,
        "details": details or {},
    })


def _extraction_recovery_stop_reason(metadata: dict[str, Any]) -> str:
    outcome = str(metadata.get("extraction_recovery_outcome") or "")
    if outcome:
        return outcome
    for attempt in reversed([item for item in metadata.get("extraction_model_attempts", []) if isinstance(item, dict)]):
        reason = str(attempt.get("reason") or attempt.get("outcome") or "")
        if reason:
            return reason
    for issue in metadata.get("extraction_validation_issues", []):
        if not isinstance(issue, dict):
            continue
        path = str(issue.get("path") or "")
        message = str(issue.get("message") or issue.get("code") or "")
        if path or message:
            return " ".join(part for part in [path, message] if part)
    return ""
