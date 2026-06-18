"""SQLAlchemy table mappings for Radar persistence.

Models describe storage shape only. Business rules, scoring, review semantics,
and job execution decisions belong to domain/application layers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from power_web_os.application.radar_records import RadarRunStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class RadarModel(Base):
    __tablename__ = "radars"

    radar_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    owner: Mapped[str] = mapped_column(String(160), nullable=False)
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    artifact_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    definitions: Mapped[list[RadarDefinitionModel]] = relationship(back_populates="radar")
    runs: Mapped[list[RadarRunModel]] = relationship(back_populates="radar")


class RadarDefinitionModel(Base):
    __tablename__ = "radar_definitions"

    definition_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    radar_id: Mapped[str] = mapped_column(ForeignKey("radars.radar_id"), nullable=False, index=True)
    definition_version: Mapped[str] = mapped_column(String(80), nullable=False)
    definition_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    radar: Mapped[RadarModel] = relationship(back_populates="definitions")


class RadarRunModel(Base):
    __tablename__ = "radar_runs"
    # Durable run state is the product truth; future worker queues are adapters.
    __table_args__ = (
        CheckConstraint(
            "status in ('queued', 'running', 'waiting_human', 'completed', 'failed', 'cancelled')",
            name="ck_radar_runs_status",
        ),
        UniqueConstraint("idempotency_key", name="uq_radar_runs_idempotency_key"),
    )

    run_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    radar_id: Mapped[str] = mapped_column(ForeignKey("radars.radar_id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default=RadarRunStatus.QUEUED.value, index=True)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    run_metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    radar: Mapped[RadarModel] = relationship(back_populates="runs")
    output: Mapped[RadarRunOutputModel | None] = relationship(back_populates="run", uselist=False)
    events: Mapped[list[RadarRunEventModel]] = relationship(back_populates="run")
    technical_traces: Mapped[list[RadarRunTechnicalTraceModel]] = relationship(back_populates="run")


class RadarRunOutputModel(Base):
    __tablename__ = "radar_run_outputs"

    run_id: Mapped[str] = mapped_column(ForeignKey("radar_runs.run_id"), primary_key=True)
    artifact_version: Mapped[str] = mapped_column(String(80), nullable=False)
    radar_payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    search_plan_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    sources_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    candidates_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    contract_validation_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    artifact_payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    run: Mapped[RadarRunModel] = relationship(back_populates="output")


class RadarReviewDecisionModel(Base):
    __tablename__ = "radar_review_decisions"
    __table_args__ = (
        CheckConstraint("subject_type in ('qualification', 'signal')", name="ck_radar_review_subject_type"),
        UniqueConstraint(
            "run_id",
            "candidate_id",
            "subject_type",
            "subject_id",
            name="uq_radar_review_decision_subject",
        ),
    )

    decision_id: Mapped[str] = mapped_column(String(360), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("radar_runs.run_id"), nullable=False, index=True)
    radar_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    candidate_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(40), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(160), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    decision_payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    score_impact_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class RadarRunEventModel(Base):
    __tablename__ = "radar_run_events"
    __table_args__ = (
        CheckConstraint("visibility in ('user', 'operator', 'debug')", name="ck_radar_run_events_visibility"),
        UniqueConstraint("run_id", "sequence", name="uq_radar_run_events_run_sequence"),
    )

    event_id: Mapped[str] = mapped_column(String(220), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("radar_runs.run_id"), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    phase: Mapped[str] = mapped_column(String(80), nullable=False)
    actor: Mapped[str] = mapped_column(String(80), nullable=False)
    node_name: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    visibility: Mapped[str] = mapped_column(String(40), nullable=False, default="user")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    source_refs_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    candidate_refs_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    run: Mapped[RadarRunModel] = relationship(back_populates="events")


class RadarRunTechnicalTraceModel(Base):
    __tablename__ = "radar_run_technical_traces"
    __table_args__ = (
        CheckConstraint(
            "trace_type in ('pipeline_input', 'pipeline_output', 'provider_request', 'provider_response', 'provider_error', 'normalization_result', 'validation_result')",
            name="ck_radar_run_technical_traces_type",
        ),
        UniqueConstraint("run_id", "sequence", name="uq_radar_run_technical_traces_run_sequence"),
    )

    trace_id: Mapped[str] = mapped_column(String(220), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("radar_runs.run_id"), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(nullable=False)
    phase: Mapped[str] = mapped_column(String(80), nullable=False)
    node_name: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    trace_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    redaction_report_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    run: Mapped[RadarRunModel] = relationship(back_populates="technical_traces")
