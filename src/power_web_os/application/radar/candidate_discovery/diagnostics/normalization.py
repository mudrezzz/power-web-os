"""Normalize provider observations into live Radar candidate contracts."""

from __future__ import annotations

import re
from typing import Any, Literal

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarCandidate,
    LiveRadarQualificationResult,
    LiveRadarScore,
    LiveRadarSignalResult,
    QualificationAssessment,
    QualificationCrossValidation,
    QualificationEvidenceFinding,
    QualificationRequirement,
    QualificationRequirementEvaluation,
    QualificationSourceUsage,
    QualificationStatus,
    QualificationTrustPolicy,
    RadarSourceEvidence,
    SignalEvidenceFinding,
    SignalScoreEvaluation,
    SignalStatus,
)
from power_web_os.application.radar.candidate_discovery.diagnostics.collections import (
    dedupe_sources as _dedupe_sources,
    rank_candidates as _rank_candidates,
)
from power_web_os.application.radar.candidate_discovery.diagnostics.contract_validation import (
    validate_live_radar_qualification_contract,
)
from power_web_os.application.radar.candidate_discovery.diagnostics.upstream_projection import (
    product_acceptance_status as _product_acceptance_status,
    promote_upstream_qualification as _promote_upstream_qualification,
    upstream_tier as _upstream_tier,
)
from power_web_os.application.radar.candidate_discovery.sources.risk import (
    refs_are_only_risky as _refs_are_only_risky,
    refs_have_verification_risk as _refs_have_verification_risk,
    source_supports_evidence as _source_supports_evidence,
)
from power_web_os.application.radar.candidate_discovery.universe.admission import (
    CandidateDiscoveryUpstreamAdmissionPolicy,
)

def normalize_live_candidate(
    payload: dict[str, Any],
    *,
    radar: dict[str, Any],
    sources: list[RadarSourceEvidence] | None = None,
) -> LiveRadarCandidate:
    legal_name = str(payload.get("legal_name") or payload.get("name") or "Unknown candidate").strip()
    qualification = _normalize_qualification(payload.get("qualification", []), radar, sources=sources or [])
    signals = _normalize_signals(payload.get("signals", []), radar, sources=sources or [])
    source_refs = sorted({
        ref
        for collection in [qualification, signals]
        for item in collection
        for ref in item.evidence_refs
    })
    admission = CandidateDiscoveryUpstreamAdmissionPolicy().decide(
        payload=payload,
        legal_name=legal_name,
        qualification=qualification,
        evidence_refs=source_refs,
        sources=sources or [],
        radar=radar,
    )
    qualification = _promote_upstream_qualification(qualification, admission)
    fit_score = sum(1 for item in qualification if item.status == "confirmed")
    intent_score = sum(item.score for item in signals if item.status == "observed")
    tier = _upstream_tier(admission.upstream_discovery_outcome)
    product_acceptance_status = _product_acceptance_status(admission.upstream_discovery_outcome, qualification)
    review_flags = [str(item) for item in payload.get("review_flags", []) if str(item).strip()]
    if any(item.status in {"weak", "unknown"} for item in qualification):
        review_flags.append("qualification_requires_human_review")
    if any(item.status == "unclear" and not item.search_status.startswith("not_searched") for item in signals):
        review_flags.append("signal_requires_human_review")
    if any(_refs_have_verification_risk(item.evidence_refs, sources or []) for item in [*qualification, *signals]):
        review_flags.append("source_verification_review")
    evidence_refs = sorted({*source_refs, *admission.upstream_source_refs})
    return LiveRadarCandidate(
        candidate_id=_stable_id(legal_name),
        legal_name=legal_name,
        description=str(payload.get("description") or ""),
        qualification=qualification,
        signals=signals,
        score=LiveRadarScore(fit_score=fit_score, intent_score=intent_score, tier=tier),
        review_flags=sorted(set(review_flags)),
        evidence_refs=evidence_refs,
        upstream_discovery_outcome=admission.upstream_discovery_outcome,
        product_acceptance_status=product_acceptance_status,
        upstream_confidence=admission.upstream_confidence,
        upstream_reason=admission.upstream_reason,
        upstream_source_refs=list(admission.upstream_source_refs),
    )


