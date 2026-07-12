"""Database engine and session lifecycle helpers for persistence adapters.

Entry points own transaction boundaries by opening `session_scope()` and passing
the resulting session into repository adapters.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import os
from time import sleep

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from power_web_os.persistence.config import DatabaseSettings


def create_database_engine(settings: DatabaseSettings | None = None, *, database_url: str | None = None) -> Engine:
    resolved = settings or DatabaseSettings.from_env(database_url=database_url)
    # SQLite is used for local smoke tests; PostgreSQL URLs skip this dialect option.
    is_sqlite = resolved.database_url.startswith("sqlite")
    connect_args = {"check_same_thread": False, "timeout": 120} if is_sqlite else {}
    engine = create_engine(resolved.database_url, echo=resolved.echo_sql, future=True, connect_args=connect_args)
    if is_sqlite:
        _configure_sqlite_engine(engine, journal_mode=os.getenv("POWER_WEB_OS_SQLITE_JOURNAL_MODE", "WAL"))
    return engine


def _configure_sqlite_engine(engine: Engine, *, journal_mode: str) -> None:
    """Keep the local Docker SQLite store usable under API and worker concurrency."""

    resolved_journal_mode = journal_mode.strip().upper()
    if resolved_journal_mode not in {"WAL", "DELETE"}:
        raise ValueError("POWER_WEB_OS_SQLITE_JOURNAL_MODE must be WAL or DELETE.")

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA busy_timeout=120000")
            for attempt in range(3):
                try:
                    cursor.execute(f"PRAGMA journal_mode={resolved_journal_mode}")
                    break
                except Exception:
                    if attempt == 2:
                        break
                    sleep(0.2)
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, future=True)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
