"""FastAPI routes for persisted Radar catalog and run contracts."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from power_web_os.api.dependencies import RadarApiContext, get_radar_api_context
from power_web_os.api.radar_dtos import (
    RadarDetailResponse,
    RadarRunCandidatesResponse,
    RadarRunJournalResponse,
    RadarRunRequest,
    RadarRunReviewsResponse,
    RadarRunSummaryResponse,
    RadarReviewDecisionRequest,
    RadarReviewDecisionResponse,
    RadarSummaryResponse,
)
from power_web_os.api.radar_mappers import (
    candidates_response,
    journal_response,
    radar_detail_response,
    radar_summary_response,
    review_response,
    reviews_response,
    run_summary_response,
)
from power_web_os.application.persisted_live_radar import PersistedLiveRadarRunCommand, QueuedLiveRadarRunService
from power_web_os.application.radar_run_journal import RadarRunJournal
from power_web_os.application.radar_review import (
    QUALIFICATION_SUBJECT,
    SIGNAL_SUBJECT,
    RadarReviewDecisionCommand,
    RadarReviewDecisionService,
    RadarReviewValidationError,
)
from power_web_os.application.radar_records import RadarRunOutputRecord, RadarRunRecord

router = APIRouter(prefix="/api", tags=["radars"])

RadarContext = Annotated[RadarApiContext, Depends(get_radar_api_context)]


@router.get("/radars", response_model=list[RadarSummaryResponse])
def list_radars(context: RadarContext) -> list[RadarSummaryResponse]:
    responses: list[RadarSummaryResponse] = []
    for radar in context.radar_repository.list():
        runs = context.run_repository.list_for_radar(radar.radar_id)
        outputs = _outputs_for_runs(context, runs)
        responses.append(radar_summary_response(radar, runs=runs, outputs_by_run_id=outputs))
    return responses


@router.get("/radars/{radar_id}", response_model=RadarDetailResponse)
def get_radar(radar_id: str, context: RadarContext) -> RadarDetailResponse:
    radar = context.radar_repository.get(radar_id)
    if radar is None:
        raise HTTPException(status_code=404, detail=f"Radar not found: {radar_id}")
    runs = context.run_repository.list_for_radar(radar_id)
    return radar_detail_response(
        radar,
        active_definition=context.definition_repository.get_active(radar_id),
        runs=runs,
        outputs_by_run_id=_outputs_for_runs(context, runs),
    )


@router.post(
    "/radars/{radar_id}/runs",
    response_model=RadarRunSummaryResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def queue_radar_run(radar_id: str, request: RadarRunRequest, context: RadarContext) -> RadarRunSummaryResponse:
    radar = context.radar_repository.get(radar_id)
    if radar is None:
        raise HTTPException(status_code=404, detail=f"Radar not found: {radar_id}")

    result = QueuedLiveRadarRunService(
        run_repository=context.run_repository,
        journal=RadarRunJournal(repository=context.event_repository),
    ).create(
        PersistedLiveRadarRunCommand(
            radar_id=radar_id,
            live=request.live,
            idempotency_key=request.idempotency_key,
            correlation_id=request.correlation_id,
            requester=request.requester,
            task_context=request.task_context,
        )
    )
    if result.should_enqueue:
        context.job_queue.enqueue_radar_run(result.run)
    return run_summary_response(result.run, output=context.output_repository.get(result.run.run_id))


@router.get("/radar-runs/{run_id}", response_model=RadarRunSummaryResponse)
def get_radar_run(run_id: str, context: RadarContext) -> RadarRunSummaryResponse:
    run = context.run_repository.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Radar run not found: {run_id}")
    return run_summary_response(run, output=context.output_repository.get(run_id))


@router.get("/radar-runs/{run_id}/candidates", response_model=RadarRunCandidatesResponse)
def get_radar_run_candidates(run_id: str, context: RadarContext) -> RadarRunCandidatesResponse:
    run, output = _run_and_output(run_id, context)
    return candidates_response(run, output, reviews=context.review_repository.list_for_run(run_id))


@router.get("/radar-runs/{run_id}/journal", response_model=RadarRunJournalResponse)
def get_radar_run_journal(run_id: str, context: RadarContext) -> RadarRunJournalResponse:
    run = context.run_repository.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Radar run not found: {run_id}")
    return journal_response(run, context.event_repository.list_for_run(run_id))


@router.get("/radar-runs/{run_id}/reviews", response_model=RadarRunReviewsResponse)
def get_radar_run_reviews(run_id: str, context: RadarContext) -> RadarRunReviewsResponse:
    run = context.run_repository.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Radar run not found: {run_id}")
    return reviews_response(run, context.review_repository.list_for_run(run_id))


@router.put(
    "/radar-runs/{run_id}/candidates/{candidate_id}/qualification/{rule_id}/review",
    response_model=RadarReviewDecisionResponse,
)
def save_qualification_review(
    run_id: str,
    candidate_id: str,
    rule_id: str,
    request: RadarReviewDecisionRequest,
    context: RadarContext,
) -> RadarReviewDecisionResponse:
    run, output = _run_and_output(run_id, context)
    subject = _qualification_subject(output, candidate_id=candidate_id, rule_id=rule_id)
    command = RadarReviewDecisionCommand(
        run_id=run.run_id,
        radar_id=run.radar_id,
        candidate_id=candidate_id,
        subject_type=QUALIFICATION_SUBJECT,
        subject_id=rule_id,
        status=request.status,
        reviewer=request.reviewer,
        comment=request.comment,
        decision_payload={
            "corrected_assessment": request.corrected_assessment if request.status == "corrected" else None,
        },
        source_payload=subject,
        reviewed_at=request.reviewed_at,
    )
    return review_response(_save_review(command, context))


@router.delete(
    "/radar-runs/{run_id}/candidates/{candidate_id}/qualification/{rule_id}/review",
    response_class=Response,
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_qualification_review(run_id: str, candidate_id: str, rule_id: str, context: RadarContext) -> Response:
    _, output = _run_and_output(run_id, context)
    _qualification_subject(output, candidate_id=candidate_id, rule_id=rule_id)
    RadarReviewDecisionService(repository=context.review_repository).delete(
        run_id=run_id,
        candidate_id=candidate_id,
        subject_type=QUALIFICATION_SUBJECT,
        subject_id=rule_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/radar-runs/{run_id}/candidates/{candidate_id}/signals/{signal_code}/review",
    response_model=RadarReviewDecisionResponse,
)
def save_signal_review(
    run_id: str,
    candidate_id: str,
    signal_code: str,
    request: RadarReviewDecisionRequest,
    context: RadarContext,
) -> RadarReviewDecisionResponse:
    run, output = _run_and_output(run_id, context)
    subject = _signal_subject(output, candidate_id=candidate_id, signal_code=signal_code)
    command = RadarReviewDecisionCommand(
        run_id=run.run_id,
        radar_id=run.radar_id,
        candidate_id=candidate_id,
        subject_type=SIGNAL_SUBJECT,
        subject_id=signal_code,
        status=request.status,
        reviewer=request.reviewer,
        comment=request.comment,
        decision_payload={
            "adjusted_score": request.adjusted_score if request.status == "corrected" else None,
            "confidence": request.confidence,
            "corrected_summary": request.corrected_summary,
            "evidence_refs": request.evidence_refs,
        },
        source_payload=subject,
        reviewed_at=request.reviewed_at,
    )
    return review_response(_save_review(command, context))


@router.delete(
    "/radar-runs/{run_id}/candidates/{candidate_id}/signals/{signal_code}/review",
    response_class=Response,
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_signal_review(run_id: str, candidate_id: str, signal_code: str, context: RadarContext) -> Response:
    _, output = _run_and_output(run_id, context)
    _signal_subject(output, candidate_id=candidate_id, signal_code=signal_code)
    RadarReviewDecisionService(repository=context.review_repository).delete(
        run_id=run_id,
        candidate_id=candidate_id,
        subject_type=SIGNAL_SUBJECT,
        subject_id=signal_code,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _outputs_for_runs(context: RadarApiContext, runs: tuple[RadarRunRecord, ...]) -> dict[str, RadarRunOutputRecord]:
    outputs = {}
    for run in runs:
        output = context.output_repository.get(run.run_id)
        if output is not None:
            outputs[run.run_id] = output
    return outputs


def _run_and_output(run_id: str, context: RadarApiContext) -> tuple[RadarRunRecord, RadarRunOutputRecord]:
    run = context.run_repository.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Radar run not found: {run_id}")
    output = context.output_repository.get(run_id)
    if output is None:
        raise HTTPException(status_code=409, detail=f"Radar run has no persisted output: {run_id}")
    return run, output


def _save_review(command: RadarReviewDecisionCommand, context: RadarApiContext):
    try:
        return RadarReviewDecisionService(repository=context.review_repository).save(command)
    except RadarReviewValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _qualification_subject(output: RadarRunOutputRecord, *, candidate_id: str, rule_id: str) -> dict[str, object]:
    candidate = _candidate_payload(output, candidate_id)
    for item in _payload_list(candidate.get("qualification")):
        if str(item.get("rule_id") or item.get("criterion_code") or "") == rule_id:
            return item
    raise HTTPException(status_code=404, detail=f"Qualification finding not found: {rule_id}")


def _signal_subject(output: RadarRunOutputRecord, *, candidate_id: str, signal_code: str) -> dict[str, object]:
    candidate = _candidate_payload(output, candidate_id)
    for item in _payload_list(candidate.get("signals")):
        if str(item.get("signal_code", "")) == signal_code:
            return item
    raise HTTPException(status_code=404, detail=f"Signal finding not found: {signal_code}")


def _candidate_payload(output: RadarRunOutputRecord, candidate_id: str) -> dict[str, object]:
    for item in _payload_list(output.artifact_payload.get("candidates")):
        if str(item.get("candidate_id", "")) == candidate_id:
            return item
    raise HTTPException(status_code=404, detail=f"Candidate not found: {candidate_id}")


def _payload_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
