from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_DATABASE_URL = "sqlite:///./demo/output/power_web_os.sqlite3"


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    database_url: str = DEFAULT_DATABASE_URL
    echo_sql: bool = False

    @classmethod
    def from_env(cls, *, database_url: str | None = None) -> "DatabaseSettings":
        url = database_url or os.getenv("POWER_WEB_OS_DATABASE_URL") or DEFAULT_DATABASE_URL
        echo = os.getenv("POWER_WEB_OS_SQL_ECHO", "").lower() in {"1", "true", "yes"}
        return cls(database_url=url, echo_sql=echo)
