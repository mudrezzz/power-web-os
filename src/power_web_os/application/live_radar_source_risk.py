"""Source verification risk helpers for live Radar normalization."""

from __future__ import annotations

from power_web_os.application.radar.candidate_discovery.contracts import RadarSourceEvidence


def source_supports_evidence(source: RadarSourceEvidence | None) -> bool:
    return source is not None and source.verification_state != "invalid_url"


def source_has_verification_risk(source: RadarSourceEvidence | None) -> bool:
    return source is not None and source.verification_state in {"blocked", "timeout", "unverified_url", "not_checked"}


def refs_are_only_risky(evidence_refs: list[str], sources_by_ref: dict[str, RadarSourceEvidence]) -> bool:
    if not evidence_refs:
        return False
    return all(source_has_verification_risk(sources_by_ref.get(ref)) for ref in evidence_refs)


def refs_have_verification_risk(evidence_refs: list[str], sources: list[RadarSourceEvidence]) -> bool:
    sources_by_ref = {source.evidence_ref: source for source in sources}
    return any(source_has_verification_risk(sources_by_ref.get(ref)) for ref in evidence_refs)
