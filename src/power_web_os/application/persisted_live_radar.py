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
        existing = self._find_existing(command)
        if existing is not None:
            return PersistedLiveRadarRunResult(run=existing, output=self._output_repository.get(existing.run_id))

        run_id = command.run_id or f"radar-run-{uuid4()}"
        correlation_id = command.correlation_id or f"corr-{run_id}"
        run = self._run_repository.create(
            RadarRunRecord(
                run_id=run_id,
                radar_id=command.radar_id,
                idempotency_key=command.idempotency_key,
                correlation_id=correlation_id,
                run_metadata={"execution_mode": "persisted_live_radar", "live": command.live},
            )
        )
        run = self._run_repository.update_status(run.run_id, RadarRunStatus.RUNNING)

        try:
            artifact = self._executor.execute(
                live=command.live,
                task_context=_task_context(command=command, run_id=run.run_id, correlation_id=correlation_id),
            )
            output = self._output_repository.upsert(_output_record(run_id=run.run_id, artifact=artifact))
            run = self._run_repository.update_status(
                run.run_id,
                RadarRunStatus.COMPLETED,
                run_metadata=_run_metadata(artifact),
            )
            return PersistedLiveRadarRunResult(run=run, output=output)
        except Exception as exc:
            run = self._run_repository.update_status(
                run.run_id,
                RadarRunStatus.FAILED,
                error_message=str(exc),
                error_metadata={"exception_type": type(exc).__name__},
            )
            return PersistedLiveRadarRunResult(run=run)

    def _find_existing(self, command: PersistedLiveRadarRunCommand) -> RadarRunRecord | None:
        if command.idempotency_key is None:
            return None
        return self._run_repository.find_by_idempotency_key(command.idempotency_key)


def _task_context(
    *,
    command: PersistedLiveRadarRunCommand,
    run_id: str,
    correlation_id: str,
) -> dict[str, Any]:
    return {
        **(command.task_context or {}),
        "task_id": f"persisted-live-mini-icp-radar-{run_id}",
        "correlation_id": correlation_id,
        "requester": command.requester,
        "radar_id": command.radar_id,
        "run_id": run_id,
    }


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
