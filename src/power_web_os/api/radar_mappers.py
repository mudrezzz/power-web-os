"""Mapping helpers from application records to Radar API DTOs."""

from __future__ import annotations

from typing import Any

from power_web_os.api.radar_dtos import (
    CandidateScoreResponse,
    EvidenceFindingResponse,
    QualificationResponse,
    RadarCandidateResponse,
    RadarDefinitionResponse,
    RadarDetailResponse,
    RadarRunCandidatesResponse,
    RadarRunOutputSummaryResponse,
    RadarRunReviewsResponse,
    RadarRunSummaryResponse,
    RadarReviewDecisionResponse,
    RadarSourceResponse,
    RadarSummaryResponse,
    SignalResponse,
    SourceUsageResponse,
)
from power_web_os.application.radar_records import (
    RadarDefinitionRecord,
    RadarRecord,
    RadarReviewDecisionRecord,
    RadarRunOutputRecord,
    RadarRunRecord,
)


def radar_summary_response(
    radar: RadarRecord,
    *,
    runs: tuple[RadarRunRecord, ...] = (),
    outputs_by_run_id: dict[str, RadarRunOutputRecord] | None = None,
) -> RadarSummaryResponse:
    latest = runs[-1] if runs else None
    return RadarSummaryResponse(
        radar_id=radar.radar_id,
        name=radar.name,
        status=radar.status,
        owner=radar.owner,
        profile=radar.profile,
        summary=radar.summary,
        artifact_path=radar.artifact_path,
        run_count=len(runs),
        latest_run=run_summary_response(latest, output=(outputs_by_run_id or {}).get(latest.run_id)) if latest else None,
    )


def radar_detail_response(
    radar: RadarRecord,
    *,
    active_definition: RadarDefinitionRecord | None,
    runs: tuple[RadarRunRecord, ...],
    outputs_by_run_id: dict[str, RadarRunOutputRecord],
) -> RadarDetailResponse:
    summary = radar_summary_response(radar, runs=runs, outputs_by_run_id=outputs_by_run_id)
    return RadarDetailResponse(
        **summary.model_dump(),
        active_definition=definition_response(active_definition) if active_definition else None,
        runs=[run_summary_response(run, output=outputs_by_run_id.get(run.run_id)) for run in runs],
    )


def definition_response(record: RadarDefinitionRecord) -> RadarDefinitionResponse:
    return RadarDefinitionResponse(
        definition_id=record.definition_id,
        radar_id=record.radar_id,
        definition_version=record.definition_version,
        definition_payload=record.definition_payload,
        is_active=record.is_active,
        updated_at=record.updated_at,
    )


def run_summary_response(
    run: RadarRunRecord,
    *,
    output: RadarRunOutputRecord | None,
) -> RadarRunSummaryResponse:
    return RadarRunSummaryResponse(
        run_id=run.run_id,
        radar_id=run.radar_id,
        status=run.status.value,
        queued_at=run.queued_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        idempotency_key=run.idempotency_key,
        correlation_id=run.correlation_id,
        error_message=run.error_message,
        error_metadata=run.error_metadata,
        run_metadata=run.run_metadata,
        output=output_summary_response(output) if output else None,
    )


def output_summary_response(output: RadarRunOutputRecord) -> RadarRunOutputSummaryResponse:
    return RadarRunOutputSummaryResponse(
        artifact_version=output.artifact_version,
        source_count=len(output.sources_payload),
        candidate_count=len(output.candidates_payload),
        contract_issue_count=len(output.contract_validation_payload),
        updated_at=output.updated_at,
    )


def candidates_response(
    run: RadarRunRecord,
    output: RadarRunOutputRecord,
    *,
    reviews: tuple[RadarReviewDecisionRecord, ...] = (),
) -> RadarRunCandidatesResponse:
    artifact = output.artifact_payload
    review_index = _review_index(reviews)
    return RadarRunCandidatesResponse(
        run_id=run.run_id,
        radar_id=run.radar_id,
        candidates=[_candidate_response(item, review_index=review_index) for item in _list(artifact.get("candidates"))],
        sources=[_source_response(item) for item in _list(artifact.get("sources"))],
        contract_validation=_list(artifact.get("contract_validation")),
    )


def reviews_response(run: RadarRunRecord, reviews: tuple[RadarReviewDecisionRecord, ...]) -> RadarRunReviewsResponse:
    return RadarRunReviewsResponse(
        run_id=run.run_id,
        radar_id=run.radar_id,
        decisions=[review_response(review) for review in reviews],
    )


def review_response(record: RadarReviewDecisionRecord) -> RadarReviewDecisionResponse:
    return RadarReviewDecisionResponse(
        decision_id=record.decision_id,
        run_id=record.run_id,
        radar_id=record.radar_id,
        candidate_id=record.candidate_id,
        subject_type=record.subject_type,
        subject_id=record.subject_id,
        status=record.status,
        reviewer=record.reviewer,
        comment=record.comment,
        decision_payload=record.decision_payload,
        score_impact=record.score_impact,
        reviewed_at=record.reviewed_at,
        updated_at=record.updated_at,
    )


