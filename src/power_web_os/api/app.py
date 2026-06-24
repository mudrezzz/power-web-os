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
from power_web_os.application.radar_runtime_config import (
    build_effective_runtime_config_report,
    runtime_config_api_overrides,
)
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
    app.state.radar_max_discovery_tasks_per_rule = api_settings.radar_max_discovery_tasks_per_rule
    app.state.radar_max_gate_tasks_per_candidate_rule = api_settings.radar_max_gate_tasks_per_candidate_rule
    app.state.radar_max_signal_tasks_per_candidate_signal = api_settings.radar_max_signal_tasks_per_candidate_signal
    app.state.radar_max_total_web_tasks_per_run = api_settings.radar_max_total_web_tasks_per_run
    app.state.radar_source_verification_mode = api_settings.radar_source_verification_mode
    app.state.radar_min_useful_sources_per_discovery_task = api_settings.radar_min_useful_sources_per_discovery_task
    app.state.radar_min_candidates_per_discovery_task = api_settings.radar_min_candidates_per_discovery_task
    app.state.radar_max_discovery_retries_per_task = api_settings.radar_max_discovery_retries_per_task
    app.state.radar_max_checkpoint_revisions_per_run = api_settings.radar_max_checkpoint_revisions_per_run
    app.state.radar_max_checkpoint_retries_per_stage = api_settings.radar_max_checkpoint_retries_per_stage
    app.state.radar_run_profile = api_settings.radar_run_profile
    app.state.radar_max_openrouter_calls_per_run = api_settings.radar_max_openrouter_calls_per_run
    app.state.radar_max_openrouter_planner_calls_per_run = api_settings.radar_max_openrouter_planner_calls_per_run
    app.state.radar_max_openrouter_web_task_calls_per_run = api_settings.radar_max_openrouter_web_task_calls_per_run
    app.state.radar_max_openrouter_server_tool_web_searches_per_run = (
        api_settings.radar_max_openrouter_server_tool_web_searches_per_run
    )
    app.state.radar_max_dadata_lookups_per_run = api_settings.radar_max_dadata_lookups_per_run
    app.state.radar_max_source_verification_requests_per_run = api_settings.radar_max_source_verification_requests_per_run
    app.state.radar_max_provider_retries_per_task = api_settings.radar_max_provider_retries_per_task
    app.state.radar_openrouter_web_max_results_per_call = api_settings.radar_openrouter_web_max_results_per_call
    app.state.radar_openrouter_web_max_total_results_per_call = api_settings.radar_openrouter_web_max_total_results_per_call
    app.state.radar_smoke_max_candidates = api_settings.radar_smoke_max_candidates
    app.state.radar_smoke_max_signals = api_settings.radar_smoke_max_signals
    app.state.runtime_config_report = build_effective_runtime_config_report(
        component="api",
        overrides=runtime_config_api_overrides(api_settings),
    ).to_payload()

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

    @app.get("/api/runtime-config", tags=["system"])
    def runtime_config() -> dict[str, object]:
        return dict(app.state.runtime_config_report)

    app.include_router(radar_router)
    return app


app = create_app()