def _normalize_qualification(
    payload: Any,
    radar: dict[str, Any],
    *,
    sources: list[RadarSourceEvidence],
) -> list[LiveRadarQualificationResult]:
    by_code = {
        str(item.get("criterion_code", item.get("code", ""))): item
        for item in payload
        if isinstance(item, dict)
    } if isinstance(payload, list) else {}
    sources_by_ref = {source.evidence_ref: source for source in sources}
    results = []
    for criterion in radar["qualification_criteria"]:
        raw = by_code.get(criterion["code"], {})
        status = _normalize_choice(str(raw.get("status", "unknown")), {"confirmed", "weak", "unknown", "rejected"}, "unknown")
        evidence_refs = [
            str(ref)
            for ref in raw.get("evidence_refs", [])
            if _source_supports_evidence(sources_by_ref.get(str(ref)))
        ]
        confidence = str(raw.get("confidence", "low"))
        if status in {"confirmed", "weak"} and not evidence_refs:
            status = "unknown"
        elif status == "confirmed" and _refs_are_only_risky(evidence_refs, sources_by_ref):
            status = "weak"
            confidence = "low"
        operator = _normalize_choice(str(raw.get("operator") or criterion.get("operator") or "AND"), {"AND", "OR", "AND_NOT", "OR_NOT"}, "AND")
        requirement_level = _normalize_choice(
            str(raw.get("requirement_level") or criterion.get("requirement_level") or "required"),
            {"required", "recommended"},
            "required",
        )
        final_assessment = _qualification_status_to_assessment(status)
        confidence_policy = _confidence_to_policy(confidence, evidence_refs=evidence_refs)
        cross_validation_required = bool(raw.get("cross_validation_required", criterion.get("cross_validation_required", False)))
        source_usages = _qualification_source_usages(evidence_refs=evidence_refs, sources_by_ref=sources_by_ref, policy=confidence_policy)
        evidence_findings = _qualification_evidence_findings(
            raw=raw,
            evidence_refs=evidence_refs,
            sources_by_ref=sources_by_ref,
            status=status,
            rationale=str(raw.get("rationale") or raw.get("summary") or "No qualification evidence found."),
        )
        cross_validation = _qualification_cross_validation(
            required=cross_validation_required,
            evidence_refs=evidence_refs,
            final_assessment=final_assessment,
        )
        requirement_evaluation = _qualification_requirement_evaluation(
            requirement_level=requirement_level,  # type: ignore[arg-type]
            final_assessment=final_assessment,
            rationale=str(raw.get("rationale") or raw.get("summary") or "No qualification evidence found."),
        )
        results.append(LiveRadarQualificationResult(
            criterion_code=criterion["code"],
            criterion=criterion["label"],
            status=status,  # type: ignore[arg-type]
            confidence=confidence,
            rationale=str(raw.get("rationale") or raw.get("summary") or "No qualification evidence found."),
            evidence_refs=evidence_refs,
            rule_id=str(raw.get("rule_id") or criterion["code"]),
            rule_text_snapshot=str(raw.get("rule_text_snapshot") or raw.get("criterion") or criterion["label"]),
            operator=operator,  # type: ignore[arg-type]
            requirement_level=requirement_level,  # type: ignore[arg-type]
            confidence_policy=confidence_policy,
            source_usages=source_usages,
            evidence_findings=evidence_findings,
            cross_validation=cross_validation,
            requirement_evaluation=requirement_evaluation,
            final_assessment=final_assessment,
            review_decision=None,
        ))
    return results


def _qualification_status_to_assessment(status: QualificationStatus) -> QualificationAssessment:
    if status == "confirmed":
        return "matches"
    if status == "weak":
        return "partially_matches"
    if status == "rejected":
        return "does_not_match"
    return "unknown"


def _confidence_to_policy(confidence: str, *, evidence_refs: list[str]) -> QualificationTrustPolicy:
    if confidence == "high" and len(evidence_refs) > 1:
        return "cross_checked"
    if confidence == "high" and evidence_refs:
        return "trusted"
    return "hitl_required"


def _qualification_source_usages(
    *,
    evidence_refs: list[str],
    sources_by_ref: dict[str, RadarSourceEvidence],
    policy: QualificationTrustPolicy,
) -> list[QualificationSourceUsage]:
    usages = []
    for ref in evidence_refs:
        source = sources_by_ref.get(ref)
        if source is None:
            continue
        usages.append(QualificationSourceUsage(
            source_ref=ref,
            source_name=source.title,
            source_origin="additional",
            trust_policy=policy,
            used_for="verification",
            url=source.url,
        ))
    return usages


def _qualification_evidence_findings(
    *,
    raw: dict[str, Any],
    evidence_refs: list[str],
    sources_by_ref: dict[str, RadarSourceEvidence],
    status: QualificationStatus,
    rationale: str,
) -> list[QualificationEvidenceFinding]:
    raw_findings = raw.get("evidence_findings")
    if isinstance(raw_findings, list):
        findings = []
        for item in raw_findings:
            if not isinstance(item, dict):
                continue
            source_ref = str(item.get("source_ref") or item.get("evidence_ref") or "")
            if source_ref not in evidence_refs:
                continue
            findings.append(QualificationEvidenceFinding(
                source_ref=source_ref,
                fact=str(item.get("fact") or item.get("quote_or_fact") or sources_by_ref[source_ref].snippet),
                excerpt=str(item.get("excerpt") or item.get("quote") or item.get("snippet") or ""),
                excerpt_type=_excerpt_type(item),
                why_it_matches_rule=str(item.get("why_it_matches_rule") or rationale),
                evidence_strength=_evidence_strength(status),
                contradicts_rule=bool(item.get("contradicts_rule", status == "rejected")),
            ))
        if findings:
            return findings
    return [
        QualificationEvidenceFinding(
            source_ref=ref,
            fact=sources_by_ref[ref].snippet,
            excerpt="",
            excerpt_type="not_available",
            why_it_matches_rule=rationale,
            evidence_strength=_evidence_strength(status),
            contradicts_rule=status == "rejected",
        )
        for ref in evidence_refs
        if ref in sources_by_ref
    ]


