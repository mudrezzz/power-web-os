"""Application ports for repositories and future Radar execution adapters.

Entry points call these protocols through application services. SQLAlchemy,
Celery, Redis, and provider-specific adapters implement the ports elsewhere.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from power_web_os.application.radar_records import (
    RadarDefinitionRecord,
    RadarRecord,
    RadarRunEventRecord,
    RadarRunOutputRecord,
    RadarRunRecord,
    RadarRunStatus,
    RadarReviewDecisionRecord,
)


class RadarRepository(Protocol):
    """Application port for persisted Radar catalog entries."""

    def upsert(self, record: RadarRecord) -> RadarRecord: ...

    def get(self, radar_id: str) -> RadarRecord | None: ...

    def list(self) -> tuple[RadarRecord, ...]: ...


class RadarDefinitionRepository(Protocol):
    """Application port for versioned Radar definitions."""

    def upsert(self, record: RadarDefinitionRecord) -> RadarDefinitionRecord: ...

    def get_active(self, radar_id: str) -> RadarDefinitionRecord | None: ...

    def list_for_radar(self, radar_id: str) -> tuple[RadarDefinitionRecord, ...]: ...


class RadarRunRepository(Protocol):
    """Application port for durable long-running Radar execution state."""

    def create(self, record: RadarRunRecord) -> RadarRunRecord: ...

    def get(self, run_id: str) -> RadarRunRecord | None: ...

    def find_by_idempotency_key(self, idempotency_key: str) -> RadarRunRecord | None: ...

    def list_for_radar(self, radar_id: str) -> tuple[RadarRunRecord, ...]: ...

    def update_status(
        self,
        run_id: str,
        status: RadarRunStatus,
        *,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        error_message: str | None = None,
        error_metadata: dict[str, object] | None = None,
        run_metadata: dict[str, object] | None = None,
    ) -> RadarRunRecord: ...


class RadarRunOutputRepository(Protocol):
    """Application port for persisted live Radar output snapshots."""

    def upsert(self, record: RadarRunOutputRecord) -> RadarRunOutputRecord: ...

    def get(self, run_id: str) -> RadarRunOutputRecord | None: ...


class RadarReviewDecisionRepository(Protocol):
    """Application port for current human review decisions on Radar findings."""

    def upsert(self, record: RadarReviewDecisionRecord) -> RadarReviewDecisionRecord: ...

    def get(
        self,
        *,
        run_id: str,
        candidate_id: str,
        subject_type: str,
        subject_id: str,
    ) -> RadarReviewDecisionRecord | None: ...

    def list_for_run(self, run_id: str) -> tuple[RadarReviewDecisionRecord, ...]: ...

    def delete(
        self,
        *,
        run_id: str,
        candidate_id: str,
        subject_type: str,
        subject_id: str,
    ) -> bool: ...


class RadarRunEventRepository(Protocol):
    """Application port for append-only structured Radar run journal events."""

    def append(self, record: RadarRunEventRecord) -> RadarRunEventRecord: ...

    def list_for_run(self, run_id: str) -> tuple[RadarRunEventRecord, ...]: ...

    def next_sequence(self, run_id: str) -> int: ...


class JobQueue(Protocol):
    """Application port for future async execution adapters."""

    def enqueue_radar_run(self, run: RadarRunRecord) -> None: ...


class RadarRunExecutor(Protocol):
    """Application port for executing an already persisted Radar run."""

    def execute(self, run_id: str) -> RadarRunRecord: ...


class LiveRadarArtifactExecutor(Protocol):
    """Application port for producing a live Radar artifact."""

    def execute(self, *, live: bool, task_context: dict[str, object]) -> dict[str, object]: ...


class RadarRunScheduler(Protocol):
    """Application port for scheduling Radar runs without owning execution."""

    def schedule_due_runs(self, *, now: datetime) -> tuple[RadarRunRecord, ...]: ...
