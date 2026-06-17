# API Layer

The API layer owns FastAPI transport contracts for Power Web OS. It validates
HTTP input, wires application services to infrastructure adapters, and returns
Pydantic DTOs.

## Ownership

- `app.py` creates the FastAPI app, shared runtime state, health routes, and
  router registration.
- `config.py` owns API settings, including the database URL used by API runs.
- `dependencies.py` wires per-request repository adapters and job queue
  adapters.
- `radar_routes.py` owns Radar catalog, run, and candidate HTTP routes.
- `radar_dtos.py` owns transport DTOs.
- `radar_mappers.py` maps application records and persisted snapshots into API
  DTOs.

## Dependency Rules

Allowed imports:

- FastAPI and Pydantic;
- application services, records, and ports;
- infrastructure adapters only in dependency wiring;
- API-local DTOs and mappers.

Forbidden behavior:

- SQL query code in route handlers;
- domain scoring or review decisions in routes;
- provider calls directly inside route handlers;
- frontend/demo artifact readers as hidden persistence.

## How To Extend

1. Add or update an application service or port first when behavior changes.
2. Add API DTOs for the transport contract.
3. Keep route handlers thin: validate input, call application services, return
   DTOs.
4. Put record-to-DTO shaping in API mappers.
5. Add `tests/test_backend_api.py` coverage and update OpenAPI expectations.

`POST /api/radars/{radar_id}/runs` creates a durable queued run and enqueues
worker execution. Clients poll `GET /api/radar-runs/{run_id}` until the run is
terminal, then read `GET /api/radar-runs/{run_id}/candidates` after output
exists.
