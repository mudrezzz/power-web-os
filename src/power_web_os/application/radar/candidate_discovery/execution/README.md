# Candidate Discovery Execution

## Ownership

Owns candidate-discovery phase orchestration, scheduler admission, search
expansion execution, budget-sensitive execution order, and migration of staged
executor behavior.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Candidate-discovery phase packages.
- Provider ports and provider-neutral task/result records.

## Forbidden imports

- FastAPI routes, SQLAlchemy models/sessions, Celery entrypoints, Redis
  clients, direct HTTP clients, provider SDKs, dotenv, and legacy
  `live_radar_*` modules from new package code.

## How to extend

Keep orchestration thin and explicit. If logic belongs to planning, sources,
extraction, universe, or diagnostics, add it to that phase package instead of
growing the executor.
