# System Architecture Overview

## Product Context

Power Web OS is a strategy layer for complex B2B sales. It runs ABM-oriented ICP Radars to discover and qualify target accounts, builds a dynamic influence map around accepted accounts, applies customer-specific sales playbook rules, and recommends explainable access routes.

The product must use `mudrezzz/langgraph-document-ai-platform` for the AI-agent workflow layer.

## Architectural Goals

- Keep recommendations white-box and evidence-backed.
- Keep ICP/account selection explicit, configurable, and aligned with ABM profile strategy.
- Keep CRM as system of record and Power Web OS as system of strategy.
- Keep humans in control of sensitive commercial actions.
- Support async batch analysis for 50-100 account MVP pilots.
- Preserve source provenance, route explanations, task audit, and review history.

## Current Product Perimeter

The current baseline has:

- domain entities for account access planning;
- deterministic Access Planner;
- deterministic ICP Radar XLSX fixture import read model;
- deterministic Account Radar accepted-portfolio read model for the current demo;
- deterministic Power Web Board selected-account read model;
- deterministic Playbook Analysis selected-account read model;
- `AccessPlanningWorkflow` with optional `langgraph-dai` integration and local fallback;
- FastAPI backend boundary with health, Radar catalog, Radar run, and Radar candidate contracts;
- SQLAlchemy/Alembic persistence foundation for Radar catalog, Radar definitions, durable Radar run state, and persisted live Radar output snapshots;
- generated ICP Radar, Account Radar, and Access Plan artifacts;
- React TypeScript Vite demo inside the Power Web OS workspace shell using `ui-design-system`;
- pytest baseline and frontend build check.

## Major Components

| Component | Responsibility | Owned data / behavior | Depends on |
|---|---|---|---|
| Web UI / BFF | Product screens and user workflow | Account workspace, review queue, demo UX | Product API |
| Frontend demo | Local product shell with active ICP Radar, Accounts, Access Plans, Account Map, and Playbook screens | Reads generated ICP Radar, Account Radar, and Access Plan artifacts and renders planned workspace placeholders | Vite, design system |
| ICP Radar | Configurable ABM account-search and signal-monitoring layer | ICP profile, structured radar definition, source policies, qualification rule groups, intent signals, scoring model, validation report, candidate queue; current demo imports XLSX fixture into a deterministic read model | Source connectors, evidence layer, domain scoring |
| Account Radar | Deterministic portfolio read model | Portfolio score, top reason, best route, owner, review status | Domain services, Access Plan artifacts |
| Power Web Board | Deterministic selected-account read model | Board summary, people/partner/missing nodes, account edges, highlighted route path | Account, Access Plan artifact |
| Playbook Analysis | Deterministic selected-account read model | Current and what-if playbook snapshots, route policy decisions, review policy, route previews | Account, Playbook, Access Plan artifact |
| Product API | External HTTP boundary | Auth, request validation, task start/status | Application services |
| Power Web Domain | Sales domain model and policies | Account, Signal, Evidence, PowerWebRole, Playbook, AccessPlan | None |
| Agent Workflows | AI orchestration and audit | LangGraph state, node events, HITL checkpoints | `langgraph-dai`, domain services |
| Evidence Layer | Source ingestion and retrieval | Canonical docs, evidence packs, source refs | `langgraph-dai`, pgvector |
| Connectors / Tools | CRM and source integrations | Tool calls, retry/idempotency/audit | Tool executor, external systems |
| Persistence | Product state and read models | Postgres tables, vectors, artifacts | PostgreSQL, pgvector |

## Dependency Direction

```text
UI / API
  -> Application services
    -> Agent workflows
      -> Domain model
      -> Ports / tools
        -> Infrastructure adapters
```

Domain logic must not depend on transport, database, UI, or vendor APIs.

## Backend API And Persistence Direction

The backend is now a first-class architectural track, developed in parallel with
the product roadmap. It should gradually move durable state out of generated
JSON artifacts and browser-local overlays without stopping frontend/product
learning loops.

Chosen stack:

