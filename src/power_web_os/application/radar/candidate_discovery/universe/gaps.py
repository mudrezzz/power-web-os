"""Candidate-universe gap helpers for staged candidate discovery."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import WebSearchProviderResult
from power_web_os.application.radar.candidate_discovery.universe.identity import (
    candidate_name,
    source_refs,
    stable_id,
)
from power_web_os.application.radar.candidate_discovery.universe.metadata import dict_list


def gap_items(result: WebSearchProviderResult) -> list[dict[str, Any]]:
    return dict_list(result.provider_metadata.get("candidate_universe_gaps"))


def gap_observations(gaps: list[dict[str, Any]], *, origin_task_id: str) -> list[dict[str, Any]]:
    observations = []
    for item in gaps:
        name = candidate_name(item)
        if not name:
            continue
        observations.append({
            "legal_name": name,
            "description": str(item.get("description") or item.get("reason") or "Candidate universe gap."),
            "qualification": [],
            "signals": [],
            "evidence_refs": source_refs(item),
            "review_flags": ["candidate_universe_gap", f"origin_task:{origin_task_id}"],
        })
    return observations


def gap_payloads(gaps: list[dict[str, Any]], *, origin_task_id: str) -> list[dict[str, Any]]:
    payloads = []
    for item in gaps:
        name = candidate_name(item)
        if not name:
            continue
        payloads.append({
            "candidate_id": stable_id(name),
            "legal_name": name,
            "origin_task_id": origin_task_id,
            "source_refs": source_refs(item),
            "reason": str(item.get("reason") or item.get("summary") or "Candidate universe gap."),
            "entity_type": str(item.get("entity_type") or "unknown_entity"),
            "resolution_status": str(item.get("resolution_status") or item.get("entity_resolution_status") or "review_needed"),
            "not_candidate_reason": str(item.get("not_candidate_reason") or ""),
            "review_flags": [str(flag) for flag in item.get("review_flags", []) if str(flag).strip()]
            if isinstance(item.get("review_flags"), list)
            else [],
        })
    return payloads


def dedupe_gap_payloads(gaps: list[dict[str, Any]], *, known_candidate_names: set[str]) -> list[dict[str, Any]]:
    known = {name.lower() for name in known_candidate_names}
    seen: set[str] = set()
    result = []
    for item in gaps:
        name = candidate_name(item)
        if not name:
            continue
        key = name.lower()
        if key in seen or key in known:
            continue
        seen.add(key)
        result.append({**item, "resolution": "unresolved"})
    return result
