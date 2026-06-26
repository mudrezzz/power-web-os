# Integrations Layer

The integrations layer owns adapters for external providers, source systems,
CRM tools, and other network-facing infrastructure.

## Ownership

- `openrouter_request_builder.py` owns compact OpenRouter prompt/request
  shaping for one Radar retrieval task card.
- `openrouter_retrieval.py` maps OpenRouter web-search annotations/citations
  into provider-neutral retrieved-source records before extraction.
- `openrouter_trace.py` owns reusable sanitized trace payload helpers for
  provider responses and normalization outcomes.
- `openrouter_discovery_planner.py` owns the OpenRouter adapter for structured
  discovery-plan proposals. It does not execute web search and does not decide
  candidate truth.
- `live_radar_openrouter.py` owns the OpenRouter request/response adapter for
  the live mini ICP Radar. It supports the default OpenRouter web path and the
  OpenRouter server-tools `perplexity` engine selected by environment settings.
- `dadata_provider.py` owns the DaData company-registry adapter. It maps DaData
  party suggestions into application-level company observations and source
  outcomes; it is not a web-search or signal-evidence provider.
- Recorded provider adapters used by tests may live here when they implement the
  same provider port without live network calls.

## Dependency Rules

Allowed imports:

- application contracts and provider ports;
- provider SDKs or HTTP clients needed by the adapter;
- local integration helpers.

Forbidden imports:

- SQLAlchemy or persistence repositories;
- FastAPI route modules;
- domain scoring hidden inside provider adapters;
- worker/scheduler ownership.

Integrations return typed observations and provider metadata. They do not decide
candidate truth, final score semantics, review outcomes, or durable run state.
When a technical trace context is active, integrations may emit sanitized
provider request/response/error observations through the application tracer.
They must never store headers, API keys, or raw hidden chain-of-thought.
OpenRouter requests must stay scoped to the current execution task: qualification
tasks must not include intent signals, and signal tasks must not discover new
candidates.
Execution prompts should contain a compact `task_card`, `response_contract`, and
`constraints`, not the full Radar definition or a duplicated single-task
`search_plan`. The full OpenRouter request may still be stored in sanitized
technical trace for developer inspection.
OpenRouter model routing is role-specific. The live search provider keeps
`OPENROUTER_MODEL` as the fast/default signal model and uses
`OPENROUTER_EXTRACTOR_MODEL` for discovery, qualification, and coverage tasks,
falling back through `OPENROUTER_ADVANCED_MODEL` to `OPENROUTER_MODEL`.
For extraction recovery only, `OPENROUTER_EXTRACTION_BACKUP_MODEL` can be tried
after the primary extractor and strict primary retry still return non-JSON or
schema-invalid payloads. The generic `OPENROUTER_BACKUP_MODEL` is accepted as a
compatibility alias, but it is not used for planner or signal-search calls.
OpenRouter planner requests are a separate boundary: they receive Radar
settings, qualification rules, source policy, and task context, then return a
JSON discovery plan for backend validation. Planner output is advisory until the
application validator accepts it. Planner requests use `OPENROUTER_PLANNER_MODEL`
with the same advanced/default fallback.

DaData source-provider requests are a separate structured-data boundary. The
adapter reads `DADATA_API_KEY`, `DADATA_SECRET_KEY`,
`POWER_WEB_OS_DADATA_MODE`, and `POWER_WEB_OS_DADATA_BASE_URL` from local
environment only. Recorded mode is suitable for tests and local smoke runs
without network credentials. Live mode calls the DaData organization suggestions
API and stores only sanitized request/response summaries in technical trace.
The adapter returns normalized company observations and explicit source outcomes
such as no match, ambiguous match, unavailable provider, invalid credentials,
rate limit, or schema-invalid response. It must not perform Radar strategy,
signal scoring, or broad candidate-universe enumeration.

## How To Extend

1. Define or reuse an application port.
2. Implement the external adapter here.
3. Keep credentials in environment/local `.env`, never in code or artifacts.
4. Add tests using recorded or mocked provider output.
5. Update architecture contract tests if a new provider boundary is introduced.