- Python application backend.
- FastAPI for HTTP and OpenAPI contracts.
- Pydantic for transport and application DTOs.
- PostgreSQL for durable product state.
- SQLAlchemy 2.x for persistence mapping.
- Alembic for migrations.
- `pgvector` later for evidence retrieval.
- `langgraph-dai` for agent workflow orchestration.

The first backend slice exposed only a health boundary. The backend now adds DB
settings, sessions, Alembic, Radar catalog/run repositories, persisted live
Radar output snapshots, and FastAPI contracts for Radar catalog, run state, and
candidate snapshots. It also has a Celery/Redis job adapter for long-running
Radar execution, durable human review decisions for live Radar findings, an
append-only structured run journal for reasoning/audit summaries, an append-only
sanitized admin technical trace for developer inspection, and a
qualification-first live Radar execution plan with compact retrieval task cards
and hierarchical execution budgets.
The frontend now exposes run-level diagnostics for queued, running, completed,
failed, and zero-candidate live Radar runs, including candidate-universe and
source-lifecycle inspection without selecting a candidate. It also renders the
sanitized developer/admin technical trace as a readable phase-grouped viewer
with search, filters, copyable sections, and collapsed raw JSON. Backend/frontend
slices should continue in this order:

1. structured company-source registry with DaData as the first real provider;
2. provider-neutral web retrieval abstraction with OpenRouter/Perplexity-style adapters;
3. multi-radar discovery benchmark over the qualification-first, coverage-enforced workflow pipeline;
4. normalized candidate/evidence query tables when API usage needs them;
5. production schedule/cadence controls.

JSON artifacts remain useful as demo exports and offline fallback, but they are
not the long-term source of truth. The frontend now prefers the Radar API for
catalog, live run, candidates, and live review decisions when the backend is
available, while browser `localStorage` overlays remain fixture/offline fallback
state.

Backend ownership boundaries:

- HTTP routes validate requests and return DTOs.
- Application services orchestrate use cases.
- Domain services own scoring, validation, review semantics, and evidence rules.
- Repository interfaces isolate application/domain code from SQLAlchemy.
- Infrastructure adapters own database, provider, and external API calls.

The current persistence slice stores `radars`, `radar_definitions`,
`radar_runs`, `radar_run_outputs`, `radar_review_decisions`, and
`radar_run_events`, and `radar_run_technical_traces`.
`radar_run_outputs` is a JSON snapshot table for the current live Radar artifact
sections. `radar_review_decisions` is mutable current review state for one
qualification or signal subject; it does not mutate the output snapshot and is
not the append-only run journal. `radar_run_events` stores ordered structured
audit events for lifecycle, planning, source collection, candidate extraction,
finding evaluation, score explanation, validation warnings, and self-check
summaries. Local regression uses SQLite for migration and repository smoke
tests, while schema and runtime configuration remain PostgreSQL-ready through
SQLAlchemy/Alembic and `POWER_WEB_OS_DATABASE_URL`.

LLM/search outputs must be persisted as reviewable evidence and run records, not
as authoritative final truth. Human review decisions are first-class product
records that explain how scores and handoff eligibility changed.

Backend module ownership is guarded like the frontend feature boundary:

| Backend boundary | Responsibility | Must not own |
|---|---|---|
| `api` | FastAPI app factory, routes, transport DTOs, dependency wiring | SQLAlchemy queries, scoring, provider calls, job execution |
| `application` | Use cases, transactions, port interfaces, orchestration | FastAPI request handling, SQLAlchemy mapping details, provider SDK details |
| `domain` | Business rules, scoring, validation, review semantics, handoff rules | FastAPI, SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs |
| `persistence` | SQLAlchemy models, sessions, migrations, repository implementations | FastAPI routes, domain decisions, provider calls |
| `integrations` | OpenRouter/source/CRM adapters and typed external observations | Candidate state decisions, final truth, persistence transactions |
| `workflows` | LangGraph workflow state, node wrappers, orchestration audit | Domain scoring hidden inside workflow wrappers, SQLAlchemy queries |
| `jobs` | Worker tasks and scheduler entrypoints | Business rules, provider normalization, persistence queries |

