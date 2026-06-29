"""Merge staged Radar provider results with entity resolution metadata."""

from __future__ import annotations

import re
from typing import Any

from power_web_os.application.live_radar_contracts import RadarSourceEvidence, WebSearchProviderResult
from power_web_os.application.live_radar_entity_resolution import RadarEntityResolutionService
from power_web_os.application.live_radar_normalization import _dedupe_sources
from power_web_os.application.live_radar_universe import merge_provider_metadata

_ENTITY_RESOLUTION_SERVICE = RadarEntityResolutionService()


def merge_result(
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    metadata: dict[str, Any],
    result: WebSearchProviderResult,
) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any]]:
    merged_sources = _dedupe_sources([*sources, *result.sources])
    merged_metadata = merge_provider_metadata(metadata, result.provider_metadata)
    resolved = _ENTITY_RESOLUTION_SERVICE.resolve(
        observations=[*observations, *result.candidate_observations],
        sources=merged_sources,
        provider_metadata=merged_metadata,
    )
    return (
        merged_sources,
        merge_candidate_observations(resolved.candidate_observations),
        resolved.provider_metadata,
    )


def merge_candidate_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in observations:
        name = str(item.get("legal_name") or item.get("name") or "").strip()
        if not name:
            continue
        key = _candidate_merge_key(item, fallback_name=name)
        target = merged.setdefault(key, {"legal_name": name, "qualification": [], "signals": [], "review_flags": []})
        target["description"] = target.get("description") or item.get("description", "")
        target["qualification"] = _merge_section(target.get("qualification", []), item.get("qualification", []), "criterion_code")
        target["signals"] = _merge_section(target.get("signals", []), item.get("signals", []), "signal_code")
        target["evidence_refs"] = sorted({
            str(ref)
            for ref in [*_as_list(target.get("evidence_refs")), *_as_list(item.get("evidence_refs"))]
            if str(ref).strip()
        })
        for metadata_key in ("entity_type", "entity_resolution_status", "not_candidate_reason", "inn", "ogrn", "okved", "normalized_legal_name", "match_quality", "matched_by", "lookup_query"):
            if item.get(metadata_key) and not target.get(metadata_key):
                target[metadata_key] = item[metadata_key]
        if isinstance(item.get("registry_facts"), dict):
            target["registry_facts"] = {**target.get("registry_facts", {}), **item["registry_facts"]}
        target["linked_entity_facts"] = _merge_fact_list(target.get("linked_entity_facts", []), item.get("linked_entity_facts", []))
        target["review_flags"] = sorted({str(flag) for flag in [*target.get("review_flags", []), *item.get("review_flags", [])] if str(flag).strip()})
    return list(merged.values())


def _candidate_merge_key(item: dict[str, Any], *, fallback_name: str) -> str:
    for key in ("inn", "ogrn"):
        value = str(item.get(key) or "").strip().lower()
        if value:
            return f"{key}:{value}"
    normalized_name = str(item.get("normalized_legal_name") or "").strip().lower()
    if normalized_name:
        return f"name:{normalized_name}"
    return f"name:{_normalize_company_name(fallback_name)}"


def _normalize_company_name(value: str) -> str:
    normalized = re.sub(r"[«»\"'.,]", " ", value.lower())
    normalized = re.sub(r"\b(ао|пао|оао|зао|ооо|нао|jsc|pjsc|llc)\b", " ", normalized, flags=re.IGNORECASE)
    return " ".join(normalized.split())


def candidate_universe_with_entity_metadata(
    candidate_universe: list[dict[str, Any]],
    observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    metadata_by_name = {
        str(item.get("legal_name", "")).lower(): item
        for item in observations
        if str(item.get("legal_name", "")).strip()
    }
    result: list[dict[str, Any]] = []
    for item in candidate_universe:
        payload = dict(item)
        metadata = metadata_by_name.get(str(payload.get("legal_name", "")).lower(), {})
        payload["entity_type"] = str(metadata.get("entity_type") or payload.get("entity_type") or "unknown_entity")
        payload["resolution_status"] = str(
            metadata.get("entity_resolution_status") or payload.get("resolution_status") or "review_needed"
        )
        linked_facts = _dict_list(metadata.get("linked_entity_facts"))
        payload["linked_fact_count"] = len(linked_facts)
        if metadata.get("not_candidate_reason") or payload.get("not_candidate_reason"):
            payload["not_candidate_reason"] = str(metadata.get("not_candidate_reason") or payload["not_candidate_reason"])
        result.append(payload)
    return result


def _merge_section(existing: object, incoming: object, key: str) -> list[dict[str, Any]]:
    merged = {str(item.get(key) or item.get("code") or ""): dict(item) for item in _dict_list(existing)}
    for item in _dict_list(incoming):
        section_id = str(item.get(key) or item.get("code") or "")
        if section_id:
            merged[section_id] = {**merged.get(section_id, {}), **item}
    return list(merged.values())


def _merge_fact_list(existing: object, incoming: object) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in [*_dict_list(existing), *_dict_list(incoming)]:
        key = "|".join(str(item.get(part, "")) for part in ("entity_name", "entity_type", "linked_legal_name"))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _as_list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []
