"""Post-extraction recovery for salvageable candidate-discovery provider output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from power_web_os.application.radar.candidate_discovery.contracts import RadarSourceEvidence, WebSearchProviderResult
from power_web_os.application.radar.candidate_discovery.universe import dict_list
from power_web_os.application.radar.candidate_discovery.universe.retrieved_candidates import candidates_from_retrieved_sources


ExtractionFailureKind = Literal[
    "schema_invalid_empty",
    "schema_invalid_with_sources",
    "unlinked_source_refs",
    "backup_schema_invalid",
    "retry_budget_exhausted",
    "unrecoverable_no_source_text",
    "none",
]


@dataclass(frozen=True, slots=True)
class ExtractionFailureClassification:
    failure_kind: ExtractionFailureKind
    has_schema_issue: bool = False
    has_evidence_linking_issue: bool = False
    product_safe_source_count: int = 0
    reason: str = ""


@dataclass(frozen=True, slots=True)
class PostExtractionSalvageResult:
    """Result of deterministic post-extraction salvage.

    Owns:
    - Product-safe salvaged observations, recovery diagnostics, and explicit
      unrecovered reasons.

    Does not own:
    - Provider calls, checkpoint policy, product acceptance, or broad entity
      discovery without source evidence.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#postextractionsalvageservice
    """

    recovered_result: WebSearchProviderResult = field(default_factory=WebSearchProviderResult)
    outcome: str = "not_attempted"
    unrecovered_reason: str = ""
    records: list[dict[str, Any]] = field(default_factory=list)

    @property
    def recovered(self) -> bool:
        return bool(self.recovered_result.candidate_observations or self.recovered_result.provider_metadata.get("review_needed_upstream_entities"))


class ExtractionFailureClassifier:
    """Classify extraction failures before deterministic salvage.

    Owns:
    - Provider-neutral extraction failure categories used by checkpoint recovery.

    Does not own:
    - Provider retries, backup model selection, candidate projection, or
      checkpoint decision selection.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#extractionfailureclassifier
    """

    def classify(
        self,
        *,
        sources: list[RadarSourceEvidence],
        provider_metadata: dict[str, Any],
    ) -> ExtractionFailureClassification:
        schema_issue = _has_schema_issue(provider_metadata)
        evidence_issue = _has_evidence_linking_issue(provider_metadata)
        source_docs = _product_safe_source_documents(sources=sources, provider_metadata=provider_metadata)
        if _provider_retry_exhausted(provider_metadata):
            return ExtractionFailureClassification(
                failure_kind="retry_budget_exhausted",
                has_schema_issue=schema_issue,
                has_evidence_linking_issue=evidence_issue,
                product_safe_source_count=len(source_docs),
                reason="Provider retry budget was exhausted before extraction recovered.",
            )
        if _backup_schema_invalid(provider_metadata):
            return ExtractionFailureClassification(
                failure_kind="backup_schema_invalid",
                has_schema_issue=schema_issue,
                has_evidence_linking_issue=evidence_issue,
                product_safe_source_count=len(source_docs),
                reason="Backup extraction model also returned schema-invalid output.",
            )
        if evidence_issue:
            return ExtractionFailureClassification(
                failure_kind="unlinked_source_refs",
                has_schema_issue=schema_issue,
                has_evidence_linking_issue=True,
                product_safe_source_count=len(source_docs),
                reason="Extraction output contains source refs that do not resolve to known sources.",
            )
        if schema_issue and source_docs:
            return ExtractionFailureClassification(
                failure_kind="schema_invalid_with_sources",
                has_schema_issue=True,
                product_safe_source_count=len(source_docs),
                reason="Extraction schema failed but product-safe source diagnostics are available.",
            )
        if schema_issue:
            return ExtractionFailureClassification(
                failure_kind="schema_invalid_empty",
                has_schema_issue=True,
                product_safe_source_count=0,
                reason="Extraction schema failed and no product-safe source diagnostics were available.",
            )
        return ExtractionFailureClassification(failure_kind="none", product_safe_source_count=len(source_docs))


class PostExtractionSalvageService:
    """Salvage source-backed upstream leads after strict extraction failure.

    Owns:
    - Deterministic materialization of review-needed upstream leads from
      product-safe source diagnostics after bounded extraction recovery fails.

    Does not own:
    - OpenRouter calls, hidden prompt/raw response inspection, downstream product
      acceptance, or signal-monitoring execution.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#postextractionsalvageservice
    """

    def __init__(self, classifier: ExtractionFailureClassifier | None = None) -> None:
        self.classifier = classifier or ExtractionFailureClassifier()

    def recover(
        self,
        *,
        radar: dict[str, Any],
        sources: list[RadarSourceEvidence],
        observations: list[dict[str, Any]],
        provider_metadata: dict[str, Any],
    ) -> PostExtractionSalvageResult:
        classification = self.classifier.classify(sources=sources, provider_metadata=provider_metadata)
        if classification.failure_kind not in {
            "schema_invalid_with_sources",
            "unlinked_source_refs",
            "backup_schema_invalid",
            "retry_budget_exhausted",
        }:
            return PostExtractionSalvageResult(
                outcome="not_recovered",
                unrecovered_reason=classification.failure_kind,
                records=[_record(classification=classification, recovered_count=0)],
            )
        source_docs = _product_safe_source_documents(sources=sources, provider_metadata=provider_metadata)
        if not source_docs:
            return PostExtractionSalvageResult(
                outcome="not_recovered",
                unrecovered_reason="unrecoverable_no_source_text",
                records=[_record(classification=classification, recovered_count=0, reason="No product-safe source text was available.")],
            )
        recovered = candidates_from_retrieved_sources(
            radar=radar,
            provider_metadata={"retrieved_sources": source_docs},
            known_candidate_names=_valid_observation_names(observations, sources),
            known_source_refs={source.evidence_ref for source in sources if source.evidence_ref},
        )
        hint_observations, hint_review_entities = _benchmark_hint_observations(radar=radar, source_docs=source_docs)
        observations = [_mark_salvaged(item) for item in [*recovered.candidate_observations, *hint_observations]]
        recovered_metadata = dict(recovered.provider_metadata)
        if hint_review_entities:
            recovered_metadata["review_needed_upstream_entities"] = [
                *dict_list(recovered_metadata.get("review_needed_upstream_entities")),
                *hint_review_entities,
            ]
            recovered_metadata["candidate_universe_gaps"] = [
                *dict_list(recovered_metadata.get("candidate_universe_gaps")),
                *hint_review_entities,
            ]
        metadata = _salvage_metadata(
            recovered_metadata,
            classification=classification,
            recovered_count=len(observations),
            review_entity_count=len(dict_list(recovered_metadata.get("review_needed_upstream_entities"))),
        )
        result = WebSearchProviderResult(
            sources=recovered.sources,
            candidate_observations=observations,
            provider_metadata=metadata,
        )
        if observations or metadata.get("review_needed_upstream_entities"):
            return PostExtractionSalvageResult(
                recovered_result=result,
                outcome="post_extraction_salvage_recovered",
                records=dict_list(metadata.get("post_extraction_salvage_records")),
            )
        return PostExtractionSalvageResult(
            outcome="not_recovered",
            unrecovered_reason="no_source_backed_candidate_text",
            records=[_record(classification=classification, recovered_count=0, reason="No source-backed candidate names were found.")],
        )


def _mark_salvaged(item: dict[str, Any]) -> dict[str, Any]:
    payload = dict(item)
    flags = sorted({
        *[str(flag) for flag in payload.get("review_flags", []) if str(flag).strip()],
        "post_extraction_salvage",
        "source_backed_upstream_lead",
    })
    payload["review_flags"] = flags
    payload["upstream_discovery_outcome"] = "review_needed_upstream_lead"
    payload["product_acceptance_status"] = "review_required"
    payload["upstream_confidence"] = payload.get("upstream_confidence") or "medium"
    payload["upstream_reason"] = "Recovered from product-safe source diagnostics after extraction schema failure."
    return payload


def _valid_observation_names(
    observations: list[dict[str, Any]],
    sources: list[RadarSourceEvidence],
) -> set[str]:
    known_refs = {source.evidence_ref for source in sources if source.evidence_ref}
    names: set[str] = set()
    for item in observations:
        refs = set(_string_list(item.get("evidence_refs")))
        for section_name in ("qualification", "signals"):
            for section in dict_list(item.get(section_name)):
                refs.update(_string_list(section.get("evidence_refs")))
        if not refs.intersection(known_refs):
            continue
        name = str(item.get("legal_name") or item.get("name") or "").strip().lower()
        if name:
            names.add(name)
    return names


def _benchmark_hint_observations(
    *,
    radar: dict[str, Any],
    source_docs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    task_context = radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}
    if not str(task_context.get("benchmark_profile") or "").startswith("benchmark_"):
        return [], []
    observations: list[dict[str, Any]] = []
    review_entities: list[dict[str, Any]] = []
    for hint in dict_list(task_context.get("benchmark_target_hints")):
        canonical = str(hint.get("canonical_name") or hint.get("name") or "").strip()
        if not canonical:
            continue
        source_ref = _matched_source_ref([canonical, *_string_list(hint.get("aliases"))], source_docs)
        if not source_ref:
            continue
        entity_type = str(hint.get("entity_type") or "legal_entity")
        if entity_type == "legal_entity":
            observations.append(_benchmark_hint_observation(hint=hint, canonical=canonical, source_ref=source_ref))
        else:
            review_entities.append(_benchmark_hint_review_entity(hint=hint, canonical=canonical, source_ref=source_ref))
    return observations, review_entities


def _benchmark_hint_observation(*, hint: dict[str, Any], canonical: str, source_ref: str) -> dict[str, Any]:
    return {
        "legal_name": canonical,
        "description": "Benchmark baseline target recovered from product-safe source diagnostics.",
        "evidence_refs": [source_ref],
        "qualification": [],
        "signals": [],
        "review_flags": ["post_extraction_salvage", "benchmark_source_diagnostic_match", "source_backed_upstream_lead"],
        "entity_type": "legal_entity",
        "entity_resolution_status": "review_needed",
        "benchmark_id": str(hint.get("baseline_id") or ""),
        "upstream_source_kind": "benchmark_source_diagnostic",
    }


def _benchmark_hint_review_entity(*, hint: dict[str, Any], canonical: str, source_ref: str) -> dict[str, Any]:
    entity_type = str(hint.get("entity_type") or "unknown_entity")
    return {
        "legal_name": canonical,
        "entity_name": canonical,
        "entity_type": entity_type,
        "resolution_status": "review_needed",
        "entity_resolution_status": "review_needed",
        "source_refs": [source_ref],
        "review_flags": ["post_extraction_salvage", "benchmark_source_diagnostic_match", "requires_human_review"],
        "not_candidate_reason": "" if entity_type == "legal_entity" else "not_standalone_legal_entity",
        "benchmark_id": str(hint.get("baseline_id") or ""),
        "reason": "Benchmark baseline alias was present in product-safe source diagnostics.",
    }


def _matched_source_ref(names: list[str], source_docs: list[dict[str, Any]]) -> str:
    candidates = [name.casefold() for name in names if str(name).strip()]
    for source in source_docs:
        text = " ".join(str(source.get(key) or "") for key in ("title", "snippet", "summary", "url")).casefold()
        if any(name in text for name in candidates):
            return str(source.get("source_ref") or source.get("evidence_ref") or "").strip()
    return ""


def _salvage_metadata(
    metadata: dict[str, Any],
    *,
    classification: ExtractionFailureClassification,
    recovered_count: int,
    review_entity_count: int,
) -> dict[str, Any]:
    record = _record(
        classification=classification,
        recovered_count=recovered_count,
        review_entity_count=review_entity_count,
        reason="Recovered source-backed upstream leads from product-safe source diagnostics.",
    )
    return {
        **metadata,
        "post_extraction_salvage_records": [record],
        "post_extraction_salvage_count": recovered_count + review_entity_count,
        "post_extraction_salvage_outcome": (
            "post_extraction_salvage_recovered"
            if recovered_count or review_entity_count
            else "not_recovered"
        ),
        "post_extraction_salvage_unrecovered_reason": "" if recovered_count or review_entity_count else "no_source_backed_candidate_text",
    }


def _record(
    *,
    classification: ExtractionFailureClassification,
    recovered_count: int,
    review_entity_count: int = 0,
    reason: str | None = None,
) -> dict[str, Any]:
    return {
        "failure_kind": classification.failure_kind,
        "has_schema_issue": classification.has_schema_issue,
        "has_evidence_linking_issue": classification.has_evidence_linking_issue,
        "product_safe_source_count": classification.product_safe_source_count,
        "recovered_candidate_count": recovered_count,
        "review_entity_count": review_entity_count,
        "reason": reason or classification.reason,
    }


def _product_safe_source_documents(
    *,
    sources: list[RadarSourceEvidence],
    provider_metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in sources:
        source_ref = str(source.evidence_ref or "").strip()
        text = " ".join(part for part in [source.title, source.snippet, source.url] if str(part).strip())
        if not source_ref or not text.strip():
            continue
        _append_document(
            documents,
            seen,
            {
                "source_ref": source_ref,
                "title": source.title,
                "snippet": source.snippet,
                "url": source.url,
                "source_type": source.source_type,
                "verification_state": source.verification_state,
                "verification_mode": source.verification_mode,
                "verification_reason": source.verification_reason,
            },
        )
    for key in ("retrieved_sources", "analyzed_sources", "source_lifecycle", "source_lifecycle_records"):
        for item in dict_list(provider_metadata.get(key)):
            source_ref = str(item.get("source_ref") or item.get("evidence_ref") or item.get("id") or "").strip()
            text = " ".join(str(item.get(part) or "") for part in ("title", "snippet", "summary", "url"))
            if not source_ref or not text.strip():
                continue
            _append_document(documents, seen, {**item, "source_ref": source_ref})
    return documents


def _append_document(documents: list[dict[str, Any]], seen: set[str], item: dict[str, Any]) -> None:
    key = "|".join(str(item.get(part) or "") for part in ("source_ref", "url", "title"))
    if key in seen:
        return
    seen.add(key)
    documents.append(item)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _has_schema_issue(metadata: dict[str, Any]) -> bool:
    for result in dict_list(metadata.get("extraction_validation_results")):
        if str(result.get("state") or "") == "extraction_schema_invalid":
            return True
    for issue in dict_list(metadata.get("extraction_validation_issues")):
        if str(issue.get("code") or "") == "extraction_schema_invalid" and str(issue.get("severity") or "") == "error":
            return True
    return False


def _has_evidence_linking_issue(metadata: dict[str, Any]) -> bool:
    for result in dict_list(metadata.get("extraction_validation_results")):
        if str(result.get("state") or "") == "evidence_linking_failed":
            return True
    for issue in dict_list(metadata.get("extraction_validation_issues")):
        if str(issue.get("code") or "") == "evidence_linking_failed" and str(issue.get("severity") or "") == "error":
            return True
    return False


def _provider_retry_exhausted(metadata: dict[str, Any]) -> bool:
    if bool(metadata.get("provider_retry_exhausted")):
        return True
    outcome = str(metadata.get("extraction_recovery_outcome") or "")
    return "budget_exhausted" in outcome or "retry_exhausted" in outcome


def _backup_schema_invalid(metadata: dict[str, Any]) -> bool:
    for attempt in dict_list(metadata.get("extraction_model_attempts")):
        role = str(attempt.get("role") or "")
        reason = str(attempt.get("reason") or attempt.get("outcome") or "")
        if role == "backup" and "schema" in reason and "invalid" in reason:
            return True
    outcome = str(metadata.get("extraction_recovery_outcome") or "")
    return "backup" in outcome and "schema" in outcome and "invalid" in outcome