The backend dependency direction is:

```text
API / CLI / workers / scheduler
  -> application services
    -> domain services + ports
      -> persistence / integrations / job adapters
```

Application services should depend on repository, queue, executor, scheduler,
and provider ports. Infrastructure adapters implement those ports. This keeps
FastAPI, SQLAlchemy, Celery, Redis, and provider SDKs out of domain code.

Long-running Radar execution is designed around durable run state first.
`radar_runs` records should carry status, timestamps, idempotency key,
correlation id, and error metadata. Celery with Redis implements the queue
adapter, but Postgres remains the source of truth for run status and audit.
FastAPI `BackgroundTasks` is not the production execution model for Radar runs
because those jobs are long, retryable, scheduled, and must survive process
restarts.

The first Radar API exposes persisted catalog, run, and candidate snapshot data.
`POST /api/radars/{radar_id}/runs` creates a queued durable run and sends only
`run_id` through Celery. Worker execution loads the run, updates
queued/running/completed/failed state, persists `radar_run_outputs`, and leaves
Celery result state outside the product contract. Clients observe progress by
polling `GET /api/radar-runs/{run_id}` and read candidates after completion.
Review endpoints save/reset current qualification and signal decisions for
existing snapshot findings, and candidate DTOs overlay those decisions without
rewriting `radar_run_outputs`.

Live Radar execution is structure-first, qualification-first, and
pipeline-shaped. The application service owns explicit provider-neutral phases:
planning, provider collection, source normalization, candidate extraction,
candidate evaluation, validation, and artifact shaping. Planning compiles a
generic `RadarExecutionPlan` from the Radar definition. It discovers the initial
candidate universe, applies qualification gates sequentially, and runs signal
searches only for candidates not rejected by required qualification rules. The
workflows layer maps optional LangGraph node names to those phases and may add
runtime metadata, but it does not own provider calls, SQLAlchemy persistence,
scoring semantics, or review decisions. Provider adapters receive bounded tasks;
OpenRouter qualification prompts do not include intent signals, and signal
prompts include only one signal and the current candidate scope. Pipeline phases
emit structured event summaries that are persisted through `RadarRunJournal`;
older artifact-derived journal mapping remains only a compatibility fallback
for existing snapshots.

Discovery strategy itself is now a bounded planning loop. The application layer
builds `RadarDiscoveryPlanningInput` from the active definition, qualification
rules, global/local source policy, task context, and run limits. A planner port
may ask OpenRouter for a structured JSON discovery plan, but the backend
validator accepts or rejects it. Accepted plans must respect configured source
policy, select or explicitly skip configured source bases with rationale, keep
qualification discovery separate from signals, and stay within run step limits.
If the first plan is invalid, one sanitized revision attempt is allowed; an
invalid revised plan fails clearly rather than falling back to a broad search.
This keeps the logic generic for holding-contour, industry/region/revenue, and
registry/source-constrained radars without hardcoding the SIBUR case.

Planning acceptance now separates criterion roles from executable search tasks.
Qualification criteria can have different roles: `upstream_discovery` criteria
define the candidate universe, `downstream_gate` criteria filter known
candidates, enrichment criteria add facts such as revenue/region/industry, and
exclusion criteria remove candidates. The LLM may propose those roles, but
`RadarDiscoveryPlanAcceptanceService` infers missing roles, applies safe repairs,
and keeps backend validation authoritative. Source configuration scope is also
separate from application scope: a source configured globally can be applied to
a rule-scoped or candidate-scoped task without being reclassified as a local
source. Safe source-scope mismatches are normalized with explicit corrections
instead of forcing a fallback plan. Hard source-policy violations, signal search
inside discovery, and invalid rule references still force revision or fallback.

