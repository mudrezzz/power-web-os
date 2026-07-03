# Candidate Discovery Extraction

## Ownership

Owns structured extraction contracts, schema validation, repair decisions, and
diagnostic issues.

## Allowed imports

- Python standard library.
- `power_web_os.application.radar.shared`.
- Candidate-discovery records needed for extracted findings.

## Forbidden imports

- Provider SDKs, HTTP clients, FastAPI, SQLAlchemy, Celery, Redis, dotenv, and
  legacy `live_radar_*` modules.

## How to extend

Treat malformed provider output as explicit diagnostic state. Do not silently
turn invalid extraction payloads into successful product state.
