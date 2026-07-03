# Candidate Discovery Retrieval

## Ownership

Owns provider-neutral retrieval task cards and retrieved source material.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Candidate-discovery source and planning records that describe retrieval scope.

## Forbidden imports

- FastAPI, SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, dotenv, and
  legacy `live_radar_*` modules.

## How to extend

Keep retrieval records provider-neutral. Actual HTTP/provider execution belongs
in integration adapters and phase executors.
