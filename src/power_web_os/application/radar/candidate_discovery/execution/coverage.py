"""Iterative coverage phase for candidate discovery staged execution."""

from __future__ import annotations

from power_web_os.application.radar.candidate_discovery.checkpoints.recovery import (
    RadarCheckpointRecoveryContext,
    RadarCheckpointRecoveryState,
)
from power_web_os.application.radar.candidate_discovery.universe import (
    candidate_name_set,
    coverage_risk,
    coverage_warnings as coverage_warning_messages,
    gap_items,
    gap_observations,
    gap_payloads,
)
from power_web_os.application.radar.candidate_discovery.execution.useful_budget import run_task_with_useful_retries
from power_web_os.application.radar.candidate_discovery.contracts import (
    RadarCoverageCheckRecord,
    RadarExecutionTask,
    WebSearchProviderResult,
)
from power_web_os.application.radar.candidate_discovery.execution.context import (
    CandidateDiscoveryExecutionContext,
    PhaseResult,
)
from power_web_os.application.radar.candidate_discovery.execution.gates import GatePhaseExecutor
from power_web_os.application.radar.candidate_discovery.execution.state import (
    CandidateDiscoveryExecutionState,
    SmokeLimitPolicy,
)
from power_web_os.application.radar.candidate_discovery.execution.task_runner import TaskExecutionService
from power_web_os.application.radar.candidate_discovery.planning.execution_plan import scoped_execution_task


