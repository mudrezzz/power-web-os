"""Resolve Radar extraction entities before account-candidate scoring.

Provider extraction may mention legal entities, production sites, projects, or
assets in the same response. The Radar shortlist is account-oriented, so only
legal entities should become scored candidates; non-account entities are linked
facts or review gaps.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from power_web_os.application.radar.candidate_discovery.contracts import (
    RadarEntityResolutionStatus,
    RadarEntityType,
    RadarSourceEvidence,
)
from power_web_os.application.radar.candidate_discovery.universe.metadata import merge_provider_metadata


class RadarLinkedEntityFact(BaseModel):
    entity_name: str
    entity_type: RadarEntityType
    linked_legal_name: str
    source_refs: list[str] = Field(default_factory=list)
    reason: str = ""


class RadarEntityResolutionResult(BaseModel):
    entity_name: str
    entity_type: RadarEntityType
    resolution_status: RadarEntityResolutionStatus
    resolved_legal_name: str = ""
    source_refs: list[str] = Field(default_factory=list)
    reason: str = ""
    not_candidate_reason: str = ""


class RadarEntityResolutionOutput(BaseModel):
    candidate_observations: list[dict[str, Any]] = Field(default_factory=list)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


class RadarEntityResolutionService:
    """Classify provider observations into account candidates and linked facts."""

    def resolve(
        self,
        *,
        observations: list[dict[str, Any]],
        sources: list[RadarSourceEvidence],
        provider_metadata: dict[str, Any] | None = None,
    ) -> RadarEntityResolutionOutput:
        legal_observations, non_account_observations, resolution_results = self._classify(observations)
        linked_facts, unresolved_gaps = self._link_non_account_entities(
            legal_observations=legal_observations,
            non_account_observations=non_account_observations,
            sources=sources,
        )
        legal_by_name = {_entity_name(item).lower(): item for item in legal_observations if _entity_name(item)}
        for fact in linked_facts:
            target = legal_by_name.get(fact.linked_legal_name.lower())
            if target is None:
                continue
            target.setdefault("linked_entity_facts", []).append(fact.model_dump())
            target["review_flags"] = sorted({
                *[str(flag) for flag in target.get("review_flags", []) if str(flag).strip()],
                "linked_non_account_entity_fact",
            })
            resolution_results.append(RadarEntityResolutionResult(
                entity_name=fact.entity_name,
                entity_type=fact.entity_type,
                resolution_status="linked_to_legal_entity",
                resolved_legal_name=fact.linked_legal_name,
                source_refs=list(fact.source_refs),
                reason=fact.reason,
            ))
        for item in unresolved_gaps:
            resolution_results.append(item)

        metadata = {
            "entity_resolution_results": [item.model_dump() for item in resolution_results],
            "linked_entity_facts": [item.model_dump() for item in linked_facts],
            "entity_resolution_warnings": [
                {
                    "entity_name": item.entity_name,
                    "entity_type": item.entity_type,
                    "reason": item.not_candidate_reason or item.reason,
                }
                for item in unresolved_gaps
            ],
            "candidate_universe_gaps": [
                {
                    "legal_name": item.entity_name,
                    "entity_type": item.entity_type,
                    "resolution_status": item.resolution_status,
                    "source_refs": list(item.source_refs),
                    "reason": item.not_candidate_reason or item.reason,
                }
                for item in unresolved_gaps
            ],
        }
        return RadarEntityResolutionOutput(
            candidate_observations=legal_observations,
            provider_metadata=merge_provider_metadata(provider_metadata or {}, metadata),
        )

    def _classify(
        self,
        observations: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[RadarEntityResolutionResult]]:
        legal_observations: list[dict[str, Any]] = []
        non_account_observations: list[dict[str, Any]] = []
        results: list[RadarEntityResolutionResult] = []
        for raw in observations:
            item = dict(raw)
            name = _entity_name(item)
            if not name:
                continue
            entity_type = _infer_entity_type(item)
            item["entity_type"] = entity_type
            item["entity_resolution_status"] = _default_status(entity_type)
            if entity_type in {"branch", "production_site", "project", "asset"}:
                item["not_candidate_reason"] = str(item.get("not_candidate_reason") or "not_standalone_legal_entity")
                non_account_observations.append(item)
            else:
                if entity_type == "unknown_entity":
                    item.setdefault("review_flags", [])
                    item["review_flags"] = sorted({
                        *[str(flag) for flag in item.get("review_flags", []) if str(flag).strip()],
                        "entity_resolution_review_needed",
                    })
                legal_observations.append(item)
            results.append(RadarEntityResolutionResult(
                entity_name=name,
                entity_type=entity_type,
                resolution_status=item["entity_resolution_status"],
                resolved_legal_name=name if entity_type == "legal_entity" else "",
                source_refs=_source_refs(item),
                reason=_resolution_reason(item, entity_type),
                not_candidate_reason=str(item.get("not_candidate_reason") or ""),
            ))
        return legal_observations, non_account_observations, results

    def _link_non_account_entities(
        self,
        *,
        legal_observations: list[dict[str, Any]],
        non_account_observations: list[dict[str, Any]],
        sources: list[RadarSourceEvidence],
    ) -> tuple[list[RadarLinkedEntityFact], list[RadarEntityResolutionResult]]:
        linked: list[RadarLinkedEntityFact] = []
        unresolved: list[RadarEntityResolutionResult] = []
        legal_names = [_entity_name(item) for item in legal_observations if _entity_name(item)]
        source_refs_by_legal = {name: set(_source_refs(item)) for name, item in zip(legal_names, legal_observations)}
        for item in non_account_observations:
            name = _entity_name(item)
            entity_type = _infer_entity_type(item)
            target = _explicit_legal_link(item, legal_names)
            refs = _source_refs(item)
            if not target:
                target = _source_overlap_link(refs, source_refs_by_legal)
            if not target:
                target = _single_legal_from_same_source(refs, sources, legal_names)
            if target:
                linked.append(RadarLinkedEntityFact(
                    entity_name=name,
                    entity_type=entity_type,
                    linked_legal_name=target,
                    source_refs=refs,
                    reason="Non-account entity was linked to a resolved legal entity.",
                ))
            else:
                unresolved.append(RadarEntityResolutionResult(
                    entity_name=name,
                    entity_type=entity_type,
                    resolution_status="unresolved_gap",
                    source_refs=refs,
                    reason="Non-account entity could not be linked to a legal entity.",
                    not_candidate_reason="entity_type_not_account",
                ))
        return linked, unresolved


def _infer_entity_type(item: dict[str, Any]) -> RadarEntityType:
    explicit = str(item.get("entity_type") or "").strip()
    if explicit in {"legal_entity", "branch", "production_site", "project", "asset", "unknown_entity"}:
        return explicit  # type: ignore[return-value]
    name = _entity_name(item)
    facts = item.get("registry_facts") if isinstance(item.get("registry_facts"), dict) else {}
    if item.get("inn") or item.get("ogrn") or facts.get("inn") or facts.get("ogrn") or _has_legal_form(name):
        return "legal_entity"
    lowered = name.lower()
    if "филиал" in lowered:
        return "branch"
    if re.search(r"\b(e[pr]|э[пр])[-\s]?\d{2,}\b", lowered, flags=re.IGNORECASE) or "проект" in lowered:
        return "project"
    if any(marker in lowered for marker in ("установка", "линия", "цех", "актив")):
        return "asset"
    if any(marker in lowered for marker in ("площадка", "комбинат", "гпз", "нпз", "месторождение")):
        return "production_site"
    if "завод" in lowered and not _has_legal_form(name):
        return "production_site"
    return "unknown_entity"


def _default_status(entity_type: RadarEntityType) -> RadarEntityResolutionStatus:
    if entity_type == "legal_entity":
        return "resolved"
    if entity_type == "unknown_entity":
        return "review_needed"
    return "review_needed"


def _entity_name(item: dict[str, Any]) -> str:
    return str(item.get("legal_name") or item.get("name") or item.get("entity_name") or "").strip()


def _source_refs(item: dict[str, Any]) -> list[str]:
    refs = item.get("evidence_refs", item.get("source_refs", []))
    return [str(ref) for ref in refs if str(ref).strip()] if isinstance(refs, list) else []


def _has_legal_form(value: str) -> bool:
    normalized = value.upper().replace("«", " ").replace("»", " ")
    return bool(re.search(r"(^|\s)(АО|ПАО|ОАО|ЗАО|ООО|НАО|ФГУП|МУП|AО|PJSC|JSC|LLC)(\s|$)", normalized))


def _resolution_reason(item: dict[str, Any], entity_type: RadarEntityType) -> str:
    if entity_type == "legal_entity":
        return "Legal entity identity was supported by registry facts or legal-form naming."
    if entity_type == "unknown_entity":
        return "Entity type is not confirmed; keep for human review."
    return "Entity appears to be a non-account branch, site, project, or asset; keep for upstream review."


def _explicit_legal_link(item: dict[str, Any], legal_names: list[str]) -> str:
    hints = [
        str(item.get(key) or "").strip()
        for key in ("resolved_legal_name", "linked_legal_name", "parent_legal_name", "account_legal_name")
    ]
    for hint in hints:
        if not hint:
            continue
        for legal_name in legal_names:
            if hint.lower() == legal_name.lower() or hint.lower() in legal_name.lower() or legal_name.lower() in hint.lower():
                return legal_name
    return ""


def _source_overlap_link(refs: list[str], refs_by_legal: dict[str, set[str]]) -> str:
    ref_set = set(refs)
    for legal_name, legal_refs in refs_by_legal.items():
        if ref_set and ref_set & legal_refs:
            return legal_name
    return ""


def _single_legal_from_same_source(refs: list[str], sources: list[RadarSourceEvidence], legal_names: list[str]) -> str:
    if len(legal_names) != 1 or not refs:
        return ""
    snippets = " ".join(
        f"{source.title} {source.snippet}"
        for source in sources
        if source.evidence_ref in refs
    ).lower()
    return legal_names[0] if legal_names[0].lower() in snippets else ""
