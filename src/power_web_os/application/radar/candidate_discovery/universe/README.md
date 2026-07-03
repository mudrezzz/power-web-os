# Candidate Discovery Universe

## Ownership

Owns candidate-universe entities, entity resolution, retrieved-candidate
materialization, review-needed flags, and product-candidate projection inputs.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Candidate-discovery source and extraction records.

## Forbidden imports

- Signal-monitoring internals, Power Web discovery internals, FastAPI,
  SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, dotenv, and legacy
  `live_radar_*` modules.

## How to extend

Keep upstream universe recall-first and product candidate projection
precision-first. Review-needed sites or branches must not become confident
account rows without explicit resolution evidence.
