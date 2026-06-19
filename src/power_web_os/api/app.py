"""FastAPI application factory for Power Web OS backend contracts."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from power_web_os.api.config import ApiSettings, get_api_settings
from power_web_os.api.dependencies import default_job_queue
from power_web_os.api.radar_routes import router as radar_router
from power_web_os.application.ports import JobQueue
from power_web_os.persistence import create_database_engine, create_session_factory


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str


def create_app(
    settings: ApiSettings | None = None,
    *,
    job_queue_factory: Callable[[], JobQueue] | None = None,
) -> FastAPI:
    api_settings = settings or get_api_settings()
    app = FastAPI(
        title=api_settings.service_name,
        version=api_settings.api_version,
        description="Persistent backend boundary for Power Web OS.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(api_settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    engine = create_database_engine(database_url=api_settings.database_url)
    app.state.session_factory = create_session_factory(engine)
    app.state.job_queue_factory = job_queue_factory or default_job_queue
    app.state.radar_max_web_tasks_per_subject = api_settings.radar_max_web_tasks_per_subject
    app.state.radar_source_verification_mode = api_settings.radar_source_verification_mode
    app.state.radar_min_useful_sources_per_discovery_task = api_settings.radar_min_useful_sources_per_discovery_task
    app.state.radar_min_candidates_per_discovery_task = api_settings.radar_min_candidates_per_discovery_task
    app.state.radar_max_discovery_retries_per_task = api_settings.radar_max_discovery_retries_per_task

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=api_settings.service_name,
            version=api_settings.api_version,
            environment=api_settings.environment,
        )

    @app.get("/api/health", response_model=HealthResponse, tags=["system"])
    def api_health() -> HealthResponse:
        return health()

    app.include_router(radar_router)
    return app


app = create_app()
