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
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunRepository,
    session_scope,
)


@dataclass(frozen=True, slots=True)
class RadarApiContext:
    radar_repository: SqlAlchemyRadarRepository
    definition_repository: SqlAlchemyRadarDefinitionRepository
    run_repository: SqlAlchemyRadarRunRepository
    output_repository: SqlAlchemyRadarRunOutputRepository
    review_repository: SqlAlchemyRadarReviewDecisionRepository
    job_queue: JobQueue


def default_job_queue() -> JobQueue:
    return CeleryJobQueue()


def get_radar_api_context(request: Request) -> Iterator[RadarApiContext]:
    session_factory = request.app.state.session_factory
    job_queue_factory = request.app.state.job_queue_factory
    with session_scope(session_factory) as session:
        yield RadarApiContext(
            radar_repository=SqlAlchemyRadarRepository(session),
            definition_repository=SqlAlchemyRadarDefinitionRepository(session),
            run_repository=SqlAlchemyRadarRunRepository(session),
            output_repository=SqlAlchemyRadarRunOutputRepository(session),
            review_repository=SqlAlchemyRadarReviewDecisionRepository(session),
            job_queue=job_queue_factory(),
        )
