from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from power_web_os.icp_radar import (
    CRITERION_CODES,
    CriterionEvidenceExplanation,
    CriterionEvidenceFact,
    EvidenceSource,
    ICPRadarCandidate,
    SignalCriterion,
)


@dataclass(frozen=True, slots=True)
class CriterionEvidenceAnnotation:
    account_id: str
    criterion_code: str
    confidence: str
    rationale: str
    facts: tuple[CriterionEvidenceFact, ...]


@dataclass(frozen=True, slots=True)
class CriterionEvidenceFixture:
    contract_version: str
    evidence_origin: str
    annotations: dict[tuple[str, str], CriterionEvidenceAnnotation]


def load_criterion_evidence_fixture(path: Path) -> CriterionEvidenceFixture:
    if not path.exists():
        return CriterionEvidenceFixture(
            contract_version="0.6.2.3",
            evidence_origin="workbook_score_fallback",
            annotations={},
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    origin = str(payload.get("evidence_origin") or "synthetic_demo_annotation")
    annotations: dict[tuple[str, str], CriterionEvidenceAnnotation] = {}

    for item in payload.get("annotations", []):
        account_id = str(item["account_id"])
        criteria = item.get("criteria", {})
        for criterion_code, criterion_payload in criteria.items():
            facts = tuple(
                CriterionEvidenceFact(
                    evidence_ref=str(fact.get("evidence_ref") or ""),
                    source_url=str(fact.get("source_url") or ""),
                    fact=str(fact.get("fact") or ""),
                    why_it_matters=str(fact.get("why_it_matters") or ""),
                )
                for fact in criterion_payload.get("facts", [])
            )
            annotations[(account_id, criterion_code)] = CriterionEvidenceAnnotation(
                account_id=account_id,
                criterion_code=criterion_code,
                confidence=str(criterion_payload.get("confidence") or "medium"),
                rationale=str(criterion_payload.get("rationale") or ""),
                facts=facts,
            )

    return CriterionEvidenceFixture(
        contract_version=str(payload.get("contract_version") or "0.6.2.3"),
        evidence_origin=origin,
        annotations=annotations,
    )


class CriterionEvidenceBuilder:
    def __init__(
        self,
        *,
        criteria: tuple[SignalCriterion, ...],
        sources: tuple[EvidenceSource, ...],
        fixture: CriterionEvidenceFixture,
    ) -> None:
        self._criteria = criteria
        self._sources_by_id = {source.source_id: source for source in sources}
        self._fixture = fixture

    def attach(self, candidates: tuple[ICPRadarCandidate, ...]) -> tuple[ICPRadarCandidate, ...]:
        return tuple(
            replace(candidate, criteria_evidence=self._build_for_candidate(candidate))
            for candidate in candidates
        )

    def _build_for_candidate(self, candidate: ICPRadarCandidate) -> dict[str, CriterionEvidenceExplanation]:
        return {
            criterion.code: self._build_explanation(candidate, criterion)
            for criterion in self._criteria
            if criterion.code in CRITERION_CODES
        }

    def _build_explanation(
        self,
        candidate: ICPRadarCandidate,
        criterion: SignalCriterion,
    ) -> CriterionEvidenceExplanation:
        score = int(candidate.criteria_scores.get(criterion.code, 0))
        annotation = self._fixture.annotations.get((candidate.account_id, criterion.code))
        if annotation is not None:
            facts = self._normalize_facts(annotation.facts)
            refs = _ordered_unique(
                [fact.evidence_ref for fact in facts if fact.evidence_ref]
                or list(candidate.evidence_refs)
            )
            urls = _ordered_unique(
                [fact.source_url for fact in facts if fact.source_url]
                or list(candidate.source_urls)
            )
            return CriterionEvidenceExplanation(
                criterion_code=criterion.code,
                score=score,
                evidence_origin=self._fixture.evidence_origin,
                evidence_status="supported",
                confidence=annotation.confidence,
                rationale=annotation.rationale,
                evidence_refs=refs,
                source_urls=urls,
                facts=facts,
            )

        if score > 0:
            return CriterionEvidenceExplanation(
                criterion_code=criterion.code,
                score=score,
                evidence_origin="workbook_score_fallback",
                evidence_status="inferred",
                confidence="low",
                rationale=(
                    "Score imported from the XLSX matrix. The demo fixture does not yet include "
                    "criterion-level facts for this candidate and criterion."
                ),
                evidence_refs=tuple(candidate.evidence_refs),
                source_urls=tuple(candidate.source_urls),
                facts=(),
            )

        return CriterionEvidenceExplanation(
            criterion_code=criterion.code,
            score=score,
            evidence_origin="workbook_score_fallback",
            evidence_status="not_observed",
            confidence="none",
            rationale="Workbook score is 0; this criterion was not observed in the demo analysis.",
            evidence_refs=(),
            source_urls=(),
            facts=(),
        )

    def _normalize_facts(self, facts: tuple[CriterionEvidenceFact, ...]) -> tuple[CriterionEvidenceFact, ...]:
        normalized = []
        for fact in facts:
            source_url = fact.source_url
            if not source_url and fact.evidence_ref in self._sources_by_id:
                source_url = self._sources_by_id[fact.evidence_ref].url
            normalized.append(replace(fact, source_url=source_url))
        return tuple(normalized)


def _ordered_unique(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result = []
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return tuple(result)
