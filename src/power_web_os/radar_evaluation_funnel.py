"""Benchmark funnel helpers for Radar evaluation reports."""

from __future__ import annotations

import json
import re
from typing import Any

from power_web_os.radar_evaluation_matching import review_entity_name_match


def is_product_candidate(payload: dict[str, Any]) -> bool:
    status = str(payload.get("product_acceptance_status") or "")
    if not status:
        return True
    return status == "product_candidate"


def upstream_lead_counts(dossier: dict[str, Any]) -> dict[str, int]:
    counts = {
        "retained_upstream_lead_count": 0,
        "confirmed_upstream_lead_count": 0,
        "review_needed_upstream_lead_count": 0,
    }
    seen: set[tuple[str, str]] = set()
    for collection_name in ("candidates", "candidate_universe"):
        for item in _list(dossier.get(collection_name)):
            if not isinstance(item, dict):
                continue
            name = _first_string(item, "legal_name", "name", "entity_name")
            outcome = str(item.get("upstream_discovery_outcome") or "")
            if not name or not outcome:
                continue
            key = (name.casefold(), outcome)
            if key in seen:
                continue
            seen.add(key)
            if outcome == "confirmed_upstream_lead":
                counts["confirmed_upstream_lead_count"] += 1
            elif outcome == "review_needed_upstream_lead":
                counts["review_needed_upstream_lead_count"] += 1
            elif outcome == "retained_upstream_lead":
                counts["retained_upstream_lead_count"] += 1
    counts["retained_upstream_lead_count"] += (
        counts["confirmed_upstream_lead_count"] + counts["review_needed_upstream_lead_count"]
    )
    return counts


def benchmark_target_funnel(
    *,
    baseline: Any,
    observed: list[Any],
    false_negative_diagnostics: list[dict[str, Any]],
    dossier: dict[str, Any],
) -> list[dict[str, Any]]:
    diagnostics_by_id = {
        str(item.get("baseline_id") or ""): item
        for item in false_negative_diagnostics
        if str(item.get("baseline_id") or "")
    }
    result: list[dict[str, Any]] = []
    for entity in baseline.entities:
        names = [entity.canonical_name, *entity.aliases]
        generated = _records_match_names(names, _list(dossier.get("expansion_target_queue")))
        selected = _records_match_names(names, _list(dossier.get("search_expansion_query_variants")))
        admitted = _records_match_names(names, _list(dossier.get("work_admission_decisions")))
        executed_records = _matching_name_records(names, _list(dossier.get("search_expansion_results")))
        executed = any(str(item.get("execution_status") or "").startswith("executed") for item in executed_records)
        source_found = any(int(item.get("source_count") or 0) > 0 for item in executed_records)
        projected = any(_observed_matches_entity(entity, item) for item in observed)
        diagnostic = diagnostics_by_id.get(entity.baseline_id, {})
        result.append({
            "baseline_id": entity.baseline_id,
            "canonical_name": entity.canonical_name,
            "entity_type": entity.entity_type,
            "generated": generated,
            "selected": selected,
            "admitted": admitted,
            "executed": executed,
            "source_found": source_found,
            "projected": projected,
            "rejected": str(diagnostic.get("bucket") or "") == "explicitly_rejected",
            "path_reason": _target_path_reason(
                entity_type=str(entity.entity_type),
                generated=generated,
                selected=selected,
                admitted=admitted,
                executed=executed,
                source_found=source_found,
                projected=projected,
                diagnostic=diagnostic,
            ),
        })
    return result


def _target_path_reason(
    *,
    entity_type: str,
    generated: bool,
    selected: bool,
    admitted: bool,
    executed: bool,
    source_found: bool,
    projected: bool,
    diagnostic: dict[str, Any],
) -> str:
    if projected:
        return "projected"
    bucket = str(diagnostic.get("bucket") or "")
    if bucket in {"present_not_projected", "source_found_not_projected"}:
        return bucket
    if not generated:
        return "not_generated"
    if not selected:
        if entity_type == "legal_entity":
            if bucket in {"expansion_not_selected", "completion_cap_exhausted", "completion_not_selected", ""}:
                return "selection_cap_exhausted_for_protected_legal_target"
        return "not_selected"
    if not admitted:
        return "not_admitted"
    if not executed:
        return "not_executed"
    if not source_found:
        return "source_not_found"
    return bucket or "present_not_projected"


def _records_match_names(names: list[str], records: list[Any]) -> bool:
    return bool(_matching_name_records(names, records))


def _matching_name_records(names: list[str], records: list[Any]) -> list[dict[str, Any]]:
    normalized_names = [_normalize_match_text(name) for name in names if str(name).strip()]
    result: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        text = _normalize_match_text(json.dumps(record, ensure_ascii=False))
        if any(name and name in text for name in normalized_names):
            result.append(record)
    return result


def _observed_matches_entity(entity: Any, observed: Any) -> bool:
    names = [_normalize_match_text(entity.canonical_name), *[_normalize_match_text(alias) for alias in entity.aliases]]
    observed_name = _normalize_match_text(observed.name)
    if any(name and (name == observed_name or name in observed_name or observed_name in name) for name in names):
        return True
    return review_entity_name_match(
        baseline_names={name for name in names if name},
        observed_name=observed_name,
    )


def _normalize_match_text(value: str) -> str:
    text = str(value or "").casefold().replace("\u0451", "\u0435")
    text = re.sub(r"[\"'\u00ab\u00bb.,(){}\[\]:;]+", " ", text)
    return " ".join(text.split())


def _first_string(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []
