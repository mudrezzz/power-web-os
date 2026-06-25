"""Application service for persisted live Radar execution.

The service owns the durable run lifecycle and depends only on repository and
executor ports. It does not know about SQLAlchemy, OpenRouter, or workflow
runtime details.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable
from uuid import uuid4

from power_web_os.application.live_radar_definition_runtime import active_definition_to_live_radar_payload
from power_web_os.application.ports import (
    LiveRadarArtifactExecutor,
    RadarDefinitionRepository,
    RadarRunOutputRepository,
    RadarRunRepository,
)
from power_web_os.application.radar_run_journal import RadarRunEventCommand, RadarRunJournal
from power_web_os.application.radar_runtime_config import (
    build_effective_runtime_config_report,
    compare_runtime_config_reports,
)
from power_web_os.application.radar_technical_trace import RadarRunTechnicalTraceCommand, RadarRunTechnicalTracer
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
    api_runtime_config: dict[str, Any] | None = None


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

    def __init__(self, *, run_repository: RadarRunRepository, journal: RadarRunJournal | None = None) -> None:
        self._run_repository = run_repository
        self._journal = journal

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
        if self._journal is not None:
            self._journal.append(
                RadarRunEventCommand(
                    run_id=run.run_id,
                    event_type="run_queued",
                    phase="lifecycle",
                    actor="application",
                    node_name="queued_live_radar_run_service",
                    summary=f"Radar run queued for {run.radar_id}.",
                    payload={
                        "radar_id": run.radar_id,
                        "live": bool(run.run_metadata.get("live", True)),
                        "requester": str(run.run_metadata.get("requester", "")),
                    },
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
        definition_repository: RadarDefinitionRepository | None = None,
        journal: RadarRunJournal | None = None,
        commit_after_start: Callable[[], None] | None = None,
        runtime_config_provider: Callable[[], dict[str, Any]] | None = None,
        technical_tracer: RadarRunTechnicalTracer | None = None,
    ) -> None:
        self._run_repository = run_repository
        self._output_repository = output_repository
        self._executor = executor
        self._definition_repository = definition_repository
        self._journal = journal
        self._commit_after_start = commit_after_start
        self._runtime_config_provider = runtime_config_provider
        self._technical_tracer = technical_tracer

    def execute(self, run_id: str) -> RadarRunRecord:
        run = self._run_repository.get(run_id)
        if run is None:
            raise KeyError(f"Radar run not found: {run_id}")
        if run.status.is_terminal:
            return run

        radar_payload = self._active_radar_payload(run)
        if radar_payload is None:
            return self._fail_run(
                run,
                message=f"No active Radar definition found for {run.radar_id}.",
                exception_type="ActiveRadarDefinitionNotFound",
            )

        worker_runtime_config = self._worker_runtime_config()
        api_runtime_config = run.run_metadata.get("api_runtime_config")
        runtime_warnings = compare_runtime_config_reports(
            expected=dict(api_runtime_config) if isinstance(api_runtime_config, dict) else None,
            actual=worker_runtime_config,
        )
        run = self._run_repository.update_status(
            run.run_id,
            RadarRunStatus.RUNNING,
            run_metadata={
                **run.run_metadata,
                "worker_runtime_config": worker_runtime_config,
                "runtime_config_warnings": runtime_warnings,
            },
        )
        if self._commit_after_start is not None:
            # Commit the running status before writing a trace through the
            # session-per-operation repository; SQLite locks otherwise.
            self._commit_after_start()
        self._append_runtime_config_trace(run, worker_runtime_config=worker_runtime_config, warnings=runtime_warnings)
        self._append_event(
            run_id=run.run_id,
            event_type="run_started",
            phase="lifecycle",
            actor="worker",
            node_name="persisted_live_radar_executor",
            summary=f"Radar run started for {run.radar_id}.",
            payload={"radar_id": run.radar_id, "correlation_id": run.correlation_id},
        )
        if self._commit_after_start is not None:
            # Long provider calls must not hold the transaction that marks the
            # run as running; otherwise API polling can stay stuck on queued.
            self._commit_after_start()
        try:
            artifact = self._executor.execute(
                live=bool(run.run_metadata.get("live", True)),
                task_context=_task_context_from_run(run),
                radar_payload=radar_payload,
            )
            self._output_repository.upsert(_output_record(run_id=run.run_id, artifact=artifact))
            if self._journal is not None:
                self._journal.append_artifact_events(run_id=run.run_id, artifact=artifact)
            completed = self._run_repository.update_status(
                run.run_id,
                RadarRunStatus.COMPLETED,
                run_metadata={**run.run_metadata, **_run_metadata(artifact)},
            )
            self._append_event(
                run_id=run.run_id,
                event_type="run_completed",
                phase="lifecycle",
                actor="worker",
                node_name="persisted_live_radar_executor",
                summary=f"Radar run completed with {len(_list_payload(artifact.get('candidates')))} candidates.",
                payload={
                    "source_count": len(_list_payload(artifact.get("sources"))),
                    "candidate_count": len(_list_payload(artifact.get("candidates"))),
                },
            )
            return completed
        except Exception as exc:
            return self._fail_run(run, message=str(exc), exception_type=type(exc).__name__)

    def _active_radar_payload(self, run: RadarRunRecord) -> dict[str, Any] | None:
        if self._definition_repository is None:
            return None
        definition = self._definition_repository.get_active(run.radar_id)
        if definition is None:
            return None
        return active_definition_to_live_radar_payload(definition)

    def _fail_run(self, run: RadarRunRecord, *, message: str, exception_type: str) -> RadarRunRecord:
        failed = self._run_repository.update_status(
            run.run_id,
            RadarRunStatus.FAILED,
            error_message=message,
            error_metadata={"exception_type": exception_type},
        )
        self._append_event(
            run_id=run.run_id,
            event_type="run_failed",
            phase="lifecycle",
            actor="worker",
            node_name="persisted_live_radar_executor",
            visibility="operator",
            summary=message,
            payload={"exception_type": exception_type},
        )
        return failed

    def _append_event(self, **kwargs: Any) -> None:
        if self._journal is not None:
            self._journal.append(RadarRunEventCommand(**kwargs))

    def _worker_runtime_config(self) -> dict[str, Any]:
        if self._runtime_config_provider is not None:
            return dict(self._runtime_config_provider())
        return build_effective_runtime_config_report(component="worker").to_payload()

    def _append_runtime_config_trace(
        self,
        run: RadarRunRecord,
        *,
        worker_runtime_config: dict[str, Any],
        warnings: list[dict[str, Any]],
    ) -> None:
        if self._technical_tracer is None:
            return
        self._technical_tracer.append(
            RadarRunTechnicalTraceCommand(
                run_id=run.run_id,
                phase="lifecycle",
                node_name="persisted_live_radar_executor",
                trace_type="validation_result",
                title="Effective runtime config",
                summary=(
                    "Worker runtime config matches API runtime config."
                    if not warnings
                    else f"Worker runtime config differs from API config in {len(warnings)} fields."
                ),
                payload={
                    "api_runtime_config": _dict_payload_soft(run.run_metadata.get("api_runtime_config")),
                    "worker_runtime_config": worker_runtime_config,
                    "runtime_config_warnings": warnings,
                },
            )
        )


class PersistedLiveRadarRunService:
    def __init__(
        self,
        *,
        run_repository: RadarRunRepository,
        output_repository: RadarRunOutputRepository,
        executor: LiveRadarArtifactExecutor,
        definition_repository: RadarDefinitionRepository | None = None,
        journal: RadarRunJournal | None = None,
        runtime_config_provider: Callable[[], dict[str, Any]] | None = None,
        technical_tracer: RadarRunTechnicalTracer | None = None,
    ) -> None:
        self._run_repository = run_repository
        self._output_repository = output_repository
        self._executor = executor
        self._definition_repository = definition_repository
        self._journal = journal
        self._runtime_config_provider = runtime_config_provider
        self._technical_tracer = technical_tracer

    def run(self, command: PersistedLiveRadarRunCommand) -> PersistedLiveRadarRunResult:
        queued = QueuedLiveRadarRunService(run_repository=self._run_repository, journal=self._journal).create(command)
        if queued.should_enqueue:
            executor = PersistedLiveRadarRunExecutor(
                run_repository=self._run_repository,
                output_repository=self._output_repository,
                executor=self._executor,
                definition_repository=self._definition_repository,
                journal=self._journal,
                runtime_config_provider=self._runtime_config_provider,
                technical_tracer=self._technical_tracer,
            )
            run = executor.execute(queued.run.run_id)
        else:
            run = queued.run
        return PersistedLiveRadarRunResult(run=run, output=self._output_repository.get(run.run_id))


def _queued_run_metadata(command: PersistedLiveRadarRunCommand) -> dict[str, Any]:
    metadata = {
        "execution_mode": "queued_live_radar",
        "live": command.live,
        "requester": command.requester,
        "task_context": dict(command.task_context or {}),
    }
    if command.api_runtime_config is not None:
        metadata["api_runtime_config"] = dict(command.api_runtime_config)
    return metadata


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


def _dict_payload_soft(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_payload(value: object) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("Expected live Radar artifact section to be a list of objects")
    return [dict(item) for item in value]
