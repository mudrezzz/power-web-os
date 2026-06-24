# Developer Guide

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m power_web_os.demo generate-icp-radar
python -m power_web_os.demo generate-icp-radar-catalog
python -m power_web_os.demo seed-radar-db
python -m power_web_os.demo generate-account-radar
npm install --prefix ./frontend
npm --prefix ./frontend run dev
```

Run the local backend API boundary:

```bash
python -m pip install -e ".[api,dev]"
power-web-os-api
```

Run the full local Radar dev stack with Docker:

```bash
docker compose up --build
```

This starts Redis, runs Alembic migrations and `seed-radar-db`, then starts the
FastAPI API, Celery worker, and Vite frontend. The default Docker stack uses the
shared SQLite file `demo/output/power_web_os.sqlite3`; API and worker containers
mount `./demo/output` so both processes see the same durable `radar_runs` state.
Keep OpenRouter credentials in local `.env`; Compose mounts it read-only into
backend containers as `/app/.env`, and `.dockerignore` keeps it out of the
Docker build context.

Useful Docker stack URLs:

```text
http://127.0.0.1:5173
http://127.0.0.1:8001/health
http://127.0.0.1:8001/docs
```

The Docker stack publishes host ports that avoid the neighboring Glavred dev
stack defaults: API on `8001` and Redis on `6380`. Containers still use API
port `8000` and Redis port `6379` internally. Override the host ports only when
needed:

```bash
POWER_WEB_OS_API_HOST_PORT=8010 POWER_WEB_OS_REDIS_HOST_PORT=6381 docker compose up --build
```

Troubleshooting:

- If the UI stays in `Demo fallback`, check that the `api` service is healthy
  and `VITE_POWER_WEB_OS_API_BASE_URL` points to `http://127.0.0.1:8001`.
- If a run stays `queued`, check the `worker` service logs and Redis service.
- If a run becomes `failed`, inspect `worker` logs and `.env` OpenRouter
  credentials/model settings.
- A Postgres Compose profile is intentionally out of scope for this dev stack;
  use `POWER_WEB_OS_DATABASE_URL` manually for PostgreSQL-backed development.

## Remote Dev Server

The supported remote development contour is documented in
`docs/deployment/REMOTE_DEV_SERVER.md`. The non-secret connection and port
settings live in `deploy/remote-dev.env`; local `.env` is copied separately and
must never be committed or printed.

Deploy or dry-run the remote Docker stack from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy_remote_dev.ps1 -DryRun
powershell -ExecutionPolicy Bypass -File scripts/deploy_remote_dev.ps1
```

Default remote URLs:

```text
http://213.148.13.45:5173
http://213.148.13.45:8001/health
http://213.148.13.45:8001/api/radars
```

Use the `$deploy-remote-dev` project skill when the task is to upload or
rebuild the remote dev stack. It reads `deploy/remote-dev.env`, checks Git
status, uses `scripts/deploy_remote_dev.ps1`, and reports health/log commands
without exposing `.env` secrets.

Useful local API URLs:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/docs
```

The browser frontend reads this API from `VITE_POWER_WEB_OS_API_BASE_URL`.
For the Docker stack the default is `http://127.0.0.1:8001`; for manual local
processes use `http://127.0.0.1:8000` unless you started uvicorn on another
port. The API allows local Vite origins by default; set
`POWER_WEB_OS_CORS_ORIGINS` to a comma-separated list when using a different
frontend host.

Run Radar persistence migrations and seed the current demo catalog:

```bash
python -m alembic upgrade head
python -m power_web_os.demo seed-radar-db
python -m power_web_os.demo run-live-mini-icp-radar-persisted --live
```

By default, local persistence uses `sqlite:///./demo/output/power_web_os.sqlite3`
so the repository can be tested without a running database service. Set
`POWER_WEB_OS_DATABASE_URL=postgresql+psycopg://user:password@host:5432/power_web_os`
for PostgreSQL-backed development.

Direct checkout demo without installing:

```bash
python demo/run_demo.py generate-icp-radar
python demo/run_demo.py generate-icp-radar-catalog
python demo/run_demo.py generate-account-radar
npm --prefix ./frontend run dev
```

Install the required LangGraph document AI framework when working on agent workflows:

```bash
python -m pip install -e ".[agent,dev]"
```

## Repository Layout

```text
src/power_web_os/      Product domain and application baseline
src/power_web_os/api/  FastAPI backend boundary and API settings
tests/                 Unit and smoke tests
demo/                  Demo fixtures and run instructions
frontend/              React TypeScript Vite demo app
docs/                  Architecture, ADRs, user and contributor docs
.external/             Local research/vendor checkouts, not committed
```

## Frontend Feature Structure

Large product screens must be split into feature modules. A file under `frontend/src/screens/` can stay as the route/shell compatibility wrapper, but feature implementation should live under `frontend/src/features/<feature>/`.

Current ICP Radar structure:

```text
frontend/src/screens/ICPRadarScreen.tsx          Thin wrapper
frontend/src/features/icp-radar/README.md        Feature onboarding, data flow, and new-radar checklist
frontend/src/features/icp-radar/ICPRadarScreen.tsx   Thin feature coordinator
frontend/src/features/icp-radar/icpRadar.css     CSS entrypoint importing feature style modules
frontend/src/features/icp-radar/styles/          CSS modules by ICP Radar UI surface
frontend/src/features/icp-radar/domain/         Pure score, status, validation, qualification helpers
frontend/src/features/icp-radar/adapters/       Raw artifacts -> canonical radar/candidate view models
frontend/src/features/icp-radar/application/    Hooks for navigation, overlays, drafts, and actions
frontend/src/features/icp-radar/components/     Catalog/header presentation components
frontend/src/features/icp-radar/model.tsx        Barrel over focused model modules
frontend/src/features/icp-radar/modelTypes.ts
frontend/src/features/icp-radar/validationModel.ts
frontend/src/features/icp-radar/radarMetaModel.ts
frontend/src/features/icp-radar/liveModel.ts
frontend/src/features/icp-radar/settingsModel.ts
frontend/src/features/icp-radar/candidateViews.tsx   Barrel for fixture candidate views
frontend/src/features/icp-radar/fixtureShortlist.tsx
frontend/src/features/icp-radar/fixturePreview.tsx
frontend/src/features/icp-radar/fixtureDetail.tsx
frontend/src/features/icp-radar/liveCandidateViews.tsx  Barrel for live candidate views
frontend/src/features/icp-radar/liveShortlist.tsx
frontend/src/features/icp-radar/liveDetail.tsx
frontend/src/features/icp-radar/criteriaBreakdown.tsx
frontend/src/features/icp-radar/settings.tsx
frontend/src/features/icp-radar/settingsBlocks.tsx
frontend/src/features/icp-radar/settingsSearch.tsx
frontend/src/features/icp-radar/settingsQualification.tsx
frontend/src/features/icp-radar/settingsMonitoring.tsx
frontend/src/features/icp-radar/settingsSignals.tsx
frontend/src/features/icp-radar/settingsScoring.tsx
frontend/src/features/icp-radar/settingsValidation.tsx
frontend/src/features/icp-radar/settingsFields.tsx
frontend/src/features/icp-radar/settingsHeader.tsx
frontend/src/features/icp-radar/detailPrimitives.tsx
```

Rules:

- Start ICP Radar frontend changes from `frontend/src/features/icp-radar/README.md`; it documents the data flow, ownership map, and checklist for adding radar types without creating new UI paradigms.
- Keep route/screen wrappers thin once a screen grows beyond a simple view.
- Keep the feature entrypoint thin; it should not own localStorage, raw fixture/live mapping, or score calculation.
- Put new radar source types behind an adapter that emits the canonical radar/candidate view model.
- Put browser-local state in application hooks, not in presentation components.
- Put backend Radar transport in `frontend/src/api/` and map API DTOs under
  `frontend/src/features/icp-radar/adapters/`. Presentation components must not
  call `fetch` directly.
- Keep model/normalization/scoring helpers separate from JSX-heavy view components.
- Keep feature-specific CSS next to the feature module; leave `frontend/src/styles.css` for app shell and shared primitives.
- Keep large feature CSS split by surface. ICP Radar styles use `icpRadar.css` only as an import entrypoint, with catalog, shortlist, preview, detail, settings, criteria, and responsive rules in `frontend/src/features/icp-radar/styles/`.
- Keep expensive or rarely used panels, such as ICP Radar Settings, behind `React.lazy` and `Suspense`.
- Add short module-boundary comments and comments for non-obvious data shaping, storage migration, scoring, or UX invariants.
- Do not add comments that repeat obvious JSX.
- Run `python -m pytest` after feature-structure changes; `tests/test_frontend_architecture_contract.py` guards the ICP Radar decomposition, application/adapters/domain/components boundaries, model barrel boundaries, feature CSS module ownership, lazy Settings loading, and i18n runtime/resource split.

