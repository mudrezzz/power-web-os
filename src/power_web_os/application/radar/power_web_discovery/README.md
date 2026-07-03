# Radar Power Web Discovery

This package is reserved for future account-access and relationship discovery.

## Ownership

Power Web discovery will own people, roles, relationships, partner paths,
influence structure, and buying-committee context for already selected
accounts.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Future stable account/candidate references exposed through shared contracts.

## Forbidden imports

- Candidate-discovery internals, signal-monitoring internals, FastAPI,
  SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, dotenv, and legacy
  `live_radar_*` modules.

## How to extend

Keep this package reserved until a dedicated Power Web discovery slice defines
its AS IS/TO BE and contracts.
