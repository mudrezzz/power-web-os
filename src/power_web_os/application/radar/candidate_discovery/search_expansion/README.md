# Candidate Discovery Search Expansion

## Ownership

Owns recall-first candidate-discovery search expansion planning, target and
variant records, deterministic variant selection, guaranteed-lane scheduling,
checkpoint targeted expansion execution, payload projection, and expansion work
admission.

## Allowed imports

- Python standard library.
- `power_web_os.application.radar.shared`.
- Candidate-discovery contracts, execution task runners, and provider-neutral
  records needed to execute already approved expansion work.
- Deferred root budget/universe helpers only until their owning cleanup slices
  move those contracts.

## Forbidden imports

- FastAPI, SQLAlchemy, Celery, Redis, direct HTTP clients, provider SDKs, dotenv,
  and moved root search-expansion/work-scheduler shims.

## How to extend

Keep expansion strategy deterministic and bounded. Add new target records,
selection diagnostics, scheduler decisions, or payload helpers in this package;
phase flow stays in `candidate_discovery/execution/expansion.py`, and checkpoint
recovery only calls `targeted_execution.py`.
