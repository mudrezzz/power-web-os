"""Celery-backed Radar job entrypoints.

Jobs carry only durable identifiers. The worker opens its own persistence
session, wires application services to infrastructure adapters, and leaves
`radar_runs` as the product source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from typing import Any

from celery import Celery

from power_web_os.application.persisted_live_radar import (
    PersistedLiveRadarRunCommand,
    PersistedLiveRadarRunExecutor,
    QueuedLiveRadarRunService,
)
from power_web_os.application.ports import JobQueue, LiveRadarArtifactExecutor, RadarRunScheduler, SignalMonitoringJobQueue
from power_web_os.application.radar.signal_monitoring.runtime import PersistedSignalMonitoringRunExecutor
from power_web_os.application.radar.signal_monitoring.service_factory import SignalMonitoringRunServiceFactory
from power_web_os.application.radar.configuration.model_profiles import default_model_profile_registry
from power_web_os.application.radar.configuration.runtime_config import build_effective_runtime_config_report
from power_web_os.application.radar.lifecycle.records import RadarRunRecord, RadarRunTechnicalTraceRecord
from power_web_os.application.radar.lifecycle.run_journal import RadarRunJournal
from power_web_os.application.radar.lifecycle.technical_trace import RadarRunTechnicalTracer
from power_web_os.integrations.openrouter_discovery_planner import OpenRouterDiscoveryPlanner
from power_web_os.integrations.live_radar_openrouter import OpenRouterWebSearchProvider
from power_web_os.integrations.openrouter_signal_monitoring import OpenRouterSignalMonitoringProvider
from power_web_os.integrations.signal_source_metadata import HttpSignalSourceMetadataProvider
from power_web_os.integrations.dadata_provider import dadata_source_registry_from_env
from power_web_os.persistence import (
    SqlAlchemyRadarDefinitionRepository,
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunEventRepository,
    SqlAlchemyRadarRunRepository,
    SqlAlchemyRadarRunTechnicalTraceRepository,
    SqlAlchemySignalMonitoringRunOutputRepository,
    create_database_engine,
    create_session_factory,
    session_scope,
)
from power_web_os.workflows.live_radar_executor import WorkflowLiveRadarArtifactExecutor


def _env_bool(name: str) -> bool:
    return os.getenv(name, "").lower() in {"1", "true", "yes"}


def _celery_app() -> Celery:
    app = Celery(
        "power_web_os_radar_jobs",
        broker=os.getenv("POWER_WEB_OS_CELERY_BROKER_URL", "redis://localhost:6379/0"),
        backend=os.getenv("POWER_WEB_OS_CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
    )
    app.conf.task_always_eager = _env_bool("POWER_WEB_OS_CELERY_TASK_ALWAYS_EAGER")
    app.conf.task_eager_propagates = _env_bool("POWER_WEB_OS_CELERY_TASK_EAGER_PROPAGATES")
    app.conf.task_routes = {
        "power_web_os.execute_radar_run": {"queue": "candidate_discovery"},
        "power_web_os.execute_signal_monitoring_run": {"queue": "signal_monitoring"},
    }
    return app


radar_celery_app = _celery_app()


def default_live_executor(
    *,
    technical_trace_repository: SqlAlchemyRadarRunTechnicalTraceRepository | None = None,
) -> LiveRadarArtifactExecutor:
    return WorkflowLiveRadarArtifactExecutor(
        provider=OpenRouterWebSearchProvider(),
        discovery_planner=OpenRouterDiscoveryPlanner(),
        source_registry=dadata_source_registry_from_env(),
        technical_trace_repository=technical_trace_repository,
    )


class CeleryJobQueue(JobQueue):
    def __init__(self, *, task=None) -> None:
        self._task = task or execute_radar_run_task

    def enqueue_radar_run(self, run: RadarRunRecord) -> None:
        self._task.delay(run.run_id)


class SignalMonitoringCeleryJobQueue(SignalMonitoringJobQueue):
    def __init__(self, *, task=None) -> None:
        self._task = task or execute_signal_monitoring_run_task

    def enqueue_signal_monitoring_run(self, run: RadarRunRecord) -> None:
        if run.pipeline_id != "signal_monitoring":
            raise ValueError("Signal monitoring queue accepts only signal-monitoring runs.")
        self._task.delay(run.run_id)


@radar_celery_app.task(name="power_web_os.execute_radar_run")
def execute_radar_run_task(run_id: str) -> dict[str, object]:
    run = execute_radar_run_once(run_id=run_id)
    return {"run_id": run.run_id, "radar_id": run.radar_id, "status": run.status.value}


def execute_radar_run_once(
    *,
    run_id: str,
    live_executor: LiveRadarArtifactExecutor | None = None,
    session_factory: Any | None = None,
) -> RadarRunRecord:
    resolved_session_factory = session_factory or create_session_factory(create_database_engine())
    with session_scope(resolved_session_factory) as session:
        technical_trace_repository = SessionPerOperationRadarRunTechnicalTraceRepository(resolved_session_factory)
        resolved_live_executor = live_executor or default_live_executor(
            technical_trace_repository=technical_trace_repository,
        )
        executor = PersistedLiveRadarRunExecutor(
            run_repository=SqlAlchemyRadarRunRepository(session),
            output_repository=SqlAlchemyRadarRunOutputRepository(session),
            executor=resolved_live_executor,
            definition_repository=SqlAlchemyRadarDefinitionRepository(session),
            journal=RadarRunJournal(repository=SqlAlchemyRadarRunEventRepository(session)),
            commit_after_start=session.commit,
            runtime_config_provider=lambda: build_effective_runtime_config_report(component="worker").to_payload(),
            technical_tracer=RadarRunTechnicalTracer(repository=technical_trace_repository, default_run_id=run_id),
        )
        return executor.execute(run_id)


@radar_celery_app.task(name="power_web_os.execute_signal_monitoring_run")
def execute_signal_monitoring_run_task(run_id: str) -> dict[str, object]:
    run = execute_signal_monitoring_run_once(run_id=run_id)
    return {
        "run_id": run.run_id,
        "radar_id": run.radar_id,
        "pipeline_id": run.pipeline_id,
        "source_run_id": run.source_run_id,
        "status": run.status.value,
    }


def execute_signal_monitoring_run_once(
    *,
    run_id: str,
    signal_executor=None,
    session_factory: Any | None = None,
) -> RadarRunRecord:
    resolved_session_factory = session_factory or create_session_factory(create_database_engine())
    registry = default_model_profile_registry()
    if signal_executor is None:
        profile = registry.require("signal_monitoring_default")
        primary_role = profile.roles["signal_extractor"]
        backup_role = profile.roles["signal_backup_extractor"]
        primary = OpenRouterSignalMonitoringProvider(
            model_id=primary_role.primary_model,
            temperature=primary_role.temperature,
        )
        backup = OpenRouterSignalMonitoringProvider(
            model_id=backup_role.primary_model or primary_role.backup_model,
            temperature=backup_role.temperature,
        )
        signal_executor = SignalMonitoringRunServiceFactory().build_composition(
            primary_provider=primary,
            backup_provider=backup,
            source_metadata_provider=HttpSignalSourceMetadataProvider(),
            model_profile_registry=registry,
        ).executor
    with session_scope(resolved_session_factory) as session:
        executor = PersistedSignalMonitoringRunExecutor(
            run_repository=SqlAlchemyRadarRunRepository(session),
            output_repository=SqlAlchemySignalMonitoringRunOutputRepository(session),
            executor=signal_executor,
            event_repository=SqlAlchemyRadarRunEventRepository(session),
            commit_after_start=session.commit,
        )
        return executor.execute(run_id)


class SessionPerOperationRadarRunTechnicalTraceRepository:
    """Persist trace records without holding a transaction across provider calls."""

    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    def append(self, record: RadarRunTechnicalTraceRecord) -> RadarRunTechnicalTraceRecord:
        with session_scope(self._session_factory) as session:
            return SqlAlchemyRadarRunTechnicalTraceRepository(session).append(record)

    def list_for_run(self, run_id: str) -> tuple[RadarRunTechnicalTraceRecord, ...]:
        with session_scope(self._session_factory) as session:
            return SqlAlchemyRadarRunTechnicalTraceRepository(session).list_for_run(run_id)

    def next_sequence(self, run_id: str) -> int:
        with session_scope(self._session_factory) as session:
            return SqlAlchemyRadarRunTechnicalTraceRepository(session).next_sequence(run_id)


@dataclass(slots=True)
class ConfiguredRadarRunScheduler(RadarRunScheduler):
    """Local scheduler adapter for known radar ids.

    Durable recurrence rules are intentionally out of scope for this slice.
    """

    radar_ids: tuple[str, ...]
    run_service: QueuedLiveRadarRunService
    job_queue: JobQueue

    def schedule_due_runs(self, *, now: datetime) -> tuple[RadarRunRecord, ...]:
        scheduled: list[RadarRunRecord] = []
        cadence_key = now.date().isoformat()
        for radar_id in self.radar_ids:
            result = self.run_service.create(
                PersistedLiveRadarRunCommand(
                    radar_id=radar_id,
                    live=True,
                    idempotency_key=f"scheduled:{radar_id}:{cadence_key}",
                    correlation_id=f"scheduled-{radar_id}-{cadence_key}",
                    requester="scheduler",
                    task_context={"scheduled_at": now.isoformat()},
                )
            )
            if result.should_enqueue:
                self.job_queue.enqueue_radar_run(result.run)
            scheduled.append(result.run)
        return tuple(scheduled)
