"""Database engine and session lifecycle helpers for persistence adapters.

Entry points own transaction boundaries by opening `session_scope()` and passing
the resulting session into repository adapters.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from power_web_os.persistence.config import DatabaseSettings


def create_database_engine(settings: DatabaseSettings | None = None, *, database_url: str | None = None) -> Engine:
    resolved = settings or DatabaseSettings.from_env(database_url=database_url)
    # SQLite is used for local smoke tests; PostgreSQL URLs skip this dialect option.
    connect_args = {"check_same_thread": False} if resolved.database_url.startswith("sqlite") else {}
    return create_engine(resolved.database_url, echo=resolved.echo_sql, future=True, connect_args=connect_args)


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
