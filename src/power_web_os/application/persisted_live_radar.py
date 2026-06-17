"""Application service for persisted live Radar execution.

The service owns the durable run lifecycle and depends only on repository and
executor ports. It does not know about SQLAlchemy, OpenRouter, or workflow
runtime details.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from power_web_os.application.ports import LiveRadarArtifactExecutor, RadarRunOutputRepository, RadarRunRepository
from power_web_os.application.radar_records import RadarRunOutputRecord, RadarRunRecord, RadarRunStatus


@dataclass(frozen=True, slots=True)
class PersistedLiveRadarRunCommand:
    radar_id: str = "toir-quick-live"
    live: bool = True
    run_id: str | None = None
    idempotency_key: str | None = None
    correlation_id: str | None = None
    requester: str = "demo"
    task_context: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class PersistedLiveRadarRunResult:
    run: RadarRunRecord
    output: RadarRunOutputRecord | None = None

    @property
    def artifact(self) -> dict[str, Any] | None:
        return self.output.artifact_payload if self.output is not None else None


@dataclass(frozen=True, slots=True)
class QueuedLiveRadarRunResult:
    run: RadarRunRecord
    should_enqueue: bool


class QueuedLiveRadarRunService:
    """Create durable queued Radar runs without executing provider work."""

    def __init__(self, *, run_repository: RadarRunRepository) -> None:
        self._run_repository = run_repository

    def create(self, command: PersistedLiveRadarRunCommand) -> QueuedLiveRadarRunResult:
        existing = _find_existing(self._run_repository, command)
        if existing is not None:
            return QueuedLiveRadarRunResult(run=existing, should_enqueue=False)

        run_id = command.run_id or f"radar-run-{uuid4()}"
        correlation_id = command.correlation_id or f"corr-{run_id}"
        run = self._run_repository.create(
            RadarRunRecord(
                run_id=run_id,
                radar_id=command.radar_id,
                idempotency_key=command.idempotency_key,
                correlation_id=correlation_id,
                run_metadata=_queued_run_metadata(command),
            )
        )
        return QueuedLiveRadarRunResult(run=run, should_enqueue=True)


class PersistedLiveRadarRunExecutor:
    """Execute an already persisted Radar run by id."""

    def __init__(
        self,
        *,
        run_repository: RadarRunRepository,
        output_repository: RadarRunOutputRepository,
        executor: LiveRadarArtifactExecutor,
    ) -> None:
        self._run_repository = run_repository
        self._output_repository = output_repository
        self._executor = executor

    def execute(self, run_id: str) -> RadarRunRecord:
        run = self._run_repository.get(run_id)
        if run is None:
            raise KeyError(f"Radar run not found: {run_id}")
        if run.status.is_terminal:
            return run

        run = self._run_repository.update_status(run.run_id, RadarRunStatus.RUNNING)
        try:
            artifact = self._executor.execute(
                live=bool(run.run_metadata.get("live", True)),
                task_context=_task_context_from_run(run),
            )
            self._output_repository.upsert(_output_record(run_id=run.run_id, artifact=artifact))
            return self._run_repository.update_status(
                run.run_id,
                RadarRunStatus.COMPLETED,
                run_metadata={**run.run_metadata, **_run_metadata(artifact)},
            )
        except Exception as exc:
            return self._run_repository.update_status(
                run.run_id,
                RadarRunStatus.FAILED,
                error_message=str(exc),
                error_metadata={"exception_type": type(exc).__name__},
            )


class PersistedLiveRadarRunService:
    def __init__(
        self,
        *,
        run_repository: RadarRunRepository,
        output_repository: RadarRunOutputRepository,
        executor: LiveRadarArtifactExecutor,
    ) -> None:
        self._run_repository = run_repository
        self._output_repository = output_repository
        self._executor = executor

    def run(self, command: PersistedLiveRadarRunCommand) -> PersistedLiveRadarRunResult:
        queued = QueuedLiveRadarRunService(run_repository=self._run_repository).create(command)
        if queued.should_enqueue:
            executor = PersistedLiveRadarRunExecutor(
                run_repository=self._run_repository,
                output_repository=self._output_repository,
                executor=self._executor,
            )
            run = executor.execute(queued.run.run_id)
        else:
            run = queued.run
        return PersistedLiveRadarRunResult(run=run, output=self._output_repository.get(run.run_id))


def _queued_run_metadata(command: PersistedLiveRadarRunCommand) -> dict[str, Any]:
    return {
        "execution_mode": "queued_live_radar",
        "live": command.live,
        "requester": command.requester,
        "task_context": dict(command.task_context or {}),
    }


def _task_context_from_run(run: RadarRunRecord) -> dict[str, Any]:
    task_context = run.run_metadata.get("task_context", {})
    if not isinstance(task_context, dict):
        task_context = {}
    return {
        **task_context,
        "task_id": f"persisted-live-mini-icp-radar-{run.run_id}",
        "correlation_id": run.correlation_id,
        "requester": run.run_metadata.get("requester", "worker"),
        "radar_id": run.radar_id,
        "run_id": run.run_id,
    }


def _find_existing(repository: RadarRunRepository, command: PersistedLiveRadarRunCommand) -> RadarRunRecord | None:
    if command.idempotency_key is None:
        return None
    return repository.find_by_idempotency_key(command.idempotency_key)


def _output_record(*, run_id: str, artifact: dict[str, object]) -> RadarRunOutputRecord:
    if artifact.get("artifact_type") != "icp_radar_live_run":
        raise ValueError("Persisted live Radar executor returned an unsupported artifact type")
    return RadarRunOutputRecord(
        run_id=run_id,
        artifact_version=str(artifact.get("artifact_version", "")),
        radar_payload=_dict_payload(artifact.get("radar")),
        search_plan_payload=_dict_payload(artifact.get("search_plan")),
        sources_payload=_list_payload(artifact.get("sources")),
        candidates_payload=_list_payload(artifact.get("candidates")),
        contract_validation_payload=_list_payload(artifact.get("contract_validation")),
        artifact_payload=dict(artifact),
    )


def _run_metadata(artifact: dict[str, object]) -> dict[str, object]:
    return {
        "execution_mode": "persisted_live_radar",
        "artifact_type": artifact.get("artifact_type"),
        "artifact_version": artifact.get("artifact_version"),
        "run_metadata": _dict_payload(artifact.get("run_metadata")),
        "source_count": len(_list_payload(artifact.get("sources"))),
        "candidate_count": len(_list_payload(artifact.get("candidates"))),
        "persisted_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
    }


def _dict_payload(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Expected live Radar artifact section to be an object")
    return dict(value)


def _list_payload(value: object) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("Expected live Radar artifact section to be a list of objects")
    return [dict(item) for item in value]
