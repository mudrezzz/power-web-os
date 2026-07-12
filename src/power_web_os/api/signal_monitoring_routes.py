"""FastAPI routes for independent Signal Monitoring runs."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from power_web_os.api.dependencies import RadarApiContext, get_radar_api_context
from power_web_os.api.radar_mappers import signal_monitoring_run_summary_response
from power_web_os.api.signal_monitoring_dtos import (
    SignalMonitoringPreflightResponse,
    SignalMonitoringRunRequest,
    SignalMonitoringRunSummaryResponse,
)
from power_web_os.application.radar.signal_monitoring.input_assembler import SignalMonitoringInputError
from power_web_os.application.radar.signal_monitoring.runtime import (
    QueuedSignalMonitoringRunService,
    SignalMonitoringRunCommand,
)
from power_web_os.application.radar_records import RadarRunRecord

router = APIRouter(prefix="/api", tags=["signal-monitoring"])

RadarContext = Annotated[RadarApiContext, Depends(get_radar_api_context)]


@router.get(
    "/radars/{radar_id}/signal-monitoring/preflight",
    response_model=SignalMonitoringPreflightResponse,
)
def signal_monitoring_preflight(
    radar_id: str,
    source_candidate_run_id: str,
    context: RadarContext,
    candidate_scope_mode: Literal["accepted_and_review_needed", "accepted_only"] = "accepted_and_review_needed",
    candidate_ids: list[str] = Query(default=[]),
    signal_codes: list[str] = Query(default=[]),
    lookback_days: int | None = Query(default=None, ge=1, le=365),
    run_profile: Literal["signal_monitoring_smoke", "signal_monitoring_quality"] = "signal_monitoring_smoke",
) -> SignalMonitoringPreflightResponse:
    _require_radar(radar_id, context)
    command = SignalMonitoringRunCommand(
        radar_id=radar_id,
        source_candidate_run_id=source_candidate_run_id,
        candidate_scope_mode=candidate_scope_mode,
        candidate_ids=tuple(candidate_ids),
        signal_codes=tuple(signal_codes),
        lookback_days=lookback_days,
        run_profile=run_profile,
    )
    payload = _service(context).preflight(command)
    issues = [str(item) for item in payload.get("issues", [])]
    if not _openrouter_credentials_available(context):
        issues.append("OPENROUTER_API_KEY is not available to the API runtime.")
    return SignalMonitoringPreflightResponse(
        radar_id=radar_id,
        source_candidate_run_id=source_candidate_run_id,
        ready_for_live_run=bool(payload.get("ready_for_live_run")) and not issues,
        issues=issues,
        candidate_count=int(payload.get("candidate_count") or 0),
        signal_rule_count=int(payload.get("signal_rule_count") or 0),
        lookback_days=int(payload.get("lookback_days") or 0),
        budget=dict(payload.get("budget") or {}),
    )


@router.post(
    "/radars/{radar_id}/signal-monitoring-runs",
    response_model=SignalMonitoringRunSummaryResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def queue_signal_monitoring_run(
    radar_id: str,
    request: SignalMonitoringRunRequest,
    context: RadarContext,
) -> SignalMonitoringRunSummaryResponse:
    _require_radar(radar_id, context)
    if not _openrouter_credentials_available(context):
        raise HTTPException(status_code=422, detail="OPENROUTER_API_KEY is required for live signal monitoring.")
    try:
        result = _service(context).create(
            SignalMonitoringRunCommand(
                radar_id=radar_id,
                source_candidate_run_id=request.source_candidate_run_id,
                candidate_scope_mode=request.candidate_scope_mode,
                candidate_ids=tuple(request.candidate_ids),
                signal_codes=tuple(request.signal_codes),
                lookback_days=request.lookback_days,
                idempotency_key=request.idempotency_key,
                correlation_id=request.correlation_id,
                requester=request.requester,
                run_profile=request.run_profile,
            )
        )
    except SignalMonitoringInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if result.should_enqueue:
        context.commit_before_enqueue()
        context.signal_monitoring_job_queue.enqueue_signal_monitoring_run(result.run)
    return signal_monitoring_run_summary_response(
        result.run,
        output=context.signal_monitoring_output_repository.get(result.run.run_id),
    )


@router.get(
    "/radars/{radar_id}/signal-monitoring-runs",
    response_model=list[SignalMonitoringRunSummaryResponse],
)
def list_signal_monitoring_runs(
    radar_id: str,
    context: RadarContext,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[SignalMonitoringRunSummaryResponse]:
    _require_radar(radar_id, context)
    runs = tuple(reversed(context.run_repository.list_for_radar(radar_id, pipeline_id="signal_monitoring")))[:limit]
    return [
        signal_monitoring_run_summary_response(
            run,
            output=context.signal_monitoring_output_repository.get(run.run_id),
        )
        for run in runs
    ]


@router.get(
    "/signal-monitoring-runs/{run_id}",
    response_model=SignalMonitoringRunSummaryResponse,
)
def get_signal_monitoring_run(run_id: str, context: RadarContext) -> SignalMonitoringRunSummaryResponse:
    run = _signal_run(run_id, context)
    return signal_monitoring_run_summary_response(
        run,
        output=context.signal_monitoring_output_repository.get(run.run_id),
    )


@router.get("/signal-monitoring-runs/{run_id}/report")
def get_signal_monitoring_report(run_id: str, context: RadarContext) -> dict[str, object]:
    run = _signal_run(run_id, context)
    output = context.signal_monitoring_output_repository.get(run.run_id)
    if output is None:
        raise HTTPException(status_code=409, detail=f"Signal monitoring run has no persisted output: {run_id}")
    return dict(output.artifact_payload)


def _service(context: RadarApiContext) -> QueuedSignalMonitoringRunService:
    return QueuedSignalMonitoringRunService(
        run_repository=context.run_repository,
        candidate_output_repository=context.output_repository,
        signal_output_repository=context.signal_monitoring_output_repository,
        definition_repository=context.definition_repository,
        event_repository=context.event_repository,
    )


def _signal_run(run_id: str, context: RadarApiContext) -> RadarRunRecord:
    run = context.run_repository.get(run_id)
    if run is None or run.pipeline_id != "signal_monitoring":
        raise HTTPException(status_code=404, detail=f"Signal monitoring run not found: {run_id}")
    return run


def _require_radar(radar_id: str, context: RadarApiContext) -> None:
    if context.radar_repository.get(radar_id) is None:
        raise HTTPException(status_code=404, detail=f"Radar not found: {radar_id}")


def _openrouter_credentials_available(context: RadarApiContext) -> bool:
    config = context.runtime_config_report.get("config")
    openrouter = config.get("openrouter") if isinstance(config, dict) else None
    return bool(openrouter.get("api_key_present")) if isinstance(openrouter, dict) else False
