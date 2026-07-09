"""Observed entity projection helpers for Radar benchmark evaluation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from power_web_os.radar_evaluation_funnel import is_product_candidate
from power_web_os.radar_evaluation_matching import normalize_name


@dataclass(slots=True)
class RadarObservedEntity:
    name: str
    entity_type: str
    source: str
    source_refs: tuple[str, ...] = ()
    review_flags: tuple[str, ...] = ()
    inn: str | None = None
    ogrn: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_name(self) -> str:
        return normalize_name(self.name)


def observed_entities(dossier: dict[str, Any]) -> list[RadarObservedEntity]:
    observed: list[RadarObservedEntity] = []
    for item in _list(dossier.get("candidates")):
        _append_observed(observed, item, source="product_candidate", default_type="legal_entity")
    for field_name, source, default_type in (
        ("candidate_universe", "candidate_universe", "unknown_entity"),
        ("entity_resolution_results", "entity_resolution", "unknown_entity"),
        ("upstream_disambiguation_results", "upstream_disambiguation", "unknown_entity"),
        ("linked_entity_facts", "linked_entity_fact", "unknown_entity"),
        ("unresolved_candidate_gaps", "unresolved_gap", "unknown_entity"),
    ):
        for item in _list(dossier.get(field_name)):
            _append_observed(observed, item, source=source, default_type=default_type)
    return _dedupe_observed(observed)


def visible_candidate_observations(items: list[RadarObservedEntity]) -> list[RadarObservedEntity]:
    return [item for item in items if item.source == "product_candidate"]


def candidate_surface_rows(dossier: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _list(dossier.get("candidates")) if isinstance(item, dict)]


def accepted_product_candidate_row_count(rows: list[dict[str, Any]]) -> int:
    return sum(1 for item in rows if is_product_candidate(item))


def review_needed_candidate_row_count(rows: list[dict[str, Any]]) -> int:
    return sum(
        1
        for item in rows
        if not is_product_candidate(item)
        and (
            str(item.get("candidate_surface_status") or "") == "review_needed_candidate"
            or str(item.get("product_acceptance_status") or "") == "review_required"
            or str(item.get("public_result_status") or "") == "review_needed_candidate"
        )
    )


def accepted_product_candidate_count(items: list[RadarObservedEntity]) -> int:
    return len({
        item.normalized_name
        for item in items
        if item.normalized_name and is_product_candidate(item.payload)
    })


def review_needed_candidate_count(items: list[RadarObservedEntity]) -> int:
    return len({
        item.normalized_name
        for item in items
        if item.normalized_name
        and not is_product_candidate(item.payload)
        and (
            str(item.payload.get("candidate_surface_status") or "") == "review_needed_candidate"
            or str(item.payload.get("product_acceptance_status") or "") == "review_required"
            or str(item.payload.get("public_result_status") or "") == "review_needed_candidate"
        )
    })


def source_index(dossier: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in _list(dossier.get("sources")) + _list(dossier.get("source_lifecycle")):
        if not isinstance(item, dict):
            continue
        ref = first_string(item, "evidence_ref", "source_ref", "id")
        if ref:
            result[ref] = item
    return result


def evidence_quality(observed: RadarObservedEntity, sources_by_ref: dict[str, dict[str, Any]]) -> str:
    if not observed.source_refs:
        return "weak"
    sources = [sources_by_ref.get(ref, {}) for ref in observed.source_refs]
    if any("sibur" in str(source.get("url") or source.get("title") or "").lower() for source in sources):
        return "strong"
    if any(source.get("state") == "used" or source.get("verification_state") == "reachable" for source in sources):
        return "strong"
    if any(source for source in sources):
        return "medium"
    return "weak"


def optional_digits(value: Any) -> str | None:
    if value is None:
        return None
    digits = re.sub(r"\D+", "", str(value))
    return digits or None


def first_string(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _append_observed(
    observed: list[RadarObservedEntity],
    item: Any,
    *,
    source: str,
    default_type: str,
) -> None:
    if not isinstance(item, dict):
        return
    name = first_string(item, "legal_name", "name", "entity_name", "linked_legal_name", "canonical_name")
    if not name:
        return
    observed.append(
        RadarObservedEntity(
            name=name,
            entity_type=str(item.get("entity_type") or default_type),
            source=source,
            source_refs=tuple(sorted(_source_refs(item))),
            review_flags=tuple(str(value) for value in item.get("review_flags", []) if isinstance(value, str)),
            inn=optional_digits(item.get("inn")),
            ogrn=optional_digits(item.get("ogrn")),
            payload=item,
        )
    )


def _dedupe_observed(items: list[RadarObservedEntity]) -> list[RadarObservedEntity]:
    result: list[RadarObservedEntity] = []
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        key = (item.normalized_name, item.source, item.entity_type)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _source_refs(payload: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in {"source_ref", "source_refs", "evidence_ref", "evidence_refs"}:
                if isinstance(value, str):
                    refs.add(value)
                elif isinstance(value, list):
                    refs.update(str(item) for item in value if item)
            elif isinstance(value, (dict, list)):
                refs.update(_source_refs(value))
    elif isinstance(payload, list):
        for item in payload:
            refs.update(_source_refs(item))
    return refs


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []
