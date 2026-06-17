"""API configuration owned by the backend boundary, not by UI or demo artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import os

from power_web_os.persistence.config import DEFAULT_DATABASE_URL


@dataclass(frozen=True)
class ApiSettings:
    service_name: str = "Power Web OS API"
    environment: str = "local"
    api_version: str = "0.7.3"
    database_url: str = DEFAULT_DATABASE_URL


def get_api_settings() -> ApiSettings:
    return ApiSettings(
        environment=os.getenv("POWER_WEB_OS_ENV", "local"),
        database_url=os.getenv("POWER_WEB_OS_DATABASE_URL", DEFAULT_DATABASE_URL),
    )
