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
