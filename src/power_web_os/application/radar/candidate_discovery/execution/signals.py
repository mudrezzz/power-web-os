"""Compatibility signal-search phase for candidate discovery runs."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarPipelineEvent,
    RadarExecutionPlan,
    RadarExecutionTask,
    WebSearchProvider,
)
from power_web_os.application.live_radar_checkpoints import RadarExecutionCheckpointDecision
from power_web_os.application.live_radar_checkpoint_execution import record_execution_checkpoint
from power_web_os.application.live_radar_checkpoints import RadarExecutionCheckpointService
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget
from power_web_os.application.live_radar_external_budget import RadarExternalCallBudget
from power_web_os.application.radar_source_obligations import obligation_decisions_from_plan
from power_web_os.application.radar.candidate_discovery.planning.execution_plan import scoped_execution_task
from power_web_os.application.radar.candidate_discovery.execution.context import (
    CandidateDiscoveryExecutionContext,
    PhaseResult,
)
from power_web_os.application.radar.candidate_discovery.execution.merge import merge_result as _merge_result
from power_web_os.application.radar.candidate_discovery.execution.projection import (
    budget_decision as _budget_decision,
    not_searched_signal_observation as _not_searched_signal_observation,
    signal_planned_event as _signal_planned_event,
    signal_status_record as _signal_status_record,
)
from power_web_os.application.radar.candidate_discovery.execution.state import CandidateDiscoveryExecutionState
from power_web_os.application.radar.candidate_discovery.execution.task_runner import (
    normalized_candidates as _normalized_candidates,
    run_task as _run_task,
)
from power_web_os.application.live_radar_universe import filter_signal_result, gap_items, gap_payloads


class SignalCompatibilityPhaseExecutor:
    """Preserves legacy signal-search projection inside candidate-discovery runs."""

    def review_before_search(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> tuple[RadarExecutionCheckpointDecision, bool, PhaseResult]:
        decision, can_run_signal_search, stopped_reason = _review_before_signal_search(
            radar=context.radar,
            execution_plan=context.execution_plan,
            sources=state.sources,
            observations=state.observations,
            provider_metadata=state.provider_metadata,
            candidate_scope=state.candidate_scope,
            coverage_checks=state.coverage_checks,
            coverage_warnings=state.coverage_warnings,
            unresolved_candidate_gaps=state.unresolved_candidate_gaps,
            task_budget=context.task_budget,
            useful_result_retry_records=state.useful_result_retry_records,
            source_policy_decisions=context.source_policy_decisions,
            checkpoint_service=context.checkpoint_service,
            checkpoint_decisions=state.checkpoint_decisions,
            adaptive_actions=state.adaptive_actions,
            checkpoint_warnings=state.checkpoint_warnings,
            events=state.events,
            stopped_for_review_reason=state.stopped_for_review_reason,
        )
        state.stopped_for_review_reason = stopped_reason
        return decision, can_run_signal_search, PhaseResult(
            phase_name="before_signal_search",
            status="continue" if can_run_signal_search else "blocked",
            reason=stopped_reason,
        )

    def run(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        *,
        tasks: list[RadarExecutionTask],
        can_run_signal_search: bool,
        pre_signal_decision: RadarExecutionCheckpointDecision,
    ) -> PhaseResult:
        (
            state.sources,
            state.observations,
            state.provider_metadata,
            state.signal_task_count,
            state.signal_search_statuses,
            state.signal_candidate_scope,
        ) = _run_signal_search_stage(
            radar=context.radar,
            execution_plan=context.execution_plan,
            provider=context.provider,
            tasks=tasks,
            candidate_scope=state.candidate_scope,
            sources=state.sources,
            observations=state.observations,
            provider_metadata=state.provider_metadata,
            unresolved_candidate_gaps=state.unresolved_candidate_gaps,
            events=state.events,
            executed_task_ids=state.executed_task_ids,
            budget=context.task_budget,
            external_budget=context.external_budget,
            can_run_signal_search=can_run_signal_search,
            pre_signal_decision=pre_signal_decision,
            stopped_for_review_reason=state.stopped_for_review_reason,
        )
        return PhaseResult(phase_name="signal_search")


def _review_before_signal_search(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    sources: list[Any],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    candidate_scope: list[str],
    coverage_checks: list[dict[str, Any]],
    coverage_warnings: list[str],
    unresolved_candidate_gaps: list[dict[str, Any]],
    task_budget: RadarExecutionBudget,
    useful_result_retry_records: list[dict[str, Any]],
    source_policy_decisions: list[dict[str, Any]] | None,
    checkpoint_service: RadarExecutionCheckpointService,
    checkpoint_decisions: list[dict[str, Any]],
    adaptive_actions: list[dict[str, Any]],
    checkpoint_warnings: list[str],
    events: list[LiveRadarPipelineEvent],
    stopped_for_review_reason: str,
) -> tuple[RadarExecutionCheckpointDecision, bool, str]:
    pre_signal_source_obligations = obligation_decisions_from_plan(
        global_policy=dict(radar.get("global_search_policy") or {}),
        steps=execution_plan.tasks,
        source_policy_decisions=source_policy_decisions or [],
        source_provider_outcomes=provider_metadata.get("source_provider_outcomes", []),
        sources=sources,
        observations=observations,
    )
    pre_signal_decision = record_execution_checkpoint(
        checkpoint_id="before-signal-search",
        phase="before_signal_search",
        service=checkpoint_service,
        candidate_count=len(_normalized_candidates(radar=radar, sources=sources, observations=observations)),
        sources=sources,
        observations=observations,
        provider_metadata=provider_metadata,
        candidate_scope=candidate_scope,
        coverage_checks=coverage_checks,
        coverage_warnings=coverage_warnings,
        unresolved_candidate_gaps=unresolved_candidate_gaps,
        budget=task_budget,
        useful_result_retry_records=useful_result_retry_records,
        source_obligation_decisions=pre_signal_source_obligations,
        checkpoint_decisions=checkpoint_decisions,
        adaptive_actions=adaptive_actions,
        checkpoint_warnings=checkpoint_warnings,
        events=events,
    )
    can_run_signal_search = (
        not stopped_for_review_reason
        and pre_signal_decision.action == "continue"
        and pre_signal_decision.should_continue
        and pre_signal_decision.should_run_signal_search
    )
    if not can_run_signal_search:
        stopped_for_review_reason = stopped_for_review_reason or pre_signal_decision.message
    return pre_signal_decision, can_run_signal_search, stopped_for_review_reason


def _run_signal_search_stage(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
    tasks: list[RadarExecutionTask],
    candidate_scope: list[str],
    sources: list[Any],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    unresolved_candidate_gaps: list[dict[str, Any]],
    events: list[LiveRadarPipelineEvent],
    executed_task_ids: list[str],
    budget: RadarExecutionBudget,
    external_budget: RadarExternalCallBudget,
    can_run_signal_search: bool,
    pre_signal_decision: RadarExecutionCheckpointDecision,
    stopped_for_review_reason: str,
) -> tuple[list[Any], list[dict[str, Any]], dict[str, Any], int, list[dict[str, Any]], list[str]]:
    signal_task_count = 0
    signal_candidate_scope = list(candidate_scope)
    signal_search_statuses: list[dict[str, Any]] = []
    if can_run_signal_search:
        for task in tasks:
            for scoped_candidate_name in signal_candidate_scope:
                scoped_task = scoped_execution_task(task, candidate_scope=[scoped_candidate_name])
                events.append(_signal_planned_event(scoped_task))
                result = _run_task(
                    provider=provider,
                    radar=radar,
                    task=scoped_task,
                    radar_id=execution_plan.radar_id,
                    budget=budget,
                    external_budget=external_budget,
                )
                budget_decision = _budget_decision(result)
                if budget_decision:
                    observations.append(_not_searched_signal_observation(scoped_candidate_name, task, budget_decision))
                    signal_search_statuses.append(_signal_status_record(scoped_candidate_name, task, budget_decision))
                    continue
                result = filter_signal_result(result, allowed_candidate_names={scoped_candidate_name})
                unresolved_candidate_gaps.extend(gap_payloads(gap_items(result), origin_task_id=task.task_id))
                sources, observations, provider_metadata = _merge_result(sources, observations, provider_metadata, result)
                executed_task_ids.append(f"{task.task_id}:{scoped_candidate_name}")
                signal_search_statuses.append({
                    "candidate_name": scoped_candidate_name,
                    "signal_id": task.subject_id,
                    "task_id": task.task_id,
                    "search_status": "searched",
                    "not_searched_reason": "",
                })
                signal_task_count += 1
    else:
        for task in tasks:
            for scoped_candidate_name in signal_candidate_scope:
                decision = {
                    "state": "not_searched_policy_limited",
                    "reason": pre_signal_decision.reason_code if not stopped_for_review_reason else "stopped_for_review",
                    "message": pre_signal_decision.message if not stopped_for_review_reason else stopped_for_review_reason,
                    "key": f"checkpoint:{pre_signal_decision.checkpoint_id}",
                }
                observations.append(_not_searched_signal_observation(scoped_candidate_name, task, decision))
                signal_search_statuses.append(_signal_status_record(scoped_candidate_name, task, decision))
    return sources, observations, provider_metadata, signal_task_count, signal_search_statuses, signal_candidate_scope
