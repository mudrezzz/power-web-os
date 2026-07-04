"""Candidate-universe review helpers for staged execution finalization."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import LiveRadarPipelineEvent
from power_web_os.application.live_radar_universe import dict_list, stable_id


def _append_review_needed_universe_entities(
    candidate_universe: list[dict[str, Any]],
    *,
    provider_metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    result = list(candidate_universe)
    known = {str(item.get("legal_name") or "").casefold(): item for item in result}
    review_sources = [
        *dict_list(provider_metadata.get("upstream_disambiguation_results")),
        *[
            item
            for item in dict_list(provider_metadata.get("candidate_universe_gaps"))
            if _string_list(item.get("source_refs")) or str(item.get("entity_type") or "") in {"branch", "production_site", "asset", "project"}
        ],
        *dict_list(provider_metadata.get("review_needed_upstream_entities")),
    ]
    for item in review_sources:
        name = str(item.get("legal_name") or item.get("entity_name") or "").strip()
        if not name:
            continue
        existing = known.get(name.casefold())
        if existing is not None:
            _merge_review_needed_metadata(existing, item)
            continue
        entity_type = str(item.get("entity_type") or "unknown_entity")
        payload = {
            "candidate_id": stable_id(name),
            "legal_name": name,
            "status": "unknown_review_needed",
            "origin_task_id": str(item.get("origin_task_id") or item.get("lookup_query") or "upstream_disambiguation"),
            "source_refs": list(item.get("source_refs", [])) if isinstance(item.get("source_refs"), list) else [],
            "gate_results": [],
            "rejection_reasons": [],
            "coverage_flags": [flag for flag in _string_list(item.get("review_flags")) if "candidate_universe" in flag or "coverage" in flag],
            "entity_type": entity_type,
            "resolution_status": str(item.get("resolution_status") or "review_needed"),
            "not_candidate_reason": str(item.get("not_candidate_reason") or ("not_standalone_legal_entity" if entity_type != "legal_entity" else "")),
            "review_flags": _string_list(item.get("review_flags")),
            "linked_fact_count": 0,
            "signal_searches": [],
        }
        result.append(payload)
        known[name.casefold()] = payload
    return result

def _merge_review_needed_metadata(target: dict[str, Any], incoming: dict[str, Any]) -> None:
    incoming_type = str(incoming.get("entity_type") or "")
    current_type = str(target.get("entity_type") or "")
    if incoming_type and incoming_type != "unknown_entity" and current_type in {"", "unknown_entity"}:
        target["entity_type"] = incoming_type
    incoming_status = str(incoming.get("resolution_status") or incoming.get("entity_resolution_status") or "")
    if incoming_status and str(target.get("resolution_status") or "") in {"", "review_needed", "unresolved"}:
        target["resolution_status"] = incoming_status
    for field_name in ("resolved_legal_name", "linked_legal_name", "not_candidate_reason"):
        value = str(incoming.get(field_name) or "").strip()
        if value and not str(target.get(field_name) or "").strip():
            target[field_name] = value
    source_refs = sorted({*_string_list(target.get("source_refs")), *_string_list(incoming.get("source_refs"))})
    if source_refs:
        target["source_refs"] = source_refs
    review_flags = sorted({*_string_list(target.get("review_flags")), *_string_list(incoming.get("review_flags"))})
    if review_flags:
        target["review_flags"] = review_flags
    if str(target.get("entity_type") or "") in {"branch", "production_site", "asset", "project"} and not target.get("not_candidate_reason"):
        target["not_candidate_reason"] = "not_standalone_legal_entity"

def _review_needed_universe_count(candidate_universe: list[dict[str, Any]]) -> int:
    return sum(1 for item in candidate_universe if str(item.get("status") or "") == "unknown_review_needed")

def _linked_branch_or_site_count(linked_facts: object) -> int:
    return sum(
        1
        for item in dict_list(linked_facts)
        if str(item.get("entity_type") or "") in {"branch", "production_site", "asset", "project"}
    )

def _upstream_disambiguation_events(
    results: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
) -> list[LiveRadarPipelineEvent]:
    events: list[LiveRadarPipelineEvent] = []
    tasks_by_entity = {str(item.get("entity_name") or ""): item for item in tasks}
    for item in results:
        name = str(item.get("legal_name") or item.get("entity_name") or "")
        task = tasks_by_entity.get(name)
        events.append(LiveRadarPipelineEvent(
            event_type="upstream_entity_retained_for_review",
            phase="collection",
            actor="application",
            node_name="upstream_disambiguation",
            visibility="operator",
            summary=f"Retained upstream entity {name} for human review.",
            payload=dict(item),
            source_refs=list(item.get("source_refs", [])) if isinstance(item.get("source_refs"), list) else [],
            candidate_refs=[name] if name else [],
        ))
        if task:
            events.append(LiveRadarPipelineEvent(
                event_type="cross_source_disambiguation_requested",
                phase="planning",
                actor="application",
                node_name="upstream_disambiguation",
                visibility="operator",
                summary=f"Planned cross-source disambiguation for {name}.",
                payload=dict(task),
                candidate_refs=[name] if name else [],
            ))
    return events

def _string_list(value: object) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []
