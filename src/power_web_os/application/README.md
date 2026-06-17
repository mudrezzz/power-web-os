# Application Layer

The application layer owns Power Web OS use-case contracts. It defines records,
ports, and orchestration helpers that API routes, CLI commands, workers, and
schedulers can call without knowing SQLAlchemy, FastAPI, Celery, Redis, or
provider SDK details.

## Ownership

- `radar_records.py` defines application records and lifecycle enums. These are
  not ORM models and not transport DTOs.
- `ports.py` defines repository and async job ports. Infrastructure adapters
  implement these protocols outside this package.
- `radar_catalog_seed.py` maps the existing deterministic demo catalog payload
  into records that repositories can persist.
- `live_radar_contracts.py` defines provider-neutral live Radar DTOs and ports.
- `live_radar_definition.py` owns the deterministic live mini Radar definition
  and search plan.
- `live_radar_normalization.py` owns provider-neutral candidate, signal,
  qualification, evidence-card, and score-evaluation normalization.
- `live_radar_service.py` orchestrates one live Radar execution pass through a
  provider port.
- `persisted_live_radar.py` owns the durable live Radar run lifecycle through
  repository and executor ports.
- `radar_review.py` validates and persists current human review decisions
  through a review repository port.

## Dependency Rules

Allowed imports:

- Python standard library;
- other `power_web_os.application` modules;
- pure domain modules when a use case needs domain decisions.

Forbidden imports:

- `sqlalchemy`, `alembic`, or `power_web_os.persistence`;
- `fastapi` or `uvicorn`;
- `celery`, `redis`, provider SDKs, `httpx`, or `dotenv`.

Application services depend on ports. They do not create sessions, run SQL
queries, call providers directly, or own worker runtime behavior.
Provider HTTP calls belong in `integrations`; LangGraph runtime wrappers belong
in `workflows`.

Persisted live Radar execution follows the same rule: application code creates
and updates run records through repository ports, then calls a
`LiveRadarArtifactExecutor` port. The workflow-backed adapter and OpenRouter
provider are wired outside the application layer.

Human review persistence follows the same rule: application code validates
qualification/signal decision semantics and stores the current decision through
a repository port. API routes own HTTP shape only, and repositories own storage
shape only.

## How To Extend

1. Add or extend an application record when a use case needs a stable internal
   contract.
2. Add or extend a port protocol for persistence, queue, provider, or scheduler
   behavior.
3. Implement adapters in the owning infrastructure package, for example
   `persistence`, `integrations`, or `jobs`.
4. Add contract tests that prove application code imports without infrastructure
   adapters.
5. Update this README and the Developer Guide when a new backend boundary is
   introduced.

`radar_runs` is the application-visible source of truth for long-running Radar
state. Celery/Redis adapters may enqueue work, but they must update and read
durable run state through application ports.