Candidate universe execution is now iterative. Accepted discovery plans may
contain executable `coverage_check` stages. The application service runs initial
candidate discovery, applies qualification gates, executes coverage checks,
merges source-backed gap candidates, re-runs qualification gates for new
candidates, and freezes the candidate universe before signal search. Signal
tasks are scoped to that frozen universe; any new entity mentioned during signal
search is stored as a `candidate_universe_gap` for dossier/trace inspection, not
as a candidate. Runtime defaults cap discovery at two iterations and fifty
candidates until benchmark data justifies different limits.
`POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT` remains a compatibility safety
limit for backend-controlled provider/search tasks. The repository
`.env.example` uses a smoke-safe value of `1`; the code fallback remains `20`
when no environment value is configured.

Execution budgets are hierarchical. The backend can cap total run tasks,
discovery tasks per qualification rule, gate tasks per candidate and rule, and
signal tasks per candidate and signal. Budget decisions are made in the
application executor before provider calls. A candidate or signal that was not
searched because a budget was exhausted is marked as `not_searched_*`, not as a
negative observation. `not_observed` means the relevant bounded search actually
ran and found no supporting evidence.

OpenRouter model routing is role-specific. `OPENROUTER_MODEL` is the fast
default for simple bounded tasks such as signal checks.
`OPENROUTER_ADVANCED_MODEL` is the shared advanced fallback, while
`OPENROUTER_PLANNER_MODEL` and `OPENROUTER_EXTRACTOR_MODEL` route discovery
planning and discovery/qualification/coverage extraction respectively. The
fallback order is explicit constructor argument, specific environment variable,
advanced model for planner/extractor, then default model.

Source visibility is split by audience. Product APIs and dossier source lists
use only evidence-bearing `used_sources`: sources used for candidate identity,
qualification evidence, signal evidence, validation warnings, or score
rationale. Sources analyzed but not used stay in execution metadata and the
sanitized technical trace with reasons such as duplicate, irrelevant,
policy-skipped, insufficient evidence, unreachable, or not used by a candidate.
The dossier exposes this as `source_lifecycle` and
`source_lifecycle_summary`: collected/parsed/reachable/linked/used/discarded
states with reason counts, so a `0` product-source run is explainable without
raw trace inspection.

Live Radar source verification is stateful rather than binary. Many useful
business sites block `HEAD` requests, time out, redirect inconsistently, or
return transient 404s. In `soft` verification mode, source-linked candidates
remain reviewable with `unverified_url`, `blocked`, `timeout`, or similar risk
state instead of being deleted. In `strict` mode, currently reachable URLs are
required before a source can support a candidate. In `off` mode, HTTP
reachability checks are skipped and sources are marked `not_checked`.
Qualification and signal findings linked only to risky sources are downgraded
to weak/unclear review-needed evidence and do not produce confident scores.
Discovery and coverage tasks also use useful-result budgets; if a bounded task
returns too few useful sources or candidates, the backend may retry within the
configured retry limit and records the retry in execution metadata and trace.

Web search is being separated into a managed retrieval pipeline. The application
layer should own task planning, source policy, useful-result budgets, retry
decisions, verification semantics, evidence linking, candidate status, and
scoring. Provider adapters in `integrations` execute bounded retrieval or
extraction tasks and return structured retrieval/source/citation material. This
keeps OpenRouter, Perplexity, or later search providers interchangeable without
letting provider-specific behavior become domain policy.

Prompt construction follows the same separation. Planner prompts may receive the
rich Radar definition, source policy, criterion-role context, and run limits
because they are responsible for proposing strategy. Bounded execution prompts
now receive compact task cards: current task type, candidate/rule/signal
scope, selected source policy, expected evidence, and a concise response
contract. They do not repeatedly include the whole Radar artifact, a
duplicated one-query search plan, or verbose schemas that do not change per
task. The durable retrieval plan and technical trace should make the compiled
task card and provider prompt inspectable without exposing secrets or raw hidden
chain-of-thought.

Structured company-data sources are separate from open web retrieval. DaData is
the planned first provider in this class because its MCP/API surface is designed
to give AI agents fresh company and address data, including organization lookup
by INN/OGRN, official company facts, address data, domain/email ownership, and
related company facts. Radar should use such sources for entity resolution and
company attributes, while web retrieval remains responsible for open evidence,
current events, and intent signals. Source adapters live in `integrations` behind
application ports; Radar definitions and source policies decide whether a
provider can be used for a rule, but provider SDK/MCP details do not leak into
domain scoring or API routes.

