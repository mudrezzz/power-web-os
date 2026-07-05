# Candidate Discovery Checkpoints

## Ownership

Owns adaptive checkpoint decisions, recovery action contracts, and policy for
continue, expand, repair, retry, revise, stop, or fail outcomes.

## Module map

- `models.py`: checkpoint literals and Pydantic records:
  `RadarExecutionCheckpointPolicy`, `RadarExecutionCheckpointInput`, and
  `RadarExecutionCheckpointDecision`.
- `policy.py`: `RadarExecutionCheckpointService`, deterministic decision
  helpers, and `checkpoint_summary`.
- `recording.py`: execution-state checkpoint recording, metric extraction,
  event emission, warning collection, and duplicate-decision suppression.
- `recovery.py`: bounded retry, repair, expansion, revision, terminal stop, and
  recovery-state contracts.
- `__init__.py`: explicit package-owned public API re-export for behavior code
  that does not need a narrower module.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Candidate-discovery diagnostics, execution, and universe records needed to
  make provider-neutral decisions.
- Documented deferred budget and search-expansion root modules only until
  slices `0.7.6.4.16` and `0.7.6.4.17` move those contracts.

## Forbidden imports

- Direct provider calls, HTTP clients, FastAPI, SQLAlchemy, Celery, Redis,
  dotenv, and moved legacy checkpoint root shims.

## How to extend

Add explicit `Decision` and `Issue` records. Checkpoints decide what should
happen; phase executors own doing the work under budget.
