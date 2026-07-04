"""Iterative coverage phase for candidate discovery staged execution."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarPipelineEvent,
    RadarCoverageCheckRecord,
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
from power_web_os.application.live_radar_checkpoints import RadarExecutionCheckpointService
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget
from power_web_os.application.live_radar_external_budget import RadarExternalCallBudget
from power_web_os.application.live_radar_useful_budget import UsefulResultBudget, run_task_with_useful_retries
from power_web_os.application.radar.candidate_discovery.planning.execution_plan import scoped_execution_task
from power_web_os.application.radar.candidate_discovery.execution.context import (
    CandidateDiscoveryExecutionContext,
    PhaseResult,
)
from power_web_os.application.radar.candidate_discovery.execution.gates import _run_qualification_gate_pass
from power_web_os.application.radar.candidate_discovery.execution.merge import merge_result as _merge_result
from power_web_os.application.radar.candidate_discovery.execution.state import CandidateDiscoveryExecutionState
from power_web_os.application.radar.candidate_discovery.execution.state import limit_smoke_candidates
from power_web_os.application.radar.candidate_discovery.execution.task_runner import (
    candidate_names_matching as _candidate_names_matching,
    combine_task_results as _combine_task_results,
    eligible_candidate_names as _eligible_candidate_names,
    normalized_candidates as _normalized_candidates,
    run_task as _run_task,
    task_event as _task_event,
)
from power_web_os.application.live_radar_universe import (
    candidate_name_set,
    coverage_risk,
    coverage_warnings as coverage_warning_messages,
    gap_items,
    gap_observations,
    gap_payloads,
)


class CoveragePhaseExecutor:
    """Runs iterative coverage tasks and after-coverage checkpoint recovery."""

    def run(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        *,
        discovery_tasks: list[RadarExecutionTask],
        gate_tasks: list[RadarExecutionTask],
        coverage_tasks: list[RadarExecutionTask],
    ) -> PhaseResult:
        (
            state.sources,
            state.observations,
            state.provider_metadata,
            state.candidate_scope,
            state.discovery_iteration_count,
        ) = _run_coverage_phase(
            radar=context.radar,
            execution_plan=context.execution_plan,
            provider=context.provider,
            discovery_tasks=discovery_tasks,
            gate_tasks=gate_tasks,
            coverage_tasks=coverage_tasks,
            sources=state.sources,
            observations=state.observations,
            provider_metadata=state.provider_metadata,
            candidate_scope=state.candidate_scope,
            completed_qualification_ids=state.completed_qualification_ids,
            gate_results=state.gate_results,
            coverage_checks=state.coverage_checks,
            unresolved_candidate_gaps=state.unresolved_candidate_gaps,
            coverage_warnings=state.coverage_warnings,
            events=state.events,
            executed_task_ids=state.executed_task_ids,
            useful_result_retry_records=state.useful_result_retry_records,
            useful_result_warnings=state.useful_result_warnings,
            task_budget=context.task_budget,
            external_budget=context.external_budget,
            useful_budget=context.useful_budget,
            max_discovery_iterations=context.max_discovery_iterations,
            max_candidate_universe_size=context.max_candidate_universe_size,
        )
        return PhaseResult(phase_name="coverage")

    def recover_after_coverage(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        coverage_tasks: list[RadarExecutionTask],
    ) -> PhaseResult:
        (
            state.sources,
            state.observations,
            state.provider_metadata,
            state.candidate_scope,
            recovery_stop_reason,
        ) = _recover_after_coverage(
            checkpoint_executor=context.checkpoint_executor,
            checkpoint_service=context.checkpoint_service,
            radar=context.radar,
            execution_plan=context.execution_plan,
            provider=context.provider,
            coverage_tasks=coverage_tasks,
            sources=state.sources,
            observations=state.observations,
            provider_metadata=state.provider_metadata,
            candidate_scope=state.candidate_scope,
            completed_qualification_ids=state.completed_qualification_ids,
            checkpoint_decisions=state.checkpoint_decisions,
            adaptive_actions=state.adaptive_actions,
            checkpoint_warnings=state.checkpoint_warnings,
            events=state.events,
            executed_task_ids=state.executed_task_ids,
            coverage_checks=state.coverage_checks,
            coverage_warnings=state.coverage_warnings,
            unresolved_candidate_gaps=state.unresolved_candidate_gaps,
            useful_result_retry_records=state.useful_result_retry_records,
            task_budget=context.task_budget,
            external_budget=context.external_budget,
            search_expansion_service=context.search_expansion_service,
            work_scheduler=context.work_scheduler,
        )
        state.stopped_for_review_reason = state.stopped_for_review_reason or recovery_stop_reason
        return PhaseResult(
            phase_name="coverage_recovery",
            status="stopped_for_review" if recovery_stop_reason else "completed",
            reason=recovery_stop_reason,
        )


def _run_coverage_phase(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
    discovery_tasks: list[RadarExecutionTask],
    gate_tasks: list[RadarExecutionTask],
    coverage_tasks: list[RadarExecutionTask],
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    candidate_scope: list[str],
    completed_qualification_ids: list[str],
    gate_results: list[dict[str, Any]],
    coverage_checks: list[dict[str, Any]],
    unresolved_candidate_gaps: list[dict[str, Any]],
    coverage_warnings: list[str],
    events: list[LiveRadarPipelineEvent],
    executed_task_ids: list[str],
    useful_result_retry_records: list[dict[str, Any]],
    useful_result_warnings: list[str],
    task_budget: RadarExecutionBudget,
    external_budget: RadarExternalCallBudget,
    useful_budget: UsefulResultBudget,
    max_discovery_iterations: int,
    max_candidate_universe_size: int,
) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any], list[str], int]:
    discovery_iteration_count = 0
    for iteration in range(1, max_discovery_iterations + 1):
        if not coverage_tasks:
            break
        if len(_normalized_candidates(radar=radar, sources=sources, observations=observations)) >= max_candidate_universe_size:
            coverage_warnings.append(f"Candidate universe reached max size {max_candidate_universe_size}.")
            break
        discovery_iteration_count = iteration
        names_before = candidate_name_set(observations)
        iteration_new_names: set[str] = set()
        for task in coverage_tasks:
            scoped_task = scoped_execution_task(task, candidate_scope=candidate_scope)
            result, run_ids, retry_records, retry_warnings = run_task_with_useful_retries(
                task=scoped_task,
                useful_budget=useful_budget,
                execution_id=f"{task.task_id}:iteration-{iteration}",
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
            gaps = gap_items(result)
            result = result.model_copy(update={
                "candidate_observations": [
                    *result.candidate_observations,
                    *gap_observations(gaps, origin_task_id=task.task_id),
                ],
            })
            sources, observations, provider_metadata = _merge_result(sources, observations, provider_metadata, result)
            executed_task_ids.extend(run_ids)
            useful_result_retry_records.extend(retry_records)
            useful_result_warnings.extend(retry_warnings)
            names_after = candidate_name_set(observations)
            new_names = names_after - names_before
            iteration_new_names.update(new_names)
            unresolved_candidate_gaps.extend(gap_payloads(gaps, origin_task_id=task.task_id))
            warnings = coverage_warning_messages(result)
            coverage_warnings.extend(warnings)
            coverage_record = RadarCoverageCheckRecord(
                task_id=task.task_id,
                iteration=iteration,
                source_count=len(result.sources),
                candidate_observation_count=len(result.candidate_observations),
                new_candidate_count=len(new_names),
                gap_count=len(gaps),
                completeness_risk=coverage_risk(result),  # type: ignore[arg-type]
                warnings=warnings,
            ).model_dump()
            coverage_checks.append(coverage_record)
            events.append(_task_event(
                scoped_task,
                result,
                "coverage_warning" if warnings else "candidate_universe_discovered",
                payload=coverage_record,
            ))
            names_before = names_after

        if not iteration_new_names:
            break
        new_candidate_scope = _candidate_names_matching(observations, iteration_new_names)
        sources, observations, provider_metadata, _ = _run_qualification_gate_pass(
            radar=radar,
            execution_plan=execution_plan,
            provider=provider,
            tasks=[*discovery_tasks, *gate_tasks],
            sources=sources,
            observations=observations,
            provider_metadata=provider_metadata,
            candidate_scope=new_candidate_scope,
            completed_qualification_ids=completed_qualification_ids,
            gate_results=gate_results,
            events=events,
            executed_task_ids=executed_task_ids,
            budget=task_budget,
            external_budget=external_budget,
        )
        candidate_scope = _eligible_candidate_names(
            radar=radar,
            sources=sources,
            observations=observations,
            completed_qualification_ids=completed_qualification_ids,
        )
        candidate_scope = limit_smoke_candidates(candidate_scope, external_budget.settings.smoke_max_candidates)
    return sources, observations, provider_metadata, candidate_scope, discovery_iteration_count


def _recover_after_coverage(
    *,
    checkpoint_executor: RadarCheckpointActionExecutor,
    checkpoint_service: RadarExecutionCheckpointService,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
    coverage_tasks: list[RadarExecutionTask],
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    candidate_scope: list[str],
    completed_qualification_ids: list[str],
    checkpoint_decisions: list[dict[str, Any]],
    adaptive_actions: list[dict[str, Any]],
    checkpoint_warnings: list[str],
    events: list[LiveRadarPipelineEvent],
    executed_task_ids: list[str],
    coverage_checks: list[dict[str, Any]],
    coverage_warnings: list[str],
    unresolved_candidate_gaps: list[dict[str, Any]],
    useful_result_retry_records: list[dict[str, Any]],
    task_budget: RadarExecutionBudget,
    external_budget: RadarExternalCallBudget,
    search_expansion_service: Any,
    work_scheduler: Any,
) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any], list[str], str]:
    recovery_state, _ = checkpoint_executor.recover(
        checkpoint_id="after-coverage",
        phase="after_coverage",
        tasks=coverage_tasks,
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
            coverage_checks=coverage_checks,
            coverage_warnings=coverage_warnings,
            unresolved_candidate_gaps=unresolved_candidate_gaps,
            useful_result_retry_records=useful_result_retry_records,
            external_budget=external_budget,
            search_expansion_service=search_expansion_service,
            work_scheduler=work_scheduler,
            smoke_candidate_limit=external_budget.settings.smoke_max_candidates,
        ),
    )
    candidate_scope = limit_smoke_candidates(recovery_state.candidate_scope, external_budget.settings.smoke_max_candidates)
    return (
        recovery_state.sources,
        recovery_state.observations,
        recovery_state.provider_metadata,
        candidate_scope,
        recovery_state.stopped_for_review_reason,
    )