`GET /api/radar-runs/{run_id}/journal` returns ordered structured audit events.
The journal is not raw hidden chain-of-thought. Application services reject
payload keys such as `chain_of_thought`, `hidden_reasoning`, and
`internal_thoughts`; supported payloads are product-facing plans, observations,
tool/source outcomes, score rationale summaries, warnings, evidence refs, and
self-check summaries.

`GET /api/radar-runs/{run_id}/dossier` is the product inspection projection for
a run. It composes existing run state, active definition summary, persisted
output snapshot, source usage links, validation issues, review overlay counts,
and non-debug journal events into a readable dossier. Queued, running, and
failed runs can return a partial dossier with `output_state`; the candidates
endpoint still returns `409` until output exists. The dossier is intentionally
not a technical trace. For completed API-backed runs, it also exposes the
accepted discovery plan, selected/skipped source-base decisions, coverage
summary, candidate universe lifecycle, executed coverage checks, unresolved
candidate gaps, and used/analyzed/skipped source counts so users can inspect why
the Radar searched the way it did.

`GET /api/radar-runs/{run_id}/technical-trace` is the developer/admin
inspection projection. It reads append-only sanitized traces for pipeline
inputs/outputs, provider requests/responses/errors, normalization results, and
validation results. Trace payloads are redacted before persistence: secret-like
keys/values are masked, long strings are capped with a redaction report, and raw
hidden reasoning keys such as `chain_of_thought`, `hidden_reasoning`, and
`internal_thoughts` are rejected. The trace tab is visible in local/dev UI now
and should be authorization-gated later.

The frontend API adapter is a thin client boundary. `frontend/src/api/` owns
transport and error normalization, `frontend/src/features/icp-radar/adapters/`
maps API DTOs into the existing Radar view contracts, and
`frontend/src/features/icp-radar/application/` owns backend mode, queued run
polling, fallback selection, and review mutations. Presentation components show
run controls, status, run-level diagnostics, product dossier sections, journal
events, and the dev/admin trace tab, but do not call `fetch` or own persistence.

Architecture contract tests enforce these rules. Existing large legacy modules
are temporary decomposition follow-ups and not examples for new backend work:
`icp_radar.py`, `icp_radar_catalog.py`, and `icp_radar_xlsx.py`.

Backend onboarding map:

| Layer | First local doc | Current implementation files | Validation |
|---|---|---|---|
| `application` | `src/power_web_os/application/README.md` | records, ports, catalog seed mapping, live Radar service/normalization | architecture contract tests |
| `integrations` | `src/power_web_os/integrations/README.md` | OpenRouter live Radar adapter and recorded provider | live Radar tests, architecture contract tests |
| `workflows` | `src/power_web_os/workflows/README.md` | optional `langgraph-dai` wrappers and fallback workflow runtime | live Radar tests, architecture contract tests |
| `persistence` | `src/power_web_os/persistence/README.md` | SQLAlchemy models, sessions, repositories, Alembic migrations | `tests/test_radar_persistence.py` |
| `api` | `src/power_web_os/api/README.md` | FastAPI app factory, health routes, Radar routes, DTOs, dependency wiring | `tests/test_backend_api.py` |
| `jobs` | `src/power_web_os/jobs/README.md` | Celery app, Radar queue adapter, worker task, scheduler adapter | `tests/test_radar_jobs.py`, architecture contract tests |

New backend boundaries should include local developer-facing README guidance and
module docstrings for non-obvious ownership. SAO remains the high-level map;
local README files explain how to extend a layer safely.

## Frontend Module Boundaries

The React frontend follows the same boundary rule as the Python domain: a screen should not become a god object. Once a product area contains its own state model, adapters, tables, previews, settings, and review controls, it must move into `frontend/src/features/<feature>/`.

