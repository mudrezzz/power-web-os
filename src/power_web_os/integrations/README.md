# Integrations Layer

The integrations layer owns adapters for external providers, source systems,
CRM tools, and other network-facing infrastructure.

## Ownership

- `live_radar_openrouter.py` owns the OpenRouter request/response adapter for
  the live mini ICP Radar.
- Recorded provider adapters used by tests may live here when they implement the
  same provider port without live network calls.

## Dependency Rules

Allowed imports:

- application contracts and provider ports;
- provider SDKs or HTTP clients needed by the adapter;
- local integration helpers.

Forbidden imports:

- SQLAlchemy or persistence repositories;
- FastAPI route modules;
- domain scoring hidden inside provider adapters;
- worker/scheduler ownership.

Integrations return typed observations and provider metadata. They do not decide
candidate truth, final score semantics, review outcomes, or durable run state.

## How To Extend

1. Define or reuse an application port.
2. Implement the external adapter here.
3. Keep credentials in environment/local `.env`, never in code or artifacts.
4. Add tests using recorded or mocked provider output.
5. Update architecture contract tests if a new provider boundary is introduced.
