"""Conservative candidate extraction from retrieved Radar sources."""

from __future__ import annotations

import re
from typing import Any

from power_web_os.application.live_radar_contracts import RadarSourceEvidence, WebSearchProviderResult

_METRIC_ROW_SUFFIX = re.compile(r"(?:,\s*\d+(?:\.\d+)?){2,}\s*$")
_LEGAL_FORM = r"(?:АО|ПАО|ОАО|ЗАО|ООО|НАО|JSC|PJSC|LLC)"
_EMPTY_LEGAL_MARKER = re.compile(rf"^\s*{_LEGAL_FORM}\s*[,.\-–—]*\s*(?:\d|$)", flags=re.IGNORECASE)
_LEGAL_NAME_PATTERN = re.compile(
    rf"\b{_LEGAL_FORM}\s+[«\"]?[^»\"\n\r;:()|]{{3,140}}[»\"]?",
    flags=re.IGNORECASE,
)


def candidates_from_retrieved_sources(
    *,
    radar: dict[str, Any],
    provider_metadata: dict[str, Any],
    known_candidate_names: set[str],
    known_source_refs: set[str],
) -> WebSearchProviderResult:
    """Create review-needed account candidates only from explicit legal names.

    Retrieved source titles/snippets are noisy. This pass intentionally accepts
    only source-backed names with legal-form markers, leaving sites/projects as
    gaps until entity resolution or a later provider result can link them.
    """

    sources: list[RadarSourceEvidence] = []
    observations: list[dict[str, Any]] = []
    extraction_records: list[dict[str, Any]] = []
    seen_names = {name.lower() for name in known_candidate_names}
    for source in _retrieved_source_payloads(provider_metadata):
        source_ref = _source_ref(source)
        if not source_ref:
            continue
        names = _legal_names_from_source(source)
        if not names:
            continue
        if source_ref not in known_source_refs:
            sources.append(_source_evidence(source, source_ref=source_ref))
        for name in names:
            key = name.lower()
            if key in seen_names:
                continue
            seen_names.add(key)
            observations.append(_candidate_observation(radar=radar, legal_name=name, source_ref=source_ref))
            extraction_records.append({
                "legal_name": name,
                "source_ref": source_ref,
                "source_title": str(source.get("title") or ""),
                "reason": "explicit_legal_name_in_retrieved_source",
            })
    if not observations:
        return WebSearchProviderResult()
    return WebSearchProviderResult(
        sources=sources,
        candidate_observations=observations,
        provider_metadata={
            "retrieved_candidate_extractions": extraction_records,
            "retrieved_candidate_extraction_count": len(observations),
        },
    )


def _retrieved_source_payloads(provider_metadata: dict[str, Any]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for key in ("retrieved_sources", "analyzed_sources"):
        value = provider_metadata.get(key)
        if isinstance(value, list):
            payloads.extend(dict(item) for item in value if isinstance(item, dict))
    return payloads


def _source_ref(source: dict[str, Any]) -> str:
    return str(source.get("source_ref") or source.get("evidence_ref") or source.get("id") or "").strip()


def _legal_names_from_source(source: dict[str, Any]) -> list[str]:
    text = " ".join(
        str(source.get(key) or "")
        for key in ("title", "snippet", "summary")
        if str(source.get(key) or "").strip()
    )
    names: list[str] = []
    for match in _LEGAL_NAME_PATTERN.finditer(text):
        name = _clean_legal_name(match.group(0))
        if name and name not in names:
            names.append(name)
    return names


def _clean_legal_name(value: str) -> str:
    if _METRIC_ROW_SUFFIX.search(value) or _EMPTY_LEGAL_MARKER.match(value):
        return ""
    cleaned = " ".join(value.strip(" .,-–—").split())
    cleaned = re.split(r"\s[-–—]\s", cleaned, maxsplit=1)[0].strip()
    cleaned = re.sub(r"\s+[|/].*$", "", cleaned).strip()
    cleaned = cleaned.strip(" .,-–—")
    if (
        len(cleaned) < 5
        or _looks_like_source_title(cleaned)
        or _looks_like_metric_row(cleaned)
        or _looks_sentence_like(cleaned)
    ):
        return ""
    return cleaned


def _looks_like_source_title(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in ("википедия", "wiki", "новости", "официальный сайт"))


def _looks_like_metric_row(value: str) -> bool:
    if _METRIC_ROW_SUFFIX.search(value):
        return True
    parts = [part.strip() for part in value.split(",")]
    numeric_parts = [part for part in parts[1:] if re.fullmatch(r"\d+(?:\.\d+)?", part)]
    return len(parts) >= 3 and len(numeric_parts) >= 2


def _looks_sentence_like(value: str) -> bool:
    words = value.split()
    if len(words) > 12:
        return True
    lowered = value.lower()
    sentence_markers = (
        " is ",
        " are ",
        " has ",
        " have ",
        " reports ",
        " announces ",
        " есть ",
        " сообщает ",
        " описывает ",
    )
    return any(marker in lowered for marker in sentence_markers)


def _source_evidence(source: dict[str, Any], *, source_ref: str) -> RadarSourceEvidence:
    return RadarSourceEvidence(
        evidence_ref=source_ref,
        title=str(source.get("title") or source_ref),
        url=str(source.get("url") or ""),
        snippet=str(source.get("snippet") or source.get("summary") or ""),
        query_id=str(source.get("query_id") or ""),
        source_type=str(source.get("source_type") or "web"),
        verification_state=source.get("verification_state") or "not_checked",
        verification_mode=source.get("verification_mode") or "soft",
        verification_reason=source.get("verification_reason") or "retrieved_source_candidate_extraction",
        verification_status_code=source.get("verification_status_code"),
    )


def _candidate_observation(*, radar: dict[str, Any], legal_name: str, source_ref: str) -> dict[str, Any]:
    qualification = [
        {
            "criterion_code": str(criterion.get("code") or ""),
            "criterion": str(criterion.get("label") or criterion.get("rule") or ""),
            "status": "weak",
            "confidence": "low",
            "rationale": "Retrieved source mentions an explicit legal-entity candidate; qualification requires review.",
            "evidence_refs": [source_ref],
            "evidence_findings": [
                {
                    "source_ref": source_ref,
                    "fact": f"Retrieved source mentions {legal_name}.",
                    "why_it_matches_rule": "The source-backed name is a candidate universe lead, not final qualification proof.",
                }
            ],
        }
        for criterion in radar.get("qualification_criteria", [])
        if isinstance(criterion, dict) and str(criterion.get("code") or "").strip()
    ]
    return {
        "legal_name": legal_name,
        "description": "Candidate extracted from retrieved source and requires qualification review.",
        "evidence_refs": [source_ref],
        "qualification": qualification,
        "signals": [],
        "review_flags": [
            "retrieved_source_candidate_requires_review",
            "candidate_universe_from_retrieved_source",
        ],
        "entity_type": "legal_entity",
        "entity_resolution_status": "review_needed",
    }
