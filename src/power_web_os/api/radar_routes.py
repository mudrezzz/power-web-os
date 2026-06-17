"""FastAPI routes for persisted Radar catalog and run contracts."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from power_web_os.api.dependencies import RadarApiContext, get_radar_api_context
from power_web_os.api.radar_dtos import (
    RadarDetailResponse,
    RadarRunCandidatesResponse,
    RadarRunRequest,
    RadarRunSummaryResponse,
    RadarSummaryResponse,
)
from power_web_os.api.radar_mappers import candidates_response, radar_detail_response, radar_summary_response, run_summary_response
from power_web_os.application.persisted_live_radar import PersistedLiveRadarRunCommand, PersistedLiveRadarRunService
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


@router.post("/radars/{radar_id}/runs", response_model=RadarRunSummaryResponse)
def run_radar_inline(radar_id: str, request: RadarRunRequest, context: RadarContext) -> RadarRunSummaryResponse:
    radar = context.radar_repository.get(radar_id)
    if radar is None:
        raise HTTPException(status_code=404, detail=f"Radar not found: {radar_id}")

    service = PersistedLiveRadarRunService(
        run_repository=context.run_repository,
        output_repository=context.output_repository,
        executor=context.live_executor,
    )
    result = service.run(
        PersistedLiveRadarRunCommand(
            radar_id=radar_id,
            live=request.live,
            idempotency_key=request.idempotency_key,
            correlation_id=request.correlation_id,
            requester=request.requester,
            task_context=request.task_context,
        )
    )
    return run_summary_response(result.run, output=result.output)


@router.get("/radar-runs/{run_id}", response_model=RadarRunSummaryResponse)
def get_radar_run(run_id: str, context: RadarContext) -> RadarRunSummaryResponse:
    run = context.run_repository.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Radar run not found: {run_id}")
    return run_summary_response(run, output=context.output_repository.get(run_id))


@router.get("/radar-runs/{run_id}/candidates", response_model=RadarRunCandidatesResponse)
def get_radar_run_candidates(run_id: str, context: RadarContext) -> RadarRunCandidatesResponse:
    run = context.run_repository.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Radar run not found: {run_id}")
    output = context.output_repository.get(run_id)
    if output is None:
        raise HTTPException(status_code=409, detail=f"Radar run has no persisted output: {run_id}")
    return candidates_response(run, output)


def _outputs_for_runs(context: RadarApiContext, runs: tuple[RadarRunRecord, ...]) -> dict[str, RadarRunOutputRecord]:
    outputs = {}
    for run in runs:
        output = context.output_repository.get(run.run_id)
        if output is not None:
            outputs[run.run_id] = output
    return outputs
