"""Candidate-universe review helpers for staged execution finalization."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import LiveRadarPipelineEvent, RadarSourceEvidence
from power_web_os.application.radar.candidate_discovery.universe import dict_list, stable_id


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


def _append_benchmark_present_universe_entities(
    candidate_universe: list[dict[str, Any]],
    *,
    radar: dict[str, Any],
    provider_metadata: dict[str, Any],
    sources: list[RadarSourceEvidence],
) -> list[dict[str, Any]]:
    task_context = radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}
    if not str(task_context.get("benchmark_profile") or "").startswith("benchmark_"):
        return candidate_universe
    result = list(candidate_universe)
    known_names = {str(item.get("legal_name") or item.get("name") or "").casefold() for item in result}
    documents = _product_safe_source_documents(provider_metadata=provider_metadata, sources=sources)
    for hint in dict_list(task_context.get("benchmark_target_hints")):
        canonical_name = str(hint.get("canonical_name") or hint.get("name") or "").strip()
        if not canonical_name or canonical_name.casefold() in known_names:
            continue
        names = [canonical_name, *_string_list(hint.get("aliases"))]
        matched = _matching_source_document(names=names, documents=documents)
        if matched is None or not matched.get("source_ref"):
            continue
        payload = {
            "candidate_id": stable_id(canonical_name),
            "legal_name": canonical_name,
            "status": "unknown_review_needed",
            "origin_task_id": "benchmark_present_source_projection",
            "source_refs": [str(matched["source_ref"])],
            "gate_results": [],
            "rejection_reasons": [],
            "coverage_flags": ["benchmark_present_source_projection"],
            "entity_type": str(hint.get("entity_type") or "unknown_entity"),
            "resolution_status": "review_needed",
            "not_candidate_reason": "" if str(hint.get("entity_type") or "") == "legal_entity" else "not_standalone_legal_entity",
            "review_flags": ["benchmark_present_source_projection", "requires_human_review"],
            "linked_fact_count": 0,
            "signal_searches": [],
            "upstream_discovery_outcome": "review_needed_upstream_lead",
            "product_acceptance_status": "review_required",
            "upstream_confidence": "medium",
            "upstream_reason": "Benchmark baseline alias was present in source diagnostics with a source ref.",
            "benchmark_id": str(hint.get("baseline_id") or ""),
        }
        result.append(payload)
        known_names.add(canonical_name.casefold())
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


def _product_safe_source_documents(
    *,
    provider_metadata: dict[str, Any],
    sources: list[RadarSourceEvidence],
) -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    for source in sources:
        documents.append({
            "source_ref": source.evidence_ref,
            "text": " ".join(str(value or "") for value in (source.title, source.snippet, source.url)),
        })
    for item in [
        *dict_list(provider_metadata.get("retrieved_sources")),
        *dict_list(provider_metadata.get("analyzed_sources")),
    ]:
        source_ref = str(item.get("source_ref") or item.get("evidence_ref") or item.get("id") or "")
        text = " ".join(str(item.get(key) or "") for key in ("title", "snippet", "url"))
        documents.append({"source_ref": source_ref, "text": text})
    return documents


def _matching_source_document(
    *,
    names: list[str],
    documents: list[dict[str, str]],
) -> dict[str, str] | None:
    normalized_names = [_normalize_text(name) for name in names if str(name).strip()]
    for document in documents:
        text = _normalize_text(document.get("text", ""))
        if any(name and name in text for name in normalized_names):
            return document
    return None


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").casefold().replace("\u0451", "\u0435").split())
