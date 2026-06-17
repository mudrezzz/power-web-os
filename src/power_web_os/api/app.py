"""FastAPI application factory for Power Web OS backend contracts."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI
from pydantic import BaseModel

from power_web_os.api.config import ApiSettings, get_api_settings
from power_web_os.api.dependencies import default_live_executor
from power_web_os.api.radar_routes import router as radar_router
from power_web_os.application.ports import LiveRadarArtifactExecutor
from power_web_os.persistence import create_database_engine, create_session_factory


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str


def create_app(
    settings: ApiSettings | None = None,
    *,
    live_executor_factory: Callable[[], LiveRadarArtifactExecutor] | None = None,
) -> FastAPI:
    api_settings = settings or get_api_settings()
    app = FastAPI(
        title=api_settings.service_name,
        version=api_settings.api_version,
        description="Persistent backend boundary for Power Web OS.",
    )
    engine = create_database_engine(database_url=api_settings.database_url)
    app.state.session_factory = create_session_factory(engine)
    app.state.live_executor_factory = live_executor_factory or default_live_executor

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
