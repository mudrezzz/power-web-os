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

The package contains architecture contracts, accepted benchmark
validation/freeze rules, source capability cards, immutable account handoff and
the pre-persistence `people_search_stage.v1` runtime. The people-search stage
compiles eight semantic role demands into accepted account-role title
hypotheses, 24 mandatory official/HH/generic tasks, bounded retries and query
revisions, product-safe receipts, source leads and role coverage checkpoints.
Source leads are inputs for profile extraction; they are not people, employment
claims or Power Web graph nodes. Runtime persistence, API, jobs and UI remain
deferred to slices `0.7.6.6.7` through `0.7.6.6.9`.

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

Slice `0.7.6.6.2` implements that generation and bounded public retrieval. HH
is accessed only as an `hh.ru`-restricted ordinary web-search lane. The stage
never uses HH API, authentication, crawling or private contacts.
