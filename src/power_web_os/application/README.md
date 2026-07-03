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
- `connector_profiles.py` loads external connector descriptions from config
  and compiles them into internal source capability cards for preflight,
  planning, source validation, and execution guards. Profiles must not expose
  internal Radar stage names to connector authors.
- `radar_model_profiles.py` loads non-secret model-role profiles from
  `config/radar/model_profiles`. It keeps candidate-discovery and
  signal-monitoring model defaults independent while `.env` remains limited to
  credentials and deployment overrides.
- `radar_runtime_settings.py` loads non-secret Radar runtime defaults from
  `config/radar/runtime_defaults.json` and `config/radar/run_profiles/*`.
  `.env` and process variables are compatibility override layers, not the
  source of truth for model rows, provider modes, or smoke budgets.
- `radar_runtime_model_profiles.py` projects model profile summaries into
  runtime-config reports without exposing secrets or provider request payloads.
- `persisted_live_radar.py` owns the durable live Radar run lifecycle through
  repository and executor ports.
- `radar_review.py` validates and persists current human review decisions
  through a review repository port.
- `radar_run_journal.py` owns structured run audit event semantics and rejects
  raw hidden chain-of-thought payload keys.
- `radar_technical_trace.py` owns sanitized developer/admin trace semantics,
  secret redaction, long-string capping, and hidden-reasoning rejection.
- Radar backend package architecture is documented in
  `docs/architecture/RADAR_BACKEND_ARCHITECTURE.md`. Current root-level
  `live_radar_*.py` modules are migration debt from candidate-discovery growth,
  not examples for new backend work. New Radar backend logic must target the
  package contract under `src/power_web_os/application/radar/` as it is
  introduced:
  - shared provider-neutral contracts and source capability primitives;
  - candidate-discovery planning, retrieval, extraction, source, universe,
    checkpoint, execution, and diagnostics packages;
  - separate signal-monitoring and future Power Web discovery packages.
- Existing root-level Radar modules remain compatibility/migration surfaces
  until the rescue slices move behavior behind package-owned services and phase
  executors. Do not add new root-level `application/live_radar_*.py` files.
- Signal-monitoring contracts, source strategy, and recorded executor are
  application-owned no-network surfaces until production runtime integration.

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
provider are wired outside the application layer. Persisted execution must load
the active `RadarDefinitionRecord` and pass the canonical live runtime payload
to the executor. Missing active definitions fail the run explicitly; only
legacy/offline demo paths may use the hardcoded live mini definition.

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
code owns execution strategy: qualification discovery, qualification gates, and
coverage checks run before signal searches. New source-backed candidates found
by coverage are merged and re-qualified before the universe is frozen. Providers
receive compact retrieval task cards instead of the whole Radar as one mixed
prompt. The legacy `RadarSearchPlan` remains a compatibility projection, but new
diagnostics and prompt shaping should prefer the accepted retrieval plan.
Structured company facts follow the same rule: application code consumes
`CompanyRegistryProvider` observations through `RadarSourceRegistry`, while
DaData HTTP/API details stay in `integrations`. Structured registry observations
may support candidate identity and qualification evidence; signal searches
remain web-based. Registry lookup requires concrete lookup terms such as a legal
name, INN, OGRN, or candidate scope; broad universe tasks should record
`registry_lookup_insufficient` and continue through web/coverage strategy. The
decision that a source is lookup-only comes from the compiled connector
capability card, not from hardcoded provider names.
Successful registry observations are injected into bounded provider prompts as
`structured_company_observations`, not as instructions for the LLM to call a
registry.

Discovery planning follows the same rule. A `RadarDiscoveryPlanner` may propose
candidate-universe, source-probe, qualification-gate, and coverage-check steps,
but `RadarDiscoveryPlanAcceptanceService` and `RadarDiscoveryPlanValidator` are
the backend authority for criterion roles, source policy, stage ordering, safe
repairs, and accepted execution. If configured global or local source bases are
present, the accepted plan must select them or explicitly skip them with a
product-safe reason. Signal search steps are compiled only after the accepted
qualification and coverage plan, and signal-stage new entities are retained as
universe gaps instead of becoming candidates.

Technical trace persistence follows the same rule: application code emits
pipeline/provider debug summaries through `RadarRunTechnicalTracer`, which
redacts payloads before they reach persistence. Provider adapters may emit
technical observations, but they must not bypass the redactor or store raw
hidden chain-of-thought.

Complex live Radar changes must pass preflight before broad live runs. The
preflight service depends on repository/source-provider contracts and recorded
fixtures; it must not enqueue jobs, call OpenRouter, call DaData, or normalize
broken provider output into apparently successful product states.

Staged live Radar execution uses application-owned adaptive checkpoints between
discovery, gate, coverage, and signal phases. `RadarExecutionCheckpointService`
reviews candidate coverage, linked source evidence, source obligations,
schema/linking issues, and budget pressure before the next expensive phase can
run. Provider adapters may supply observations, but they do not decide whether a
weak candidate universe is good enough for signal search.

Central work scheduling follows the same rule. `RadarWorkScheduler` decides
whether checkpoint-approved work may consume protected capacity before local
executors call providers. `RadarExecutionBudget` and `RadarExternalCallBudget`
remain counters and guards; the scheduler owns admission order for guaranteed
work lanes.

Signal monitoring follows the same boundary discipline. The source strategy is
application-owned and capability-driven: a source can be used for signal
evidence only if the source card says it supports signal evidence, or if a
known source ref from candidate discovery is being re-inspected directly. A
lookup/enrichment-only registry connector is skipped by capability, not by
provider name. A future registry-like connector can participate without code
changes if its connector profile compiles to a signal-capable source card.
Signal monitoring also owns an independent model-profile id and signal-specific
budget counters. Candidate-discovery OpenRouter env tuning must not silently
change the no-network signal monitoring contract.

The checkpoint decision service is not enough to claim full adaptive execution.
The follow-up recovery layer must apply checkpoint actions explicitly in the
application layer: retry a bounded task, expand to an allowed source scope,
request a compact planner revision, stop as review-needed, or fail hard. Each
action must be budgeted, recorded in execution metadata, and covered by
fake/recorded tests before broad live runs are used as evidence.

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
