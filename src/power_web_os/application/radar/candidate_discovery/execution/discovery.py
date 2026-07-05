"""Discovery and initial qualification gate phase for candidate discovery."""

from __future__ import annotations

from power_web_os.application.radar.candidate_discovery.checkpoints.recovery import (
    RadarCheckpointRecoveryContext,
    RadarCheckpointRecoveryState,
)
from power_web_os.application.radar.candidate_discovery.checkpoints.recording import record_execution_checkpoint
from power_web_os.application.radar.candidate_discovery.universe.cross_source_disambiguation import execute_cross_source_disambiguation
from power_web_os.application.radar.candidate_discovery.universe.retrieved_candidates import candidates_from_retrieved_sources
from power_web_os.application.radar.candidate_discovery.execution.useful_budget import run_task_with_useful_retries
from power_web_os.application.radar.candidate_discovery.universe import candidate_name_set
from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarPipelineEvent,
    RadarExecutionTask,
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


class DiscoveryPhaseExecutor:
    """Runs discovery, retrieval extraction, first checkpoint recovery, and initial gates.

    Owns:
    - Initial discovery tasks, retrieved-candidate extraction, first checkpoint
      recovery, initial gate execution, and candidate-scope refresh.

    Does not own:
    - Coverage iteration, target-aware expansion, final metadata projection, or
      provider adapter implementation.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#discoveryphaseexecutor
    """

    phase_name = "discovery"

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
        discovery_tasks: list[RadarExecutionTask],
    ) -> tuple[list[RadarExecutionTask], PhaseResult]:
        self._run_discovery_tasks(context, state, discovery_tasks)
        self.extract_retrieved_candidates(context, state)
        self._execute_cross_source_disambiguation(context, state)
        self._recover_after_discovery(context, state, discovery_tasks)
        gate_tasks = [] if state.stopped_for_review_reason else self._task_service.tasks_for_stage(
            context.execution_plan, "qualification_gate"
        )
        self._gate_executor.run(context, state, gate_tasks)
        self._apply_smoke_limit(context, state)
        self._record_gate_checkpoint(context, state)
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
        retrieved_candidates = candidates_from_retrieved_sources(
            radar=context.radar,
            provider_metadata=state.provider_metadata,
            known_candidate_names=candidate_name_set(state.observations),
            known_source_refs={source.evidence_ref for source in state.sources if source.evidence_ref},
        )
        if not retrieved_candidates.candidate_observations:
            return PhaseResult(phase_name="retrieved_candidate_extraction")

        state.sources, state.observations, state.provider_metadata = self._task_service.merger.merge_result(
            state.sources,
            state.observations,
            state.provider_metadata,
            retrieved_candidates,
        )
        state.candidate_scope = self._candidate_scope(context, state)
        self._append_retrieved_candidate_event(state, retrieved_candidates)
        return PhaseResult(phase_name="retrieved_candidate_extraction")

    def _run_discovery_tasks(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        discovery_tasks: list[RadarExecutionTask],
    ) -> None:
        for task in discovery_tasks:
            result, run_ids, retry_records, retry_warnings = run_task_with_useful_retries(
                task=task,
                useful_budget=context.useful_budget,
                execution_id=task.task_id,
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
            state.sources, state.observations, state.provider_metadata = self._task_service.merger.merge_result(
                state.sources,
                state.observations,
                state.provider_metadata,
                result,
            )
            state.executed_task_ids.extend(run_ids)
            state.useful_result_retry_records.extend(retry_records)
            state.useful_result_warnings.extend(retry_warnings)
            state.completed_qualification_ids.append(task.subject_id)
            state.candidate_scope = self._candidate_scope(context, state)
            state.events.append(self._task_service.events.task_event(task, result, "qualification_discovery_planned"))

    def _execute_cross_source_disambiguation(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> None:
        state.sources, state.observations, state.provider_metadata = execute_cross_source_disambiguation(
            radar=context.radar,
            execution_plan=context.execution_plan,
            provider=context.provider,
            sources=state.sources,
            observations=state.observations,
            provider_metadata=state.provider_metadata,
            budget=context.task_budget,
            external_budget=context.external_budget,
            events=state.events,
            executed_task_ids=state.executed_task_ids,
        )
        state.candidate_scope = self._candidate_scope(context, state)

    def _recover_after_discovery(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        discovery_tasks: list[RadarExecutionTask],
    ) -> None:
        recovery_state, _ = context.checkpoint_executor.recover(
            checkpoint_id="after-discovery",
            phase="after_discovery",
            tasks=discovery_tasks,
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
        state.stopped_for_review_reason = recovery_state.stopped_for_review_reason

    def _record_gate_checkpoint(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> None:
        record_execution_checkpoint(
            checkpoint_id="after-qualification-gates",
            phase="after_qualification_gates",
            service=context.checkpoint_service,
            candidate_count=len(self._task_service.normalized_candidates(
                radar=context.radar,
                sources=state.sources,
                observations=state.observations,
            )),
            sources=state.sources,
            observations=state.observations,
            provider_metadata=state.provider_metadata,
            candidate_scope=state.candidate_scope,
            coverage_checks=state.coverage_checks,
            coverage_warnings=state.coverage_warnings,
            unresolved_candidate_gaps=state.unresolved_candidate_gaps,
            budget=context.task_budget,
            useful_result_retry_records=state.useful_result_retry_records,
            source_obligation_decisions=[],
            checkpoint_decisions=state.checkpoint_decisions,
            adaptive_actions=state.adaptive_actions,
            checkpoint_warnings=state.checkpoint_warnings,
            events=state.events,
        )

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

    def _limit_candidates(self, context: CandidateDiscoveryExecutionContext, candidate_names: list[str]) -> list[str]:
        return self._smoke_policy.limit_candidates(
            candidate_names,
            context.external_budget.settings.smoke_max_candidates,
        )

    def _apply_smoke_limit(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> None:
        state.candidate_scope = self._limit_candidates(context, state.candidate_scope)

    @staticmethod
    def _append_retrieved_candidate_event(
        state: CandidateDiscoveryExecutionState,
        retrieved_candidates: object,
    ) -> None:
        state.events.append(LiveRadarPipelineEvent(
            event_type="candidate_universe_extracted_from_retrieval",
            phase="collection",
            actor="application",
            node_name="retrieved_candidate_extraction",
            visibility="operator",
            summary=(
                "Extracted "
                f"{len(retrieved_candidates.candidate_observations)} review-needed candidates from retrieved sources."
            ),
            payload={
                "candidate_observation_count": len(retrieved_candidates.candidate_observations),
                "source_count": len(retrieved_candidates.sources),
                "extractions": retrieved_candidates.provider_metadata.get("retrieved_candidate_extractions", []),
            },
            source_refs=[source.evidence_ref for source in retrieved_candidates.sources if source.evidence_ref],
        ))
