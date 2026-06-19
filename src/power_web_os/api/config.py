"""API configuration owned by the backend boundary, not by UI or demo artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import os

from power_web_os.persistence.config import DEFAULT_DATABASE_URL


@dataclass(frozen=True)
class ApiSettings:
    service_name: str = "Power Web OS API"
    environment: str = "local"
    api_version: str = "0.7.6.1.5"
    database_url: str = DEFAULT_DATABASE_URL
    cors_origins: tuple[str, ...] = (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    )
    radar_max_web_tasks_per_subject: int = 20


def get_api_settings() -> ApiSettings:
    return ApiSettings(
        environment=os.getenv("POWER_WEB_OS_ENV", "local"),
        database_url=os.getenv("POWER_WEB_OS_DATABASE_URL", DEFAULT_DATABASE_URL),
        cors_origins=_cors_origins(os.getenv("POWER_WEB_OS_CORS_ORIGINS")),
        radar_max_web_tasks_per_subject=_positive_int(
            os.getenv("POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT"),
            ApiSettings.radar_max_web_tasks_per_subject,
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
