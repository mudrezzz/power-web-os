"""Small helpers for staged Radar execution loops."""

from __future__ import annotations

from typing import Any

from power_web_os.application.live_radar_contracts import (
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
from power_web_os.application.live_radar_execution_plan import execution_task_to_search_plan, scoped_execution_task
from power_web_os.application.live_radar_normalization import _dedupe_sources
from power_web_os.application.live_radar_staged_merge import merge_candidate_observations, merge_result
from power_web_os.application.live_radar_staged_support import (
    candidate_filtered_events,
    candidate_names_matching as support_candidate_names_matching,
    candidate_rejected,
    gate_summary,
    normalized_candidates as support_normalized_candidates,
    task_event,
)


def run_task(
    *,
    provider: WebSearchProvider,
    radar: dict[str, Any],
    task: RadarExecutionTask,
    radar_id: str,
    budget: RadarExecutionBudget,
    external_budget: RadarExternalCallBudget | None = None,
) -> WebSearchProviderResult:
    if not budget.reserve(task):
        decision = budget.last_decision
        return WebSearchProviderResult(
            sources=[],
            candidate_observations=[],
            provider_metadata={
                "provider": "execution_budget",
                "budget_decision": {
                    "accepted": decision.accepted,
                    "key": decision.key,
                    "limit": decision.limit,
                    "current": decision.current,
                    "state": decision.state,
                    "reason": decision.reason,
                    "message": decision.message,
                },
                "coverage_findings": [{
                    "summary": decision.message or f"Web task budget reached for {task.subject_id}.",
                    "completeness_risk": "medium",
                    "warnings": [decision.message] if decision.message else [],
                }],
            },
        )
    result = provider.run_search_plan(radar=radar, search_plan=execution_task_to_search_plan(task, radar_id=radar_id))
    retries = 0
    while _provider_schema_invalid(result) and external_budget is not None:
        decision = external_budget.reserve("provider_retry", key=task.task_id, task_id=task.task_id)
        if not decision.accepted:
            return _result_with_retry_exhaustion(result, decision.to_payload())
        retries += 1
        external_budget.record_retry(
            task_id=task.task_id,
            reason="provider_schema_invalid",
            attempt=retries,
            decision=decision,
        )
        result = provider.run_search_plan(radar=radar, search_plan=execution_task_to_search_plan(task, radar_id=radar_id))
    return result


def combine_task_results(first: WebSearchProviderResult, second: WebSearchProviderResult) -> WebSearchProviderResult:
    sources, observations, metadata = merge_result(
        first.sources,
        first.candidate_observations,
        first.provider_metadata,
        second,
    )
    return WebSearchProviderResult(sources=sources, candidate_observations=observations, provider_metadata=metadata)


def useful_result_warning_event(warnings: list[str]) -> LiveRadarPipelineEvent:
    return LiveRadarPipelineEvent(
        event_type="validation_warning",
        phase="collection",
        actor="application",
        node_name="useful_result_budget",
        visibility="operator",
        summary="Useful-result budget triggered bounded discovery retries.",
        payload={"warnings": warnings},
    )


def tasks_for_stage(execution_plan: RadarExecutionPlan, stage: str) -> list[RadarExecutionTask]:
    return [task for task in execution_plan.tasks if task.stage == stage]


def eligible_candidate_names(
    *,
    radar: dict[str, Any],
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    completed_qualification_ids: list[str],
) -> list[str]:
    return [
        candidate.legal_name
        for candidate in normalized_candidates(radar=radar, sources=sources, observations=observations)
        if not candidate_rejected(candidate, completed_qualification_ids=completed_qualification_ids)
    ]


def candidate_names_matching(observations: list[dict[str, Any]], lower_names: set[str]) -> list[str]:
    return support_candidate_names_matching(observations, lower_names)


def normalized_candidates(
    *,
    radar: dict[str, Any],
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
) -> list[LiveRadarCandidate]:
    return support_normalized_candidates(
        radar=radar,
        sources=sources,
        observations=observations,
        merge_observations=merge_candidate_observations,
    )


def dedupe_sources(sources: list[RadarSourceEvidence]) -> list[RadarSourceEvidence]:
    return _dedupe_sources(sources)


def run_gate_pass(
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
        scopes = candidate_scope if task.stage == "qualification_gate" and candidate_scope else [None]
        for scoped_candidate_name in scopes:
            scoped_scope = [scoped_candidate_name] if scoped_candidate_name else candidate_scope
            scoped_task = scoped_execution_task(task, candidate_scope=scoped_scope)
            result = run_task(
                provider=provider,
                radar=radar,
                task=scoped_task,
                radar_id=execution_plan.radar_id,
                budget=budget,
                external_budget=external_budget,
            )
            sources, observations, provider_metadata = merge_result(sources, observations, provider_metadata, result)
            executed_task_ids.append(task.task_id if not scoped_scope else f"{task.task_id}:{','.join(scoped_scope)}")
        candidates = normalized_candidates(radar=radar, sources=sources, observations=observations)
        summary = gate_summary(candidates, task.subject_id)
        gate_results.append(summary)
        events.append(task_event(scoped_task, result, "qualification_gate_applied", payload=summary))
        events.extend(candidate_filtered_events(task, candidates))
        if task.subject_id not in completed_qualification_ids:
            completed_qualification_ids.append(task.subject_id)
        candidate_scope = eligible_candidate_names(
            radar=radar,
            sources=sources,
            observations=observations,
            completed_qualification_ids=completed_qualification_ids,
        )
    return sources, observations, provider_metadata, candidate_scope


def _provider_schema_invalid(result: WebSearchProviderResult) -> bool:
    metadata = result.provider_metadata
    if metadata.get("provider_error"):
        return True
    for issue in metadata.get("extraction_validation_issues", []):
        if isinstance(issue, dict) and issue.get("severity") == "error":
            return True
    return False


def _result_with_retry_exhaustion(result: WebSearchProviderResult, decision: dict[str, object]) -> WebSearchProviderResult:
    return result.model_copy(update={
        "provider_metadata": {
            **result.provider_metadata,
            "provider_retry_exhausted": True,
            "budget_decision": {
                "accepted": False,
                "key": decision.get("key", "provider_retry"),
                "limit": decision.get("limit"),
                "current": decision.get("current"),
                "state": "not_executed_budget_limited",
                "reason": decision.get("reason", "external_call_budget_exhausted"),
                "message": decision.get("message", "Provider retry budget exhausted."),
            },
            "coverage_findings": [{
                "summary": decision.get("message", "Provider retry budget exhausted."),
                "completeness_risk": "medium",
                "warnings": [str(decision.get("message", "Provider retry budget exhausted."))],
            }],
        },
    })
