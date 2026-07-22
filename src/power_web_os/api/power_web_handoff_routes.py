"""HTTP transport for Radar product policy and Power Web handoff preparation."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from power_web_os.api.dependencies import PowerWebHandoffApiContext, get_power_web_handoff_api_context
from power_web_os.api.power_web_handoff_dtos import (
    PowerWebHandoffCreateRequest,
    RadarPowerWebPolicyUpdateRequest,
)
from power_web_os.application.radar.power_web_discovery.contracts import (
    PowerWebHandoffPreflight,
    PowerWebHandoffSnapshot,
    RadarPowerWebPolicyVersion,
)
from power_web_os.application.radar.power_web_discovery.handoff import (
    PowerWebHandoffConflictError,
    PowerWebHandoffError,
    PowerWebHandoffPreflightService,
    PowerWebHandoffService,
    RadarPowerWebPolicyService,
)


router = APIRouter(prefix="/api", tags=["power-web-handoff"])
Context = Annotated[PowerWebHandoffApiContext, Depends(get_power_web_handoff_api_context)]


@router.get("/radars/{radar_id}/power-web-policy", response_model=RadarPowerWebPolicyVersion | None)
def get_policy(radar_id: str, context: Context) -> RadarPowerWebPolicyVersion | None:
    _require_radar(radar_id, context)
    return context.policy_repository.get_active(radar_id)


@router.put("/radars/{radar_id}/power-web-policy", response_model=RadarPowerWebPolicyVersion)
def update_policy(
    radar_id: str,
    request: RadarPowerWebPolicyUpdateRequest,
    context: Context,
) -> RadarPowerWebPolicyVersion:
    _require_radar(radar_id, context)
    try:
        return RadarPowerWebPolicyService(
            policy_repository=context.policy_repository,
            product_reader=context.product_reader,
        ).update(
            radar_id=radar_id,
            product_ids=tuple(request.product_ids),
            expected_policy_version_id=request.expected_policy_version_id,
            requester=request.requester,
        )
    except PowerWebHandoffConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PowerWebHandoffError as exc:
        raise HTTPException(status_code=422, detail=list(exc.reasons)) from exc


@router.get("/radars/{radar_id}/power-web-policy/versions", response_model=list[RadarPowerWebPolicyVersion])
def list_policy_versions(
    radar_id: str,
    context: Context,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[RadarPowerWebPolicyVersion]:
    _require_radar(radar_id, context)
    return list(context.policy_repository.list_versions(radar_id)[:limit])


@router.get("/radars/{radar_id}/power-web-handoff/preflight", response_model=PowerWebHandoffPreflight)
def preflight(
    radar_id: str,
    source_candidate_run_id: str,
    candidate_id: str,
    context: Context,
    product_ids: Annotated[list[str] | None, Query()] = None,
    review_acknowledged: bool = False,
    include_latest_signal_context: bool = True,
) -> PowerWebHandoffPreflight:
    _require_radar(radar_id, context)
    return _preflight_service(context).inspect(
        radar_id=radar_id,
        source_candidate_run_id=source_candidate_run_id,
        candidate_id=candidate_id,
        product_ids=tuple(product_ids) if product_ids is not None else None,
        review_acknowledged=review_acknowledged,
        include_latest_signal_context=include_latest_signal_context,
    )


@router.post(
    "/radars/{radar_id}/power-web-handoffs",
    response_model=PowerWebHandoffSnapshot,
    status_code=status.HTTP_201_CREATED,
)
def create_handoff(
    radar_id: str,
    request: PowerWebHandoffCreateRequest,
    context: Context,
) -> PowerWebHandoffSnapshot:
    _require_radar(radar_id, context)
    acknowledgement = request.review_needed_acknowledgement
    reviewer = acknowledgement.reviewer if acknowledgement and acknowledgement.acknowledged else None
    comment = acknowledgement.comment if reviewer else None
    try:
        return _handoff_service(context).create(
            radar_id=radar_id,
            source_candidate_run_id=request.source_candidate_run_id,
            candidate_id=request.candidate_id,
            product_ids=tuple(request.product_ids) if request.product_ids is not None else None,
            include_latest_signal_context=request.include_latest_signal_context,
            reviewer=reviewer,
            acknowledgement_comment=comment,
            idempotency_key=request.idempotency_key,
            requester=request.requester,
        )
    except PowerWebHandoffConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PowerWebHandoffError as exc:
        raise HTTPException(status_code=422, detail=list(exc.reasons)) from exc


@router.get("/radars/{radar_id}/power-web-handoffs", response_model=list[PowerWebHandoffSnapshot])
def list_handoffs(
    radar_id: str,
    source_candidate_run_id: str,
    candidate_id: str,
    context: Context,
) -> list[PowerWebHandoffSnapshot]:
    _require_radar(radar_id, context)
    return list(context.handoff_repository.list_for_candidate(
        radar_id=radar_id,
        source_candidate_run_id=source_candidate_run_id,
        candidate_id=candidate_id,
    ))


@router.get("/power-web-handoffs/{handoff_id}", response_model=PowerWebHandoffSnapshot)
def get_handoff(handoff_id: str, context: Context) -> PowerWebHandoffSnapshot:
    handoff = context.handoff_repository.get(handoff_id)
    if handoff is None:
        raise HTTPException(status_code=404, detail=f"Power Web handoff not found: {handoff_id}")
    return handoff


def _preflight_service(context: PowerWebHandoffApiContext) -> PowerWebHandoffPreflightService:
    return PowerWebHandoffPreflightService(
        policy_repository=context.policy_repository,
        candidate_reader=context.candidate_reader,
        product_reader=context.product_reader,
        signal_reader=context.signal_reader,
    )


def _handoff_service(context: PowerWebHandoffApiContext) -> PowerWebHandoffService:
    return PowerWebHandoffService(
        policy_repository=context.policy_repository,
        handoff_repository=context.handoff_repository,
        candidate_reader=context.candidate_reader,
        product_reader=context.product_reader,
        signal_reader=context.signal_reader,
    )


def _require_radar(radar_id: str, context: PowerWebHandoffApiContext) -> None:
    if context.radar_repository.get(radar_id) is None:
        raise HTTPException(status_code=404, detail=f"Radar not found: {radar_id}")
