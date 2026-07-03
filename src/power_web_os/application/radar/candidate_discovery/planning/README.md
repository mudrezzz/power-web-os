# Candidate Discovery Planning

## Ownership

Owns planner input, source-card-aware plan validation, plan acceptance, and
execution-plan projection.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Candidate-discovery records needed to describe executable plans.

## Forbidden imports

- Retrieval, provider adapters, FastAPI, SQLAlchemy, Celery, Redis, HTTP
  clients, provider SDKs, dotenv, and legacy `live_radar_*` modules.

## How to extend

Add planning contracts before adding new planner behavior. Execution belongs in
`candidate_discovery/execution`, not here.

Current source-of-truth modules:

- `definition_runtime.py`;
- `discovery_planning.py`;
- `plan_acceptance.py`;
- `planning_pipeline.py`;
- `execution_plan.py`;
- `retrieval_plan.py`.
