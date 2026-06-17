# Jobs Layer

The jobs layer owns worker and scheduler entrypoints for long-running Power Web
OS tasks. It is execution infrastructure, not product state.

## Ownership

- `radar_jobs.py` owns the Celery app, Radar queue adapter, worker task, and
  local scheduler adapter.
- Celery messages carry durable identifiers such as `run_id`, not provider
  payloads, candidate lists, or artifacts.
- Worker tasks open their own database session and call application services.

## Dependency Rules

Allowed imports:

- application services and ports;
- persistence repository adapters for worker session wiring;
- integration/workflow adapters needed to execute a job;
- Celery and Redis runtime libraries.

Forbidden behavior:

- business scoring or review semantics inside worker tasks;
- provider normalization inside worker tasks;
- SQL query code inside worker tasks;
- trusting Celery result state as product truth.

`radar_runs` and `radar_run_outputs` remain the source of truth. Redis/Celery
only transport execution requests.

## How To Run

Start Redis locally, then run:

```bash
python -m alembic upgrade head
python -m power_web_os.demo seed-radar-db
celery -A power_web_os.jobs.radar_jobs.radar_celery_app worker --loglevel=INFO --pool=solo
power-web-os-api
```

Useful environment variables:

```text
POWER_WEB_OS_CELERY_BROKER_URL=redis://localhost:6379/0
POWER_WEB_OS_CELERY_RESULT_BACKEND=redis://localhost:6379/1
POWER_WEB_OS_CELERY_TASK_ALWAYS_EAGER=1
POWER_WEB_OS_CELERY_TASK_EAGER_PROPAGATES=1
```

Use eager mode only for tests and local diagnostics. Normal API usage should
enqueue a run and let the worker update durable run state.

## How To Extend

1. Add or update an application port before adding a new worker adapter.
2. Keep task payloads to durable identifiers such as `run_id`.
3. Open a fresh persistence session inside the worker entrypoint.
4. Wire repositories, provider adapters, and workflow adapters at the edge.
5. Keep business decisions in application/domain services and add job tests for
   success, failure, idempotency, and source-of-truth state.
