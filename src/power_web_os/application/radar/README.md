# Radar Application Package

This package is the source of truth for Radar backend application code. Root
Radar-prefixed application modules are compatibility shims only.

See `docs/architecture/RADAR_BACKEND_ARCHITECTURE.md` for the full migration
contract.
See `docs/architecture/radar/RADAR_ROOT_NAMESPACE_DEBT.md` for the complete
root `live_radar_*`, `radar_search_*`, and `signal_monitoring_*` debt
inventory.

## Ownership

`application/radar` owns provider-neutral application orchestration for Radar
pipelines:

- shared contracts used by more than one Radar pipeline;
- shared run lifecycle, configuration, and preflight services;
- candidate discovery phase packages;
- signal monitoring and the reserved Power Web discovery package.

Provider-level external-call budget contracts live in `shared/budgets`.
Candidate-discovery task budgets and useful-result retry budgets live in
`candidate_discovery/execution` because they depend on candidate-discovery task
stages and result semantics.
Live mini Radar definition builders and provider-neutral web retrieval records
live under `candidate_discovery/retrieval`; provider HTTP/SDK adapters remain
outside this application package.

Since slice `0.7.6.4.19`, every root-level Radar-prefixed file is a thin
compatibility shim. The centralized map is `radar/compatibility.py`; no root
file may regain behavior.

## Allowed imports

- Python standard library.
- `power_web_os.application` ports and package-owned lifecycle records.
- `power_web_os.domain` value objects when needed.
- Sibling packages under `power_web_os.application.radar` following the import
  direction documented in the architecture guide.

## Forbidden imports

- FastAPI, SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, and dotenv.
- `power_web_os.persistence`, `power_web_os.api`, `power_web_os.jobs`, and
  provider adapters under `power_web_os.integrations`.
- Any root-level `power_web_os.application.radar_*`,
  `power_web_os.application.live_radar_*`, or
  `power_web_os.application.signal_monitoring_*` shim.

## How to extend

1. Read the architecture document and this package README.
2. Pick the pipeline package that owns the behavior.
3. Use stable component contracts such as `Input`, `Result`, `Decision`,
   `Issue`, `Event`, and `Service`.
4. Add focused tests for the package boundary and behavior.
5. Do not create a new root-level Radar-prefixed module.
6. Prefer package-owned imports such as
   `power_web_os.application.radar.candidate_discovery.contracts`.
7. Do not add behavior tests or production imports through moved root shims;
   compatibility tests are the only allowed old-path assertions.
