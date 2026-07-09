"""Offline Radar benchmark evaluation over persisted run dossiers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from power_web_os.radar_evaluation_diagnostics import false_negative_diagnostics
from power_web_os.radar_evaluation_funnel import (
    benchmark_target_funnel as _benchmark_target_funnel,
    is_product_candidate as _is_product_candidate,
    upstream_lead_counts as _upstream_lead_counts,
)
from power_web_os.radar_evaluation_reconciliation import (
    candidate_discovery_reconciliation as _candidate_discovery_reconciliation,
    product_acceptance_ledger as _product_acceptance_ledger,
)
from power_web_os.radar_evaluation_matching import (
    contains_strong_name,
    entity_type_compatible,
    match_rank,
    normalize_name,
    review_entity_name_match,
)
from power_web_os.radar_evaluation_observed import (
    RadarObservedEntity,
    accepted_product_candidate_row_count,
    candidate_surface_rows,
    evidence_quality,
    observed_entities,
    optional_digits,
    review_needed_candidate_row_count,
    source_index,
    visible_candidate_observations,
)
SIBUR_CONTOUR_RADAR_ID = "benchmark-sibur-holding-contour"
EVALUATION_ARTIFACT_VERSION = "0.7.6.3"

@dataclass(slots=True)
class RadarEvaluationEntity:
    baseline_id: str
    canonical_name: str
    entity_type: str
    aliases: tuple[str, ...] = ()
    inn: str | None = None
    ogrn: str | None = None
    expected_relation: str = ""
    expected_source_hints: tuple[str, ...] = ()
    evaluation_weight: float = 1.0

    @property
    def normalized_names(self) -> set[str]:
        return {normalized for name in (self.canonical_name, *self.aliases) if (normalized := normalize_name(name))}

@dataclass(slots=True)
class RadarEvaluationBaseline:
    baseline_id: str
    version: str
    radar_id: str
    description: str
    entities: tuple[RadarEvaluationEntity, ...]


@dataclass(slots=True)
class RadarEvaluationMatch:
    baseline: RadarEvaluationEntity
    observed: RadarObservedEntity
    match_type: str
    confidence: str
    evidence_quality: str

def load_evaluation_baseline(path: Path) -> RadarEvaluationBaseline:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entities = tuple(
        RadarEvaluationEntity(
            baseline_id=str(item["baseline_id"]),
            canonical_name=str(item["canonical_name"]),
            entity_type=str(item["entity_type"]),
            aliases=tuple(str(value) for value in item.get("aliases", [])),
            inn=optional_digits(item.get("inn")),
            ogrn=optional_digits(item.get("ogrn")),
            expected_relation=str(item.get("expected_relation") or ""),
            expected_source_hints=tuple(str(value) for value in item.get("expected_source_hints", [])),
            evaluation_weight=float(item.get("evaluation_weight", 1.0)),
        )
        for item in payload.get("entities", [])
        if isinstance(item, dict)
    )
    if not entities:
        raise ValueError(f"Evaluation baseline has no entities: {path}")
    return RadarEvaluationBaseline(
        baseline_id=str(payload.get("baseline_id") or path.stem),
        version=str(payload.get("version") or "v1"),
        radar_id=str(payload.get("radar_id") or SIBUR_CONTOUR_RADAR_ID),
        description=str(payload.get("description") or ""),
        entities=entities,
    )


def evaluate_radar_dossier(
    *,
    run: dict[str, Any],
    dossier: dict[str, Any],
    baseline: RadarEvaluationBaseline,
) -> dict[str, Any]:
    run_radar_id = str(run.get("radar_id") or dossier.get("radar_id") or "")
    if run_radar_id != baseline.radar_id:
        raise ValueError(f"Baseline {baseline.baseline_id} targets {baseline.radar_id}, got run for {run_radar_id}.")
    observed = observed_entities(dossier)
    sources_by_ref = source_index(dossier)
    matches, ambiguous = _match_entities(baseline=baseline, observed=observed, source_index=sources_by_ref)
    visible_observations = visible_candidate_observations(observed)
    visible_rows = candidate_surface_rows(dossier)
    matched_baseline_ids = {match.baseline.baseline_id for match in matches}
    ambiguous_baseline_ids = {match.baseline.baseline_id for match in ambiguous}
    product_observations = [
        item
        for item in visible_observations
        if _is_product_candidate(item.payload)
    ]
    matched_product_ids = {
        id(match.observed)
        for match in matches
        if match.observed.source == "product_candidate"
        and _is_product_candidate(match.observed.payload)
        and match.baseline.entity_type == "legal_entity"
    }
    ambiguous_product_ids = {
        id(match.observed)
        for match in ambiguous
        if match.observed.source == "product_candidate" and _is_product_candidate(match.observed.payload)
    }
    false_positives = [
        _observed_payload(item)
        for item in product_observations
        if id(item) not in matched_product_ids and id(item) not in ambiguous_product_ids
    ]
    false_negatives = [
        _baseline_payload(item)
        for item in baseline.entities
        if item.evaluation_weight > 0 and item.baseline_id not in matched_baseline_ids and item.baseline_id not in ambiguous_baseline_ids
    ]
    false_negative_diagnostic_items = false_negative_diagnostics(false_negatives=false_negatives, dossier=dossier)
    legal_baseline = [item for item in baseline.entities if item.entity_type == "legal_entity" and item.evaluation_weight > 0]
    review_baseline = [item for item in baseline.entities if item.entity_type != "legal_entity" and item.evaluation_weight > 0]
    strict_hits = {match.baseline.baseline_id for match in matches if match.baseline.entity_type == "legal_entity"}
    review_hits = {match.baseline.baseline_id for match in matches if match.baseline.entity_type != "legal_entity"}
    legal_visible_hits = {
        match.baseline.baseline_id
        for match in [*matches, *ambiguous]
        if match.baseline.entity_type == "legal_entity"
        and match.observed.source == "product_candidate"
    }
    accepted_product_count = accepted_product_candidate_row_count(visible_rows)
    review_needed_count = review_needed_candidate_row_count(visible_rows)
    summary = _dict(dossier.get("summary"))
    evidence_quality_values = [match.evidence_quality for match in matches + ambiguous] + ["missing"] * len(false_negatives)
    upstream_counts = _upstream_lead_counts(dossier)
    benchmark_target_funnel = _benchmark_target_funnel(
        baseline=baseline,
        observed=observed,
        false_negative_diagnostics=false_negative_diagnostic_items,
        dossier=dossier,
    )
    reconciliation = _candidate_discovery_reconciliation(dossier)
    product_acceptance_ledger = _product_acceptance_ledger(dossier)
    funnel_reason_counts = _count_by(str(item.get("path_reason") or "") for item in benchmark_target_funnel)
    report = {
        "artifact_type": "radar_evaluation_report",
        "artifact_version": EVALUATION_ARTIFACT_VERSION,
        "run_id": run.get("run_id"),
        "radar_id": run_radar_id,
        "status": run.get("status"),
        "execution_outcome": summary.get("execution_outcome"),
        "execution_outcome_reason": summary.get("execution_outcome_reason"),
        "baseline": {
            "baseline_id": baseline.baseline_id,
            "version": baseline.version,
            "entity_count": len(baseline.entities),
            "description": baseline.description,
        },
        "metrics": {
            "strict_recall": _ratio(len(strict_hits), len(legal_baseline)),
            "review_recall": _ratio(len(review_hits), len(review_baseline)),
            "precision": _ratio(len(matched_product_ids), len(product_observations)),
            "true_positive_count": len(strict_hits),
            "review_match_count": len(review_hits),
            "false_positive_count": len(false_positives),
            "false_negative_count": len(false_negatives),
            "ambiguous_match_count": len(ambiguous),
            "retained_upstream_lead_count": upstream_counts["retained_upstream_lead_count"],
            "confirmed_upstream_lead_count": upstream_counts["confirmed_upstream_lead_count"],
            "review_needed_upstream_lead_count": upstream_counts["review_needed_upstream_lead_count"],
            "product_candidate_count": len(product_observations),
            "visible_candidate_count": len(visible_rows),
            "accepted_product_candidate_count": accepted_product_count,
            "review_needed_candidate_count": review_needed_count,
            "legal_baseline_visible_count": len(legal_visible_hits),
            "unexplained_drop_count": int(reconciliation.get("unexplained_drop_count") or 0),
            "present_not_projected_count": funnel_reason_counts.get("present_not_projected", 0),
        },
        "evidence_quality_summary": _count_by(evidence_quality_values),
        "true_positives": [_match_payload(match) for match in matches if match.baseline.entity_type == "legal_entity"],
        "review_matches": [_match_payload(match) for match in matches if match.baseline.entity_type != "legal_entity"],
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "false_negative_diagnostics": false_negative_diagnostic_items,
        "ambiguous_matches": [_match_payload(match) for match in ambiguous],
        "coverage_probe_summary": {},
        "candidate_projection_note": (
            "Precision counts strict product candidates only. Retained upstream leads, universe-only rows, and "
            "not-promoted entities are reported separately from product acceptance."
        ),
        "candidate_discovery_reconciliation": reconciliation,
        "product_acceptance_ledger": product_acceptance_ledger,
        "benchmark_target_funnel": benchmark_target_funnel,
        "recommended_followup_buckets": _followup_buckets(
            summary=summary,
            false_positives=false_positives,
            false_negatives=false_negatives,
            ambiguous=ambiguous,
            matches=matches,
        ),
        "diagnostics": {
            "observed_entity_count": len(observed),
            "product_candidate_count": len(product_observations),
            "visible_candidate_count": len(visible_rows),
            "accepted_product_candidate_count": accepted_product_count,
            "review_needed_candidate_count": review_needed_count,
            "legal_baseline_visible_count": len(legal_visible_hits),
            **upstream_counts,
            "candidate_discovery_reconciliation": reconciliation,
            "product_acceptance_ledger_count": len(product_acceptance_ledger),
            "benchmark_target_path_reasons": funnel_reason_counts,
            "source_lifecycle_count": len(sources_by_ref),
            "stopped_for_review_reason": dossier.get("stopped_for_review_reason"),
        },
    }
    _assert_no_secrets(report)
    return report


def write_evaluation_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _match_entities(
    *,
    baseline: RadarEvaluationBaseline,
    observed: list[RadarObservedEntity],
    source_index: dict[str, dict[str, Any]],
) -> tuple[list[RadarEvaluationMatch], list[RadarEvaluationMatch]]:
    matches: list[RadarEvaluationMatch] = []
    ambiguous: list[RadarEvaluationMatch] = []
    used_observed: set[int] = set()
    for entity in baseline.entities:
        candidates = [_candidate_match(entity, item, source_index) for item in observed if id(item) not in used_observed]
        candidates = [item for item in candidates if item is not None]
        if not candidates:
            continue
        candidates.sort(key=lambda item: match_rank(item.match_type, item.confidence), reverse=True)
        selected = candidates[0]
        used_observed.add(id(selected.observed))
        if selected.confidence == "ambiguous":
            ambiguous.append(selected)
        else:
            matches.append(selected)
    return matches, ambiguous


def _candidate_match(
    baseline: RadarEvaluationEntity,
    observed: RadarObservedEntity,
    source_index: dict[str, dict[str, Any]],
) -> RadarEvaluationMatch | None:
    if not entity_type_compatible(baseline_entity_type=baseline.entity_type, observed_entity_type=observed.entity_type):
        return None
    if baseline.inn and observed.inn and baseline.inn == observed.inn:
        return _match(baseline, observed, "inn", "high", source_index)
    if baseline.ogrn and observed.ogrn and baseline.ogrn == observed.ogrn:
        return _match(baseline, observed, "ogrn", "high", source_index)
    if observed.normalized_name in baseline.normalized_names:
        return _match(baseline, observed, "normalized_name", "high", source_index)
    if baseline.entity_type != "legal_entity" and observed.source_refs and review_entity_name_match(baseline_names=baseline.normalized_names, observed_name=observed.normalized_name):
        return _match(baseline, observed, "source_backed_partial", "medium", source_index)
    if any(contains_strong_name(observed.normalized_name, name) for name in baseline.normalized_names):
        confidence = "medium" if observed.source != "product_candidate" else "ambiguous"
        return _match(baseline, observed, "source_backed_partial", confidence, source_index)
    return None


def _match(
    baseline: RadarEvaluationEntity,
    observed: RadarObservedEntity,
    match_type: str,
    confidence: str,
    source_index: dict[str, dict[str, Any]],
) -> RadarEvaluationMatch:
    return RadarEvaluationMatch(
        baseline=baseline,
        observed=observed,
        match_type=match_type,
        confidence=confidence,
        evidence_quality=evidence_quality(observed, source_index),
    )


def _followup_buckets(
    *,
    summary: dict[str, Any],
    false_positives: list[dict[str, Any]],
    false_negatives: list[dict[str, Any]],
    ambiguous: list[RadarEvaluationMatch],
    matches: list[RadarEvaluationMatch],
) -> list[str]:
    buckets: list[str] = []
    outcome = str(summary.get("execution_outcome") or "")
    reason = str(summary.get("execution_outcome_reason") or "")
    if "budget" in outcome or "budget" in reason:
        buckets.append("tune_benchmark_budgets")
    if "extraction" in reason:
        buckets.append("repair_extraction_quality")
    if false_negatives:
        buckets.append("improve_recall")
    if false_positives:
        buckets.append("improve_precision")
    if ambiguous:
        buckets.append("improve_entity_disambiguation")
    if any(match.evidence_quality in {"weak", "missing"} for match in matches):
        buckets.append("improve_evidence_quality")
    return buckets or ["ready_for_manual_quality_review"]


def _match_payload(match: RadarEvaluationMatch) -> dict[str, Any]:
    return {
        "baseline_id": match.baseline.baseline_id,
        "baseline_name": match.baseline.canonical_name,
        "baseline_entity_type": match.baseline.entity_type,
        "observed_name": match.observed.name,
        "observed_entity_type": match.observed.entity_type,
        "observed_source": match.observed.source,
        "match_type": match.match_type,
        "confidence": match.confidence,
        "evidence_quality": match.evidence_quality,
        "source_refs": list(match.observed.source_refs),
        "review_flags": list(match.observed.review_flags),
    }


def _baseline_payload(entity: RadarEvaluationEntity) -> dict[str, Any]:
    return {
        "baseline_id": entity.baseline_id,
        "canonical_name": entity.canonical_name,
        "entity_type": entity.entity_type,
        "aliases": list(entity.aliases),
        "expected_relation": entity.expected_relation,
        "expected_source_hints": list(entity.expected_source_hints),
        "evaluation_weight": entity.evaluation_weight,
    }


def _observed_payload(item: RadarObservedEntity) -> dict[str, Any]:
    return {
        "observed_name": item.name,
        "entity_type": item.entity_type,
        "source": item.source,
        "source_refs": list(item.source_refs),
        "review_flags": list(item.review_flags),
    }


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def _count_by(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _assert_no_secrets(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    forbidden = (
        "OPENROUTER_API_KEY",
        "DADATA_API_KEY",
        "DADATA_SECRET_KEY",
        "Authorization",
        "Bearer",
        "chain_of_thought",
        "hidden_reasoning",
        "internal_thoughts",
    )
    if any(token in serialized for token in forbidden):
        raise ValueError("Radar evaluation report contains forbidden secret or hidden reasoning marker.")