def _excerpt_type(item: dict[str, Any]) -> Literal["quote", "paraphrase", "not_available"]:
    value = str(item.get("excerpt_type") or "")
    if value == "quote":
        return "quote"
    if value == "paraphrase":
        return "paraphrase"
    if value == "not_available":
        return "not_available"
    if item.get("excerpt") or item.get("quote") or item.get("snippet"):
        return "paraphrase"
    return "not_available"


def _evidence_strength(status: QualificationStatus) -> Literal["strong", "medium", "weak"]:
    if status == "confirmed":
        return "strong"
    if status == "weak":
        return "medium"
    return "weak"


def _qualification_cross_validation(
    *,
    required: bool,
    evidence_refs: list[str],
    final_assessment: QualificationAssessment,
) -> QualificationCrossValidation:
    if not required:
        return QualificationCrossValidation(required=False, status="not_required", source_count=len(evidence_refs), notes="Cross-validation is not required for this rule.")
    if len(evidence_refs) > 1 and final_assessment in {"matches", "partially_matches"}:
        return QualificationCrossValidation(required=True, status="passed", source_count=len(evidence_refs), notes="Multiple sources support the rule.")
    if evidence_refs:
        return QualificationCrossValidation(required=True, status="weak", source_count=len(evidence_refs), notes="Only one source supports the rule; human review is recommended.")
    return QualificationCrossValidation(required=True, status="failed", source_count=0, notes="No source evidence was found for required cross-validation.")


def _qualification_requirement_evaluation(
    *,
    requirement_level: QualificationRequirement,
    final_assessment: QualificationAssessment,
    rationale: str,
) -> QualificationRequirementEvaluation:
    satisfied = final_assessment == "matches" or (requirement_level == "recommended" and final_assessment == "partially_matches")
    if final_assessment == "unknown":
        satisfied_value: bool | None = None
    else:
        satisfied_value = satisfied
    return QualificationRequirementEvaluation(
        requirement_level=requirement_level,
        satisfied=satisfied_value,
        explanation=rationale,
    )


def _normalize_signals(
    payload: Any,
    radar: dict[str, Any],
    *,
    sources: list[RadarSourceEvidence],
) -> list[LiveRadarSignalResult]:
    by_code = {
        str(item.get("signal_code", item.get("code", ""))): item
        for item in payload
        if isinstance(item, dict)
    } if isinstance(payload, list) else {}
    sources_by_ref = {source.evidence_ref: source for source in sources}
    results = []
    for signal in radar["intent_signals"]:
        raw = by_code.get(signal["code"], {})
        status = _normalize_choice(str(raw.get("status", "not_observed")), {"observed", "not_observed", "unclear"}, "not_observed")
        search_status = str(raw.get("search_status") or "searched")
        not_searched_reason = str(raw.get("not_searched_reason") or "") or None
        if search_status.startswith("not_searched"):
            status = "unclear"
        raw_score = raw.get("score", 0)
        try:
            score = max(0, min(2, int(raw_score)))
        except (TypeError, ValueError):
            score = 0
        if status != "observed":
            score = 0
        evidence_refs = [
            str(ref)
            for ref in raw.get("evidence_refs", [])
            if _source_supports_evidence(sources_by_ref.get(str(ref)))
        ]
        confidence = str(raw.get("confidence", "low"))
        if status == "observed" and not evidence_refs:
            status = "not_observed"
            score = 0
        elif status == "observed" and _refs_are_only_risky(evidence_refs, sources_by_ref):
            status = "unclear"
            score = 0
            confidence = "low"
        summary = str(raw.get("summary") or "No signal evidence found.")
        source_policy = _confidence_to_policy(confidence, evidence_refs=evidence_refs)
        source_usages = _qualification_source_usages(evidence_refs=evidence_refs, sources_by_ref=sources_by_ref, policy=source_policy)
        evidence_findings = _signal_evidence_findings(
            raw=raw,
            evidence_refs=evidence_refs,
            sources_by_ref=sources_by_ref,
            status=status,  # type: ignore[arg-type]
            score=score,
            summary=summary,
        )
        cross_validation = _qualification_cross_validation(
            required=source_policy == "cross_checked",
            evidence_refs=evidence_refs,
            final_assessment="matches" if status == "observed" else "unknown",
        )
        score_evaluation = _signal_score_evaluation(raw=raw, score=score, status=status, summary=summary)  # type: ignore[arg-type]
        results.append(LiveRadarSignalResult(
            signal_code=signal["code"],
            signal=signal["label"],
            status=status,  # type: ignore[arg-type]
            search_status=search_status,
            not_searched_reason=not_searched_reason,
            score=score,
            confidence=confidence,
            summary=summary,
            evidence_refs=evidence_refs,
            source_usages=source_usages,
            evidence_findings=evidence_findings,
            cross_validation=cross_validation,
            score_evaluation=score_evaluation,
        ))
    return results


