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

## Input configuration

Slice `0.7.6.6.0.1` implements the upstream sales-playbook configuration in the
separate `power_web_os.application.sales_playbook` package. A future discovery
run must receive an immutable active product and semantic-role-policy snapshot.
This package must not import the sales-playbook implementation directly; the
handoff will use stable provider-neutral snapshot contracts in the next slice.

Slice `0.7.6.6.0.2` narrows that handoff to product plus semantic roles.
AccessPlaybook routes are not a discovery input. Account title variants,
queries and evidence hints will be generated later as reviewable hypotheses,
not authored into the global role policy.