When adding ICP Radar UI, prefer the existing module boundary instead of adding new logic to `ICPRadarScreen.tsx`: source-specific artifact/API mapping goes to `adapters/`, browser-local and backend workflows go to `application/`, domain decisions go to `domain/`, shortlist/table changes go to `fixtureShortlist.tsx` or `liveShortlist.tsx`, preview-only changes go to `fixturePreview.tsx`, detail/review changes go to `fixtureDetail.tsx` or `liveDetail.tsx`, and settings block changes go to the relevant `settings*` module.

## Backend API Baseline

The persistent backend boundary lives in `src/power_web_os/api/`.

Current files:

```text
src/power_web_os/api/README.md          API layer ownership guide
src/power_web_os/api/app.py             FastAPI app factory and router registration
src/power_web_os/api/config.py          API settings boundary
src/power_web_os/api/dependencies.py    Repository/job queue dependency wiring
src/power_web_os/api/radar_routes.py    Radar catalog/run/candidate endpoints
src/power_web_os/api/radar_dtos.py      Pydantic transport contracts
src/power_web_os/api/radar_mappers.py   Application record -> API DTO mapping
src/power_web_os/api/__main__.py        Local uvicorn runner for power-web-os-api
```

Current Radar endpoints:

```text
GET  /api/radars
GET  /api/radars/{radar_id}
GET  /api/radars/{radar_id}/preflight
POST /api/radars/{radar_id}/runs
GET  /api/radar-runs/{run_id}
GET  /api/radar-runs/{run_id}/candidates
GET  /api/radar-runs/{run_id}/reviews
PUT  /api/radar-runs/{run_id}/candidates/{candidate_id}/qualification/{rule_id}/review
DELETE /api/radar-runs/{run_id}/candidates/{candidate_id}/qualification/{rule_id}/review
PUT  /api/radar-runs/{run_id}/candidates/{candidate_id}/signals/{signal_code}/review
DELETE /api/radar-runs/{run_id}/candidates/{candidate_id}/signals/{signal_code}/review
```

Rules:

- Keep FastAPI routes thin: validate transport input, call application services, return DTOs.
- Keep domain logic outside routes.
- Keep database access behind repository interfaces once persistence is introduced.
- Keep generated JSON artifacts as demo/export fallback, not long-term source of truth.
- Do not import frontend/demo artifact readers into API routes as hidden persistence.
- Use Pydantic DTOs for request/response contracts and keep OpenAPI stable.
- `POST /api/radars/{radar_id}/runs` creates a queued run, enqueues worker
  execution through `JobQueue`, and returns `202 Accepted`.
- Clients poll `GET /api/radar-runs/{run_id}` until the status is terminal,
  then call `GET /api/radar-runs/{run_id}/candidates` after output exists.
- Review endpoints persist current human decisions for existing qualification
  and signal findings. The frontend uses those endpoints when a live Radar run
  is API-backed, and keeps browser `localStorage` only for fixture/offline
  fallback state.

Run locally after migrations and seed:

```bash
python -m alembic upgrade head
python -m power_web_os.demo seed-radar-db
power-web-os-api
```

Useful Radar API URLs:

```text
http://127.0.0.1:8000/api/radars
http://127.0.0.1:8000/api/radars/toir-quick-live
http://127.0.0.1:8000/api/radars/toir-quick-live/preflight
http://127.0.0.1:8000/api/radar-runs/{run_id}/journal
http://127.0.0.1:8000/api/radar-runs/{run_id}/dossier
http://127.0.0.1:8000/api/radar-runs/{run_id}/technical-trace
http://127.0.0.1:8000/docs
```

Validation:

```bash
python -m pytest tests/test_backend_api.py
```

## Backend Jobs

Radar jobs are queued through Celery and transported by Redis, while
`radar_runs` remains the source of truth.

Current files:

```text
src/power_web_os/jobs/README.md       Jobs layer ownership guide
src/power_web_os/jobs/radar_jobs.py   Celery app, queue adapter, worker task, scheduler adapter
```

Local worker flow:

```bash
python -m alembic upgrade head
python -m power_web_os.demo seed-radar-db
celery -A power_web_os.jobs.radar_jobs.radar_celery_app worker --loglevel=INFO --pool=solo
power-web-os-api
$env:VITE_POWER_WEB_OS_API_BASE_URL="http://127.0.0.1:8000"
npm --prefix ./frontend run dev
```

With Redis and the worker running, open `ICP Radar`, select
`ТОиР Quick Live Radar`, and click `Check setup` / `Проверка` before a long
manual run. The UI calls `GET /api/radars/{radar_id}/preflight` and shows a
human-readable readiness panel: failed checks and remediation, redacted API
runtime settings, and API/worker parity for the latest run when a worker
snapshot exists. This UI check is offline/static; use the CLI
`preflight-radar --live-probes --probe ...` flags for bounded live DaData or
OpenRouter probes. Then click `Run radar`. The UI posts a queued run, polls
`GET /api/radar-runs/{run_id}`, and reads
`GET /api/radar-runs/{run_id}/candidates` plus
`GET /api/radar-runs/{run_id}/journal` after output exists. It also reads
`GET /api/radar-runs/{run_id}/dossier` to show the product run dossier: run
context, definition version, task context, persisted qualification-first search
plan, source usage, validation warnings, and non-debug timeline events. The
dossier also exposes checkpoint metadata: after discovery, gates, coverage, and
before signal search the application records whether execution continued,
retried a bounded task, expanded to an allowed source scope, attempted a compact
revision-style recovery, stopped for review, or recommended hard failure. The
first adaptive recovery loop runs after discovery and coverage checkpoints; it
does not start signal search until the latest pre-signal checkpoint returns
`continue`. Treat `stopped_for_review_reason`, `checkpoint_warnings`, and
`adaptive_actions` as the first place to inspect why a run did or did not
recover from weak discovery. The dossier is safe for the normal product UI.
API-backed live runs also expose a
separate `Trace` tab backed by
`GET /api/radar-runs/{run_id}/technical-trace`; it is developer/admin oriented
and contains sanitized per-task pipeline/provider payloads plus redaction
reports. The UI groups trace steps by Radar phase, highlights error/warning
steps, provides search and quick filters, shows readable request/provider/
parsed/validation sections, and keeps raw JSON collapsed by default with copy
actions for sanitized payloads. Do not store or display raw hidden
chain-of-thought. If the backend is unavailable, the same screen stays in
explicit demo fallback mode and reads the generated JSON files.

Use `Inspect run` / `Диагностика запуска` from the live run status, empty state,
failed state, completed state, or zero-candidate state when you need run-level
inspection without selecting a candidate. The diagnostics panel shows run
context, execution counts, coverage warnings, candidate-universe lifecycle,
source lifecycle, product-safe dossier/journal sections, and trace availability.
Candidate detail tabs remain the place for candidate-specific evidence, review
decisions, and signal rows.

Default queue settings:

