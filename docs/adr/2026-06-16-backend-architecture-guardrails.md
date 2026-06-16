# ADR: Backend architecture guardrails

## Status

Accepted

## Context

Power Web OS is adding a persistent backend after several frontend ICP Radar
refactoring slices. The frontend already has ADRs, local feature documentation,
and architecture contract tests that prevent a product screen from collapsing
back into one mixed-responsibility file.

The backend is about to add persistence, API contracts, long-running radar runs,
human review records, and eventually async workers. Without equivalent
guardrails, the backend could repeat the same failure mode as a large module that
mixes API transport, persistence, provider calls, scoring, workflow orchestration,
and export shaping.

## Decision

Backend work must follow explicit module ownership boundaries:

- `api`: thin FastAPI routes, transport DTOs, and dependency wiring.
- `application`: use cases, transactions, orchestration, and port interfaces.
- `domain`: business rules, scoring, validation, review semantics, and handoff rules.
- `persistence`: SQLAlchemy models, sessions, migrations, and repository implementations.
- `integrations`: provider, source, CRM, and external API adapters.
- `workflows`: LangGraph workflow wrappers and workflow state.
- `jobs`: worker and scheduler entrypoints.

Dependency direction is:

```text
entrypoints: API / CLI / workers / scheduler
  -> application services
    -> domain services + repository/queue/provider ports
      -> infrastructure adapters
```

OOP and single-responsibility rules are enforced at the module boundary:

- API routes, CLI commands, worker tasks, and scheduler triggers are entrypoints only.
- Application services own use cases and transaction boundaries.
- Domain services do not import FastAPI, SQLAlchemy, Celery, Redis, HTTP clients, dotenv, uvicorn, or provider SDKs.
- Repository interfaces are application ports; SQLAlchemy details stay in persistence implementations.
- Provider adapters return typed observations and evidence; they do not decide candidate state or final truth.
- Workflow wrappers orchestrate and audit execution; domain scoring and review semantics stay outside the workflow wrapper.

Long-running radar execution will use durable run records first. `radar_runs`
status, timestamps, idempotency keys, correlation ids, errors, and events will
live in Postgres. Celery/Redis can be added later as an execution adapter, but
Postgres remains the source of truth for run state and audit.

Architecture contract tests must guard these boundaries. Existing large modules
are temporary legacy exceptions, not patterns for new backend work:

- `src/power_web_os/live_icp_radar.py`
- `src/power_web_os/icp_radar.py`
- `src/power_web_os/icp_radar_catalog.py`
- `src/power_web_os/icp_radar_xlsx.py`

Backend boundaries must also be discoverable for developers and future agents.
Each active backend layer should have local README guidance when it owns a
meaningful extension path. Key modules should include short module docstrings
that explain ownership, not implementation trivia. Architecture contract tests
guard the presence of these onboarding docs for active backend layers.

## Consequences

- Slice 0.7.1 can introduce persistence behind repository/application boundaries instead of embedding SQLAlchemy in routes or domain logic.
- Future Celery/Redis work can reuse queue and executor ports instead of becoming the application boundary.
- Tests fail when new backend modules introduce cross-layer imports, oversized mixed-responsibility files, or hidden persistence in API routes.
- Tests fail when active backend layers lose their local onboarding docs or key module ownership docstrings.
- Existing large Radar modules are allowed temporarily, but follow-up work should decompose them after persistence boundaries are established.

## Alternatives considered

- **Rely on written guidance only**: rejected because the frontend monolith was prevented from recurring only after contract tests were added.
- **Refactor all large Python modules now**: rejected because this slice is governance-only and should not delay persistence foundation work.
- **Add Celery/Redis immediately**: rejected because durable run state and queue ports should come first; worker infrastructure is a later adapter.
