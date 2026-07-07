"""Recall-first admission policy for candidate-discovery upstream leads."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import urlparse

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarQualificationResult,
    RadarSourceEvidence,
)

UpstreamDiscoveryOutcome = Literal[
    "confirmed_upstream_lead",
    "review_needed_upstream_lead",
    "retained_upstream_lead",
    "rejected_noise",
]
ProductAcceptanceStatus = Literal["not_product_accepted", "review_required", "product_candidate"]
UpstreamConfidence = Literal["high", "medium", "low"]

_INDUSTRIAL_MARKERS = (
    "\u0437\u0430\u0432\u043e\u0434",
    "\u043f\u043b\u043e\u0449\u0430\u0434\u043a",
    "\u043f\u0440\u0435\u0434\u043f\u0440\u0438\u044f\u0442",
    "\u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434",
    "\u043d\u0435\u0444\u0442\u0435\u0445\u0438\u043c",
    "\u0445\u0438\u043c",
    "\u043a\u0430\u0443\u0447\u0443\u043a",
    "\u043f\u043e\u043b\u0438\u043c\u0435\u0440",
    "\u0433\u043f\u0437",
    "\u043d\u043f\u0437",
    "plant",
    "site",
    "production",
    "facility",
    "petrochemical",
    "chemical",
    "asset",
    "branch",
)


@dataclass(frozen=True)
class CandidateDiscoveryUpstreamAdmissionDecision:
    upstream_discovery_outcome: UpstreamDiscoveryOutcome
    product_acceptance_status: ProductAcceptanceStatus
    upstream_confidence: UpstreamConfidence
    upstream_reason: str
    upstream_source_refs: list[str] = field(default_factory=list)
    promotes_official_relation: bool = False
    promotes_industrial_evidence: bool = False


class CandidateDiscoveryUpstreamAdmissionPolicy:
    """Decides recall-first upstream retention for candidate discovery.

    Owns:
    - Source-backed upstream lead retention, official-domain promotion, registry
      identity retention, and the split between upstream discovery and strict
      product acceptance.

    Does not own:
    - Signal-monitoring execution, provider calls, downstream account approval,
      or benchmark-specific hardcoded SIBUR entity names.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidate-discovery-upstream-admission-policy
    """

    def decide(
        self,
        *,
        payload: dict[str, Any],
        legal_name: str,
        qualification: list[LiveRadarQualificationResult],
        evidence_refs: list[str],
        sources: list[RadarSourceEvidence],
        radar: dict[str, Any],
    ) -> CandidateDiscoveryUpstreamAdmissionDecision:
        source_refs = _dedupe_refs([*evidence_refs, *_string_list(payload.get("evidence_refs"))])
        sources_by_ref = {source.evidence_ref: source for source in sources}
        supporting_sources = [sources_by_ref[ref] for ref in source_refs if ref in sources_by_ref]
        if _explicitly_rejected(payload, qualification):
            return CandidateDiscoveryUpstreamAdmissionDecision(
                upstream_discovery_outcome="rejected_noise",
                product_acceptance_status="not_product_accepted",
                upstream_confidence="low",
                upstream_reason="Candidate has explicit rejection or invalid supporting evidence.",
                upstream_source_refs=source_refs,
            )

        if _has_concrete_registry_identity(payload):
            confidence: UpstreamConfidence = "high" if _high_quality_registry_identity(payload) else "medium"
            return CandidateDiscoveryUpstreamAdmissionDecision(
                upstream_discovery_outcome="confirmed_upstream_lead" if confidence == "high" else "retained_upstream_lead",
                product_acceptance_status=_product_acceptance(qualification, high_confidence=confidence == "high"),
                upstream_confidence=confidence,
                upstream_reason="Structured registry identity was retained as source-backed upstream evidence.",
                upstream_source_refs=source_refs,
            )

        if supporting_sources and qualification and all(item.final_assessment == "matches" for item in qualification):
            return CandidateDiscoveryUpstreamAdmissionDecision(
                upstream_discovery_outcome="confirmed_upstream_lead",
                product_acceptance_status=_product_acceptance(qualification, high_confidence=True),
                upstream_confidence="high",
                upstream_reason="Source-backed qualification evidence already satisfies the candidate-discovery rules.",
                upstream_source_refs=source_refs,
            )

        official_sources = _official_sources(
            sources=supporting_sources,
            radar=radar,
        )
        official_name_match = any(_name_matches_source(legal_name, source) for source in official_sources)
        industrial_evidence = any(_has_industrial_marker(_source_text(source)) for source in official_sources)
        if official_sources and official_name_match:
            return CandidateDiscoveryUpstreamAdmissionDecision(
                upstream_discovery_outcome="confirmed_upstream_lead",
                product_acceptance_status=_product_acceptance(qualification, high_confidence=True),
                upstream_confidence="high",
                upstream_reason="High-trust official source mentions the candidate name or alias.",
                upstream_source_refs=source_refs,
                promotes_official_relation=True,
                promotes_industrial_evidence=industrial_evidence,
            )

        if supporting_sources:
            if official_sources:
                return CandidateDiscoveryUpstreamAdmissionDecision(
                    upstream_discovery_outcome="retained_upstream_lead",
                    product_acceptance_status="review_required",
                    upstream_confidence="medium",
                    upstream_reason="High-trust official source supports the lead, but name relation needs review.",
                    upstream_source_refs=source_refs,
                    promotes_industrial_evidence=industrial_evidence,
                )
            return CandidateDiscoveryUpstreamAdmissionDecision(
                upstream_discovery_outcome="review_needed_upstream_lead",
                product_acceptance_status="review_required",
                upstream_confidence="medium",
                upstream_reason="Open-web source-backed candidate retained for upstream review.",
                upstream_source_refs=source_refs,
            )

        if source_refs:
            return CandidateDiscoveryUpstreamAdmissionDecision(
                upstream_discovery_outcome="review_needed_upstream_lead",
                product_acceptance_status="review_required",
                upstream_confidence="low",
                upstream_reason="Candidate carries source refs that are not present in the source index.",
                upstream_source_refs=source_refs,
            )

        return CandidateDiscoveryUpstreamAdmissionDecision(
            upstream_discovery_outcome="review_needed_upstream_lead",
            product_acceptance_status="not_product_accepted",
            upstream_confidence="low",
            upstream_reason="No source refs or concrete registry identity were available.",
            upstream_source_refs=[],
        )


def _product_acceptance(
    qualification: list[LiveRadarQualificationResult],
    *,
    high_confidence: bool,
) -> ProductAcceptanceStatus:
    if high_confidence and qualification and all(item.final_assessment == "matches" for item in qualification):
        return "product_candidate"
    return "review_required"


def _official_sources(
    *,
    sources: list[RadarSourceEvidence],
    radar: dict[str, Any],
) -> list[RadarSourceEvidence]:
    official_domains = _official_domains(radar)
    result: list[RadarSourceEvidence] = []
    for source in sources:
        if str(source.verification_state or "") == "invalid_url":
            continue
        domain = _host(source.url)
        if not domain:
            continue
        if any(domain == official or domain.endswith(f".{official}") for official in official_domains):
            result.append(source)
    return result


def _official_domains(radar: dict[str, Any]) -> set[str]:
    policy = radar.get("global_search_policy") if isinstance(radar.get("global_search_policy"), dict) else {}
    result: set[str] = set()
    for source in policy.get("sources", []) if isinstance(policy.get("sources"), list) else []:
        if not isinstance(source, dict):
            continue
        trust_level = str(source.get("trust_level") or source.get("trust") or "").casefold()
        source_type = str(source.get("source_type") or source.get("type") or "").casefold()
        if trust_level != "high":
            continue
        if source_type and source_type not in {"url", "website", "official_website", "web", "site"}:
            continue
        for key in ("reference", "url", "source_id", "domain"):
            host = _host(str(source.get(key) or ""))
            if host:
                result.add(host)
    return result


def _host(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = urlparse(text if "://" in text else f"https://{text}")
    host = (parsed.netloc or parsed.path.split("/", 1)[0]).casefold().strip()
    return host.removeprefix("www.")


def _source_text(source: RadarSourceEvidence) -> str:
    return " ".join(str(value or "") for value in (source.title, source.snippet, source.url)).casefold()


def _name_matches_source(name: str, source: RadarSourceEvidence) -> bool:
    normalized_name = _normalize_name(name)
    text = _normalize_name(_source_text(source))
    if normalized_name and normalized_name in text:
        return True
    tokens = {token for token in normalized_name.split() if len(token) >= 4 and token not in {"sibur"}}
    text_tokens = set(text.split())
    return bool(len(tokens) >= 1 and tokens.issubset(text_tokens))


def _has_industrial_marker(text: str) -> bool:
    normalized = text.casefold().replace("\u0451", "\u0435")
    return any(marker in normalized for marker in _INDUSTRIAL_MARKERS)


def _normalize_name(value: str) -> str:
    text = str(value or "").casefold().replace("\u0451", "\u0435")
    text = re.sub(r"[\"'\u00ab\u00bb.,()\[\]]", " ", text)
    text = re.sub(r"\b(ooo|oao|ao|pao|zao|nao|llc|jsc|pjsc|inc|ltd)\b", " ", text)
    text = re.sub(
        r"\b(\u043e\u043e\u043e|\u043e\u0430\u043e|\u0430\u043e|\u043f\u0430\u043e|\u0437\u0430\u043e|\u043d\u0430\u043e)\b",
        " ",
        text,
    )
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def _has_concrete_registry_identity(payload: dict[str, Any]) -> bool:
    if _digits(payload.get("inn")) or _digits(payload.get("ogrn")):
        return True
    facts = payload.get("registry_facts")
    if isinstance(facts, dict):
        return any(str(facts.get(key) or "").strip() for key in ("inn", "ogrn", "legal_name", "name"))
    return False


def _high_quality_registry_identity(payload: dict[str, Any]) -> bool:
    if _digits(payload.get("inn")) or _digits(payload.get("ogrn")):
        return True
    quality = str(payload.get("match_quality") or "").casefold()
    return quality in {"exact", "high", "resolved"}


def _explicitly_rejected(payload: dict[str, Any], qualification: list[LiveRadarQualificationResult]) -> bool:
    if str(payload.get("entity_resolution_status") or "") == "rejected":
        return True
    if str(payload.get("not_candidate_reason") or "") in {"invalid_url", "explicitly_rejected", "rejected_noise"}:
        return True
    return bool(qualification and all(item.status == "rejected" for item in qualification))


def _digits(value: object) -> str:
    return re.sub(r"\D+", "", str(value or ""))


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _dedupe_refs(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        ref = str(value).strip()
        if ref and ref not in seen:
            seen.add(ref)
            result.append(ref)
    return result
