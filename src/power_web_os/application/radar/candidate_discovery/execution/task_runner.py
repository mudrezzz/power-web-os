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
from power_web_os.application.radar.candidate_discovery.execution.merge import merge_candidate_observations, merge_result
from power_web_os.application.radar.candidate_discovery.execution.projection import (
    candidate_filtered_events,
    candidate_names_matching as support_candidate_names_matching,
    candidate_rejected,
    gate_summary,
    normalized_candidates as support_normalized_candidates,
    task_event,
)
from power_web_os.application.radar_lookup_terms import is_placeholder_candidate_scope


def run_task(
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
                    "reserve_key": decision.reserve_key,
                    "used_semantic_reserve": decision.used_semantic_reserve,
                },
                "coverage_findings": [{
                    "summary": decision.message or f"Web task budget reached for {task.subject_id}.",
                    "completeness_risk": "medium",
                    "warnings": [decision.message] if decision.message else [],
                }],
            },
        )
    result = provider.run_search_plan(radar=radar, search_plan=execution_task_to_search_plan(task, radar_id=radar_id))
    if budget.last_decision.used_semantic_reserve:
        result = result.model_copy(update={
            "provider_metadata": {
                **result.provider_metadata,
                "semantic_task_budget_decision": _budget_decision_payload(budget.last_decision),
            },
        })
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


def _budget_decision_payload(decision: Any) -> dict[str, Any]:
    return {
        "accepted": decision.accepted,
        "key": decision.key,
        "limit": decision.limit,
        "current": decision.current,
        "state": decision.state,
        "reason": decision.reason,
        "message": decision.message,
        "reserve_key": decision.reserve_key,
        "used_semantic_reserve": decision.used_semantic_reserve,
    }


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
    seen: set[str] = set()
    result: list[str] = []
    for candidate in normalized_candidates(radar=radar, sources=sources, observations=observations):
        if candidate_rejected(candidate, completed_qualification_ids=completed_qualification_ids):
            continue
        key = candidate.legal_name.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(candidate.legal_name)
    return result


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
        materialized_scope, materialization_event = _materialized_candidate_scope_for_task(
            task=task,
            radar=radar,
            sources=sources,
            observations=observations,
            runtime_candidate_scope=candidate_scope,
            completed_qualification_ids=completed_qualification_ids,
        )
        if materialization_event is not None:
            events.append(materialization_event)
        if task.stage == "qualification_gate" and _needs_concrete_candidate_scope(task) and not materialized_scope:
            outcomes = _not_executed_input_outcomes(radar=radar, task=task)
            provider_metadata = _append_source_outcomes(provider_metadata, outcomes)
            executed_task_ids.append(f"{task.task_id}:not_executed_input_not_available")
            events.append(task_event(
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
            continue
        scopes = materialized_scope if task.stage == "qualification_gate" and materialized_scope else [None]
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


def _materialized_candidate_scope_for_task(
    *,
    task: RadarExecutionTask,
    radar: dict[str, Any],
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    runtime_candidate_scope: list[str],
    completed_qualification_ids: list[str],
) -> tuple[list[str], LiveRadarPipelineEvent | None]:
    if task.stage != "qualification_gate":
        return list(runtime_candidate_scope), None
    runtime_scope = _non_placeholder_scope(runtime_candidate_scope)
    planned_scope = _non_placeholder_scope(task.candidate_scope)
    derived_scope = _non_placeholder_scope(eligible_candidate_names(
        radar=radar,
        sources=sources,
        observations=observations,
        completed_qualification_ids=completed_qualification_ids,
    ))
    materialized_scope = runtime_scope or planned_scope or derived_scope
    original_scope = list(runtime_candidate_scope) or list(task.candidate_scope)
    if original_scope == materialized_scope and materialized_scope:
        return materialized_scope, None
    reason = "materialized_from_candidate_universe" if materialized_scope else "no_concrete_candidates_available"
    return materialized_scope, LiveRadarPipelineEvent(
        event_type="candidate_scope_materialized",
        phase="qualification",
        actor="application",
        node_name="candidate_scope_materialization",
        visibility="operator",
        summary=(
            f"Materialized {len(materialized_scope)} concrete candidates for {task.task_id}."
            if materialized_scope
            else f"No concrete candidate scope available for {task.task_id}."
        ),
        payload={
            "task_id": task.task_id,
            "original_runtime_candidate_scope": list(runtime_candidate_scope),
            "planned_candidate_scope": list(task.candidate_scope),
            "materialized_candidate_scope": list(materialized_scope),
            "candidate_count": len(materialized_scope),
            "reason": reason,
        },
        candidate_refs=list(materialized_scope),
    )


def _non_placeholder_scope(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = " ".join(str(value).split())
        if not text or is_placeholder_candidate_scope(text):
            continue
        key = text.lower()
        if key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _needs_concrete_candidate_scope(task: RadarExecutionTask) -> bool:
    if task.stage != "qualification_gate":
        return False
    if any(is_placeholder_candidate_scope(value) for value in task.candidate_scope):
        return True
    return bool(task.source_ids)


def _not_executed_input_outcomes(*, radar: dict[str, Any], task: RadarExecutionTask) -> list[dict[str, Any]]:
    selected = set(task.source_ids)
    policy = radar.get("global_search_policy") if isinstance(radar.get("global_search_policy"), dict) else {}
    sources = [
        dict(source)
        for source in policy.get("sources", [])
        if isinstance(source, dict)
        and str(source.get("source_type") or "") == "company_registry"
        and (not selected or str(source.get("source_id") or source.get("reference") or "") in selected)
    ]
    return [
        {
            "source_ref": "",
            "source_id": str(source.get("source_id") or source.get("reference") or "company_registry"),
            "provider_id": str(source.get("provider_id") or "company_registry"),
            "connector_profile_id": str(source.get("connector_profile_id") or source.get("source_id") or ""),
            "source_type": "company_registry",
            "outcome": "not_executed_input_not_available",
            "reason": "No concrete legal entity name, INN, OGRN, or materialized candidate scope was available.",
            "query": task.query,
            "observation_count": 0,
        }
        for source in sources
    ]


def _append_source_outcomes(provider_metadata: dict[str, Any], outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    if not outcomes:
        return provider_metadata
    return {
        **provider_metadata,
        "source_provider_outcomes": [*provider_metadata.get("source_provider_outcomes", []), *outcomes],
        "source_outcomes": [*provider_metadata.get("source_outcomes", []), *outcomes],
    }


def _provider_schema_invalid(result: WebSearchProviderResult) -> bool:
    metadata = result.provider_metadata
    if metadata.get("provider_error"):
        return True
    for item in metadata.get("extraction_validation_results", []):
        if isinstance(item, dict) and item.get("state") == "extraction_schema_invalid":
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
