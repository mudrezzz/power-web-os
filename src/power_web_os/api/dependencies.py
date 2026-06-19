"""API dependency wiring for Radar repositories and queue adapters."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from fastapi import Request

from power_web_os.application.ports import JobQueue
from power_web_os.jobs import CeleryJobQueue
from power_web_os.persistence import (
    SqlAlchemyRadarDefinitionRepository,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarReviewDecisionRepository,
    SqlAlchemyRadarRunEventRepository,
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunRepository,
    SqlAlchemyRadarRunTechnicalTraceRepository,
    session_scope,
)


@dataclass(frozen=True, slots=True)
class RadarApiContext:
    radar_repository: SqlAlchemyRadarRepository
    definition_repository: SqlAlchemyRadarDefinitionRepository
    run_repository: SqlAlchemyRadarRunRepository
    output_repository: SqlAlchemyRadarRunOutputRepository
    review_repository: SqlAlchemyRadarReviewDecisionRepository
    event_repository: SqlAlchemyRadarRunEventRepository
    technical_trace_repository: SqlAlchemyRadarRunTechnicalTraceRepository
    job_queue: JobQueue
    radar_max_web_tasks_per_subject: int
    radar_source_verification_mode: str
    radar_min_useful_sources_per_discovery_task: int
    radar_min_candidates_per_discovery_task: int
    radar_max_discovery_retries_per_task: int


def default_job_queue() -> JobQueue:
    return CeleryJobQueue()


def get_radar_api_context(request: Request) -> Iterator[RadarApiContext]:
    session_factory = request.app.state.session_factory
    job_queue_factory = request.app.state.job_queue_factory
    radar_max_web_tasks_per_subject = int(getattr(request.app.state, "radar_max_web_tasks_per_subject", 20))
    radar_source_verification_mode = str(getattr(request.app.state, "radar_source_verification_mode", "soft"))
    radar_min_useful_sources_per_discovery_task = int(
        getattr(request.app.state, "radar_min_useful_sources_per_discovery_task", 3)
    )
    radar_min_candidates_per_discovery_task = int(getattr(request.app.state, "radar_min_candidates_per_discovery_task", 5))
    radar_max_discovery_retries_per_task = int(getattr(request.app.state, "radar_max_discovery_retries_per_task", 2))
    with session_scope(session_factory) as session:
        yield RadarApiContext(
            radar_repository=SqlAlchemyRadarRepository(session),
            definition_repository=SqlAlchemyRadarDefinitionRepository(session),
            run_repository=SqlAlchemyRadarRunRepository(session),
            output_repository=SqlAlchemyRadarRunOutputRepository(session),
            review_repository=SqlAlchemyRadarReviewDecisionRepository(session),
            event_repository=SqlAlchemyRadarRunEventRepository(session),
            technical_trace_repository=SqlAlchemyRadarRunTechnicalTraceRepository(session),
            job_queue=job_queue_factory(),
            radar_max_web_tasks_per_subject=radar_max_web_tasks_per_subject,
            radar_source_verification_mode=radar_source_verification_mode,
            radar_min_useful_sources_per_discovery_task=radar_min_useful_sources_per_discovery_task,
            radar_min_candidates_per_discovery_task=radar_min_candidates_per_discovery_task,
            radar_max_discovery_retries_per_task=radar_max_discovery_retries_per_task,
        )
