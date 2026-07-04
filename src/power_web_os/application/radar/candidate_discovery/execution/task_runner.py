"""Small helpers for staged Radar execution loops."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarCandidate,
    LiveRadarPipelineEvent,
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
    WebSearchProvider,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget
from power_web_os.application.live_radar_external_budget import RadarExternalCallBudget
from power_web_os.application.radar.candidate_discovery.planning.execution_plan import execution_task_to_search_plan, scoped_execution_task
from power_web_os.application.live_radar_normalization import _dedupe_sources
from power_web_os.application.radar.candidate_discovery.execution.merge import ExecutionResultMerger
from power_web_os.application.radar.candidate_discovery.execution.projection import (
    CandidateProjectionService,
    PipelineEventFactory,
)
from power_web_os.application.radar.candidate_discovery.execution.task_runner_payloads import (
    _append_source_outcomes,
    _budget_decision_payload,
    _materialized_candidate_scope_for_task,
    _needs_concrete_candidate_scope,
    _not_executed_input_outcomes,
    _provider_schema_invalid,
    _result_with_retry_exhaustion,
)


class TaskExecutionService:
    """Runs provider tasks, gate passes, candidate projection, and task-level retries.

    Owns:
    - Provider-port task execution, task-budget reservation, schema retry loop,
      gate pass execution, and candidate task utilities.

    Does not own:
    - Phase order, checkpoint policy, expansion target selection, or final dossier
      projection.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#taskexecutionservice
    """

    def __init__(
        self,
        *,
        merger: ExecutionResultMerger | None = None,
        projection: CandidateProjectionService | None = None,
        events: PipelineEventFactory | None = None,
    ) -> None:
        self.merger = merger or ExecutionResultMerger()
        self.projection = projection or CandidateProjectionService()
        self.events = events or PipelineEventFactory(self.projection)

    def run_task(
        self,
        *,
        provider: WebSearchProvider,
        radar: dict[str, Any],
        task: RadarExecutionTask,
        radar_id: str,
        budget: RadarExecutionBudget,
        external_budget: RadarExternalCallBudget | None = None,
        semantic_reserve_key: str | None = None,
    ) -> WebSearchProviderResult:
        if not budget.reserve(task, semantic_reserve_key=semantic_reserve_key):
            return self._budget_limited_result(task, budget.last_decision)
        result = provider.run_search_plan(radar=radar, search_plan=execution_task_to_search_plan(task, radar_id=radar_id))
        result = self._record_semantic_reserve_if_used(result, budget)
        return self._retry_schema_invalid_result(
            provider=provider,
            radar=radar,
            task=task,
            radar_id=radar_id,
            result=result,
            external_budget=external_budget,
        )

    def combine_task_results(
        self,
        first: WebSearchProviderResult,
        second: WebSearchProviderResult,
    ) -> WebSearchProviderResult:
        sources, observations, metadata = self.merger.merge_result(
            first.sources,
            first.candidate_observations,
            first.provider_metadata,
            second,
        )
        return WebSearchProviderResult(sources=sources, candidate_observations=observations, provider_metadata=metadata)

    def tasks_for_stage(self, execution_plan: RadarExecutionPlan, stage: str) -> list[RadarExecutionTask]:
        return [task for task in execution_plan.tasks if task.stage == stage]

    def eligible_candidate_names(
        self,
        *,
        radar: dict[str, Any],
        sources: list[RadarSourceEvidence],
        observations: list[dict[str, Any]],
        completed_qualification_ids: list[str],
    ) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for candidate in self.normalized_candidates(radar=radar, sources=sources, observations=observations):
            if self.projection.candidate_rejected(candidate, completed_qualification_ids=completed_qualification_ids):
                continue
            key = candidate.legal_name.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(candidate.legal_name)
        return result

    def candidate_names_matching(self, observations: list[dict[str, Any]], lower_names: set[str]) -> list[str]:
        return self.projection.candidate_names_matching(observations, lower_names)

    def normalized_candidates(
        self,
        *,
        radar: dict[str, Any],
        sources: list[RadarSourceEvidence],
        observations: list[dict[str, Any]],
    ) -> list[LiveRadarCandidate]:
        return self.projection.normalized_candidates(
            radar=radar,
            sources=sources,
            observations=observations,
            merge_observations=self.merger.merge_candidate_observations,
        )

    def dedupe_sources(self, sources: list[RadarSourceEvidence]) -> list[RadarSourceEvidence]:
        return _dedupe_sources(sources)

    def run_gate_pass(
        self,
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
        external_budget: RadarExternalCallBudget | None = None,
    ) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any], list[str]]:
        for task in tasks:
            sources, observations, provider_metadata, candidate_scope = self._run_gate_task(
                radar=radar,
                execution_plan=execution_plan,
                provider=provider,
                task=task,
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
        return sources, observations, provider_metadata, candidate_scope

    def _run_gate_task(
        self,
        *,
        radar: dict[str, Any],
        execution_plan: RadarExecutionPlan,
        provider: WebSearchProvider,
        task: RadarExecutionTask,
        sources: list[RadarSourceEvidence],
        observations: list[dict[str, Any]],
        provider_metadata: dict[str, Any],
        candidate_scope: list[str],
        completed_qualification_ids: list[str],
        gate_results: list[dict[str, Any]],
        events: list[LiveRadarPipelineEvent],
        executed_task_ids: list[str],
        budget: RadarExecutionBudget,
        external_budget: RadarExternalCallBudget | None,
    ) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any], list[str]]:
        materialized_scope, materialization_event = _materialized_candidate_scope_for_task(
            task=task,
            radar=radar,
            sources=sources,
            observations=observations,
            runtime_candidate_scope=candidate_scope,
            completed_qualification_ids=completed_qualification_ids,
            candidate_service=self,
        )
        if materialization_event is not None:
            events.append(materialization_event)
        if self._should_skip_gate_for_missing_input(task, materialized_scope):
            return self._skip_gate_for_missing_input(
                radar=radar,
                task=task,
                sources=sources,
                observations=observations,
                provider_metadata=provider_metadata,
                candidate_scope=candidate_scope,
                events=events,
                executed_task_ids=executed_task_ids,
            )
        return self._execute_gate_scopes(
            radar=radar,
            execution_plan=execution_plan,
            provider=provider,
            task=task,
            materialized_scope=materialized_scope,
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

    def _execute_gate_scopes(
        self,
        *,
        radar: dict[str, Any],
        execution_plan: RadarExecutionPlan,
        provider: WebSearchProvider,
        task: RadarExecutionTask,
        materialized_scope: list[str],
        sources: list[RadarSourceEvidence],
        observations: list[dict[str, Any]],
        provider_metadata: dict[str, Any],
        candidate_scope: list[str],
        completed_qualification_ids: list[str],
        gate_results: list[dict[str, Any]],
        events: list[LiveRadarPipelineEvent],
        executed_task_ids: list[str],
        budget: RadarExecutionBudget,
        external_budget: RadarExternalCallBudget | None,
    ) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any], list[str]]:
        result = WebSearchProviderResult()
        scopes = materialized_scope if task.stage == "qualification_gate" and materialized_scope else [None]
        for scoped_candidate_name in scopes:
            scoped_scope = [scoped_candidate_name] if scoped_candidate_name else candidate_scope
            scoped_task = scoped_execution_task(task, candidate_scope=scoped_scope)
            result = self.run_task(
                provider=provider,
                radar=radar,
                task=scoped_task,
                radar_id=execution_plan.radar_id,
                budget=budget,
                external_budget=external_budget,
            )
            sources, observations, provider_metadata = self.merger.merge_result(sources, observations, provider_metadata, result)
            executed_task_ids.append(task.task_id if not scoped_scope else f"{task.task_id}:{','.join(scoped_scope)}")
        candidate_scope = self._finish_gate_task(
            radar=radar,
            task=task,
            result=result,
            sources=sources,
            observations=observations,
            completed_qualification_ids=completed_qualification_ids,
            gate_results=gate_results,
            events=events,
        )
        return sources, observations, provider_metadata, candidate_scope

    def _finish_gate_task(
        self,
        *,
        radar: dict[str, Any],
        task: RadarExecutionTask,
        result: WebSearchProviderResult,
        sources: list[RadarSourceEvidence],
        observations: list[dict[str, Any]],
        completed_qualification_ids: list[str],
        gate_results: list[dict[str, Any]],
        events: list[LiveRadarPipelineEvent],
    ) -> list[str]:
        candidates = self.normalized_candidates(radar=radar, sources=sources, observations=observations)
        summary = self.projection.gate_summary(candidates, task.subject_id)
        gate_results.append(summary)
        events.append(self.events.task_event(task, result, "qualification_gate_applied", payload=summary))
        events.extend(self.events.candidate_filtered_events(task, candidates))
        if task.subject_id not in completed_qualification_ids:
            completed_qualification_ids.append(task.subject_id)
        return self.eligible_candidate_names(
            radar=radar,
            sources=sources,
            observations=observations,
            completed_qualification_ids=completed_qualification_ids,
        )

    def _should_skip_gate_for_missing_input(self, task: RadarExecutionTask, materialized_scope: list[str]) -> bool:
        return task.stage == "qualification_gate" and _needs_concrete_candidate_scope(task) and not materialized_scope

    def _skip_gate_for_missing_input(
        self,
        *,
        radar: dict[str, Any],
        task: RadarExecutionTask,
        sources: list[RadarSourceEvidence],
        observations: list[dict[str, Any]],
        provider_metadata: dict[str, Any],
        candidate_scope: list[str],
        events: list[LiveRadarPipelineEvent],
        executed_task_ids: list[str],
    ) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any], list[str]]:
        outcomes = _not_executed_input_outcomes(radar=radar, task=task)
        provider_metadata = _append_source_outcomes(provider_metadata, outcomes)
        executed_task_ids.append(f"{task.task_id}:not_executed_input_not_available")
        events.append(self.events.task_event(
            task,
            WebSearchProviderResult(provider_metadata={"source_provider_outcomes": outcomes, "source_outcomes": outcomes}),
            "qualification_gate_skipped",
            payload={
                "task_id": task.task_id,
                "reason": "not_executed_input_not_available",
                "candidate_scope": [],
                "source_outcomes": outcomes,
            },
        ))
        return sources, observations, provider_metadata, candidate_scope

    def _budget_limited_result(self, task: RadarExecutionTask, decision: Any) -> WebSearchProviderResult:
        return WebSearchProviderResult(
            sources=[],
            candidate_observations=[],
            provider_metadata={
                "provider": "execution_budget",
                "budget_decision": _budget_decision_payload(decision),
                "coverage_findings": [{
                    "summary": decision.message or f"Web task budget reached for {task.subject_id}.",
                    "completeness_risk": "medium",
                    "warnings": [decision.message] if decision.message else [],
                }],
            },
        )

    def _record_semantic_reserve_if_used(
        self,
        result: WebSearchProviderResult,
        budget: RadarExecutionBudget,
    ) -> WebSearchProviderResult:
        if not budget.last_decision.used_semantic_reserve:
            return result
        return result.model_copy(update={
            "provider_metadata": {
                **result.provider_metadata,
                "semantic_task_budget_decision": _budget_decision_payload(budget.last_decision),
            },
        })

    def _retry_schema_invalid_result(
        self,
        *,
        provider: WebSearchProvider,
        radar: dict[str, Any],
        task: RadarExecutionTask,
        radar_id: str,
        result: WebSearchProviderResult,
        external_budget: RadarExternalCallBudget | None,
    ) -> WebSearchProviderResult:
        retries = 0
        while _provider_schema_invalid(result) and external_budget is not None:
            decision = external_budget.reserve("provider_retry", key=task.task_id, task_id=task.task_id)
            if not decision.accepted:
                return _result_with_retry_exhaustion(result, decision.to_payload())
            retries += 1
            external_budget.record_retry(task_id=task.task_id, reason="provider_schema_invalid", attempt=retries, decision=decision)
            result = provider.run_search_plan(radar=radar, search_plan=execution_task_to_search_plan(task, radar_id=radar_id))
        return result
