"""Recall-first upstream entity retention helpers for live Radar execution."""

from __future__ import annotations

import re
from typing import Any

from power_web_os.application.live_radar_contracts import RadarExecutionTask


def review_needed_ambiguous_registry_observations(
    result: Any,
    request: Any,
    *,
    provider_id: str,
) -> list[dict[str, Any]]:
    if not any(getattr(outcome, "outcome", "") == "ambiguous_match" for outcome in getattr(result, "outcomes", [])):
        return []
    review_entities: list[dict[str, Any]] = []
    for observation in getattr(result, "observations", []):
        if getattr(observation, "match_quality", "") == "high" or getattr(observation, "matched_by", "") in {"inn", "ogrn"}:
            continue
        legal_name = str(getattr(observation, "legal_name", "") or "")
        source_ref = getattr(observation, "source_ref", "") or stable_source_ref(provider_id, legal_name)
        entity_type = upstream_entity_type(observation)
        review_entities.append({
            "entity_name": legal_name,
            "legal_name": legal_name,
            "entity_type": entity_type,
            "resolution_status": "review_needed",
            "not_candidate_reason": "not_standalone_legal_entity" if entity_type != "legal_entity" else "",
            "source_refs": [source_ref],
            "source_id": getattr(request, "source_id", ""),
            "provider_id": provider_id,
            "lookup_query": getattr(observation, "lookup_query", "") or getattr(request, "query", ""),
            "inn": getattr(observation, "inn", ""),
            "ogrn": getattr(observation, "ogrn", ""),
            "okved": getattr(observation, "okved", ""),
            "matched_by": getattr(observation, "matched_by", ""),
            "match_quality": getattr(observation, "match_quality", ""),
            "review_flags": [
                "registry_match_ambiguous",
                "requires_human_review",
                *([] if entity_type == "legal_entity" else ["not_standalone_legal_entity"]),
            ],
            "reason": "Ambiguous registry observation retained for recall-first upstream discovery.",
        })
    return review_entities


def candidate_gap_from_review_entity(item: dict[str, Any], *, task: RadarExecutionTask) -> dict[str, Any]:
    return {
        "legal_name": str(item.get("legal_name") or item.get("entity_name") or ""),
        "entity_type": str(item.get("entity_type") or "unknown_entity"),
        "resolution_status": str(item.get("resolution_status") or "review_needed"),
        "source_refs": list(item.get("source_refs", [])) if isinstance(item.get("source_refs"), list) else [],
        "reason": str(item.get("reason") or "Review-needed upstream entity."),
        "origin_task_id": task.task_id,
        "review_flags": list(item.get("review_flags", [])) if isinstance(item.get("review_flags"), list) else [],
        "not_candidate_reason": str(item.get("not_candidate_reason") or ""),
    }


def cross_source_disambiguation_tasks(
    *,
    radar: dict[str, Any],
    task: RadarExecutionTask,
    review_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_ids = _cross_check_source_ids(radar)
    if not source_ids:
        return []
    return [
        {
            "task_id": f"cross-check:{task.task_id}:{stable_source_ref('entity', str(item.get('legal_name') or item.get('entity_name') or 'unknown'))}",
            "origin_task_id": task.task_id,
            "entity_name": str(item.get("legal_name") or item.get("entity_name") or ""),
            "entity_type": str(item.get("entity_type") or "unknown_entity"),
            "source_ids": source_ids,
            "purpose": "Cross-check ambiguous upstream registry observation through official or web evidence.",
            "status": "planned",
            "review_flags": list(item.get("review_flags", [])) if isinstance(item.get("review_flags"), list) else [],
        }
        for item in review_entities
        if str(item.get("legal_name") or item.get("entity_name") or "").strip()
    ]


def upstream_entity_type(observation: Any) -> str:
    entity_type = str(getattr(observation, "entity_type", "") or "")
    if entity_type and entity_type != "legal_entity":
        return entity_type
    name = str(getattr(observation, "legal_name", "") or "").lower()
    if "филиал" in name:
        return "branch"
    if any(marker in name for marker in ("гпз", "нпз", "комбинат", "месторождение", "завод")):
        return "production_site"
    if any(marker in name for marker in ("проект", "ep-", "ер-", "эр-")):
        return "project"
    if any(marker in name for marker in ("установка", "линия", "цех", "актив")):
        return "asset"
    return "legal_entity"


def stable_source_ref(provider_id: str, value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return f"{provider_id}_{normalized or 'company'}"[:80]


def _cross_check_source_ids(radar: dict[str, Any]) -> list[str]:
    policy = radar.get("global_search_policy") if isinstance(radar.get("global_search_policy"), dict) else {}
    result: list[str] = []
    for source in policy.get("sources", []):
        if not isinstance(source, dict):
            continue
        source_id = str(source.get("source_id") or source.get("reference") or "")
        source_type = str(source.get("source_type") or "")
        usage = str(source.get("usage_obligation") or source.get("usage_mode") or "")
        if source_id and source_type in {"search_engine", "official_website", "web", "website"}:
            result.append(source_id)
        elif source_id and usage in {"required_for_coverage", "required_for_signal", "preferred"} and source_type != "company_registry":
            result.append(source_id)
    return result
