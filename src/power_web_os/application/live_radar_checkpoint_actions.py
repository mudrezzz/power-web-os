"""Apply adaptive checkpoint actions for staged Radar execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from power_web_os.application.live_radar_checkpoint_execution import record_execution_checkpoint
from power_web_os.application.live_radar_checkpoints import RadarExecutionCheckpointDecision, RadarExecutionCheckpointService
from power_web_os.application.live_radar_contracts import (
    LiveRadarPipelineEvent,
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
    WebSearchProvider,
)
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget
from power_web_os.application.live_radar_external_budget import RadarExternalCallBudget
from power_web_os.application.live_radar_staged_helpers import eligible_candidate_names, run_task
from power_web_os.application.live_radar_staged_merge import merge_result


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
    """Execute bounded adaptive actions selected by checkpoint review."""

    def __init__(self, plan_reviser: RadarExecutionPlanReviser | None = None) -> None:
        self._plan_reviser = plan_reviser or DefaultRadarExecutionPlanReviser()

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
                    state.stopped_for_review_reason = "Extraction repair limit reached before extraction recovered."
                    _record_terminal_stop(checkpoint_id, phase, state.stopped_for_review_reason, context, reason_code="extraction_repair_exhausted")
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
            result = run_task(
                provider=context.provider,
                radar=context.radar,
                task=task,
                radar_id=context.execution_plan.radar_id,
                budget=context.budget,
                external_budget=context.external_budget,
            )
            state.sources, state.observations, state.provider_metadata = merge_result(
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
            state.candidate_scope = eligible_candidate_names(
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
        "details": {},
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
    })