`frontend/src/screens/ICPRadarScreen.tsx` is now a thin wrapper. The ICP Radar feature owns:

- screen orchestration through a small feature entrypoint;
- application hooks for local navigation state, draft overlays, API-backed live runs, signal validation, and qualification review;
- fixture, API-backed live, JSON-backed live, and empty radar adapters;
- canonical radar and candidate view-model contracts;
- canonical shortlist, preview, and detail views;
- C1-C20 signal evidence and validation review;
- block-editable radar settings;
- pure domain helpers for score normalization, status/tone mapping, and review decisions.

The Settings editor is lazy-loaded so the default catalog/shortlist path does not pull the whole editor into the initial JavaScript chunk. Contract tests guard this boundary and fail if ICP Radar collapses back into one monolithic screen file.

ICP Radar CSS is owned by `frontend/src/features/icp-radar/icpRadar.css` as a small import entrypoint plus surface-specific modules under `frontend/src/features/icp-radar/styles/`. Global `frontend/src/styles.css` remains the app shell and shared primitive stylesheet. Runtime i18n initialization is separated from EN/RU resource modules. ICP Radar model helpers are also split by role: constants/types, validation scoring, radar metadata, live-radar helpers, and settings definition helpers.

The canonical ICP Radar UI is split by interaction surface: fixture/live shortlist modules own table scan and inline preview, fixture/live detail modules own tabbed evidence review, settings modules own block-level editing, and the feature entrypoint only assembles the current application state into the right surface. React stays functional; OOP principles are applied through module ownership, typed contracts, adapters, hooks, and pure domain services rather than class-component inheritance.

The local feature onboarding guide at `frontend/src/features/icp-radar/README.md` is the first stop for ICP Radar frontend work. It documents the data flow from raw artifacts through adapters and canonical view models into application hooks and UI surfaces, plus the checklist for adding a new radar type without creating a new screen-specific UX.

## Main Data Flow

Target ICP Radar flow:

```text
ICP profile
  -> account discovery rules
  -> account universe / legal entities
  -> signal monitoring runs
  -> evidence-backed signal observations
  -> human signal validation
  -> transparent ICP score and tier
  -> radar candidate queue
  -> take into work
  -> Power Web discovery
```

Current demo ICP Radar flow:

```text
demo/fixtures/icp_radar/sibur_icp_pass1.xlsx
  -> ICPRadarXlsxImport
  -> deterministic imported workbook score fields
  -> structured radar definition with fit / intent / tier configuration
  -> demo/output/icp_radar.json
  -> frontend/public/demo/icp_radar.json
  -> ICP Radar screen
```

```text
Target accounts
  -> synthetic portfolio fixture
  -> account radar
  -> access planning workflow per account
  -> account radar artifact + access plan artifacts
  -> power web board data inside each access plan artifact
  -> playbook analysis data inside each access plan artifact
  -> local frontend workspace shell
  -> ICP Radar screen
  -> Accounts screen
  -> selected Access Plans screen / Account Map screen / Playbook screen
```

Target production-oriented flow:

```text
ICP profile / radar definition
  -> account discovery
  -> source collection and monitoring
  -> canonical ingestion / indexing
  -> signal extraction and validation
  -> ICP score / candidate decision
  -> Power Web draft
  -> playbook rule evaluation
  -> access route generation
  -> compliance / HITL review
  -> CRM task export
  -> outcome feedback
  -> Power Web state update
```

## ICP Radar Boundary

An ICP Radar is not the Power Web itself. It is the ABM funnel layer that decides which accounts are worth taking into work for a specific product and ICP profile.

An ICP Radar owns:

