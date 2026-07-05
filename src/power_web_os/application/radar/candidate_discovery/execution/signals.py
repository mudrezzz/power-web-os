"""Compatibility signal-search phase for candidate discovery runs."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.checkpoints.recording import record_execution_checkpoint
from power_web_os.application.radar.candidate_discovery.checkpoints import RadarExecutionCheckpointDecision
from power_web_os.application.radar.candidate_discovery.universe import filter_signal_result, gap_items, gap_payloads
from power_web_os.application.radar.candidate_discovery.contracts import RadarExecutionTask
from power_web_os.application.radar.candidate_discovery.execution.context import (
    CandidateDiscoveryExecutionContext,
    PhaseResult,
)
from power_web_os.application.radar.candidate_discovery.execution.state import CandidateDiscoveryExecutionState
from power_web_os.application.radar.candidate_discovery.execution.task_runner import TaskExecutionService
from power_web_os.application.radar.candidate_discovery.planning.execution_plan import scoped_execution_task
from power_web_os.application.radar_source_obligations import obligation_decisions_from_plan


class SignalCompatibilityPhaseExecutor:
    """Preserves legacy signal-search projection inside candidate-discovery runs.

    Owns:
    - The compatibility signal-search stage inside candidate-discovery runs,
      including not-searched projection when checkpoints block signal work.

    Does not own:
    - The standalone signal-monitoring pipeline, signal source strategy, or
      candidate discovery qualification.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#signalcompatibilityphaseexecutor
    """

    phase_name = "signal_search"

    def __init__(self, task_service: TaskExecutionService | None = None) -> None:
        self._task_service = task_service or TaskExecutionService()

    def review_before_search(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> tuple[RadarExecutionCheckpointDecision, bool, PhaseResult]:
        pre_signal_decision = self._record_pre_signal_checkpoint(context, state)
        can_run_signal_search = self._can_run_signal_search(state, pre_signal_decision)
        if not can_run_signal_search:
            state.stopped_for_review_reason = state.stopped_for_review_reason or pre_signal_decision.message
        return pre_signal_decision, can_run_signal_search, PhaseResult(
            phase_name="before_signal_search",
            status="continue" if can_run_signal_search else "blocked",
            reason=state.stopped_for_review_reason,
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
        state.signal_task_count = 0
        state.signal_candidate_scope = list(state.candidate_scope)
        state.signal_search_statuses = []
        if can_run_signal_search:
            self._run_signal_tasks(context, state, tasks)
        else:
            self._project_not_searched_signals(state, tasks, pre_signal_decision)
        return PhaseResult(phase_name="signal_search")

    def _record_pre_signal_checkpoint(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> RadarExecutionCheckpointDecision:
        pre_signal_source_obligations = obligation_decisions_from_plan(
            global_policy=dict(context.radar.get("global_search_policy") or {}),
            steps=context.execution_plan.tasks,
            source_policy_decisions=context.source_policy_decisions or [],
            source_provider_outcomes=state.provider_metadata.get("source_provider_outcomes", []),
            sources=state.sources,
            observations=state.observations,
        )
        return record_execution_checkpoint(
            checkpoint_id="before-signal-search",
            phase="before_signal_search",
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
            source_obligation_decisions=pre_signal_source_obligations,
            checkpoint_decisions=state.checkpoint_decisions,
            adaptive_actions=state.adaptive_actions,
            checkpoint_warnings=state.checkpoint_warnings,
            events=state.events,
        )

    @staticmethod
    def _can_run_signal_search(
        state: CandidateDiscoveryExecutionState,
        pre_signal_decision: RadarExecutionCheckpointDecision,
    ) -> bool:
        return (
            not state.stopped_for_review_reason
            and pre_signal_decision.action == "continue"
            and pre_signal_decision.should_continue
            and pre_signal_decision.should_run_signal_search
        )

    def _run_signal_tasks(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        tasks: list[RadarExecutionTask],
    ) -> None:
        for task in tasks:
            for scoped_candidate_name in state.signal_candidate_scope:
                self._run_signal_task_for_candidate(context, state, task, scoped_candidate_name)

    def _run_signal_task_for_candidate(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        task: RadarExecutionTask,
        scoped_candidate_name: str,
    ) -> None:
        scoped_task = scoped_execution_task(task, candidate_scope=[scoped_candidate_name])
        state.events.append(self._task_service.events.signal_planned_event(scoped_task))
        result = self._task_service.run_task(
            provider=context.provider,
            radar=context.radar,
            task=scoped_task,
            radar_id=context.execution_plan.radar_id,
            budget=context.task_budget,
            external_budget=context.external_budget,
        )
        budget_decision = self._task_service.events.budget_decision(result)
        if budget_decision:
            self._project_budget_limited_signal(state, scoped_candidate_name, task, budget_decision)
            return
        result = filter_signal_result(result, allowed_candidate_names={scoped_candidate_name})
        state.unresolved_candidate_gaps.extend(gap_payloads(gap_items(result), origin_task_id=task.task_id))
        state.sources, state.observations, state.provider_metadata = self._task_service.merger.merge_result(
            state.sources,
            state.observations,
            state.provider_metadata,
            result,
        )
        state.executed_task_ids.append(f"{task.task_id}:{scoped_candidate_name}")
        state.signal_search_statuses.append(_searched_signal_status(scoped_candidate_name, task))
        state.signal_task_count += 1

    def _project_budget_limited_signal(
        self,
        state: CandidateDiscoveryExecutionState,
        candidate_name: str,
        task: RadarExecutionTask,
        decision: dict[str, Any],
    ) -> None:
        state.observations.append(self._task_service.events.not_searched_signal_observation(
            candidate_name,
            task,
            decision,
        ))
        state.signal_search_statuses.append(self._task_service.events.signal_status_record(
            candidate_name,
            task,
            decision,
        ))

    def _project_not_searched_signals(
        self,
        state: CandidateDiscoveryExecutionState,
        tasks: list[RadarExecutionTask],
        pre_signal_decision: RadarExecutionCheckpointDecision,
    ) -> None:
        for task in tasks:
            for scoped_candidate_name in state.signal_candidate_scope:
                decision = self._policy_limited_decision(state, pre_signal_decision)
                state.observations.append(self._task_service.events.not_searched_signal_observation(
                    scoped_candidate_name,
                    task,
                    decision,
                ))
                state.signal_search_statuses.append(self._task_service.events.signal_status_record(
                    scoped_candidate_name,
                    task,
                    decision,
                ))

    @staticmethod
    def _policy_limited_decision(
        state: CandidateDiscoveryExecutionState,
        pre_signal_decision: RadarExecutionCheckpointDecision,
    ) -> dict[str, str]:
        stopped = bool(state.stopped_for_review_reason)
        return {
            "state": "not_searched_policy_limited",
            "reason": pre_signal_decision.reason_code if not stopped else "stopped_for_review",
            "message": pre_signal_decision.message if not stopped else state.stopped_for_review_reason,
            "key": f"checkpoint:{pre_signal_decision.checkpoint_id}",
        }


def _searched_signal_status(candidate_name: str, task: RadarExecutionTask) -> dict[str, str]:
    return {
        "candidate_name": candidate_name,
        "signal_id": task.subject_id,
        "task_id": task.task_id,
        "search_status": "searched",
        "not_searched_reason": "",
    }
