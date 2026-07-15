"""Application records for Radar catalog, definitions, and durable run state.

These dataclasses are stable use-case contracts. They are intentionally separate
from SQLAlchemy ORM models and FastAPI transport DTOs so application code can
depend on records and ports without importing infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RadarRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in {self.COMPLETED, self.FAILED, self.CANCELLED}


@dataclass(frozen=True, slots=True)
class RadarRecord:
    radar_id: str
    name: str
    status: str
    owner: str
    profile: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    artifact_path: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RadarDefinitionRecord:
    definition_id: str
    radar_id: str
    definition_payload: dict[str, Any]
    definition_version: str
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RadarRunRecord:
    run_id: str
    radar_id: str
    pipeline_id: str = "candidate_discovery"
    source_run_id: str | None = None
    status: RadarRunStatus = RadarRunStatus.QUEUED
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    idempotency_key: str | None = None
    correlation_id: str | None = None
    error_message: str | None = None
    error_metadata: dict[str, Any] = field(default_factory=dict)
    run_metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RadarRunOutputRecord:
    """Persisted live Radar output snapshot for one durable run.

    The record intentionally stores JSON payload sections instead of normalized
    candidate/evidence rows. This preserves the current live artifact contract
    while later slices design API-oriented tables.
    """

    run_id: str
    artifact_version: str
    radar_payload: dict[str, Any]
    search_plan_payload: dict[str, Any]
    sources_payload: list[dict[str, Any]]
    candidates_payload: list[dict[str, Any]]
    contract_validation_payload: list[dict[str, Any]] = field(default_factory=list)
    artifact_payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RadarRunOutputSummaryRecord:
    run_id: str
    artifact_version: str
    source_count: int
    candidate_count: int
    contract_issue_count: int
    visible_candidate_count: int = 0
    accepted_candidate_count: int = 0
    review_needed_candidate_count: int = 0
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class SignalMonitoringRunOutputRecord:
    """Persisted output owned by the standalone signal-monitoring pipeline."""

    run_id: str
    source_run_id: str
    artifact_version: str
    input_snapshot_payload: dict[str, Any]
    plan_payload: dict[str, Any]
    observations_payload: list[dict[str, Any]]
    artifact_payload: dict[str, Any]
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RadarReviewDecisionRecord:
    """Current human review decision for one persisted live Radar finding."""

    decision_id: str
    run_id: str
    radar_id: str
    candidate_id: str
    subject_type: str
    subject_id: str
    status: str
    reviewer: str
    comment: str
    decision_payload: dict[str, Any] = field(default_factory=dict)
    score_impact: dict[str, Any] = field(default_factory=dict)
    reviewed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RadarRunEventRecord:
    """Append-only structured audit event for one durable Radar run."""

    event_id: str
    run_id: str
    sequence: int
    event_type: str
    phase: str
    actor: str
    node_name: str = ""
    visibility: str = "user"
    summary: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    source_refs: list[str] = field(default_factory=list)
    candidate_refs: list[str] = field(default_factory=list)
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RadarRunTechnicalTraceRecord:
    """Append-only sanitized developer trace for one durable Radar run."""

    trace_id: str
    run_id: str
    sequence: int
    phase: str
    node_name: str
    trace_type: str
    title: str
    summary: str = ""
    duration_ms: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    redaction_report: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
