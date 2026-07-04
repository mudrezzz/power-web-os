"""Payload and schema helpers for task execution service."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarPipelineEvent,
    RadarExecutionTask,
    RadarSourceEvidence,
    WebSearchProviderResult,
)
from power_web_os.application.radar_lookup_terms import is_placeholder_candidate_scope


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


def _materialized_candidate_scope_for_task(
    *,
    task: RadarExecutionTask,
    radar: dict[str, Any],
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    runtime_candidate_scope: list[str],
    completed_qualification_ids: list[str],
    candidate_service: Any,
) -> tuple[list[str], LiveRadarPipelineEvent | None]:
    if task.stage != "qualification_gate":
        return list(runtime_candidate_scope), None
    runtime_scope = _non_placeholder_scope(runtime_candidate_scope)
    planned_scope = _non_placeholder_scope(task.candidate_scope)
    derived_scope = _non_placeholder_scope(candidate_service.eligible_candidate_names(
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
