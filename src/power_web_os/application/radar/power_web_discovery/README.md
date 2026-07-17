# Radar Power Web Discovery

This package defines the provider-neutral architecture contracts for future
account-access and relationship discovery. Slice `0.7.6.6.0` does not add a
production runtime.

## Ownership

Power Web discovery owns role demand, source-native profiles, reversible
identity hypotheses, confirmed identities, employment and relationship claims,
influence hypotheses, evidence-backed graph projection, gaps and diagnostics.
Existing `PowerWebRole`, `PowerWebBoard` and Access Planner remain downstream
compatibility/read-model contracts.

## Allowed imports

- `power_web_os.application.radar.shared`.
- Stable account/candidate references exposed through shared contracts.
- Pydantic and Python standard-library types.

## Forbidden imports

- Candidate-discovery internals, signal-monitoring internals, FastAPI,
  SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, dotenv, and legacy
  `live_radar_*` modules.

## How to extend

Add provider integrations through later integration-layer adapters. Application
services accept ports and product-safe receipts; they do not import HTTP or
provider SDKs. Keep benchmark controls outside planning context and keep
identity merge decisions reversible.

## Current status

The package currently contains architecture contracts, accepted benchmark
validation/freeze rules, source capability cards and a bounded HH public-web
probe contract. The accepted workbook intake retains no private contacts.
Retrieval, persistence, API, jobs and UI are intentionally deferred to child
slices.
