from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CRITERION_CODES = tuple(f"C{index}" for index in range(1, 21))
FIT_CRITERIA = tuple(f"C{index}" for index in range(13, 18))
INTENT_CRITERIA = tuple([*(f"C{index}" for index in range(1, 10)), "C18", "C19"])
TRIGGER_CRITERIA = ("C10", "C11", "C12", "C20")


@dataclass(frozen=True, slots=True)
class ICPProfile:
    profile_id: str
    name: str
    product: str
    holding: str
    run_mode: str
    source_workbook: str
    scoring_formula: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SignalCriterion:
    code: str
    name: str
    description: str
    scoring_guidance: str


@dataclass(frozen=True, slots=True)
class EvidenceSource:
    source_id: str
    url: str
    usage: str


@dataclass(frozen=True, slots=True)
class RadarDefinition:
    definition_id: str
    product: str
    segment: str
    holding: str
    market_scope: str
    exclusions: tuple[str, ...]
    assumptions: tuple[str, ...]
    legal_entity_source: str
    discovery_mode: str
    discovery_filters: tuple[str, ...]
    monitoring_sources: tuple[str, ...]
    cadence: str
    lookback_window: str
    run_mode: str
    scoring_formula: dict[str, Any]
    tier_thresholds: dict[str, str]
    criteria: tuple[SignalCriterion, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ICPRadarScore:
    fit_score: int
    intent_score: int
    trigger_score: int
    total_score: int
    tier: str


@dataclass(frozen=True, slots=True)
class CriterionEvidenceFact:
    evidence_ref: str
    source_url: str
    fact: str
    why_it_matters: str


@dataclass(frozen=True, slots=True)
class CriterionEvidenceExplanation:
    criterion_code: str
    score: int
    evidence_origin: str
    evidence_status: str
    confidence: str
    rationale: str
    evidence_refs: tuple[str, ...]
    source_urls: tuple[str, ...]
    facts: tuple[CriterionEvidenceFact, ...]


@dataclass(frozen=True, slots=True)
class ICPRadarCandidate:
    rank: int
    account_id: str
    ppo: str
    legal_name: str
    account_type: str
    description: str
    inn: str
    revenue: str
    site: str
    confidence: str
    signal_summary: str
    main_signal: str
    comment: str
    source_urls: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    criteria_scores: dict[str, int]
    criteria_evidence: dict[str, CriterionEvidenceExplanation]
    score: ICPRadarScore


@dataclass(frozen=True, slots=True)
class ICPRadarArtifact:
    profile: ICPProfile
    criteria: tuple[SignalCriterion, ...]
    sources: tuple[EvidenceSource, ...]
    definition: RadarDefinition
    candidates: tuple[ICPRadarCandidate, ...]
    workflow_metadata: dict[str, Any]


class ICPRadar:
    def build_score(self, criteria_scores: dict[str, int]) -> ICPRadarScore:
        normalized = {code: int(criteria_scores.get(code, 0)) for code in CRITERION_CODES}
        fit_score = sum(normalized[code] for code in FIT_CRITERIA)
        intent_score = sum(normalized[code] for code in INTENT_CRITERIA)
        trigger_score = sum(normalized[code] for code in TRIGGER_CRITERIA)
        total_score = sum(normalized.values())
        return ICPRadarScore(
            fit_score=fit_score,
            intent_score=intent_score,
            trigger_score=trigger_score,
            total_score=total_score,
            tier=self._tier(total_score),
        )

    def rank(self, candidates: list[ICPRadarCandidate]) -> tuple[ICPRadarCandidate, ...]:
        ranked = sorted(
            candidates,
            key=lambda item: (-item.score.total_score, -item.score.intent_score, item.legal_name),
        )
        return tuple(
            ICPRadarCandidate(
                rank=index,
                account_id=item.account_id,
                ppo=item.ppo,
                legal_name=item.legal_name,
                account_type=item.account_type,
                description=item.description,
                inn=item.inn,
                revenue=item.revenue,
                site=item.site,
                confidence=item.confidence,
                signal_summary=item.signal_summary,
                main_signal=item.main_signal,
                comment=item.comment,
                source_urls=item.source_urls,
                evidence_refs=item.evidence_refs,
                criteria_scores=item.criteria_scores,
                criteria_evidence=item.criteria_evidence,
                score=item.score,
            )
            for index, item in enumerate(ranked, start=1)
        )

    @staticmethod
    def _tier(total_score: int) -> str:
        if total_score >= 38:
            return "Tier 1"
        if total_score >= 25:
            return "Tier 2"
        if total_score >= 15:
            return "Tier 3"
        return "Monitor"


def icp_radar_artifact_to_payload(artifact: ICPRadarArtifact) -> dict[str, Any]:
    return {
        "artifact_type": "icp_radar",
        "artifact_version": "0.6.2.5",
        "criteria_evidence_contract_version": "0.6.2.3",
        "radar": {
            "profile": profile_to_payload(artifact.profile),
            "definition": radar_definition_to_payload(artifact.definition),
            "criteria": [criterion_to_payload(item) for item in artifact.criteria],
            "sources": [source_to_payload(item) for item in artifact.sources],
        },
        "candidates": [candidate_to_payload(item) for item in artifact.candidates],
        "workflow_metadata": artifact.workflow_metadata,
    }


def profile_to_payload(profile: ICPProfile) -> dict[str, Any]:
    return {
        "profile_id": profile.profile_id,
        "name": profile.name,
        "product": profile.product,
        "holding": profile.holding,
        "run_mode": profile.run_mode,
        "source_workbook": profile.source_workbook,
        "scoring_formula": profile.scoring_formula,
    }


def criterion_to_payload(criterion: SignalCriterion) -> dict[str, Any]:
    return {
        "code": criterion.code,
        "name": criterion.name,
        "description": criterion.description,
        "scoring_guidance": criterion.scoring_guidance,
    }


def source_to_payload(source: EvidenceSource) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "url": source.url,
        "usage": source.usage,
    }


