"""Candidate-universe helpers for staged live Radar execution."""

from __future__ import annotations

import re
from typing import Any

from power_web_os.application.live_radar_contracts import (
    LiveRadarCandidate,
    RadarCandidateUniverseEntry,
    WebSearchProviderResult,
)


def merge_provider_metadata(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = {**existing, **incoming}
    for key in (
        "candidate_universe_gaps",
        "coverage_findings",
        "retrieved_sources",
        "retrieval_source_outcomes",
        "source_outcomes",
        "source_provider_outcomes",
        "source_verification_results",
        "extraction_validation_results",
        "extraction_validation_issues",
        "extraction_repair_results",
        "entity_resolution_results",
        "linked_entity_facts",
        "entity_resolution_warnings",
        "structured_company_observations",
        "upstream_disambiguation_results",
        "cross_source_disambiguation_tasks",
    ):
        merged[key] = [*dict_list(existing.get(key)), *dict_list(incoming.get(key))]
    return merged


def filter_signal_result(result: WebSearchProviderResult, *, allowed_candidate_names: set[str]) -> WebSearchProviderResult:
    allowed = {name.lower() for name in allowed_candidate_names}
    accepted: list[dict[str, Any]] = []
    gaps = dict_list(result.provider_metadata.get("candidate_universe_gaps"))
    for item in result.candidate_observations:
        name = candidate_name(item)
        if name.lower() in allowed:
            accepted.append(item)
        elif name:
            gaps.append({
                "legal_name": name,
                "description": str(item.get("description") or ""),
                "source_refs": list(item.get("evidence_refs", [])) if isinstance(item.get("evidence_refs"), list) else [],
                "reason": "Signal task mentioned a new entity after candidate universe freeze.",
            })
    return result.model_copy(update={
        "candidate_observations": accepted,
        "provider_metadata": {**result.provider_metadata, "candidate_universe_gaps": gaps},
    })


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


def coverage_warnings(result: WebSearchProviderResult) -> list[str]:
    warnings: list[str] = []
    for item in dict_list(result.provider_metadata.get("coverage_findings")):
        if isinstance(item.get("warnings"), list):
            warnings.extend(str(value) for value in item.get("warnings", []) if str(value).strip())
        if str(item.get("completeness_risk") or "") == "high":
            warnings.append(str(item.get("summary") or "Coverage risk is high."))
    return [item for item in warnings if item]


def coverage_risk(result: WebSearchProviderResult) -> str:
    risks = [str(item.get("completeness_risk") or "medium") for item in dict_list(result.provider_metadata.get("coverage_findings"))]
    if "high" in risks:
        return "high"
    if "medium" in risks:
        return "medium"
    if "low" in risks:
        return "low"
    return "medium"


def candidate_universe_entries(
    *,
    candidates: list[LiveRadarCandidate],
    completed_qualification_ids: list[str],
    origin_task_id: str,
    gap_names: set[str],
) -> list[RadarCandidateUniverseEntry]:
    entries: list[RadarCandidateUniverseEntry] = []
    for candidate in candidates:
        rejection_reasons = [
            item.criterion_code
            for item in candidate.qualification
            if item.criterion_code in completed_qualification_ids
            and item.requirement_level == "required"
            and item.final_assessment == "does_not_match"
        ]
        completed_rules = [item for item in candidate.qualification if item.criterion_code in completed_qualification_ids]
        if rejection_reasons:
            status = "rejected"
        elif any(item.final_assessment in {"unknown", "partially_matches"} for item in completed_rules):
            status = "unknown_review_needed"
        elif completed_rules:
            status = "qualified"
        elif candidate.legal_name in gap_names:
            status = "gap"
        else:
            status = "discovered"
        entries.append(RadarCandidateUniverseEntry(
            candidate_id=candidate.candidate_id,
            legal_name=candidate.legal_name,
            status=status,  # type: ignore[arg-type]
            origin_task_id=origin_task_id,
            source_refs=list(candidate.evidence_refs),
            gate_results=[
                {
                    "criterion_code": item.criterion_code,
                    "final_assessment": item.final_assessment,
                    "confidence": item.confidence,
                    "evidence_refs": list(item.evidence_refs),
                }
                for item in candidate.qualification
                if item.criterion_code in completed_qualification_ids
            ],
            rejection_reasons=rejection_reasons,
            coverage_flags=[flag for flag in candidate.review_flags if "candidate_universe" in flag or "coverage" in flag],
        ))
    return entries


def candidate_name_set(observations: list[dict[str, Any]]) -> set[str]:
    return {name.lower() for item in observations for name in [candidate_name(item)] if name}


def candidate_name(item: dict[str, Any]) -> str:
    return str(item.get("legal_name") or item.get("name") or "").strip()


def first_task_id(tasks: list[Any]) -> str:
    return str(tasks[0].task_id) if tasks else ""


def dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def source_refs(item: dict[str, Any]) -> list[str]:
    return [str(ref) for ref in item.get("source_refs", []) if str(ref).strip()] if isinstance(item.get("source_refs"), list) else []


def stable_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ]+", "-", value.lower()).strip("-")
    return normalized or "candidate"
