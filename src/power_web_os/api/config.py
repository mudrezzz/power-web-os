"""API configuration owned by the backend boundary, not by UI or demo artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import os

from power_web_os.application.radar_runtime_settings import effective_runtime_env
from power_web_os.persistence.config import DEFAULT_DATABASE_URL


@dataclass(frozen=True)
class ApiSettings:
    service_name: str = "Power Web OS API"
    environment: str = "local"
    api_version: str = "0.7.6.1.11.9"
    database_url: str = DEFAULT_DATABASE_URL
    cors_origins: tuple[str, ...] = (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    )
    radar_max_web_tasks_per_subject: int = 20
    radar_max_discovery_tasks_per_rule: int | None = None
    radar_max_gate_tasks_per_candidate_rule: int | None = None
    radar_max_signal_tasks_per_candidate_signal: int | None = None
    radar_max_total_web_tasks_per_run: int | None = None
    radar_source_verification_mode: str = "soft"
    radar_min_useful_sources_per_discovery_task: int = 3
    radar_min_candidates_per_discovery_task: int = 5
    radar_max_discovery_retries_per_task: int = 2
    radar_max_checkpoint_revisions_per_run: int = 2
    radar_max_checkpoint_retries_per_stage: int = 1
    radar_run_profile: str = "live"
    radar_max_openrouter_calls_per_run: int | None = None
    radar_max_openrouter_planner_calls_per_run: int | None = None
    radar_max_openrouter_web_task_calls_per_run: int | None = None
    radar_max_openrouter_server_tool_web_searches_per_run: int | None = None
    radar_max_dadata_lookups_per_run: int | None = None
    radar_max_source_verification_requests_per_run: int | None = None
    radar_max_provider_retries_per_task: int | None = None
    radar_openrouter_web_max_results_per_call: int | None = None
    radar_openrouter_web_max_total_results_per_call: int | None = None
    radar_smoke_max_candidates: int | None = None
    radar_smoke_max_signals: int | None = None


def get_api_settings() -> ApiSettings:
    runtime_env = effective_runtime_env()
    return ApiSettings(
        environment=os.getenv("POWER_WEB_OS_ENV", "local"),
        database_url=os.getenv("POWER_WEB_OS_DATABASE_URL", DEFAULT_DATABASE_URL),
        cors_origins=_cors_origins(os.getenv("POWER_WEB_OS_CORS_ORIGINS")),
        radar_max_web_tasks_per_subject=_positive_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT"),
            ApiSettings.radar_max_web_tasks_per_subject,
        ),
        radar_max_discovery_tasks_per_rule=_optional_positive_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_DISCOVERY_TASKS_PER_RULE"),
        ),
        radar_max_gate_tasks_per_candidate_rule=_optional_positive_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_GATE_TASKS_PER_CANDIDATE_RULE"),
        ),
        radar_max_signal_tasks_per_candidate_signal=_optional_positive_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_SIGNAL_TASKS_PER_CANDIDATE_SIGNAL"),
        ),
        radar_max_total_web_tasks_per_run=_optional_positive_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_TOTAL_WEB_TASKS_PER_RUN"),
        ),
        radar_source_verification_mode=_verification_mode(
            runtime_env.get("POWER_WEB_OS_RADAR_SOURCE_VERIFICATION_MODE"),
            ApiSettings.radar_source_verification_mode,
        ),
        radar_min_useful_sources_per_discovery_task=_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MIN_USEFUL_SOURCES_PER_DISCOVERY_TASK"),
            ApiSettings.radar_min_useful_sources_per_discovery_task,
        ),
        radar_min_candidates_per_discovery_task=_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MIN_CANDIDATES_PER_DISCOVERY_TASK"),
            ApiSettings.radar_min_candidates_per_discovery_task,
        ),
        radar_max_discovery_retries_per_task=_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_DISCOVERY_RETRIES_PER_TASK"),
            ApiSettings.radar_max_discovery_retries_per_task,
        ),
        radar_max_checkpoint_revisions_per_run=_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_CHECKPOINT_REVISIONS_PER_RUN"),
            ApiSettings.radar_max_checkpoint_revisions_per_run,
        ),
        radar_max_checkpoint_retries_per_stage=_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_CHECKPOINT_RETRIES_PER_STAGE"),
            ApiSettings.radar_max_checkpoint_retries_per_stage,
        ),
        radar_run_profile=_run_profile(runtime_env.get("POWER_WEB_OS_RADAR_RUN_PROFILE"), ApiSettings.radar_run_profile),
        radar_max_openrouter_calls_per_run=_optional_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_OPENROUTER_CALLS_PER_RUN"),
        ),
        radar_max_openrouter_planner_calls_per_run=_optional_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_OPENROUTER_PLANNER_CALLS_PER_RUN"),
        ),
        radar_max_openrouter_web_task_calls_per_run=_optional_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_OPENROUTER_WEB_TASK_CALLS_PER_RUN"),
        ),
        radar_max_openrouter_server_tool_web_searches_per_run=_optional_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_OPENROUTER_SERVER_TOOL_WEB_SEARCHES_PER_RUN"),
        ),
        radar_max_dadata_lookups_per_run=_optional_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_DADATA_LOOKUPS_PER_RUN"),
        ),
        radar_max_source_verification_requests_per_run=_optional_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_SOURCE_VERIFICATION_REQUESTS_PER_RUN"),
        ),
        radar_max_provider_retries_per_task=_optional_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_MAX_PROVIDER_RETRIES_PER_TASK"),
        ),
        radar_openrouter_web_max_results_per_call=_optional_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_OPENROUTER_WEB_MAX_RESULTS_PER_CALL"),
        ),
        radar_openrouter_web_max_total_results_per_call=_optional_non_negative_int(
            runtime_env.get("POWER_WEB_OS_RADAR_OPENROUTER_WEB_MAX_TOTAL_RESULTS_PER_CALL"),
        ),
        radar_smoke_max_candidates=_optional_non_negative_int(runtime_env.get("POWER_WEB_OS_RADAR_SMOKE_MAX_CANDIDATES")),
        radar_smoke_max_signals=_optional_non_negative_int(runtime_env.get("POWER_WEB_OS_RADAR_SMOKE_MAX_SIGNALS")),
    )


def _cors_origins(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ApiSettings.cors_origins
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def _positive_int(raw: str | None, default: int) -> int:
    try:
        value = int(raw or "")
    except ValueError:
        return default
    return value if value > 0 else default


def _non_negative_int(raw: str | None, default: int) -> int:
    try:
        value = int(raw or "")
    except ValueError:
        return default
    return value if value >= 0 else default


def _optional_positive_int(raw: str | None) -> int | None:
    try:
        value = int(raw or "")
    except ValueError:
        return None
    return value if value > 0 else None


def _optional_non_negative_int(raw: str | None) -> int | None:
    try:
        value = int(raw or "")
    except ValueError:
        return None
    return value if value >= 0 else None


def _verification_mode(raw: str | None, default: str) -> str:
    value = (raw or default).strip().lower()
    return value if value in {"strict", "soft", "off"} else default


def _run_profile(raw: str | None, default: str) -> str:
    value = (raw or default).strip().lower()
    return value if value in {"live", "smoke"} else default
