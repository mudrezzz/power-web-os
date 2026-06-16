"""FastAPI application factory.

The API layer is intentionally thin in Slice 0.7.0: it exposes a stable HTTP
entrypoint while product state still lives in demo artifacts and domain services.
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from power_web_os.api.config import ApiSettings, get_api_settings


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    api_settings = settings or get_api_settings()
    app = FastAPI(
        title=api_settings.service_name,
        version=api_settings.api_version,
        description="Persistent backend boundary for Power Web OS.",
    )

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

    return app


app = create_app()