- `RadarDefinition`: executable radar configuration with metadata, global search policy, account qualification rules, intent signals, monitoring policy, scoring model, and validation report.
- `SourceDefinition` and `SourcePolicy`: typed source/API/MCP/search/manual-dataset references and the logic for how rules or signals can use them.
- `RuleGroup` and `AtomicRule`: stable legal-entity qualification rules, such as holding membership, industry, revenue, asset type, and whether buying decisions are likely made independently. Rules are description-first for users; optional generated technical fields may support future agent execution.
- `IntentSignalDefinition`: configurable interest signals, such as TOiR/EAM, predictive diagnostics, tenders, hiring, modernization, incidents, import substitution, or ESG/safety, each with detection rules and a `0/1/2` scoring rubric.
- `RadarScoringModel`: fit model, intent model, tier model, formula preset, optional custom formula, tier thresholds, and confidence penalties.
- `RadarDefinitionValidator`: conservative structural validation for required fields, duplicate ids, source-policy misuse, `NOT` misuse, simple numeric contradictions, and invalid custom formula references.

Older conceptual names such as account discovery rules and signal criteria map into the structured `RuleGroup` / `AtomicRule` and `IntentSignalDefinition` contracts. Qualification filters and intent signals are intentionally separate domain concepts.

- `ICPProfile`: product, target industries, company-size thresholds, geography, exclusions, and qualification assumptions.
- `RadarDefinition`: search scope, sources, run cadence, full/incremental mode, and radar-specific overrides.
- `AccountDiscoveryRule`: stable legal-entity discovery and filtering rules, such as revenue, holding membership, asset type, and whether buying decisions are likely made independently.
- `SignalCriterion`: configurable signal definitions, such as ТОиР/EAM, predictive diagnostics, tenders, hiring, modernization, incidents, import substitution, or ESG/safety.
- `SignalObservation`: a concrete found signal with source, date, confidence, strength, evidence refs, novelty fingerprint, and validation status.
- `ICPScoringFormula`: transparent fit/intent aggregation and tier thresholds.
- `RadarCandidate`: a scored account candidate before it is accepted into Power Web work.

Radar configuration is a first-class product boundary. There can be many ICP Radars running in parallel for different products, markets, holdings, or source scopes. Each radar owns its definition and can produce its own candidate shortlist; only approved candidates should flow into the shared `Accounts` portfolio and then into Power Web work. The current implementation exposes this through an `icp_radar_catalog` artifact and a block-editable selected-radar settings editor backed by browser-local demo state. The settings editor exposes business-language rules, source entities, generated codes, and scoring presets; it does not require users to edit internal IDs or field/operator/value triples. Production persistence, scheduling, live connector execution, and run history are planned as later concentric slices.

The first realistic demo ICP profile uses `demo/fixtures/icp_radar/sibur_icp_pass1.xlsx` as a fixture. It discovers Russian legal entities inside a holding, scores them against ТОиР criteria, and shows a ranked candidate shortlist for the active `ТОиР / SIBUR` radar. The catalog also includes configured/planned radar examples without generated candidates yet. Numeric C1-C20 scores come from the XLSX. `radar.definition.intent_signals` is the canonical C1-C20 dictionary; top-level `criteria` is generated from it only as a backward-compatible alias. Criterion-level evidence is added by a separate curated synthetic fixture, `demo/fixtures/icp_radar/toir_sibur_criterion_evidence.json`, so the demo can exercise evidence-backed score explanation before production source extraction exists.

The first live ICP Radar path is intentionally separate from the stable XLSX fixture. `TOIR Quick Live Radar` uses a small definition with two qualification rules and three intent signals, runs from the CLI, and writes a separate `icp_radar_live_run` artifact only when a provider returns usable evidence. The live path is split by backend boundary: application modules own contracts, definition, qualification-first execution planning, provider-neutral normalization, and the live run service; `integrations` owns the OpenRouter adapter and recorded provider; `workflows` owns the optional `langgraph-dai` `BaseWorkflow` wrapper plus local fallback runtime. `live_icp_radar.py` remains only a compatibility facade for existing imports. OpenRouter is therefore the first provider, not the domain boundary. Live outputs are reviewable artifacts, not accepted accounts, and the system must not fabricate candidates when provider evidence is missing.

