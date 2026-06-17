# Persistence Layer

The persistence layer owns database infrastructure for Power Web OS. It
implements application repository ports using SQLAlchemy and manages schema
changes through Alembic migrations.

## Ownership

- `models.py` contains SQLAlchemy table mappings only.
- `repositories.py` adapts SQLAlchemy sessions to application repository ports.
- `engine.py` creates engines, session factories, and transaction scopes.
- `migrations/` contains Alembic environment and versioned schema changes.
- `seed.py` persists deterministic demo Radar catalog data through repository
  adapters.
- `radar_run_outputs` stores live Radar output snapshots as JSON artifact
  sections until later API slices normalize candidate/evidence query tables.
- `radar_review_decisions` stores the current human review decision for one
  qualification or signal finding. It is mutable current state, not an
  append-only journal.

## Dependency Rules

Allowed imports:

- SQLAlchemy and Alembic migration tooling;
- application records and ports;
- persistence-local helpers.

Forbidden imports:

- `fastapi` or API route modules;
- provider SDKs, `httpx`, or live source clients;
- frontend/demo UI code;
- domain scoring or review decisions hidden inside repositories.

Persistence adapters do not decide candidate truth, score semantics, or worker
execution policy. They store and retrieve records requested by application
services. Review validation belongs in the application layer, not in repository
methods.

## Transaction Boundary

The caller owns the transaction boundary. Use `session_scope()` in CLI or worker
entrypoints, and later wire equivalent session lifecycle through API
dependencies. Repository methods flush so tests can observe generated database
state, but they do not commit.

## Local Commands

```bash
python -m alembic upgrade head
python -m power_web_os.demo seed-radar-db
python -m power_web_os.demo run-live-mini-icp-radar-persisted --live
python -m pytest tests/test_radar_persistence.py
```

The default local database is `sqlite:///./demo/output/power_web_os.sqlite3`.
Set `POWER_WEB_OS_DATABASE_URL` to a PostgreSQL URL for a database-backed
development environment.

## How To Extend

1. Add or update an application record and port first.
2. Add a SQLAlchemy model only for storage shape.
3. Add an Alembic migration for schema changes.
4. Implement a repository adapter that converts between ORM models and
   application records.
5. Add repository tests with SQLite smoke coverage and architecture contract
   checks for dependency direction.

`radar_runs` remains the durable source of truth for long-running job state.
Celery/Redis enqueues execution through the jobs layer, but queue result state
must not replace persisted run status, timestamps, idempotency, correlation, or
errors.
