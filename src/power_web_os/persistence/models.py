"""SQLAlchemy table mappings for Radar persistence.

Models describe storage shape only. Business rules, scoring, review semantics,
and job execution decisions belong to domain/application layers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from power_web_os.application.radar.lifecycle.records import RadarRunStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class ProductModel(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("lifecycle in ('draft', 'active', 'archived')", name="ck_products_lifecycle"),
        UniqueConstraint("product_code", name="uq_products_product_code"),
    )

    product_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    product_code: Mapped[str] = mapped_column(String(80), nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", index=True)
    active_version_id: Mapped[str | None] = mapped_column(String(180), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class SalesPlaybookDraftModel(Base):
    __tablename__ = "sales_playbook_drafts"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), primary_key=True)
    draft_revision: Mapped[int] = mapped_column(nullable=False, default=1)
    base_version_id: Mapped[str | None] = mapped_column(String(180), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    updated_by: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class ProductDefinitionVersionModel(Base):
    __tablename__ = "product_definition_versions"

    version_id: Mapped[str] = mapped_column(String(180), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    published_by: Mapped[str] = mapped_column(String(160), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class BuyingRolePolicyVersionModel(Base):
    __tablename__ = "buying_role_policy_versions"

    version_id: Mapped[str] = mapped_column(String(180), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(nullable=False)
    payload_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    published_by: Mapped[str] = mapped_column(String(160), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class AccessPlaybookVersionModel(Base):
    __tablename__ = "access_playbook_versions"

    version_id: Mapped[str] = mapped_column(String(180), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    published_by: Mapped[str] = mapped_column(String(160), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class SalesPlaybookDefinitionVersionModel(Base):
    __tablename__ = "sales_playbook_definition_versions"
    __table_args__ = (UniqueConstraint("product_id", "version_number", name="uq_sales_playbook_product_version"),)

    version_id: Mapped[str] = mapped_column(String(180), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(nullable=False)
    product_definition_version_id: Mapped[str] = mapped_column(
        ForeignKey("product_definition_versions.version_id"), nullable=False
    )
    buying_role_policy_version_id: Mapped[str] = mapped_column(
        ForeignKey("buying_role_policy_versions.version_id"), nullable=False
    )
    access_playbook_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("access_playbook_versions.version_id"), nullable=True
    )
    published_by: Mapped[str] = mapped_column(String(160), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


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


class RadarPowerWebPolicyVersionModel(Base):
    __tablename__ = "radar_power_web_policy_versions"
    __table_args__ = (
        UniqueConstraint("radar_id", "version_number", name="uq_radar_power_web_policy_version"),
    )

    policy_version_id: Mapped[str] = mapped_column(String(180), primary_key=True)
    radar_id: Mapped[str] = mapped_column(ForeignKey("radars.radar_id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class RadarPowerWebPolicyProductBindingModel(Base):
    __tablename__ = "radar_power_web_policy_product_bindings"
    __table_args__ = (
        UniqueConstraint("policy_version_id", "position", name="uq_radar_power_web_policy_position"),
    )

    policy_version_id: Mapped[str] = mapped_column(
        ForeignKey("radar_power_web_policy_versions.policy_version_id"), primary_key=True
    )
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), primary_key=True)
    position: Mapped[int] = mapped_column(nullable=False)


class RadarPowerWebPolicyHeadModel(Base):
    __tablename__ = "radar_power_web_policy_heads"

    radar_id: Mapped[str] = mapped_column(ForeignKey("radars.radar_id"), primary_key=True)
    active_policy_version_id: Mapped[str] = mapped_column(
        ForeignKey("radar_power_web_policy_versions.policy_version_id"), nullable=False, unique=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class PowerWebHandoffModel(Base):
    __tablename__ = "power_web_handoffs"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_power_web_handoff_idempotency"),)

    handoff_id: Mapped[str] = mapped_column(String(180), primary_key=True)
    radar_id: Mapped[str] = mapped_column(ForeignKey("radars.radar_id"), nullable=False, index=True)
    policy_version_id: Mapped[str] = mapped_column(
        ForeignKey("radar_power_web_policy_versions.policy_version_id"), nullable=False
    )
    source_candidate_run_id: Mapped[str] = mapped_column(
        ForeignKey("radar_runs.run_id"), nullable=False, index=True
    )
    source_candidate_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    source_signal_run_id: Mapped[str | None] = mapped_column(ForeignKey("radar_runs.run_id"), nullable=True)
    account_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="ready")
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(80), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_by: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class RadarRunModel(Base):
    __tablename__ = "radar_runs"
    # Durable run state is the product truth; future worker queues are adapters.
    __table_args__ = (
        CheckConstraint(
            "status in ('queued', 'running', 'waiting_human', 'completed', 'failed', 'cancelled')",
            name="ck_radar_runs_status",
        ),
        UniqueConstraint("idempotency_key", name="uq_radar_runs_idempotency_key"),
        CheckConstraint(
            "pipeline_id in ('candidate_discovery', 'signal_monitoring')",
            name="ck_radar_runs_pipeline_id",
        ),
        Index(
            "ix_radar_runs_summary_covering",
            "pipeline_id",
            "status",
            "radar_id",
            "queued_at",
            "run_id",
            "source_run_id",
            "started_at",
            "completed_at",
            "idempotency_key",
            "correlation_id",
            "error_message",
            "display_execution_mode",
            "display_requester",
            "display_run_profile",
            "display_benchmark_profile",
            "display_benchmark_mode",
            "display_signal_execution_mode",
            "created_at",
            "updated_at",
        ),
    )

    run_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    radar_id: Mapped[str] = mapped_column(ForeignKey("radars.radar_id"), nullable=False, index=True)
    pipeline_id: Mapped[str] = mapped_column(String(60), nullable=False, default="candidate_discovery", index=True)
    source_run_id: Mapped[str | None] = mapped_column(ForeignKey("radar_runs.run_id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default=RadarRunStatus.QUEUED.value, index=True)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    run_metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    display_execution_mode: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    display_requester: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    display_run_profile: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    display_benchmark_profile: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    display_benchmark_mode: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    display_signal_execution_mode: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    radar: Mapped[RadarModel] = relationship(back_populates="runs")
    output: Mapped[RadarRunOutputModel | None] = relationship(back_populates="run", uselist=False)
    signal_monitoring_output: Mapped[SignalMonitoringRunOutputModel | None] = relationship(
        back_populates="run",
        uselist=False,
        foreign_keys="SignalMonitoringRunOutputModel.run_id",
    )
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
    source_count: Mapped[int] = mapped_column(nullable=False, default=0)
    candidate_count: Mapped[int] = mapped_column(nullable=False, default=0)
    contract_issue_count: Mapped[int] = mapped_column(nullable=False, default=0)
    visible_candidate_count: Mapped[int] = mapped_column(nullable=False, default=0)
    accepted_candidate_count: Mapped[int] = mapped_column(nullable=False, default=0)
    review_needed_candidate_count: Mapped[int] = mapped_column(nullable=False, default=0)
    artifact_payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    run: Mapped[RadarRunModel] = relationship(back_populates="output")


class RadarRunOutputSummaryModel(Base):
    """Lightweight read model kept outside rows containing multi-megabyte artifacts."""

    __tablename__ = "radar_run_output_summaries"

    run_id: Mapped[str] = mapped_column(ForeignKey("radar_runs.run_id"), primary_key=True)
    artifact_version: Mapped[str] = mapped_column(String(80), nullable=False)
    source_count: Mapped[int] = mapped_column(nullable=False, default=0)
    candidate_count: Mapped[int] = mapped_column(nullable=False, default=0)
    contract_issue_count: Mapped[int] = mapped_column(nullable=False, default=0)
    visible_candidate_count: Mapped[int] = mapped_column(nullable=False, default=0)
    accepted_candidate_count: Mapped[int] = mapped_column(nullable=False, default=0)
    review_needed_candidate_count: Mapped[int] = mapped_column(nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

class SignalMonitoringRunOutputModel(Base):
    __tablename__ = "radar_signal_monitoring_outputs"

    run_id: Mapped[str] = mapped_column(ForeignKey("radar_runs.run_id"), primary_key=True)
    source_run_id: Mapped[str] = mapped_column(ForeignKey("radar_runs.run_id"), nullable=False, index=True)
    artifact_version: Mapped[str] = mapped_column(String(80), nullable=False)
    input_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    plan_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    observations_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    artifact_payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    run: Mapped[RadarRunModel] = relationship(
        back_populates="signal_monitoring_output", foreign_keys=[run_id]
    )


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