def radar_definition_to_payload(definition: RadarDefinition) -> dict[str, Any]:
    return {
        "definition_id": definition.definition_id,
        "product": definition.product,
        "segment": definition.segment,
        "holding": definition.holding,
        "market_scope": definition.market_scope,
        "exclusions": list(definition.exclusions),
        "assumptions": list(definition.assumptions),
        "legal_entity_source": definition.legal_entity_source,
        "discovery_mode": definition.discovery_mode,
        "discovery_filters": list(definition.discovery_filters),
        "monitoring_sources": list(definition.monitoring_sources),
        "cadence": definition.cadence,
        "lookback_window": definition.lookback_window,
        "run_mode": definition.run_mode,
        "scoring_formula": definition.scoring_formula,
        "tier_thresholds": definition.tier_thresholds,
        "criteria": [criterion_to_payload(item) for item in definition.criteria],
        "limitations": list(definition.limitations),
    }


def candidate_to_payload(candidate: ICPRadarCandidate) -> dict[str, Any]:
    return {
        "rank": candidate.rank,
        "account_id": candidate.account_id,
        "ppo": candidate.ppo,
        "legal_name": candidate.legal_name,
        "account_type": candidate.account_type,
        "description": candidate.description,
        "inn": candidate.inn,
        "revenue": candidate.revenue,
        "site": candidate.site,
        "confidence": candidate.confidence,
        "signal_summary": candidate.signal_summary,
        "main_signal": candidate.main_signal,
        "comment": candidate.comment,
        "source_urls": list(candidate.source_urls),
        "evidence_refs": list(candidate.evidence_refs),
        "criteria_scores": dict(candidate.criteria_scores),
        "criteria_evidence": {
            code: criterion_evidence_to_payload(item)
            for code, item in sorted(candidate.criteria_evidence.items())
        },
        "score": score_to_payload(candidate.score),
    }


def criterion_evidence_to_payload(explanation: CriterionEvidenceExplanation) -> dict[str, Any]:
    return {
        "criterion_code": explanation.criterion_code,
        "score": explanation.score,
        "evidence_origin": explanation.evidence_origin,
        "evidence_status": explanation.evidence_status,
        "confidence": explanation.confidence,
        "rationale": explanation.rationale,
        "evidence_refs": list(explanation.evidence_refs),
        "source_urls": list(explanation.source_urls),
        "facts": [criterion_evidence_fact_to_payload(item) for item in explanation.facts],
    }


def criterion_evidence_fact_to_payload(fact: CriterionEvidenceFact) -> dict[str, Any]:
    return {
        "evidence_ref": fact.evidence_ref,
        "source_url": fact.source_url,
        "fact": fact.fact,
        "why_it_matters": fact.why_it_matters,
    }


def score_to_payload(score: ICPRadarScore) -> dict[str, Any]:
    return {
        "fit_score": score.fit_score,
        "intent_score": score.intent_score,
        "trigger_score": score.trigger_score,
        "total_score": score.total_score,
        "tier": score.tier,
    }
