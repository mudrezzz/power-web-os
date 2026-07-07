"""Projection helpers for upstream admission decisions."""

from __future__ import annotations

from power_web_os.application.radar.candidate_discovery.contracts import LiveRadarQualificationResult
from power_web_os.application.radar.candidate_discovery.universe.admission import (
    CandidateDiscoveryUpstreamAdmissionDecision,
)


def upstream_tier(outcome: str) -> str:
    if outcome == "confirmed_upstream_lead":
        return "Upstream confirmed"
    if outcome == "review_needed_upstream_lead":
        return "Upstream review"
    if outcome == "retained_upstream_lead":
        return "Upstream retained"
    return "Rejected noise"


def promote_upstream_qualification(
    qualification: list[LiveRadarQualificationResult],
    admission: CandidateDiscoveryUpstreamAdmissionDecision,
) -> list[LiveRadarQualificationResult]:
    if not admission.promotes_official_relation:
        return qualification
    promoted: list[LiveRadarQualificationResult] = []
    for item in qualification:
        should_promote = item.status in {"weak", "unknown"} and bool(item.evidence_refs)
        if should_promote:
            rationale = item.rationale
            if admission.promotes_industrial_evidence:
                rationale = f"{rationale} Official source and industrial context support upstream qualification."
            else:
                rationale = f"{rationale} Official source supports upstream relation evidence."
            promoted.append(
                item.model_copy(
                    update={
                        "status": "confirmed",
                        "confidence": "high",
                        "rationale": rationale,
                        "final_assessment": "matches",
                        "confidence_policy": "trusted",
                    }
                )
            )
            continue
        promoted.append(item)
    return promoted


def product_acceptance_status(
    upstream_outcome: str,
    qualification: list[LiveRadarQualificationResult],
) -> str:
    if (
        upstream_outcome == "confirmed_upstream_lead"
        and qualification
        and all(item.final_assessment == "matches" for item in qualification)
    ):
        return "product_candidate"
    if upstream_outcome in {"confirmed_upstream_lead", "review_needed_upstream_lead", "retained_upstream_lead"}:
        return "review_required"
    return "not_product_accepted"
