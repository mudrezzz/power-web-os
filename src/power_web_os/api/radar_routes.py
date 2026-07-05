"""FastAPI routes for persisted Radar catalog and run contracts."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from power_web_os.api.dependencies import RadarApiContext, get_radar_api_context
from power_web_os.api.radar_dtos import (
    RadarDetailResponse,
    RadarDefinitionUpdateRequest,
    RadarPreflightResponse,
    RadarRunCandidatesResponse,
    RadarRunDossierResponse,
    RadarRunJournalResponse,
    RadarRunRequest,
    RadarRunReviewsResponse,
    RadarRunSummaryResponse,
    RadarRunTechnicalTraceResponse,
    RadarReviewDecisionRequest,
    RadarReviewDecisionResponse,
    RadarSummaryResponse,
)
from power_web_os.api.radar_dossier_mappers import dossier_response
from power_web_os.api.radar_mappers import (
    candidates_response,
    journal_response,
    radar_detail_response,
    radar_summary_response,
    review_response,
    reviews_response,
    run_summary_response,
    technical_trace_response,
)
from power_web_os.application.persisted_live_radar import PersistedLiveRadarRunCommand, QueuedLiveRadarRunService
from power_web_os.application.radar_definition_update import (
    RadarDefinitionUpdateCommand,
    RadarDefinitionUpdateError,
    RadarDefinitionUpdateService,
)
from power_web_os.application.radar.candidate_discovery.planning.definition_runtime import active_definition_to_live_radar_payload
from power_web_os.application.radar_preflight import RadarExecutionPreflightService
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


@router.put("/radars/{radar_id}/definition", response_model=RadarDetailResponse)
def update_radar_definition(
    radar_id: str,
    request: RadarDefinitionUpdateRequest,
    context: RadarContext,
) -> RadarDetailResponse:
    radar = context.radar_repository.get(radar_id)
    if radar is None:
        raise HTTPException(status_code=404, detail=f"Radar not found: {radar_id}")
    try:
        RadarDefinitionUpdateService(context.definition_repository).update_active(
            RadarDefinitionUpdateCommand(
                radar_id=radar_id,
                definition_payload=request.definition_payload,
                definition_version=request.definition_version,
                is_active=request.is_active,
            )
        )
    except RadarDefinitionUpdateError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    runs = context.run_repository.list_for_radar(radar_id)
    return radar_detail_response(
        radar,
        active_definition=context.definition_repository.get_active(radar_id),
        runs=runs,
        outputs_by_run_id=_outputs_for_runs(context, runs),
    )


@router.get("/radars/{radar_id}/preflight", response_model=RadarPreflightResponse)
def get_radar_preflight(
    radar_id: str,
    context: RadarContext,
    include_runtime_config: bool = True,
) -> RadarPreflightResponse:
    radar = context.radar_repository.get(radar_id)
    if radar is None:
        raise HTTPException(status_code=404, detail=f"Radar not found: {radar_id}")
    service = RadarExecutionPreflightService(
        definition_repository=context.definition_repository,
        runtime_definition_provider=lambda: _active_runtime_definition_payload(context, radar_id),
        company_registry_provider_ids=_available_company_registry_provider_ids(context),
    )
    payload = service.run(radar_id=radar_id).to_payload()
    if include_runtime_config:
        payload["runtime_config"] = context.runtime_config_report
    return RadarPreflightResponse.model_validate(payload)


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
            task_context=_run_task_context(request.task_context, context),
            api_runtime_config=context.runtime_config_report,
        )
    )
    if result.should_enqueue:
        context.commit_before_enqueue()
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


@router.get("/radar-runs/{run_id}/technical-trace", response_model=RadarRunTechnicalTraceResponse)
def get_radar_run_technical_trace(run_id: str, context: RadarContext) -> RadarRunTechnicalTraceResponse:
    run = context.run_repository.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Radar run not found: {run_id}")
    return technical_trace_response(run, context.technical_trace_repository.list_for_run(run_id))


@router.get("/radar-runs/{run_id}/dossier", response_model=RadarRunDossierResponse)
def get_radar_run_dossier(run_id: str, context: RadarContext) -> RadarRunDossierResponse:
    run = context.run_repository.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Radar run not found: {run_id}")
    return dossier_response(
        run,
        output=context.output_repository.get(run_id),
        active_definition=context.definition_repository.get_active(run.radar_id),
        events=context.event_repository.list_for_run(run_id),
        reviews=context.review_repository.list_for_run(run_id),
    )


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


def _active_runtime_definition_payload(context: RadarApiContext, radar_id: str) -> dict[str, object]:
    definition = context.definition_repository.get_active(radar_id)
    if definition is None:
        return {}
    return active_definition_to_live_radar_payload(definition)


def _available_company_registry_provider_ids(context: RadarApiContext) -> set[str]:
    config = context.runtime_config_report.get("config")
    dadata = config.get("dadata") if isinstance(config, dict) else None
    if not isinstance(dadata, dict):
        return set()
    mode = str(dadata.get("mode") or "recorded")
    if mode == "recorded":
        return {"dadata"}
    return {"dadata"} if bool(dadata.get("credentials_present")) else set()


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


def _run_task_context(request_task_context: dict[str, object], context: RadarApiContext) -> dict[str, object]:
    defaults = (
        ("max_web_tasks_per_subject", context.radar_max_web_tasks_per_subject),
        ("max_discovery_tasks_per_rule", context.radar_max_discovery_tasks_per_rule),
        ("max_gate_tasks_per_candidate_rule", context.radar_max_gate_tasks_per_candidate_rule),
        ("max_signal_tasks_per_candidate_signal", context.radar_max_signal_tasks_per_candidate_signal),
        ("max_total_web_tasks_per_run", context.radar_max_total_web_tasks_per_run),
        ("source_verification_mode", context.radar_source_verification_mode),
        ("min_useful_sources_per_discovery_task", context.radar_min_useful_sources_per_discovery_task),
        ("min_candidates_per_discovery_task", context.radar_min_candidates_per_discovery_task),
        ("max_discovery_retries_per_task", context.radar_max_discovery_retries_per_task),
        ("max_checkpoint_revisions_per_run", context.radar_max_checkpoint_revisions_per_run),
        ("max_checkpoint_retries_per_stage", context.radar_max_checkpoint_retries_per_stage),
        ("run_profile", context.radar_run_profile),
        ("max_openrouter_calls_per_run", context.radar_max_openrouter_calls_per_run),
        ("max_openrouter_planner_calls_per_run", context.radar_max_openrouter_planner_calls_per_run),
        ("max_openrouter_web_task_calls_per_run", context.radar_max_openrouter_web_task_calls_per_run),
        ("max_openrouter_server_tool_web_searches_per_run", context.radar_max_openrouter_server_tool_web_searches_per_run),
        ("max_dadata_lookups_per_run", context.radar_max_dadata_lookups_per_run),
        ("max_source_verification_requests_per_run", context.radar_max_source_verification_requests_per_run),
        ("max_provider_retries_per_task", context.radar_max_provider_retries_per_task),
        ("openrouter_web_max_results_per_call", context.radar_openrouter_web_max_results_per_call),
        ("openrouter_web_max_total_results_per_call", context.radar_openrouter_web_max_total_results_per_call),
        ("smoke_max_candidates", context.radar_smoke_max_candidates),
        ("smoke_max_signals", context.radar_smoke_max_signals),
    )
    return {
        **request_task_context,
        **{key: _task_context_or_default(request_task_context, key, default) for key, default in defaults},
    }


def _task_context_or_default(task_context: dict[str, object], key: str, default: object) -> object:
    if key in task_context:
        return task_context[key]
    return default
