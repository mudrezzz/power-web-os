# ADR: Use Python FastAPI for the persistent backend foundation

## Status

Accepted

## Context

Power Web OS started as a deterministic Python domain/demo product with JSON
artifacts and a React frontend. The ICP Radar UI has matured enough that
browser-local overlays and generated JSON are no longer sufficient for durable
state, live run audit, and human review decisions.

The team considered introducing a backend now instead of continuing to add
frontend-only stubs. The main stack question was whether the backend should be
Python or Node.js.

## Decision

Use Python as the product backend language and FastAPI as the HTTP boundary.

The backend stack is:

- FastAPI for HTTP routes and OpenAPI.
- Pydantic for request/response DTOs.
- PostgreSQL for durable product state.
- SQLAlchemy 2.x for persistence mapping.
- Alembic for migrations.
- `pgvector` later for evidence retrieval.
- `langgraph-dai` for agent workflow orchestration.

Generated JSON artifacts remain supported as demo exports and offline fallback,
but they are not the long-term source of truth. Browser-local overlays remain
temporary demo state until a matching persisted domain record exists.

Backend growth is incremental:

1. API foundation and health/OpenAPI contract.
2. Persistence foundation.
3. Radar catalog API.
4. Live radar run persistence.
5. Human review persistence.
6. Frontend API adapter.
7. Run journal and evidence audit.

## Consequences

- The existing Python domain and workflow code can move behind API/application
  services without a rewrite.
- `langgraph-dai` integration stays in the same runtime as the backend.
- Frontend differences between JSON artifacts and API data must be handled by
  adapters, not by new visual paradigms.
- API routes must stay thin; domain logic belongs in domain/application services,
  and database logic belongs behind repositories.
- LLM/search outputs are stored as reviewable evidence and run records, not as
  authoritative final truth.
- Human review decisions become first-class persisted product records.

## Alternatives considered

- **Node.js backend**: attractive for frontend/BFF proximity, but it would split
  domain and agent workflow ownership across two runtimes while the core domain
  already exists in Python.
- **Continue with JSON/localStorage only**: useful for early UX discovery, but it
  cannot support durable run history, multi-step review, audit, or production
  API contracts.
- **Build full backend all at once**: rejected because it would pause product
  learning and risk a large unreviewable infrastructure rewrite.
