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
