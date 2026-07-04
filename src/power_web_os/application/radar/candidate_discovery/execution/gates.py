"""Qualification gate phase for candidate discovery staged execution."""

from __future__ import annotations

from power_web_os.application.radar.candidate_discovery.contracts import RadarExecutionTask
from power_web_os.application.radar.candidate_discovery.execution.context import CandidateDiscoveryExecutionContext
from power_web_os.application.radar.candidate_discovery.execution.state import CandidateDiscoveryExecutionState
from power_web_os.application.radar.candidate_discovery.execution.task_runner import TaskExecutionService


class GatePhaseExecutor:
    """Runs qualification gate tasks and writes gate outputs back to execution state.

    Owns:
    - Qualification gate pass execution for an explicit task list and candidate
      scope.

    Does not own:
    - Discovery task selection, coverage iteration, expansion scheduling, or
      final projection.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#gatephaseexecutor
    """

    phase_name = "qualification_gate"

    def __init__(self, task_service: TaskExecutionService | None = None) -> None:
        self._task_service = task_service or TaskExecutionService()

    def run(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        tasks: list[RadarExecutionTask],
        candidate_scope: list[str] | None = None,
    ) -> None:
        state.sources, state.observations, state.provider_metadata, state.candidate_scope = self._task_service.run_gate_pass(
            radar=context.radar,
            execution_plan=context.execution_plan,
            provider=context.provider,
            tasks=tasks,
            sources=state.sources,
            observations=state.observations,
            provider_metadata=state.provider_metadata,
            candidate_scope=state.candidate_scope if candidate_scope is None else candidate_scope,
            completed_qualification_ids=state.completed_qualification_ids,
            gate_results=state.gate_results,
            events=state.events,
            executed_task_ids=state.executed_task_ids,
            budget=context.task_budget,
            external_budget=context.external_budget,
        )
