"""Transport contracts for Signal Monitoring run APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SignalMonitoringRunRequest(BaseModel):
    source_candidate_run_id: str
    candidate_scope_mode: Literal["accepted_and_review_needed", "accepted_only"] = "accepted_and_review_needed"
    candidate_ids: list[str] = Field(default_factory=list)
    signal_codes: list[str] = Field(default_factory=list)
    lookback_days: int | None = Field(default=None, ge=1, le=3650)
    run_profile: Literal["signal_monitoring_smoke", "signal_monitoring_quality"] = "signal_monitoring_smoke"
    idempotency_key: str | None = None
    correlation_id: str | None = None
    requester: str = "api"


class SignalMonitoringPreflightResponse(BaseModel):
    artifact_type: str = "signal_monitoring_preflight_report"
    pipeline_id: str = "signal_monitoring"
    radar_id: str
    source_candidate_run_id: str
    ready_for_live_run: bool
    issues: list[str] = Field(default_factory=list)
    candidate_count: int = 0
    signal_rule_count: int = 0
    lookback_days: int = 0
    budget: dict[str, Any] = Field(default_factory=dict)
    effective_signal_policies: list[dict[str, Any]] = Field(default_factory=list)


class SignalMonitoringOutputSummaryResponse(BaseModel):
    artifact_version: str
    completion_state: str
    candidate_count: int
    observation_count: int
    provider_call_count: int
    updated_at: datetime | None = None


class SignalMonitoringRunSummaryResponse(BaseModel):
    run_id: str
    radar_id: str
    pipeline_id: str = "signal_monitoring"
    source_run_id: str
    status: str
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    idempotency_key: str | None = None
    correlation_id: str | None = None
    error_message: str | None = None
    error_metadata: dict[str, Any] = Field(default_factory=dict)
    run_metadata: dict[str, Any] = Field(default_factory=dict)
    output: SignalMonitoringOutputSummaryResponse | None = None