def _candidate_response(
    payload: dict[str, Any],
    *,
    review_index: dict[tuple[str, str, str], RadarReviewDecisionRecord],
) -> RadarCandidateResponse:
    score = _dict(payload.get("score"))
    candidate_id = str(payload.get("candidate_id", ""))
    return RadarCandidateResponse(
        candidate_id=candidate_id,
        legal_name=str(payload.get("legal_name", "")),
        description=str(payload.get("description", "")),
        score=CandidateScoreResponse(
            fit_score=_optional_int(score.get("fit_score")),
            intent_score=_optional_int(score.get("intent_score")),
            tier=str(score.get("tier")) if score.get("tier") is not None else None,
        ),
        review_flags=[str(item) for item in payload.get("review_flags", []) if isinstance(item, str)],
        evidence_refs=[str(item) for item in payload.get("evidence_refs", []) if isinstance(item, str)],
        qualification=[
            _qualification_response(item, review=_find_review(review_index, candidate_id, "qualification", _qualification_subject_id(item)))
            for item in _list(payload.get("qualification"))
        ],
        signals=[
            _signal_response(item, review=_find_review(review_index, candidate_id, "signal", str(item.get("signal_code", ""))))
            for item in _list(payload.get("signals"))
        ],
    )


def _qualification_response(
    payload: dict[str, Any],
    *,
    review: RadarReviewDecisionRecord | None = None,
) -> QualificationResponse:
    return QualificationResponse(
        criterion_code=str(payload.get("criterion_code", "")),
        criterion=str(payload.get("criterion", "")),
        status=str(payload.get("status", "unknown")),
        confidence=str(payload.get("confidence", "low")),
        rationale=str(payload.get("rationale", "")),
        evidence_refs=[str(item) for item in payload.get("evidence_refs", []) if isinstance(item, str)],
        rule_id=str(payload.get("rule_id", "")),
        rule_text_snapshot=str(payload.get("rule_text_snapshot", "")),
        operator=str(payload.get("operator", "AND")),
        requirement_level=str(payload.get("requirement_level", "required")),
        confidence_policy=str(payload.get("confidence_policy", "hitl_required")),
        source_usages=[_source_usage_response(item) for item in _list(payload.get("source_usages"))],
        evidence_findings=[_evidence_finding_response(item) for item in _list(payload.get("evidence_findings"))],
        cross_validation=_dict(payload.get("cross_validation")),
        requirement_evaluation=_dict(payload.get("requirement_evaluation")),
        final_assessment=str(payload.get("final_assessment", "unknown")),
        review_decision=_review_payload(review) or _dict_or_none(payload.get("review_decision")),
    )


def _signal_response(
    payload: dict[str, Any],
    *,
    review: RadarReviewDecisionRecord | None = None,
) -> SignalResponse:
    return SignalResponse(
        signal_code=str(payload.get("signal_code", "")),
        signal=str(payload.get("signal", "")),
        status=str(payload.get("status", "unclear")),
        score=int(payload.get("score", 0) or 0),
        confidence=str(payload.get("confidence", "low")),
        summary=str(payload.get("summary", "")),
        evidence_refs=[str(item) for item in payload.get("evidence_refs", []) if isinstance(item, str)],
        source_usages=[_source_usage_response(item) for item in _list(payload.get("source_usages"))],
        evidence_findings=[_evidence_finding_response(item) for item in _list(payload.get("evidence_findings"))],
        cross_validation=_dict(payload.get("cross_validation")),
        score_evaluation=_dict_or_none(payload.get("score_evaluation")),
        review_decision=_review_payload(review),
    )


def _source_usage_response(payload: dict[str, Any]) -> SourceUsageResponse:
    return SourceUsageResponse(**_known(payload, SourceUsageResponse.model_fields))


def _evidence_finding_response(payload: dict[str, Any]) -> EvidenceFindingResponse:
    return EvidenceFindingResponse(**_known(payload, EvidenceFindingResponse.model_fields))


def _source_response(payload: dict[str, Any]) -> RadarSourceResponse:
    return RadarSourceResponse(**_known(payload, RadarSourceResponse.model_fields))


def _known(payload: dict[str, Any], fields: dict[str, object]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key in fields}


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _dict_or_none(value: object) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, dict) else None


def _optional_int(value: object) -> int | None:
    return int(value) if isinstance(value, int | float | str) and str(value).isdigit() else None


def _review_index(
    reviews: tuple[RadarReviewDecisionRecord, ...],
) -> dict[tuple[str, str, str], RadarReviewDecisionRecord]:
    return {
        (review.candidate_id, review.subject_type, review.subject_id): review
        for review in reviews
    }


def _find_review(
    review_index: dict[tuple[str, str, str], RadarReviewDecisionRecord],
    candidate_id: str,
    subject_type: str,
    subject_id: str,
) -> RadarReviewDecisionRecord | None:
    return review_index.get((candidate_id, subject_type, subject_id))


def _qualification_subject_id(payload: dict[str, Any]) -> str:
    return str(payload.get("rule_id") or payload.get("criterion_code") or "")


def _review_payload(review: RadarReviewDecisionRecord | None) -> dict[str, Any] | None:
    if review is None:
        return None
    return {
        "status": review.status,
        **review.decision_payload,
        "comment": review.comment,
        "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at is not None else "",
    }
