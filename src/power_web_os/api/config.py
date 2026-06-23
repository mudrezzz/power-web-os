"""API configuration owned by the backend boundary, not by UI or demo artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import os

from power_web_os.persistence.config import DEFAULT_DATABASE_URL


@dataclass(frozen=True)
class ApiSettings:
    service_name: str = "Power Web OS API"
    environment: str = "local"
    api_version: str = "0.7.6.1.11.5"
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


def get_api_settings() -> ApiSettings:
    return ApiSettings(
        environment=os.getenv("POWER_WEB_OS_ENV", "local"),
        database_url=os.getenv("POWER_WEB_OS_DATABASE_URL", DEFAULT_DATABASE_URL),
        cors_origins=_cors_origins(os.getenv("POWER_WEB_OS_CORS_ORIGINS")),
        radar_max_web_tasks_per_subject=_positive_int(
            os.getenv("POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT"),
            ApiSettings.radar_max_web_tasks_per_subject,
        ),
        radar_max_discovery_tasks_per_rule=_optional_positive_int(
            os.getenv("POWER_WEB_OS_RADAR_MAX_DISCOVERY_TASKS_PER_RULE"),
        ),
        radar_max_gate_tasks_per_candidate_rule=_optional_positive_int(
            os.getenv("POWER_WEB_OS_RADAR_MAX_GATE_TASKS_PER_CANDIDATE_RULE"),
        ),
        radar_max_signal_tasks_per_candidate_signal=_optional_positive_int(
            os.getenv("POWER_WEB_OS_RADAR_MAX_SIGNAL_TASKS_PER_CANDIDATE_SIGNAL"),
        ),
        radar_max_total_web_tasks_per_run=_optional_positive_int(
            os.getenv("POWER_WEB_OS_RADAR_MAX_TOTAL_WEB_TASKS_PER_RUN"),
        ),
        radar_source_verification_mode=_verification_mode(
            os.getenv("POWER_WEB_OS_RADAR_SOURCE_VERIFICATION_MODE"),
            ApiSettings.radar_source_verification_mode,
        ),
        radar_min_useful_sources_per_discovery_task=_non_negative_int(
            os.getenv("POWER_WEB_OS_RADAR_MIN_USEFUL_SOURCES_PER_DISCOVERY_TASK"),
            ApiSettings.radar_min_useful_sources_per_discovery_task,
        ),
        radar_min_candidates_per_discovery_task=_non_negative_int(
            os.getenv("POWER_WEB_OS_RADAR_MIN_CANDIDATES_PER_DISCOVERY_TASK"),
            ApiSettings.radar_min_candidates_per_discovery_task,
        ),
        radar_max_discovery_retries_per_task=_non_negative_int(
            os.getenv("POWER_WEB_OS_RADAR_MAX_DISCOVERY_RETRIES_PER_TASK"),
            ApiSettings.radar_max_discovery_retries_per_task,
        ),
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


def _verification_mode(raw: str | None, default: str) -> str:
    value = (raw or default).strip().lower()
    return value if value in {"strict", "soft", "off"} else default
