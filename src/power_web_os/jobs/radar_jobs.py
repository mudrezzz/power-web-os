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
from power_web_os.application.ports import JobQueue, LiveRadarArtifactExecutor, RadarRunScheduler
from power_web_os.application.radar_run_journal import RadarRunJournal
from power_web_os.application.radar_records import RadarRunRecord
from power_web_os.integrations.openrouter_discovery_planner import OpenRouterDiscoveryPlanner
from power_web_os.integrations.live_radar_openrouter import OpenRouterWebSearchProvider
from power_web_os.persistence import (
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunEventRepository,
    SqlAlchemyRadarRunRepository,
    SqlAlchemyRadarRunTechnicalTraceRepository,
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
    return app


radar_celery_app = _celery_app()


def default_live_executor(
    *,
    technical_trace_repository: SqlAlchemyRadarRunTechnicalTraceRepository | None = None,
) -> LiveRadarArtifactExecutor:
    return WorkflowLiveRadarArtifactExecutor(
        provider=OpenRouterWebSearchProvider(),
        discovery_planner=OpenRouterDiscoveryPlanner(),
        technical_trace_repository=technical_trace_repository,
    )


class CeleryJobQueue(JobQueue):
    def __init__(self, *, task=None) -> None:
        self._task = task or execute_radar_run_task

    def enqueue_radar_run(self, run: RadarRunRecord) -> None:
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
        technical_trace_repository = SqlAlchemyRadarRunTechnicalTraceRepository(session)
        resolved_live_executor = live_executor or default_live_executor(
            technical_trace_repository=technical_trace_repository,
        )
        executor = PersistedLiveRadarRunExecutor(
            run_repository=SqlAlchemyRadarRunRepository(session),
            output_repository=SqlAlchemyRadarRunOutputRepository(session),
            executor=resolved_live_executor,
            journal=RadarRunJournal(repository=SqlAlchemyRadarRunEventRepository(session)),
        )
        return executor.execute(run_id)


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
