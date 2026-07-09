"""Database engine and session lifecycle helpers for persistence adapters.

Entry points own transaction boundaries by opening `session_scope()` and passing
the resulting session into repository adapters.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

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
        _configure_sqlite_engine(engine)
    return engine


def _configure_sqlite_engine(engine: Engine) -> None:
    """Keep the local Docker SQLite store usable under API and worker concurrency."""

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=120000")
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
