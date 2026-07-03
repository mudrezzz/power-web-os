# Radar Candidate Discovery

This package is the target home for the upstream Radar pipeline: finding and
qualifying companies, legal entities, and review-needed upstream entities.

## Ownership

Candidate discovery owns planning, retrieval, extraction, source routing,
candidate universe construction, checkpoints, execution, and diagnostics for
the "who should we monitor" pipeline.

## Allowed imports

- Python standard library.
- `power_web_os.application.radar.shared`.
- Candidate-discovery subpackages following phase ownership.
- Provider-neutral application/domain records.

## Forbidden imports

- `power_web_os.application.radar.signal_monitoring`.
- `power_web_os.application.radar.power_web_discovery`.
- FastAPI, SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, and dotenv.
- Legacy `power_web_os.application.live_radar_*` modules from new package code.

## How to extend

Choose the smallest phase package that owns the behavior. If a change crosses
multiple phases, introduce a narrow `Service` or `Decision` contract instead of
adding broad helper functions or a new root-level module.
