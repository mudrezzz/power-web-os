# Candidate Discovery Checkpoints

## Ownership

Owns adaptive checkpoint decisions, recovery action contracts, and policy for
continue, expand, repair, retry, revise, stop, or fail outcomes.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Candidate-discovery diagnostics, execution, and universe records needed to
  make provider-neutral decisions.

## Forbidden imports

- Direct provider calls, HTTP clients, FastAPI, SQLAlchemy, Celery, Redis,
  dotenv, and legacy `live_radar_*` modules.

## How to extend

Add explicit `Decision` and `Issue` records. Checkpoints decide what should
happen; phase executors own doing the work under budget.