The persisted live Radar MVP adds an application service around that same
workflow-backed execution path. The service creates a durable `radar_runs`
record, updates queued/running/completed/failed state, and stores the current
`icp_radar_live_run` payload in `radar_run_outputs` as a JSON snapshot. The
snapshot is deliberately not a normalized candidate/evidence schema yet; it is a
compatibility layer that lets the backend reproduce the current live script
while API-oriented normalized tables are designed in later slices.

Live qualification results use a richer review contract than the radar settings rule definition. Each candidate-level qualification result carries the rule snapshot, operator, requirement level, source usages, source origin, trust/check policy, evidence findings, cross-validation status, requirement evaluation, final assessment, and optional human review decision. The backend normalizer may enrich simpler provider output into this contract, but the frontend must not render raw Q1/Q2 labels without evidence, source, trust, and final-assessment context.

The current criterion evidence contract is deliberately explicit:

- `supported`: curated synthetic demo facts exist for this candidate and criterion;
- `inferred`: the XLSX score is nonzero, but the demo does not yet contain criterion-level facts;
- `not_observed`: the XLSX score is zero.

This read model is not a substitute for production extraction. It defines the UI and artifact surface that future source ingestion should populate. The current demo adds browser-local signal validation on top of the generated artifact: confirmed and unreviewed signals keep their score, corrected signals use an adjusted score, and rejected/stale signals remain visible but contribute `0`.

Signal validation is part of the ICP Radar boundary. A human must be able to confirm, correct, reject, or mark a signal as stale. Validation changes must affect the score and preserve an audit trail explaining why the candidate score changed. Backend review APIs now persist current qualification and signal decisions for live run snapshots, while the frontend still uses browser-local demo state until the frontend API adapter slice. Multi-user audit history and live source re-checking remain future boundaries.

The frontend ICP Radar workspace should be table-first. The main screen is a broad shortlist table with a sticky account column, bounded inline candidate preview, effective score deltas, and a separate candidate detail screen. The detail screen is the intended surface for signal validation actions; the shortlist should stay optimized for scanning and comparison.

## LangGraph Platform Usage

The referenced platform should be used as follows:

- `BaseWorkflow` and typed state for access planning workflows.
- `ToolExecutor` policy for source and CRM connector calls.
- task lifecycle for queued/running/waiting_human/completed/failed states.
- HITL pattern for reviewable Access Plans and outreach drafts.
- canonical ingestion/retrieval and `EvidencePack` for evidence-backed recommendations.
- async batch pattern for account radar workloads.
- MCP boundaries for reusable repository, retrieval, configuration, and future CRM tools.

## Testing Strategy

- Unit tests for deterministic domain scoring and state transitions.
- Workflow tests for LangGraph state, audit, and resume behavior.
- Integration tests for persistence and connectors once added.
- Smoke tests for demo and API startup once API exists.
- E2E tests for signal-to-Access-Plan workflow once UI/API exists.

## Demo Implications

The demo should evolve through these stages:

1. Local deterministic Access Plan from fixture data.
2. LangGraph workflow output with node audit.
3. React frontend workspace shell over generated artifact.
4. Account Radar batch over multiple fixtures.
5. Power Web Lite board for the selected account.
6. Playbook Analysis for current and no-partner-motion route previews.
7. ICP Radar fixture using the ТОиР/SIBUR-style analysis and Russian-language demo companies.
8. ICP Radar signal validation with score recalculation.
9. Take-into-work handoff from ICP Radar candidates to Power Web.
10. Review queue and approved CRM task export.

## Trade-Offs

- Start with Postgres-friendly edge tables instead of a graph database. This keeps MVP infrastructure small.
- Start with deterministic planner rules before LLM orchestration. This keeps explanations testable.
- Keep external source connectors behind tools. This prevents scraping/vendor concerns from leaking into the domain.
- Split account discovery from signal monitoring. Legal-entity discovery changes slowly and can be imported or run manually; signal monitoring is recurring and should support incremental dedupe.
- Treat ICP Radar scoring as configurable but constrained. Formulas should be transparent and auditable, not arbitrary executable code.

## Open Questions

- First CRM target.
- First live source target.
- Whether a graph database becomes necessary after MVP.
- UI technology choice.
