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
  and backward-compatible search-plan projection.
- `live_radar_execution_plan.py` compiles generic Radar definitions into
  qualification-first staged execution plans.
- `live_radar_discovery_planning.py` owns the discovery planner contracts,
  deterministic fallback planner, source-policy validation, and product-source
  visibility helpers.
- `live_radar_planning_pipeline.py` builds the accepted discovery plan through
  a planner/validator/revision loop before compiling execution tasks.
- `live_radar_staged_execution.py` executes staged provider tasks and suppresses
  signal searches for rejected qualification candidates.
- `live_radar_normalization.py` owns provider-neutral candidate, signal,
  qualification, evidence-card, and score-evaluation normalization.
- `live_radar_service.py` orchestrates one live Radar execution pass through
  explicit planning, provider collection, source normalization, candidate
  extraction, candidate evaluation, validation, and artifact-shaping phases.
- `persisted_live_radar.py` owns the durable live Radar run lifecycle through
  repository and executor ports.
- `radar_review.py` validates and persists current human review decisions
  through a review repository port.
- `radar_run_journal.py` owns structured run audit event semantics and rejects
  raw hidden chain-of-thought payload keys.
- `radar_technical_trace.py` owns sanitized developer/admin trace semantics,
  secret redaction, long-string capping, and hidden-reasoning rejection.

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

Structured run journal persistence follows the same rule: application code
emits lifecycle, planning, evidence, scoring, validation, and self-check event
semantics through a `RadarRunEventRepository` port. Raw hidden reasoning fields
such as `chain_of_thought`, `hidden_reasoning`, and `internal_thoughts` are not
valid application payloads.

Live Radar pipeline phases emit structured event summaries through application
contracts. The persisted run service writes those events through
`RadarRunJournal`. Artifact-derived journal mapping remains a compatibility
fallback for existing snapshots, not the preferred extension path. Application
code owns execution strategy: qualification discovery and gates run before
signal searches, and providers receive bounded tasks instead of the whole Radar
as one mixed prompt.

Discovery planning follows the same rule. A `RadarDiscoveryPlanner` may propose
candidate-universe, source-probe, qualification-gate, and coverage-check steps,
but `RadarDiscoveryPlanValidator` is the backend authority for source policy,
stage ordering, and accepted execution. If configured global or local source
bases are present, the accepted plan must select them or explicitly skip them
with a product-safe reason. Signal search steps are compiled only after the
accepted qualification plan.

Technical trace persistence follows the same rule: application code emits
pipeline/provider debug summaries through `RadarRunTechnicalTracer`, which
redacts payloads before they reach persistence. Provider adapters may emit
technical observations, but they must not bypass the redactor or store raw
hidden chain-of-thought.

## How To Extend

1. Add or extend an application record when a use case needs a stable internal
   contract.
2. Add or extend a port protocol for persistence, queue, provider, or scheduler
   behavior.
3. For live Radar workflow behavior, add or extend the execution plan compiler,
   discovery planner/validator, staged execution helper, or relevant pipeline
   phase before changing workflow wrappers.
4. Implement adapters in the owning infrastructure package, for example
   `persistence`, `integrations`, or `jobs`.
5. Add contract tests that prove application code imports without infrastructure
   adapters.
6. Update this README and the Developer Guide when a new backend boundary is
   introduced.

`radar_runs` is the application-visible source of truth for long-running Radar
state. Celery/Redis adapters may enqueue work, but they must update and read
durable run state through application ports.
