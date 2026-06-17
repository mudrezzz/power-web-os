"""API dependency wiring for Radar repositories and execution adapters."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from fastapi import Request

from power_web_os.application.ports import LiveRadarArtifactExecutor
from power_web_os.integrations.live_radar_openrouter import OpenRouterWebSearchProvider
from power_web_os.persistence import (
    SqlAlchemyRadarDefinitionRepository,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunRepository,
    session_scope,
)
from power_web_os.workflows.live_radar_executor import WorkflowLiveRadarArtifactExecutor


@dataclass(frozen=True, slots=True)
class RadarApiContext:
    radar_repository: SqlAlchemyRadarRepository
    definition_repository: SqlAlchemyRadarDefinitionRepository
    run_repository: SqlAlchemyRadarRunRepository
    output_repository: SqlAlchemyRadarRunOutputRepository
    live_executor: LiveRadarArtifactExecutor


def default_live_executor() -> LiveRadarArtifactExecutor:
    return WorkflowLiveRadarArtifactExecutor(provider=OpenRouterWebSearchProvider())


def get_radar_api_context(request: Request) -> Iterator[RadarApiContext]:
    session_factory = request.app.state.session_factory
    live_executor_factory = request.app.state.live_executor_factory
    with session_scope(session_factory) as session:
        yield RadarApiContext(
            radar_repository=SqlAlchemyRadarRepository(session),
            definition_repository=SqlAlchemyRadarDefinitionRepository(session),
            run_repository=SqlAlchemyRadarRunRepository(session),
            output_repository=SqlAlchemyRadarRunOutputRepository(session),
            live_executor=live_executor_factory(),
        )