```text
POWER_WEB_OS_CELERY_BROKER_URL=redis://localhost:6379/0
POWER_WEB_OS_CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

For tests and local diagnostics without Redis:

```text
POWER_WEB_OS_CELERY_TASK_ALWAYS_EAGER=1
POWER_WEB_OS_CELERY_TASK_EAGER_PROPAGATES=1
```

Validation:

```bash
python -m pytest tests/test_radar_jobs.py
```

## Backend Persistence Foundation

Radar persistence is split across application contracts and SQLAlchemy
adapters:

```text
src/power_web_os/application/radar_records.py       Radar records and run status
src/power_web_os/application/ports.py               Repository and async job ports
src/power_web_os/application/radar_catalog_seed.py  Demo catalog -> records mapper
src/power_web_os/application/persisted_live_radar.py Durable live Radar run service
src/power_web_os/application/radar_review.py        Human review decision service
src/power_web_os/application/radar_run_journal.py   Structured run audit service
src/power_web_os/persistence/models.py              SQLAlchemy table mappings
src/power_web_os/persistence/repositories.py        SQLAlchemy repository adapters
src/power_web_os/persistence/migrations/            Alembic migration environment
```

Rules:

- Application modules define records, use-case ports, and payload mapping only.
- SQLAlchemy imports, sessions, models, and queries stay inside `persistence`.
- `radar_runs` is the durable source of truth for queued/running/waiting-human/completed/failed/cancelled state.
- `radar_run_outputs` stores the current live Radar artifact as a JSON snapshot;
  do not treat it as a final normalized candidate/evidence schema.
- `radar_review_decisions` stores the current mutable human review decision per
  run/candidate/qualification-or-signal subject. It does not replace an
  append-only audit journal.
- `radar_run_events` stores ordered append-only lifecycle, planning, collection,
  extraction, scoring, validation, and self-check audit events.
- `radar_run_events` must not store raw hidden chain-of-thought fields such as
  `chain_of_thought`, `hidden_reasoning`, or `internal_thoughts`.
- Celery/Redis implement `JobQueue`, but queue state must not replace `radar_runs`.
- The seed command upserts current demo radars and active definitions; it does not execute live searches or create run records.
- The persisted live run command executes the existing live workflow path,
  persists run state and output, and exports the same JSON artifact shape for
  demo/frontend fallback.
- Persisted live execution is active-definition-first. The worker loads the
  active `RadarDefinitionRecord`, adapts it into the live runtime payload, and
  passes that payload into the workflow executor. The hardcoded live mini radar
  definition remains only for legacy/offline demo commands that do not provide
  an explicit runtime payload.
- If an active definition is missing, the persisted run fails with explicit
  error metadata instead of silently falling back to the hardcoded mini radar.
- Live Radar execution is now an explicit qualification-first application
  pipeline. Extend `RadarExecutionPlan` compilation, provider collection,
  source normalization, candidate extraction, candidate evaluation, validation,
  or artifact shaping as separate phase methods/contracts before changing the
  workflow wrapper. The workflow wrapper maps runtime nodes onto those phases;
  it must not become the owner of provider calls, scoring semantics, review
  decisions, or persistence.
- Discovery strategy is planned separately from execution. Add or modify
  `RadarDiscoveryPlanningInput`, `RadarDiscoveryPlanner`, and
  `RadarDiscoveryPlanValidator` when the system needs smarter candidate-universe
  planning. The LLM planner proposes source bases, bounded steps, expected
  evidence, and coverage hypotheses; backend validation remains authoritative
  for source policy, stage ordering, and accepted execution.
- Source policy is an executable contract, not just context for the LLM. New
  source policy work must distinguish source trust from source usage obligation:
  required, preferred, optional, fallback, disabled, and stage-scoped variants
  such as required for identity, coverage, or signal evidence. Required sources
  must be used in an accepted stage or produce an explicit review/failure state;
  they must not be silently skipped by planner output.
- Qualification tasks and signal tasks must remain separate. Provider adapters
  execute one bounded task at a time; application services own stage ordering
  and rejected-candidate signal suppression.
- Candidate discovery is iterative. Application services execute coverage
  checks before signal search, merge source-backed gap candidates into the
  universe, re-run qualification gates for new candidates, and freeze the final
  universe before any signal task starts. Signal tasks must not add candidates;
  late-mentioned entities become `candidate_universe_gap` metadata for dossier
  and trace inspection.
- Product source lists must contain only evidence-bearing used sources. Keep
  analyzed/skipped sources in execution metadata or sanitized technical trace so
  users see clean evidence while developers can debug source selection.
- Adaptive execution checkpoints should guard expensive live runs. After
  discovery, gates, and coverage, check candidate counts, linked-source counts,
  required-source usage, schema/linking failures, budget pressure, and coverage
  risk. The first recovery loop can run bounded retry, allowed source expansion,
  and compact revision-style attempts under explicit budgets; if recovery does
  not improve the result, execution stops as review-needed instead of silently
  freezing a weak candidate universe and proceeding to signal search.
- DaData and future structured registries are backend source providers. The
  backend should call them, normalize typed observations, and pass facts into
  extraction/evaluation. Do not ask the LLM to "use DaData" as if it were a
  hidden tool unless the backend has actually provided such a tool.
- Structured journal events should come from pipeline phase outputs through
  `RadarRunJournal`. Artifact-derived journal mapping exists only as a
  backward-compatible fallback for older snapshots and fake test executors.

Validation:

```bash
python -m pytest tests/test_radar_persistence.py
python -m pytest tests/test_persisted_live_radar.py
python -m pytest tests/test_radar_review_decisions.py
```

### How To Extend Backend Persistence

Use this path for new durable backend behavior:

1. Start in `src/power_web_os/application/README.md` and
   `src/power_web_os/persistence/README.md`.
2. Add or update an application record for the use-case contract.
3. Add or update an application port protocol for repository, queue, scheduler,
   executor, or provider behavior.
4. Add a SQLAlchemy model only for storage shape.
5. Add an Alembic migration for schema changes.
6. Implement a repository adapter that converts ORM models to application
   records and back.
7. Add repository tests and architecture contract tests.
8. Update local layer README files when ownership, dependencies, or extension
   rules change.

Do not import `power_web_os.persistence`, SQLAlchemy, Alembic, FastAPI, Celery,
Redis, or provider SDKs from `application`. Do not put SQLAlchemy queries in
FastAPI routes. Do not let worker tasks, scheduler triggers, or queue adapters
own scoring, provider normalization, review semantics, or final candidate state.

## Backend Architecture Guardrails

Backend work must follow the same explicit-boundary rule as the ICP Radar
frontend feature. New backend code should use these ownership boundaries:

```text
src/power_web_os/api/           FastAPI app, routes, DTOs, dependency wiring
src/power_web_os/application/   Use cases, transactions, ports, orchestration
src/power_web_os/domain/        Business rules, scoring, validation, review semantics
src/power_web_os/persistence/   SQLAlchemy models, sessions, repositories, migrations
src/power_web_os/integrations/  Provider, source, CRM, and external API adapters
src/power_web_os/workflows/     LangGraph workflow wrappers and workflow state
src/power_web_os/jobs/          Worker and scheduler entrypoints
```

Rules:

- API routes validate transport input, call application services, and return DTOs.
- Application services own use cases and transaction boundaries.
- Domain services own scoring, validation, review semantics, evidence rules, and handoff rules.
- Domain modules must not import FastAPI, SQLAlchemy, Celery, Redis, `httpx`, `dotenv`, `uvicorn`, or provider SDKs.
- Persistence implementations own SQLAlchemy models, sessions, and queries behind repository interfaces.
- Provider adapters return typed observations and evidence; they do not decide candidate state or final truth.
- Workflow wrappers orchestrate execution and audit, but do not hide domain scoring or review semantics.
- Worker tasks and scheduler triggers are entrypoints only. They call application services and update durable run state through repositories.
- New backend modules should stay under 500 lines unless an explicit architecture contract allowlist gives a temporary reason.

Long-running Radar jobs should be modeled as durable runs before adding
production worker infrastructure. `radar_runs` remains the source of truth for
status, timestamps, idempotency, correlation, errors, and audit. Celery/Redis
implements the queue adapter, but Celery result state must not become the
product state. FastAPI `BackgroundTasks` is not the production execution model
for Radar runs.

Temporary legacy-large modules are allowed until a later decomposition slice:
`icp_radar.py`, `icp_radar_catalog.py`, and `icp_radar_xlsx.py`. Do not copy
their size or mixed responsibilities into new backend work.

Validation:

```bash
python -m pytest tests/test_backend_architecture_contract.py
```

## Domain Baseline

The current Python package contains:

- `Account`
- `Signal`
- `Evidence`
- `PowerWebRole`
- `Playbook`
- `AccessRoute`
- `AccessPlan`
- `DeterministicAccessPlanner`
- `AccountRadar`
- `PowerWebBoardBuilder`
- `PlaybookAnalysisBuilder`
- `AccessPlanningState`
- `AccessPlanningWorkflow`
- `ICPRadar`
- `ICPRadarXlsxImport`

The deterministic planner owns route scoring. `AccessPlanningWorkflow` orchestrates typed state, planner invocation, artifact shaping, and workflow metadata. `ICPRadarXlsxImport` normalizes the ТОиР/SIBUR workbook into an `ICPRadarArtifact`. `AccountRadar` builds the accepted-portfolio read model from generated Access Plans and owns deterministic account ranking. `PowerWebBoardBuilder` builds the selected-account board read model from the generated Access Plan and current account roles/missing roles. `PlaybookAnalysisBuilder` builds a read-only explanation of playbook effects over the generated routes, including the current playbook and the deterministic `no_partner_motion` what-if variant. The workflow uses `langgraph-dai` when the optional `agent` extra is installed and falls back to a local runner for base tests.

## ICP Radar Funnel

The next ABM layer is `ICP Radar`. It sits before the current Account / Power Web / Access Plan loop.

Terminology:

- `ICP Radar`: product/ICP-specific radar that discovers and monitors candidate accounts.
- `AccountRadar`: current deterministic portfolio read model in code. It may remain as an internal compatibility name until the ICP Radar layer is implemented.
- `Account discovery`: stable or manually imported legal-entity discovery, for example companies inside a holding.
- `Signal monitoring`: recurring search for current evidence and buying signals against discovered accounts.
- `Radar candidate`: an account that has been scored but has not yet been accepted into Power Web work.

Implemented first fixture:

- Use `demo/fixtures/icp_radar/sibur_icp_pass1.xlsx` as the source workbook fixture.
- Write the normalized artifact to `demo/fixtures/icp_radar/toir_sibur_icp_radar.json`.
- Model the `Criteria` sheet as `SignalCriterion` records.
- Model the `ICP Matrix` sheet as legal entities, evidence refs, criterion scores, fit/intent/trigger totals, and tier.
- Model `Sources` as evidence-source metadata.
- Keep numeric C1-C20 scores sourced from the XLSX.
- Add criterion-level explanation from `demo/fixtures/icp_radar/toir_sibur_criterion_evidence.json` where curated demo facts exist.
- Mark curated criterion explanations as `evidence_origin: synthetic_demo_annotation`; they are demo annotations, not fields extracted from the XLSX.
- Fill every candidate and every C1-C20 criterion with `criteria_evidence`:
  - `supported` when curated demo facts exist;
  - `inferred` when score is nonzero but no criterion-level facts exist;
  - `not_observed` when score is zero.
- Use Russian-language company names and people in generated accepted-account demo data.

Radar catalog and configuration loop:

- Since Slice 0.6.5.2, `RadarDefinition` is an executable structured model:
  - `metadata`: name, description, owner, status;
  - `global_search_policy`: reusable typed sources, keywords, exclusions, and whether the system may use additional sources;
  - `account_qualification.rule_group`: rules that decide whether a legal entity belongs in the radar universe;
  - `intent_signals[]`: signals that decide why a qualified account is interesting now;
  - `intent_signals[].scoring_rubric`: fixed `0/1/2` signal scoring rules;
  - `monitoring_policy`: cadence, lookback window, run mode, dedupe, and stale settings;
  - `scoring_model`: fit model, intent model, tier model, preset choice, optional custom formula, tier thresholds, and confidence penalties;
  - `validation_report`: structural and obvious contradiction findings from `RadarDefinitionValidator`.
- Settings are edited by block: selected radar header, Global search base, Account qualification rules, Monitoring, Signal scale, Intent signals, Scoring model, and Validation. Do not reintroduce one global edit mode or a standalone Settings action row.
- The selected radar header owns human metadata and lifecycle controls: name, description, active/inactive status, read-only owner, duplicate, local delete, and reset. Keep actions in the top-right header row, and keep status/local/read-only metadata with the radar description on the left.
- Do not repeat monitoring run mode in the selected radar header; run mode belongs to the Monitoring settings block.
- Sources are entities, not textarea blobs. The UI shows the global source base as a bounded numbered table, can add local per-rule/per-signal sources, and stores generated source ids only as internal contract fields.
- Rule and signal IDs/codes are generated by the system. They may be displayed compactly for custom formula references, but they must not be manually edited in the UI.
- Account qualification rules and signal detection rules are description-first. The UI must not expose `target field`, `comparison operator`, or `value` as user-authored controls. Optional generated technical fields may remain in the artifact for future agent execution and validator support.
- The visible qualification editor is intentionally flat: no nested group editor. It may use a root `RuleGroup` internally, but users only edit natural-language criteria, `AND` / `OR`, optional `NOT`, requirement level, global-base usage, local sources, cross-validation, and HITL additional-source switches. View mode should be an aligned table with operator, rule, source, cross-check, additional-source, and requirement columns.
- The visible source policy editor must not expose source IDs, source logic, or fallback confidence. Use user-facing trust policies: trusted, cross-check, and HITL required.
- Boolean source policies and active/inactive state use the shared switch control. Disabled switches are read-only indicators and must not fire state changes; active switch thumbs must remain inside the track.
- Monitoring duration fields are stored as strings in the artifact for compatibility, but the UI edits them as number plus unit.
- Intent signals use a separate global scoring rubric table by default. Per-signal rubric editing is hidden behind an explicit override switch. View mode should be an aligned table with code, detection rule, source, cross-check, additional-source, and scale-override columns.
- Qualification filters and intent signals are different domain concepts and must remain separate.
- Treat `RadarDefinition` as a first-class configuration contract, not only metadata inside a generated report.
- `generate-icp-radar` writes the active shortlist artifact and includes `radar.definition`.
- `generate-icp-radar-catalog` writes the portfolio artifact for multiple configured ICP Radars.
- The frontend loads `/demo/icp_radars.json` for radar cards and `/demo/icp_radar.json` for the active fixture-backed `ТОиР / SIBUR` shortlist.
- Editable configuration uses constrained controls. Formula presets are preferred; custom formulas are allowed only through an explicit preset and should reference generated rule IDs or signal codes.
- Generated artifacts remain read-only. The frontend stores created/edited radar definitions in browser `localStorage` under `power-web-os-icp-radar-config-overrides`.
- The localStorage overlay shape is keyed by `radar_id` and stores `{ override_type, radar, saved_at }`. `override_type` is `created`, `edited`, or `deleted`; UI-only radar statuses may be `local_draft` or `modified_locally`. `deleted` hides a generated radar until demo changes are reset and does not mutate generated artifacts.
- Normalize radar definitions loaded from both generated artifacts and `localStorage` before rendering Settings. Local browser drafts can outlive artifact-contract changes; missing arrays, source policies, rule groups, monitoring fields, scoring fields, or validation arrays must be defaulted rather than allowed to crash a switch interaction.
- Edited settings do not call a production API, do not write JSON artifacts, do not run live connectors, and do not recalculate the fixture shortlist in this slice.
- The catalog must expose reset behavior so a user can return to generated artifact state.
- Run history and monitoring schedule come after configuration, with explicit separation between one-time account discovery and recurring signal monitoring.

Imported workbook scoring fields:

```text
fit_score = C13 + C14 + C15 + C16 + C17
intent_score = C1..C9 + C18 + C19
trigger_score = C10 + C11 + C12 + C20
total_score = sum(C1..C20)
tiers = >=38 Tier 1, >=25 Tier 2, >=15 Tier 3, else Monitor
```

These fields remain on imported candidates for backward compatibility with the XLSX fixture. They are not the editable radar settings model. Radar Settings expose only:

```text
Fit model: aggregate account qualification criteria
Intent model: aggregate intent signals
Tier model: classify candidates by thresholds
```

Generated command:

```bash
python -m power_web_os.demo generate-icp-radar
python -m power_web_os.demo generate-icp-radar-catalog
```

It writes:

```text
demo/output/icp_radar.json
demo/output/icp_radars.json
frontend/public/demo/icp_radar.json
frontend/public/demo/icp_radars.json
demo/fixtures/icp_radar/toir_sibur_icp_radar.json
```

The generated ICP Radar artifact version is `0.6.5.2`. It keeps `criteria_evidence_contract_version: "0.6.2.3"` and writes the structured `radar.definition` model. `radar.definition.intent_signals` is the canonical C1-C20 dictionary for Settings, candidate scores, and evidence explanations. The top-level `criteria` field is generated from `intent_signals` as a backward-compatible alias and must not diverge. Each candidate keeps the backward-compatible fields `criteria_scores`, `evidence_refs`, and `source_urls`, and adds:

```text
candidates[].criteria_evidence[criterion_code]
candidates[].criteria_evidence[criterion_code].evidence_status
candidates[].criteria_evidence[criterion_code].confidence
candidates[].criteria_evidence[criterion_code].rationale
candidates[].criteria_evidence[criterion_code].facts[]
```

## Live Mini ICP Radar

`Slice 0.6.3.1` adds the first provider-backed ICP Radar run without changing the stable XLSX fixture radar. The live radar is intentionally small: `toir-quick-live`, two qualification criteria, and three intent signals.

The backend boundary is provider-neutral:

- `WebSearchProvider` is the interface used by the workflow.
- `OpenRouterWebSearchProvider` is the first live provider.
- `RecordedWebSearchProvider` is used by tests and mocked runs.
- `LiveICPRadarRunWorkflow` follows the optional `langgraph-dai` / `BaseWorkflow` pattern used elsewhere in the project.

Current ownership:

```text
src/power_web_os/application/live_radar_contracts.py       Provider-neutral contracts and ports
src/power_web_os/application/live_radar_definition.py      Live mini Radar definition and search plan
src/power_web_os/application/live_radar_execution_plan.py  Qualification-first execution plan compiler
src/power_web_os/application/live_radar_staged_execution.py Staged provider-call executor
src/power_web_os/application/live_radar_normalization.py   Candidate, signal, evidence, and score normalization
src/power_web_os/application/live_radar_service.py         One provider-neutral live run pass
src/power_web_os/integrations/openrouter_request_builder.py Bounded OpenRouter prompt/request shaping
src/power_web_os/integrations/live_radar_openrouter.py     OpenRouter and recorded provider adapters
src/power_web_os/workflows/live_icp_radar_workflow.py      Optional langgraph-dai wrapper and fallback runtime
src/power_web_os/live_icp_radar.py                        Compatibility facade for historical imports
```

Environment variables are loaded from the process environment or local `.env`:

```text
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4.1-mini
OPENROUTER_ADVANCED_MODEL=deepseek/deepseek-v3.2
OPENROUTER_PLANNER_MODEL=deepseek/deepseek-v3.2
OPENROUTER_EXTRACTOR_MODEL=deepseek/deepseek-v3.2
OPENROUTER_WEB_MODE=server_tools
POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT=1
POWER_WEB_OS_RADAR_MAX_DISCOVERY_TASKS_PER_RULE=
POWER_WEB_OS_RADAR_MAX_GATE_TASKS_PER_CANDIDATE_RULE=
POWER_WEB_OS_RADAR_MAX_SIGNAL_TASKS_PER_CANDIDATE_SIGNAL=
POWER_WEB_OS_RADAR_MAX_TOTAL_WEB_TASKS_PER_RUN=
```

For local CLI demo runs, explicit constructor arguments are strongest, then project `.env`, then ambient OS environment variables. This prevents an old Windows/user `OPENROUTER_API_KEY` from silently overriding the key in the repository-local `.env`.

Model routing is role-specific. `OPENROUTER_MODEL` is the fast/default model for
simple bounded tasks such as signal checks. Planner calls use
`OPENROUTER_PLANNER_MODEL`; discovery, qualification, and coverage extraction
use `OPENROUTER_EXTRACTOR_MODEL`. If a specific model is absent, planner and
extractor fall back to `OPENROUTER_ADVANCED_MODEL`, then to `OPENROUTER_MODEL`.

`POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT` is a compatibility safety limit
for backend-controlled live Radar web/provider tasks. The checked-in
`.env.example` uses a smoke-safe value of `1` so Docker/dev manual runs can
finish quickly while the pipeline is still being tuned. The code fallback is
`20` when no environment value is configured.

Hierarchical budget variables override the compatibility alias when set:

```text
POWER_WEB_OS_RADAR_MAX_DISCOVERY_TASKS_PER_RULE=
POWER_WEB_OS_RADAR_MAX_GATE_TASKS_PER_CANDIDATE_RULE=
POWER_WEB_OS_RADAR_MAX_SIGNAL_TASKS_PER_CANDIDATE_SIGNAL=
POWER_WEB_OS_RADAR_MAX_TOTAL_WEB_TASKS_PER_RUN=
```

Discovery budgets are counted per qualification/discovery rule. Gate budgets
are counted per `(candidate, qualification_rule)`. Signal budgets are counted
per `(candidate, signal)`. The total run budget caps all backend-controlled
provider tasks. A candidate that was never searched because a budget was
exhausted is projected as `not_searched_budget_limited`, not as
`not_observed`. `not_observed` means the relevant bounded search actually ran
and found no supporting evidence.

Source verification and useful-result budget variables:

```text
POWER_WEB_OS_RADAR_SOURCE_VERIFICATION_MODE=soft
POWER_WEB_OS_RADAR_MIN_USEFUL_SOURCES_PER_DISCOVERY_TASK=3
POWER_WEB_OS_RADAR_MIN_CANDIDATES_PER_DISCOVERY_TASK=5
POWER_WEB_OS_RADAR_MAX_DISCOVERY_RETRIES_PER_TASK=2
POWER_WEB_OS_RADAR_WEB_RETRIEVAL_PROVIDER=openrouter
POWER_WEB_OS_OPENROUTER_WEB_SEARCH_ENGINE=auto
```

`POWER_WEB_OS_RADAR_SOURCE_VERIFICATION_MODE` controls how provider-returned
URLs affect candidate evidence:

- `strict`: currently reachable URLs are required before a source can support a
  product finding.
- `soft`: failed reachability keeps source-linked findings as risk-bearing,
  review-needed evidence instead of deleting the candidate.
- `off`: skip HTTP reachability checks for diagnostic runs.

Useful-result budgets are separate from the hard task limit. If a discovery or
coverage task returns too few useful sources/candidates, or only unverified
material, the backend can retry the bounded task until
`POWER_WEB_OS_RADAR_MAX_DISCOVERY_RETRIES_PER_TASK` is reached. This prevents a
single empty or broken retrieval response from freezing the candidate universe.

`POWER_WEB_OS_RADAR_WEB_RETRIEVAL_PROVIDER` selects the web retrieval boundary.
Use `openrouter` for the default OpenRouter web path. Use
`openrouter_perplexity` to keep OpenRouter authentication/runtime but request
the OpenRouter server-tools web-search engine `perplexity`. The direct
Perplexity Search API is intentionally deferred because it needs its own API key
and HTTP contract.

`POWER_WEB_OS_OPENROUTER_WEB_SEARCH_ENGINE` is passed to OpenRouter server-side
web search. `auto` keeps the default engine; `perplexity` asks OpenRouter to use
Perplexity-backed retrieval where supported. Technical trace separates
`retrieval_request`, `retrieval_response`, and extraction/normalization records,
so provider URL/snippet/citation behavior can be inspected before candidate
scoring.

Prompt construction is also a boundary. Planner prompts may carry rich Radar
context because they produce strategy. Execution prompts are compiled from
compact task cards: current candidate/rule/signal scope, selected source policy,
expected evidence, and a concise response contract. Do not send the whole Radar
definition, duplicated one-query search plan, and full verbose schema to every
bounded provider call. Technical trace shows both the task card and the compiled
provider prompt.

DaData is the first implemented structured company-source provider, not a web
search replacement. The source registry port lives in `application`; DaData
API/MCP client code lives in `integrations/dadata_provider.py`. Use it for
legal-entity normalization, INN/OGRN/company facts, address/status/OKVED/revenue
enrichment, domain/email-owner lookup, and other registry-style facts when the
Radar source policy allows it. Keep open web retrieval for current evidence and
intent signals. Local secrets such as `DADATA_API_KEY` and `DADATA_SECRET_KEY`
must remain in `.env` only and must not appear in traces, artifacts, docs, or
tests.

DaData lookup is bounded identity/enrichment, not holding-contour enumeration.
The source registry builds concrete lookup terms from candidate scope,
legal-name-like text, INN, OGRN, and source keywords. If a task only asks for a
broad universe such as "find all companies in a holding", DaData returns an
explicit `registry_lookup_insufficient` outcome and the adaptive pipeline should
use web/coverage strategy instead of pretending the registry enumerated the
contour.

When DaData returns observations, the backend injects them into subsequent
provider calls as `structured_company_observations`: source ref, legal name,
normalized name, INN, OGRN, status, address, OKVED, match quality, and match
reason. The prompt should receive these as already executed source-backed facts,
not as an instruction for the LLM to "use DaData". Signal-search tasks do not
call DaData and must still rely on web evidence for intent signals.

Entity resolution runs in the application layer before Radar candidate scoring.
`RadarEntityResolutionService` classifies provider observations as
`legal_entity`, `production_site`, `project`, `asset`, or `unknown_entity`.
Only legal entities are normal account candidates. Sites, projects, and assets
must be linked to a resolved legal entity or reported as review-needed
candidate-universe gaps with `entity_type_not_account`; do not let provider
output such as project codes or plant names become standalone scored accounts.

DaData local settings:

```text
DADATA_API_KEY=
DADATA_SECRET_KEY=
POWER_WEB_OS_DADATA_MODE=recorded
POWER_WEB_OS_DADATA_BASE_URL=https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party
```

Use `POWER_WEB_OS_DADATA_MODE=recorded` for tests and local smoke without
network credentials. Use `live` only when both DaData keys are present. Dossier
source lifecycle and technical trace show DaData source outcomes; signal-search
tasks do not call DaData.

Before using DaData in a long live Radar run, run the targeted provider probe.
The normal test suite skips the live call; opt in explicitly when local keys are
present:

```bash
python -m pytest tests/test_dadata_provider.py -rs
```

PowerShell live probe:

```powershell
$env:POWER_WEB_OS_RUN_LIVE_DADATA_TESTS='1'; python -m pytest tests/test_dadata_provider.py -m live_dadata -rs
```

The live probe performs one bounded company lookup using
`POWER_WEB_OS_DADATA_TEST_QUERY` or `1651025328` by default. It should return at
least one company observation and must not print or persist DaData secrets.

Supported web modes are `auto`, `server_tools`, `plugin_web`, and `model_native`. `auto` tries OpenRouter server-side web search first and falls back to the OpenRouter web plugin if server tools are unsupported.

Commands:

```bash
python -m power_web_os.demo run-live-mini-icp-radar --dry-run-plan
python -m power_web_os.demo run-live-mini-icp-radar --live
python -m power_web_os.demo run-live-mini-icp-radar-persisted --live
```

`--dry-run-plan` does not call the network and does not create fake candidates. `--live` requires `OPENROUTER_API_KEY` and writes:

```text
demo/output/live_mini_icp_radar_run.json
frontend/public/demo/live_mini_icp_radar_run.json
```

The persisted command requires the Alembic schema and seeded Radar catalog. It
uses the same OpenRouter-backed workflow path, creates a `radar_runs` record,
stores the `icp_radar_live_run` snapshot in `radar_run_outputs`, and exports the
same JSON artifact paths for the current frontend fallback.

Live artifacts must never contain API keys, authorization headers, bearer
tokens, or raw provider dumps. Current live runs use explicit source
verification state: risky source-linked findings can remain reviewable instead
of vanishing, but they should not produce confident scores without stronger
evidence. If OpenRouter rejects the credentials or no usable sources are
returned, the frontend should show the live radar empty state rather than
fabricated candidates.

Source, retrieval, and score debugging now has a TDD-first hardening path before
broad quality benchmarking:

1. Source lifecycle visibility: dossier exposes `source_lifecycle` and
   `source_lifecycle_summary`, explaining how many sources were collected,
   parsed, verified, linked to candidate evidence, used in product, or
   discarded. Product `sources` still contains only evidence-bearing used
   sources.
2. Soft source verification and useful-result budgets: verification should
   preserve evidence-bearing sources with explicit risk state instead of
   silently losing useful sources because a site blocks `HEAD`/`GET`; discovery
   tasks that return no useful material should retry within bounded limits.
3. Criterion role inference and plan acceptance repair: implemented through
   `RadarDiscoveryPlanAcceptanceService`. Planner output may include criterion
   roles, source base, and application scope; missing roles are inferred,
   configured global sources applied to rule-scoped tasks are corrected, and
   multi-rule strategic steps are split before execution. Dossier/trace payloads
   expose accepted corrections and fallback metadata.
4. Run-level diagnostics and source lifecycle UI: dossier, journal, and
   technical trace should be reachable from the run itself even when there are
   no candidates, and candidate universe tables should show budget-limited,
   skipped, rejected, unknown, and signal-searched states.
5. Readable technical trace viewer: technical traces should be grouped by
   planning, discovery, gate, coverage, signal, normalization, scoring, and
   validation phases, with wrapped JSON, summaries, filters, and copy/raw
   controls.
6. Compact task prompts and retrieval plan contract: execution calls use compact
   task cards instead of repeated heavy Radar JSON; dossier/trace should
   show the accepted retrieval plan and compiled prompt.
7. DaData source provider and source registry: add a real structured
   company-data source behind a source-provider port before claiming discovery
   quality from web-only runs.
8. Web retrieval provider abstraction and Perplexity adapter: compare default
   OpenRouter retrieval and OpenRouter Perplexity-engine retrieval after
   prompts, budgets, and structured company sources are controlled.
9. Radar execution preflight and red tests: prove active definition wiring,
   source-provider selection, extraction schema, evidence-ref linking, and
   controlled failure states with fast fixtures before expensive live runs.
10. Score contract and quality smoke: recorded fixtures should prove that
   source-backed confirmed qualification and observed signals survive
   persistence/API/frontend mapping and produce nonzero scores before live
   multi-radar benchmarks are treated as meaningful.
11. Multi-radar benchmark: only after the planning and observability path can
   explain failures should real-model SIBUR, industry/region/revenue, and
   source-constrained discovery scenarios be used as quality evidence.

Complex LLM pipeline work must follow a TDD/preflight loop. Do not use a
30-minute full live Radar run as the first validation signal for planning,
retrieval, extraction, source-provider, evidence-linking, or scoring changes.
Add fast red/green tests first:

1. Static/config preflight: active persisted definition, runtime definition
   wiring, source ids, source-provider settings, and source-policy references.
2. Recorded pipeline fixtures: planner, retrieval, DaData/source registry,
   extraction, verification, retries, and known malformed provider outputs.
3. Targeted live probes: one bounded DaData/source-provider lookup, one web
   retrieval call, and one extraction-only schema check.
4. Full live run: final smoke or benchmark only after the cheaper layers are
   green, unless the run is explicitly marked exploratory.

Negative fixtures are required for provider outputs that are prose-first,
return dicts where lists are required, omit stable source refs, link evidence to
unknown refs, or return retrievable material that cannot be tied to candidate
evidence. These cases should become explicit diagnostic states such as
`extraction_schema_invalid` or `evidence_linking_failed`, not normal zero scores.
The runtime uses the same extraction gate as preflight: repairable shapes such
as one candidate object instead of a one-item list are recorded as
`extraction_repair_needed`, while unresolvable source refs remain hard
`evidence_linking_failed` diagnostics. If retrieved sources exist but extraction
cannot link them to candidate evidence, the run dossier must show extraction
issues and retrieved/analyzed source counts instead of looking like a clean
"nothing found" result.

Run the current Radar execution preflight before manual live testing:

```bash
python -m power_web_os.demo preflight-radar --radar-id toir-quick-live --json --show-runtime-config
```

The command reads the active persisted Radar definition from
`POWER_WEB_OS_DATABASE_URL` or `--database-url`, performs no network calls, and
does not create `radar_runs` or `radar_run_outputs`. It exits non-zero when
`ready_for_live_run=false`. The seeded `toir-quick-live` definition should no
longer fail `definition_runtime_mismatch`; if it does, persisted execution is
not using the same active definition payload as the worker. Important check
codes:

- `definition_runtime_mismatch`: persisted active definition and workflow
  runtime definition differ; this should be green for seeded active definitions.
- `source_base_not_executable`: source ids or source types cannot be resolved
  to executable source bases.
- `company_registry_provider_available`: a configured company registry source
  such as DaData has, or lacks, an available provider.
- `extraction_schema_invalid`: recorded provider output violates the expected
  extraction shape.
- `extraction_repair_needed`: provider output was accepted only after a safe
  shape/source-ref repair, such as prose cleanup or URL-to-source-ref
  reconciliation.
- `evidence_linking_failed`: candidate/finding evidence refs do not resolve to
  normalized sources.
- `invalid_zero_score_projection`: unsearched or invalid signal output would be
  shown as a normal searched-negative zero score.

Runtime config is part of the Radar execution contract. The preflight report
shows the effective, redacted settings for the current process: OpenRouter model
routing, web mode, retrieval provider/engine, DaData mode and credential
presence, source verification mode, budgets, database kind, Celery broker kind,
and a deterministic non-secret fingerprint. This is the first check before a
manual live run because it catches stale Docker/env mismatches before a long
worker job starts.

Adaptive checkpoint caps are part of that same runtime contract:

```text
POWER_WEB_OS_RADAR_MAX_CHECKPOINT_REVISIONS_PER_RUN=2
POWER_WEB_OS_RADAR_MAX_CHECKPOINT_RETRIES_PER_STAGE=1
```

They keep review checkpoints deterministic. They are persisted with checkpoint
decisions and enforced by the first adaptive recovery loop. The fast
fake/recorded tests prove:

- weak discovery can execute a bounded retry and then continue;
- source expansion creates a bounded allowed-source task, never a broad fallback;
- planner revision is called with compact checkpoint facts and the validated
  revision is applied;
- retry/revision limits stop as review-needed instead of continuing blindly;
- signal search starts only after the final pre-signal checkpoint returns
  `continue`.

The adaptive execution harness lives in `tests/test_radar_adaptive_execution.py`:

```bash
python -m pytest tests/test_radar_adaptive_execution.py -q
```

The expected result is a fully green suite. It runs without OpenRouter, DaData,
Redis, Celery, a database, or a local API server. It verifies weak-discovery
retry, allowed source expansion, required-source failures, compact
revision-style recovery, evidence-linking failures, high coverage risk,
retry/revision caps, budget exhaustion, and the rule that signal search starts
only after the final pre-signal checkpoint returns `continue`. Treat this suite
as the fast gate between static preflight/live probes and a long manual Radar
run.

After the offline gates are green, use the Radar smoke profile before a broad
live run. Smoke does not judge discovery quality. It proves that the live path
obeys external-call budgets and reaches a terminal diagnostic state without
expanding into dozens of provider calls.

```text
POWER_WEB_OS_RADAR_RUN_PROFILE=smoke
POWER_WEB_OS_RADAR_MAX_OPENROUTER_CALLS_PER_RUN=8
POWER_WEB_OS_RADAR_MAX_DADATA_LOOKUPS_PER_RUN=3
POWER_WEB_OS_RADAR_MAX_SOURCE_VERIFICATION_REQUESTS_PER_RUN=20
POWER_WEB_OS_RADAR_MAX_PROVIDER_RETRIES_PER_TASK=1
POWER_WEB_OS_RADAR_SMOKE_MAX_CANDIDATES=2
POWER_WEB_OS_RADAR_SMOKE_MAX_SIGNALS=1
```

If `POWER_WEB_OS_RADAR_RUN_PROFILE=smoke` is set and a specific cap is omitted,
the backend applies those smoke defaults. Explicit values, including `0`, win
over the defaults. Exhausted external actions are recorded as
`not_executed_budget_limited`; invalid provider responses can retry only while
`POWER_WEB_OS_RADAR_MAX_PROVIDER_RETRIES_PER_TASK` allows it. The dossier and
technical trace expose `run_profile`, `external_call_budget_counters`,
`external_call_budget_exhaustion_events`, and `provider_retry_records`.

Targeted live probes are opt-in and bounded. Use them only after static
preflight is readable:

```bash
python -m power_web_os.demo preflight-radar --radar-id toir-quick-live --json --show-runtime-config --live-probes --probe dadata
python -m power_web_os.demo preflight-radar --radar-id toir-quick-live --json --show-runtime-config --live-probes --probe openrouter-web
python -m power_web_os.demo preflight-radar --radar-id toir-quick-live --json --show-runtime-config --live-probes --probe openrouter-perplexity
python -m power_web_os.demo preflight-radar --radar-id toir-quick-live --json --show-runtime-config --live-probes --probe extraction-schema
```

The API exposes the current API-process config at:

```bash
curl http://127.0.0.1:8000/api/runtime-config
```

When a run is queued, the API config snapshot and fingerprint are stored in
`radar_runs.run_metadata`. When the worker starts the run, it stores its own
snapshot and fingerprint. If critical values differ, the run records
`runtime_config_mismatch` warnings in metadata and technical trace. The warning
is diagnostic in this slice: it does not fail the run automatically.

Frontend rendering for live radar results must go through the canonical ICP Radar UX contract. Treat `icp_radar_live_run` as a different data adapter, not as permission to create a separate live-only grid, side panel, table column set, preview, or detail surface. Runtime provider metadata belongs in the candidate `Journal` tab.

Candidate qualification results must use the shared qualification evidence contract before they reach the UI. Provider output can be sparse, but the backend normalizer must shape each Q-rule result into rule snapshot, operator, requirement level, source usages, source origin, trust/check policy, evidence findings, optional short excerpt, cross-validation, requirement evaluation, final assessment, and optional review decision. The candidate detail qualification tab renders that contract as a table-first review surface with expandable rows and browser-local approve/reject/correct decisions. Keep the collapsed row scan-first: code, rule, operator, assessment, source count, cross-validation, and local decision. In expanded rows, render evidence as cards that combine source ref/title/origin/trust with fact, excerpt, and why-it-matches text; do not duplicate a separate sources table there. Requirement level, evidence strength, cross-validation status, confidence, and recommended action belong inside the expanded `Requirement fit` section. Reject/correct decisions must require a comment. Do not render provider-specific raw Q1/Q2 rows directly.

Live signal results follow the same evidence-card rule, but they evaluate intent score rather than qualification fit. The backend normalizer may accept sparse provider output, but the frontend view model must see source usages, source-linked evidence findings, optional excerpt/excerpt type, cross-validation, and score evaluation when available, with controlled fallbacks when missing. The candidate detail signals tab must expand each signal into `Signal score evaluation` -> evidence cards -> human review. Do not render the old summary plus source-list shape as the main expanded signal content. Confirm/reject/stale/correct decisions reuse the browser-local signal validation overlay, and reject/stale/correct require comments.

Expected future domain objects:

```text
ICPProfile
RadarDefinition
RuleGroup
AtomicRule
SourceDefinition
SourcePolicy
IntentSignalDefinition
SignalObservation
SignalValidation
RadarScoringModel
RadarCandidate
RadarRun
```

`SourceDefinition.trust_level` and `SourceDefinition.usage_obligation` are
separate controls. Trust describes how much weight a source deserves when it is
used. Usage obligation describes whether the planner is allowed to skip it.
Supported obligations are `required`, `preferred`, `optional`, `fallback`,
`disabled`, `required_for_identity`, `required_for_coverage`, and
`required_for_signal`. The backend validates planner output against these
obligations before execution: required sources must appear in the matching
stage, preferred sources need a skip rationale, disabled sources are rejected,
and fallback sources cannot be used before required/preferred source decisions
are resolved. Inspect the result in the run dossier fields
`source_obligations`, `source_obligation_decisions`, and
`source_obligation_summary`.

In API-backed mode, Radar settings save the full active definition through
`PUT /api/radars/{radar_id}/definition`. The UI source editor exposes
`usage_obligation` per source in the global search base, so catalog seed values
are only defaults. Persisted worker execution and preflight read the updated
active definition, not hardcoded TOIR source modes. Presentation components do
not call the API directly; `RadarApiClient.updateRadarDefinition` is used from
the ICP Radar application hook.

Current catalog artifact:

```text
artifact_type = icp_radar_catalog
artifact_version = 0.6.5.2
radars[].radar_id
radars[].name
radars[].status
radars[].profile
radars[].summary
radars[].definition
radars[].artifact_path
```

Discovery and monitoring must stay separate. Discovery can be run once or imported manually because legal-entity structure changes slowly. Monitoring should run repeatedly and support incremental mode through evidence fingerprints so previously seen facts are not scored as new signals.

Signal validation is a first-class domain concern. A user must be able to:

- confirm a found signal;
- correct its criterion, strength, confidence, summary, or evidence mapping;
- reject it as wrong or distorted;
- mark it stale when it is no longer actionable.

Validated signals feed the final score. Rejected and stale signals must reduce or remove their scoring contribution while preserving evidence and audit history. The score explanation must show raw observations, validation decisions, and the resulting fit/intent/tier contribution.

The current demo stores validation decisions in browser-local state under:

```text
power-web-os-icp-radar-signal-validation
```

The decision key is `radar_id + account_id + signal_code`. The decision payload contains status, original score, adjusted score, confidence override, corrected summary, selected evidence refs, comment, and `reviewed_at`. The frontend applies this overlay with the same deterministic semantics as `ICPRadarValidationScorer`: `unreviewed` and `confirmed` keep the original score, `corrected` uses the adjusted score, and `rejected` / `stale` contribute `0`. Generated JSON artifacts are not mutated by local validation.

## Access Planning Workflow

The first product loop is:

```text
demo/sample_portfolio.json
-> AccountRadar
-> AccessPlanningWorkflow per account
-> demo/output/account_radar.json
-> frontend/public/demo/account_radar.json
-> frontend/public/demo/access_plans/{account_id}.json
-> Vite demo UI
```

ICP Radar demo flow:

```text
demo/fixtures/icp_radar/sibur_icp_pass1.xlsx
-> ICPRadarXlsxImport
-> demo/output/icp_radar.json
-> frontend/public/demo/icp_radar.json
-> ICP Radar screen
```

The single-account debug path remains available:

```bash
python -m power_web_os.demo generate-access-plan
```

Portfolio fixture entries use the existing `{ account, playbook }` shape with a small `stage` field for Account Radar display.

Access Plan artifacts include a non-breaking `power_web_board` field:

```text
power_web_board.summary
power_web_board.nodes[]
power_web_board.edges[]
power_web_board.route_path[]
```

The board read model is deterministic and belongs to `src/power_web_os/board.py`. It should stay presentation-friendly but source-of-truth-neutral: do not put graph database behavior, editing state, CRM state, or live source extraction in this builder.

Access Plan artifacts also include a non-breaking `playbook_analysis` field:

```text
playbook_analysis.contract_version
playbook_analysis.current
playbook_analysis.variants[]
*.route_decisions[]
*.route_preview.routes[]
```

The playbook read model is deterministic and belongs to `src/power_web_os/playbook_analysis.py`. It explains allowed routes, blocked channels, available assets, review rules, policy decisions, and generated route previews. The `no_partner_motion` variant is generated at artifact-build time by disabling `partner_intro` and partner-case assets, then running the Python planner again. Frontend code must render this payload; it must not duplicate planner scoring or policy logic.

Do not put CRM/source connector logic directly inside domain classes. Add ports/tools and keep connector calls auditable.

## Frontend Demo

The frontend is a local React + TypeScript + Vite app in `frontend/`.

Current structure:

```text
frontend/src/App.tsx                  App state and artifact loading
frontend/src/components/              Token-based UI primitives
frontend/src/features/                Feature modules with owned screens, models, and CSS
frontend/src/i18n.ts                  Locale initialization
frontend/src/i18n/                    EN/RU UI resource modules
frontend/src/demoLocalization.ts      Presentation-layer localization for deterministic demo data
frontend/src/layout/                  Power Web OS shell, sidebar, top bar
frontend/src/screens/                 Product screens and planned placeholders
frontend/src/styles.css               App shell and shared primitive styling
```

Rules:

- Import `ui-design-system/colors_and_type.css`.
- Use `ui-design-system/app-prototype/AppShell.jsx` for product shell structure.
- Use the relevant `ui-design-system/app-prototype/*Screen.jsx` file before implementing a screen.
- Follow the frontend workspace UX ADR family, starting with `2026-06-12-frontend-workspace-ux-principles.md`, for bounded SPA behavior, table-first dense data, sticky identity, evidence-first drilldown, explicit settings state, local draft boundaries, i18n, responsive constraints, and the canonical ICP Radar UX contract.
- Use `lucide-react` for icons.
- Keep UI copy sentence case, with uppercase only for mono eyebrow labels.
- Add visible UI strings through `frontend/src/i18n/en.ts` and `frontend/src/i18n/ru.ts`; keep English/Russian resources synchronized.
- Keep the app shell viewport-bounded; `body` should not be the normal scroll container for product screens.
- Put scrolling inside workspace panes and dense table/card wrappers.
- Use `min-width: 0`, wrapping, ellipsis, or owned horizontal scroll so text never overlaps neighboring columns.
- Load the portfolio artifact from `/demo/account_radar.json`.
- Load selected-account plans from `/demo/access_plans/{account_id}.json`.
- Render the selected account's Power Web Lite board from `artifact.power_web_board` on `Account Map`.
- Render the selected account's playbook analysis from `artifact.playbook_analysis` on `Playbook`.
- Load the ICP Radar artifact from `/demo/icp_radar.json`.
- Keep `ICP Radar` as a separate upstream screen; do not merge it with `Accounts`.
- Treat the ICP Radar catalog as list-first: one configured radar per wide row with stable columns for identity, status, metrics, run mode, and action, not a three-column card grid or floating metric layout that truncates names and counts on laptop screens.
- Treat the main `ICP Radar` screen as a table-first workspace:
  - account/company identity belongs in the first sticky column;
  - horizontal scroll is owned by the table wrapper;
  - the sticky column must keep its own background and z-index so scrolled columns do not bleed through;
  - candidate row preview expands inline under the selected row and has one bounded scroll area for the whole preview;
  - expanded preview content is anchored to the visible table wrapper, not to the horizontally scrolled column grid;
  - preview blocks start at the left of the visible workspace and must not require horizontal scrolling on laptop widths;
  - preview actions sit below the content blocks instead of using a separate left rail;
  - do not put nested scroll containers inside the preview lists;
  - preview is intentionally short: top-5 evidence refs, top-5 criteria, main signal, and short recommendation;
  - score/tier values stay in the table row and should not be repeated inside the preview;
  - full candidate evidence/criteria work belongs on a separate candidate detail screen with breadcrumbs back to `ICP Radar`;
  - the candidate detail view keeps a compact sticky header so account identity remains visible while criteria scroll.
- Apply that same table-preview-detail pattern to every ICP Radar shortlist source, including live/provider-backed radars:
  - map each source into a canonical radar/candidate view model before rendering;
  - use the canonical shortlist columns: company, total, fit, intent, trigger, tier, evidence, action;
  - unsupported score slots render as `—`, not as a changed table shape;
  - preview always has four blocks: summary, tier, qualification, signals;
  - preview never renders source lists or runtime/provider metadata;
  - detail uses tabs: overview, qualification, signals, sources, journal, and optional API-backed trace;
  - product runtime context, queries, warnings, and source usage render in the journal/dossier tab;
  - sanitized provider request/response and pipeline debug payloads render only in the dev/admin trace tab;
  - do not add provider-specific split grids, custom shortlist columns, custom previews, or always-visible side detail panels.
- Treat candidate signal validation as table-first inside the detail view:
  - C1-C20 initially render as compact rows, not fully expanded evidence cards;
  - filter by signal validation status before drilling into detail;
  - sort by score, status, or confidence;
  - expand one signal row at a time for rationale, facts, source refs, and validation controls;
  - local confirm/correct/reject/stale controls must be clearly labelled as browser-local demo state until durable persistence exists.
- Keep `ICP Radar` navigation local to `ICPRadarScreen` until a broader routing need appears:
  - `expandedCandidateId` owns inline preview state;
  - `detailCandidateId` owns the read-only candidate detail view;
  - do not introduce React Router only for ICP Radar candidate drilldown.
- Treat `Take into work` as planned until Slice 0.6.4 implements the handoff.
- Keep unfinished navigation entries visible only as planned placeholders; do not fake unavailable functionality.

The frontend default locale is `en`. The supported locales are `en` and `ru`, and the selected locale is stored in browser `localStorage`. UI chrome is localized through `i18n.ts`; visible deterministic artifact values such as stages, owners, route titles, rationale, risks, state changes, signal summaries, and missing-role labels are localized in `demoLocalization.ts`. Keep raw source refs, IDs, company names, and person names as artifact data unless a slice explicitly changes that policy.

## Test Commands

```bash
python -m pytest
python -m power_web_os.demo generate-icp-radar
python -m power_web_os.demo generate-icp-radar-catalog
python -m power_web_os.demo generate-account-radar
python -m power_web_os.demo generate-access-plan
python demo/run_demo.py generate-icp-radar
python demo/run_demo.py generate-icp-radar-catalog
python demo/run_demo.py generate-account-radar
python demo/run_demo.py generate-access-plan
npm --prefix ./frontend run build
npm --prefix ./frontend run visual:smoke
npm --prefix ./frontend run settings:toggle-smoke
```

## Visual Smoke

Use Playwright visual smoke whenever frontend layout, shell navigation, user-facing screens, or documentation screenshots change.

```bash
python -m power_web_os.demo generate-icp-radar
python -m power_web_os.demo generate-icp-radar-catalog
python -m power_web_os.demo generate-account-radar
npm --prefix ./frontend run visual:smoke
```

The script starts Vite through the Vite Node API, opens Chromium, captures key workspace screens at `1280x720` and `1366x768`, and writes screenshots to `docs/qa/screenshots/visual-smoke/`.

The screenshot set is smoke evidence, not pixel-perfect regression. It should still be refreshed when the documented UI changes.

Use the Settings toggle smoke when changing ICP Radar Settings, switches, local draft state, or editor block layout:

```bash
npm --prefix ./frontend run settings:toggle-smoke
```

The script starts Vite, opens the first ICP Radar in Russian locale, verifies the global-search switch through save and reload, injects a legacy partial localStorage override, enters every editable Settings block, clicks each visible switch twice, and fails on browser errors, an under-rendered workspace, or any viewport drift where `.app-shell` leaves the visible frame.

## GitHub Wiki Publishing

The GitHub Wiki is generated from repository docs and QA screenshots.

Build locally without pushing:

```bash
python scripts/publish_github_wiki.py --dry-run
```

Publish to GitHub Wiki:

```bash
python scripts/publish_github_wiki.py
```

The script builds:

- `Home.md`
- `_Sidebar.md`
- `User-Guide.md`
- `Developer-Guide.md`
- `Architecture.md`
- `Demo.md`
- `Roadmap.md`
- `QA-Visual-Smoke.md`
- `assets/screenshots/visual-smoke/*.png`

Wiki screenshot pages are curated through the screenshot walkthrough manifest in `scripts/publish_github_wiki.py`. Do not generate user-facing headings directly from screenshot filenames. When adding or replacing a documented screen:

- add or update the manifest item with a human title, short explanation, and both viewport image paths;
- add the same user-facing walkthrough context to `docs/user/USER_GUIDE.md`;
- keep `docs/qa/README.md` focused on reproducible QA assets and regeneration commands;
- run `python scripts/publish_github_wiki.py --dry-run` and inspect `.wiki-build/User-Guide.md`, `.wiki-build/Home.md`, and `.wiki-build/QA-Visual-Smoke.md` before publishing.

If GitHub has Wiki enabled but the wiki git repository does not exist yet, create one page in the GitHub Wiki web UI once, then rerun the publisher.

## Documentation Rules

Update `ROADMAP.md`, architecture docs, demo docs, and user docs in the same slice when behavior changes.