def _signal_evidence_findings(
    *,
    raw: dict[str, Any],
    evidence_refs: list[str],
    sources_by_ref: dict[str, RadarSourceEvidence],
    status: SignalStatus,
    score: int,
    summary: str,
) -> list[SignalEvidenceFinding]:
    raw_findings = raw.get("evidence_findings")
    if isinstance(raw_findings, list):
        findings = []
        for item in raw_findings:
            if not isinstance(item, dict):
                continue
            source_ref = str(item.get("source_ref") or item.get("evidence_ref") or "")
            if source_ref not in evidence_refs:
                continue
            source = sources_by_ref[source_ref]
            findings.append(SignalEvidenceFinding(
                source_ref=source_ref,
                fact=str(item.get("fact") or item.get("quote_or_fact") or source.snippet),
                excerpt=str(item.get("excerpt") or item.get("quote") or item.get("snippet") or ""),
                excerpt_type=_excerpt_type(item),
                why_it_matches_signal=str(item.get("why_it_matches_signal") or item.get("why_it_matches_rule") or summary),
                why_score_applies=str(item.get("why_score_applies") or _signal_score_rationale(score=score, status=status, summary=summary)),
                evidence_strength=_signal_evidence_strength(status=status, score=score),
                contradicts_signal=bool(item.get("contradicts_signal", status == "not_observed")),
            ))
        if findings:
            return findings
    return [
        SignalEvidenceFinding(
            source_ref=ref,
            fact=sources_by_ref[ref].snippet,
            excerpt="",
            excerpt_type="not_available",
            why_it_matches_signal=summary,
            why_score_applies=_signal_score_rationale(score=score, status=status, summary=summary),
            evidence_strength=_signal_evidence_strength(status=status, score=score),
            contradicts_signal=status == "not_observed",
        )
        for ref in evidence_refs
        if ref in sources_by_ref
    ]


def _signal_score_evaluation(
    *,
    raw: dict[str, Any],
    score: int,
    status: SignalStatus,
    summary: str,
) -> SignalScoreEvaluation:
    raw_evaluation = raw.get("score_evaluation")
    if isinstance(raw_evaluation, dict):
        try:
            applied_score = max(0, min(2, int(raw_evaluation.get("applied_score", score))))
        except (TypeError, ValueError):
            applied_score = score
        return SignalScoreEvaluation(
            scale=str(raw_evaluation.get("scale") or "0-2"),
            applied_score=applied_score,
            max_score=2,
            rule_snapshot=str(raw_evaluation.get("rule_snapshot") or _signal_score_rule(score)),
            explanation=str(raw_evaluation.get("explanation") or _signal_score_rationale(score=score, status=status, summary=summary)),
        )
    return SignalScoreEvaluation(
        scale="0-2",
        applied_score=score,
        max_score=2,
        rule_snapshot=_signal_score_rule(score),
        explanation=_signal_score_rationale(score=score, status=status, summary=summary),
    )


def _signal_score_rule(score: int) -> str:
    if score >= 2:
        return "Score 2 applies when the signal is directly supported by relevant source evidence."
    if score == 1:
        return "Score 1 applies when the signal is weak, indirect, or requires human review."
    return "Score 0 applies when the signal is not observed or not source-backed."


def _signal_score_rationale(*, score: int, status: SignalStatus, summary: str) -> str:
    if status != "observed":
        return "The signal does not currently contribute to intent score because it is not observed or remains unclear."
    return f"Score {score} is based on the observed signal summary: {summary}"


def _signal_evidence_strength(*, status: SignalStatus, score: int) -> Literal["strong", "medium", "weak"]:
    if status == "observed" and score >= 2:
        return "strong"
    if status == "observed":
        return "medium"
    return "weak"


def _normalize_choice(value: str, allowed: set[str], fallback: str) -> str:
    return value if value in allowed else fallback


def _stable_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ]+", "-", value.lower()).strip("-")
    return normalized or "candidate"
