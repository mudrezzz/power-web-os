"""Discovery and initial qualification gate phase for candidate discovery."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarPipelineEvent,
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
    WebSearchProvider,
)
from power_web_os.application.live_radar_checkpoint_actions import (
    RadarCheckpointActionExecutor,
    RadarCheckpointRecoveryContext,
    RadarCheckpointRecoveryState,
)
from power_web_os.application.live_radar_checkpoint_execution import record_execution_checkpoint
from power_web_os.application.live_radar_checkpoints import RadarExecutionCheckpointService
from power_web_os.application.live_radar_cross_disambiguation import execute_cross_source_disambiguation
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget
from power_web_os.application.live_radar_external_budget import RadarExternalCallBudget
from power_web_os.application.live_radar_retrieved_candidates import candidates_from_retrieved_sources
from power_web_os.application.live_radar_useful_budget import UsefulResultBudget, run_task_with_useful_retries
from power_web_os.application.radar.candidate_discovery.execution.context import (
    CandidateDiscoveryExecutionContext,
    PhaseResult,
)
from power_web_os.application.radar.candidate_discovery.execution.gates import GatePhaseExecutor
from power_web_os.application.radar.candidate_discovery.execution.merge import merge_result as _merge_result
from power_web_os.application.radar.candidate_discovery.execution.gates import _run_qualification_gate_pass
from power_web_os.application.radar.candidate_discovery.execution.state import CandidateDiscoveryExecutionState
from power_web_os.application.radar.candidate_discovery.execution.state import limit_smoke_candidates
from power_web_os.application.radar.candidate_discovery.execution.task_runner import (
    combine_task_results as _combine_task_results,
    eligible_candidate_names as _eligible_candidate_names,
    normalized_candidates as _normalized_candidates,
    run_task as _run_task,
    task_event as _task_event,
    tasks_for_stage as _tasks_for_stage,
)
from power_web_os.application.live_radar_universe import candidate_name_set


class DiscoveryPhaseExecutor:
    """Runs discovery, retrieval-based candidate extraction, first checkpoint, and gates."""

    def __init__(self, gate_executor: GatePhaseExecutor | None = None) -> None:
        self._gate_executor = gate_executor or GatePhaseExecutor()

    def run(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        discovery_tasks: list[RadarExecutionTask],
    ) -> tuple[list[RadarExecutionTask], PhaseResult]:
        (
            state.sources,
            state.observations,
            state.provider_metadata,
            state.candidate_scope,
            gate_tasks,
            state.stopped_for_review_reason,
        ) = _run_discovery_and_gate_phase(
            radar=context.radar,
            execution_plan=context.execution_plan,
            provider=context.provider,
            discovery_tasks=discovery_tasks,
            checkpoint_executor=context.checkpoint_executor,
            checkpoint_service=context.checkpoint_service,
            sources=state.sources,
            observations=state.observations,
            provider_metadata=state.provider_metadata,
            events=state.events,
            executed_task_ids=state.executed_task_ids,
            completed_qualification_ids=state.completed_qualification_ids,
            gate_results=state.gate_results,
            candidate_scope=state.candidate_scope,
            coverage_checks=state.coverage_checks,
            coverage_warnings=state.coverage_warnings,
            unresolved_candidate_gaps=state.unresolved_candidate_gaps,
            useful_result_retry_records=state.useful_result_retry_records,
            useful_result_warnings=state.useful_result_warnings,
            checkpoint_decisions=state.checkpoint_decisions,
            adaptive_actions=state.adaptive_actions,
            checkpoint_warnings=state.checkpoint_warnings,
            task_budget=context.task_budget,
            external_budget=context.external_budget,
            useful_budget=context.useful_budget,
            search_expansion_service=context.search_expansion_service,
            work_scheduler=context.work_scheduler,
        )
        return gate_tasks, PhaseResult(
            phase_name="discovery",
            status="stopped_for_review" if state.stopped_for_review_reason else "completed",
            reason=state.stopped_for_review_reason,
        )

    def extract_retrieved_candidates(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> PhaseResult:
        state.sources, state.observations, state.provider_metadata, state.candidate_scope = _extract_retrieved_candidates(
            radar=context.radar,
            sources=state.sources,
            observations=state.observations,
            provider_metadata=state.provider_metadata,
            candidate_scope=state.candidate_scope,
            completed_qualification_ids=state.completed_qualification_ids,
            events=state.events,
            smoke_candidate_limit=context.external_budget.settings.smoke_max_candidates,
        )
        return PhaseResult(phase_name="retrieved_candidate_extraction")


def _run_discovery_and_gate_phase(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
    discovery_tasks: list[RadarExecutionTask],
    checkpoint_executor: RadarCheckpointActionExecutor,
    checkpoint_service: RadarExecutionCheckpointService,
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    events: list[LiveRadarPipelineEvent],
    executed_task_ids: list[str],
    completed_qualification_ids: list[str],
    gate_results: list[dict[str, Any]],
    candidate_scope: list[str],
    coverage_checks: list[dict[str, Any]],
    coverage_warnings: list[str],
    unresolved_candidate_gaps: list[dict[str, Any]],
    useful_result_retry_records: list[dict[str, Any]],
    useful_result_warnings: list[str],
    checkpoint_decisions: list[dict[str, Any]],
    adaptive_actions: list[dict[str, Any]],
    checkpoint_warnings: list[str],
    task_budget: RadarExecutionBudget,
    external_budget: RadarExternalCallBudget,
    useful_budget: UsefulResultBudget,
    search_expansion_service: Any,
    work_scheduler: Any,
) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any], list[str], list[RadarExecutionTask], str]:
    for task in discovery_tasks:
        result, run_ids, retry_records, retry_warnings = run_task_with_useful_retries(
            task=task,
            useful_budget=useful_budget,
            execution_id=task.task_id,
            run_task=lambda current_task: _run_task(
                provider=provider,
                radar=radar,
                task=current_task,
                radar_id=execution_plan.radar_id,
                budget=task_budget,
                external_budget=external_budget,
            ),
            combine_results=_combine_task_results,
        )
        sources, observations, provider_metadata = _merge_result(sources, observations, provider_metadata, result)
        executed_task_ids.extend(run_ids)
        useful_result_retry_records.extend(retry_records)
        useful_result_warnings.extend(retry_warnings)
        completed_qualification_ids.append(task.subject_id)
        candidate_scope = _eligible_candidate_names(
            radar=radar,
            sources=sources,
            observations=observations,
            completed_qualification_ids=completed_qualification_ids,
        )
        events.append(_task_event(task, result, "qualification_discovery_planned"))

    sources, observations, provider_metadata, candidate_scope = _extract_retrieved_candidates(
        radar=radar,
        sources=sources,
        observations=observations,
        provider_metadata=provider_metadata,
        candidate_scope=candidate_scope,
        completed_qualification_ids=completed_qualification_ids,
        events=events,
        smoke_candidate_limit=external_budget.settings.smoke_max_candidates,
    )
    sources, observations, provider_metadata = execute_cross_source_disambiguation(
        radar=radar,
        execution_plan=execution_plan,
        provider=provider,
        sources=sources,
        observations=observations,
        provider_metadata=provider_metadata,
        budget=task_budget,
        external_budget=external_budget,
        events=events,
        executed_task_ids=executed_task_ids,
    )
    candidate_scope = _eligible_candidate_names(
        radar=radar,
        sources=sources,
        observations=observations,
        completed_qualification_ids=completed_qualification_ids,
    )
    candidate_scope = limit_smoke_candidates(candidate_scope, external_budget.settings.smoke_max_candidates)

    recovery_state, _ = checkpoint_executor.recover(
        checkpoint_id="after-discovery",
        phase="after_discovery",
        tasks=discovery_tasks,
        state=RadarCheckpointRecoveryState(sources, observations, provider_metadata, candidate_scope),
        context=RadarCheckpointRecoveryContext(
            radar=radar,
            execution_plan=execution_plan,
            provider=provider,
            service=checkpoint_service,
            budget=task_budget,
            completed_qualification_ids=completed_qualification_ids,
            checkpoint_decisions=checkpoint_decisions,
            adaptive_actions=adaptive_actions,
            checkpoint_warnings=checkpoint_warnings,
            events=events,
            executed_task_ids=executed_task_ids,
            useful_result_retry_records=useful_result_retry_records,
            external_budget=external_budget,
            search_expansion_service=search_expansion_service,
            work_scheduler=work_scheduler,
            smoke_candidate_limit=external_budget.settings.smoke_max_candidates,
        ),
    )
    sources, observations = recovery_state.sources, recovery_state.observations
    provider_metadata, candidate_scope = recovery_state.provider_metadata, recovery_state.candidate_scope
    candidate_scope = limit_smoke_candidates(candidate_scope, external_budget.settings.smoke_max_candidates)
    stopped_for_review_reason = recovery_state.stopped_for_review_reason

    terminal_stop_after_discovery = bool(stopped_for_review_reason)
    gate_tasks = [] if terminal_stop_after_discovery else _tasks_for_stage(execution_plan, "qualification_gate")
    sources, observations, provider_metadata, candidate_scope = _run_qualification_gate_pass(
        radar=radar,
        execution_plan=execution_plan,
        provider=provider,
        tasks=gate_tasks,
        sources=sources,
        observations=observations,
        provider_metadata=provider_metadata,
        candidate_scope=candidate_scope,
        completed_qualification_ids=completed_qualification_ids,
        gate_results=gate_results,
        events=events,
        executed_task_ids=executed_task_ids,
        budget=task_budget,
        external_budget=external_budget,
    )
    candidate_scope = limit_smoke_candidates(candidate_scope, external_budget.settings.smoke_max_candidates)

    record_execution_checkpoint(
        checkpoint_id="after-qualification-gates",
        phase="after_qualification_gates",
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
        source_obligation_decisions=[],
        checkpoint_decisions=checkpoint_decisions,
        adaptive_actions=adaptive_actions,
        checkpoint_warnings=checkpoint_warnings,
        events=events,
    )
    return sources, observations, provider_metadata, candidate_scope, gate_tasks, stopped_for_review_reason


def _extract_retrieved_candidates(
    *,
    radar: dict[str, Any],
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    candidate_scope: list[str],
    completed_qualification_ids: list[str],
    events: list[LiveRadarPipelineEvent],
    smoke_candidate_limit: int | None,
) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any], list[str]]:
    retrieved_candidates = candidates_from_retrieved_sources(
        radar=radar,
        provider_metadata=provider_metadata,
        known_candidate_names=candidate_name_set(observations),
        known_source_refs={source.evidence_ref for source in sources if source.evidence_ref},
    )
    if not retrieved_candidates.candidate_observations:
        return sources, observations, provider_metadata, candidate_scope
    merged_sources, merged_observations, merged_metadata = _merge_result(sources, observations, provider_metadata, retrieved_candidates)
    merged_scope = _eligible_candidate_names(
        radar=radar,
        sources=merged_sources,
        observations=merged_observations,
        completed_qualification_ids=completed_qualification_ids,
    )
    merged_scope = limit_smoke_candidates(merged_scope, smoke_candidate_limit)
    events.append(LiveRadarPipelineEvent(
        event_type="candidate_universe_extracted_from_retrieval",
        phase="collection",
        actor="application",
        node_name="retrieved_candidate_extraction",
        visibility="operator",
        summary=f"Extracted {len(retrieved_candidates.candidate_observations)} review-needed candidates from retrieved sources.",
        payload={
            "candidate_observation_count": len(retrieved_candidates.candidate_observations),
            "source_count": len(retrieved_candidates.sources),
            "extractions": retrieved_candidates.provider_metadata.get("retrieved_candidate_extractions", []),
        },
        source_refs=[source.evidence_ref for source in retrieved_candidates.sources if source.evidence_ref],
    ))
    return merged_sources, merged_observations, merged_metadata, merged_scope
