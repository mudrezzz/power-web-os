"""API configuration owned by the backend boundary, not by UI or demo artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ApiSettings:
    service_name: str = "Power Web OS API"
    environment: str = "local"
    api_version: str = "0.7.0"


def get_api_settings() -> ApiSettings:
    return ApiSettings(
        environment=os.getenv("POWER_WEB_OS_ENV", "local"),
    )
