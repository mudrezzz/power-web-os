"""Qualification gate phase for candidate discovery staged execution."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarPipelineEvent,
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
    WebSearchProvider,
)
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget
from power_web_os.application.live_radar_external_budget import RadarExternalCallBudget
from power_web_os.application.radar.candidate_discovery.execution.context import CandidateDiscoveryExecutionContext
from power_web_os.application.radar.candidate_discovery.execution.state import CandidateDiscoveryExecutionState
from power_web_os.application.radar.candidate_discovery.execution.task_runner import run_gate_pass as _run_gate_pass


class GatePhaseExecutor:
    """Runs qualification gate tasks and writes gate outputs back to execution state."""

    def run(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        tasks: list[RadarExecutionTask],
        candidate_scope: list[str] | None = None,
    ) -> None:
        state.sources, state.observations, state.provider_metadata, state.candidate_scope = _run_qualification_gate_pass(
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


def _run_qualification_gate_pass(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
    tasks: list[RadarExecutionTask],
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    candidate_scope: list[str],
    completed_qualification_ids: list[str],
    gate_results: list[dict[str, Any]],
    events: list[LiveRadarPipelineEvent],
    executed_task_ids: list[str],
    budget: RadarExecutionBudget,
    external_budget: RadarExternalCallBudget,
) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any], list[str]]:
    return _run_gate_pass(
        radar=radar,
        execution_plan=execution_plan,
        provider=provider,
        tasks=tasks,
        sources=sources,
        observations=observations,
        provider_metadata=provider_metadata,
        candidate_scope=candidate_scope,
        completed_qualification_ids=completed_qualification_ids,
        gate_results=gate_results,
        events=events,
        executed_task_ids=executed_task_ids,
        budget=budget,
        external_budget=external_budget,
    )