class CoveragePhaseExecutor:
    """Runs iterative coverage tasks and after-coverage checkpoint recovery.

    Owns:
    - Coverage iterations, coverage checks, gap merge, gates for newly found
      candidate names, and after-coverage checkpoint recovery.

    Does not own:
    - Initial discovery, expansion target selection, final candidate-universe
      projection, or provider adapter implementation.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#coveragephaseexecutor
    """

    phase_name = "coverage"

    def __init__(
        self,
        gate_executor: GatePhaseExecutor | None = None,
        task_service: TaskExecutionService | None = None,
        smoke_policy: SmokeLimitPolicy | None = None,
    ) -> None:
        self._task_service = task_service or TaskExecutionService()
        self._smoke_policy = smoke_policy or SmokeLimitPolicy()
        self._gate_executor = gate_executor or GatePhaseExecutor(self._task_service)

    def run(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        *,
        discovery_tasks: list[RadarExecutionTask],
        gate_tasks: list[RadarExecutionTask],
        coverage_tasks: list[RadarExecutionTask],
    ) -> PhaseResult:
        state.discovery_iteration_count = 0
        for iteration in range(1, context.max_discovery_iterations + 1):
            if not coverage_tasks or self._candidate_universe_is_full(context, state):
                break
            state.discovery_iteration_count = iteration
            new_names = self._run_coverage_iteration(context, state, coverage_tasks, iteration)
            if not new_names:
                break
            self._run_gates_for_new_names(context, state, discovery_tasks, gate_tasks, new_names)
        return PhaseResult(phase_name="coverage")

    def recover_after_coverage(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        coverage_tasks: list[RadarExecutionTask],
    ) -> PhaseResult:
        recovery_state, _ = context.checkpoint_executor.recover(
            checkpoint_id="after-coverage",
            phase="after_coverage",
            tasks=coverage_tasks,
            state=RadarCheckpointRecoveryState(
                state.sources,
                state.observations,
                state.provider_metadata,
                state.candidate_scope,
            ),
            context=RadarCheckpointRecoveryContext(
                radar=context.radar,
                execution_plan=context.execution_plan,
                provider=context.provider,
                service=context.checkpoint_service,
                budget=context.task_budget,
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
                external_budget=context.external_budget,
                search_expansion_service=context.search_expansion_service,
                work_scheduler=context.work_scheduler,
                smoke_candidate_limit=context.external_budget.settings.smoke_max_candidates,
            ),
        )
        state.sources = recovery_state.sources
        state.observations = recovery_state.observations
        state.provider_metadata = recovery_state.provider_metadata
        state.candidate_scope = self._limit_candidates(context, recovery_state.candidate_scope)
        state.stopped_for_review_reason = (
            state.stopped_for_review_reason or recovery_state.stopped_for_review_reason
        )
        return PhaseResult(
            phase_name="coverage_recovery",
            status="stopped_for_review" if recovery_state.stopped_for_review_reason else "completed",
            reason=recovery_state.stopped_for_review_reason,
        )

    def _run_coverage_iteration(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        coverage_tasks: list[RadarExecutionTask],
        iteration: int,
    ) -> set[str]:
        names_before = candidate_name_set(state.observations)
        iteration_new_names: set[str] = set()
        for task in coverage_tasks:
            scoped_task = scoped_execution_task(task, candidate_scope=state.candidate_scope)
            result = self._execute_coverage_task(context, state, task, scoped_task, iteration)
            names_after = candidate_name_set(state.observations)
            new_names = names_after - names_before
            iteration_new_names.update(new_names)
            self._record_coverage_check(state, scoped_task, task, result, iteration, new_names)
            names_before = names_after
        return iteration_new_names

    def _execute_coverage_task(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        task: RadarExecutionTask,
        scoped_task: RadarExecutionTask,
        iteration: int,
    ) -> WebSearchProviderResult:
        result, run_ids, retry_records, retry_warnings = run_task_with_useful_retries(
            task=scoped_task,
            useful_budget=context.useful_budget,
            execution_id=f"{task.task_id}:iteration-{iteration}",
            run_task=lambda current_task: self._task_service.run_task(
                provider=context.provider,
                radar=context.radar,
                task=current_task,
                radar_id=context.execution_plan.radar_id,
                budget=context.task_budget,
                external_budget=context.external_budget,
            ),
            combine_results=self._task_service.combine_task_results,
        )
        result = self._result_with_gap_observations(result, task)
        state.sources, state.observations, state.provider_metadata = self._task_service.merger.merge_result(
            state.sources,
            state.observations,
            state.provider_metadata,
            result,
        )
        state.executed_task_ids.extend(run_ids)
        state.useful_result_retry_records.extend(retry_records)
        state.useful_result_warnings.extend(retry_warnings)
        state.unresolved_candidate_gaps.extend(gap_payloads(gap_items(result), origin_task_id=task.task_id))
        return result

    def _run_gates_for_new_names(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        discovery_tasks: list[RadarExecutionTask],
        gate_tasks: list[RadarExecutionTask],
        new_names: set[str],
    ) -> None:
        new_candidate_scope = self._task_service.candidate_names_matching(state.observations, new_names)
        self._gate_executor.run(context, state, [*discovery_tasks, *gate_tasks], candidate_scope=new_candidate_scope)
        state.candidate_scope = self._candidate_scope(context, state)

    def _record_coverage_check(
        self,
        state: CandidateDiscoveryExecutionState,
        scoped_task: RadarExecutionTask,
        task: RadarExecutionTask,
        result: WebSearchProviderResult,
        iteration: int,
        new_names: set[str],
    ) -> None:
        gaps = gap_items(result)
        warnings = coverage_warning_messages(result)
        state.coverage_warnings.extend(warnings)
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
        state.coverage_checks.append(coverage_record)
        state.events.append(self._task_service.events.task_event(
            scoped_task,
            result,
            "coverage_warning" if warnings else "candidate_universe_discovered",
            payload=coverage_record,
        ))

    @staticmethod
    def _result_with_gap_observations(
        result: WebSearchProviderResult,
        task: RadarExecutionTask,
    ) -> WebSearchProviderResult:
        gaps = gap_items(result)
        return result.model_copy(update={
            "candidate_observations": [
                *result.candidate_observations,
                *gap_observations(gaps, origin_task_id=task.task_id),
            ],
        })

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
        return self._limit_candidates(context, scope)

    def _candidate_universe_is_full(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> bool:
        candidate_count = len(self._task_service.normalized_candidates(
            radar=context.radar,
            sources=state.sources,
            observations=state.observations,
        ))
        if candidate_count < context.max_candidate_universe_size:
            return False
        state.coverage_warnings.append(f"Candidate universe reached max size {context.max_candidate_universe_size}.")
        return True

    def _limit_candidates(self, context: CandidateDiscoveryExecutionContext, candidate_names: list[str]) -> list[str]:
        return self._smoke_policy.limit_candidates(
            candidate_names,
            context.external_budget.settings.smoke_max_candidates,
        )
