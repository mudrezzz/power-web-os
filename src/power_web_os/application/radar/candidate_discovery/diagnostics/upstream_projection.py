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


def product_acceptance_reason(
    *,
    product_acceptance_status: str,
    upstream_reason: str,
    qualification: list[LiveRadarQualificationResult],
) -> str:
    if product_acceptance_status == "product_candidate":
        return "deterministic_qualification_and_upstream_evidence_passed"
    if any(item.final_assessment == "does_not_match" for item in qualification):
        return "required_product_qualification_rejected"
    if any(item.final_assessment in {"unknown", "partially_matches"} for item in qualification):
        return "requires_human_review_before_product_acceptance"
    return upstream_reason or "insufficient_product_acceptance_evidence"
