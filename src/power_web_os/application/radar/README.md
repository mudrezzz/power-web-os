# Radar Application Package

This package is the target home for Radar backend application code. It exists
so new Radar work has a real package boundary instead of adding more
root-level `application/live_radar_*.py` modules.

See `docs/architecture/RADAR_BACKEND_ARCHITECTURE.md` for the full migration
contract.
See `docs/architecture/radar/RADAR_ROOT_NAMESPACE_DEBT.md` for the complete
root `live_radar_*`, `radar_search_*`, and `signal_monitoring_*` debt
inventory.

## Ownership

`application/radar` owns provider-neutral application orchestration for Radar
pipelines:

- shared contracts used by more than one Radar pipeline;
- candidate discovery phase packages;
- reserved packages for signal monitoring and Power Web discovery.

Provider-level external-call budget contracts live in `shared/budgets`.
Candidate-discovery task budgets and useful-result retry budgets live in
`candidate_discovery/execution` because they depend on candidate-discovery task
stages and result semantics.

Root-level Radar-prefixed files are transition debt, not package ownership.
Some `live_radar_*` files are thin moved shims, while deferred
`live_radar_*`, `radar_search_*`, and `signal_monitoring_*` files remain
behavior owners only until their documented migration slices run.

## Allowed imports

- Python standard library.
- `power_web_os.application` ports and pure application records.
- `power_web_os.domain` value objects when needed.
- Sibling packages under `power_web_os.application.radar` following the import
  direction documented in the architecture guide.

## Forbidden imports

- FastAPI, SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, and dotenv.
- `power_web_os.persistence`, `power_web_os.api`, `power_web_os.jobs`, and
  provider adapters under `power_web_os.integrations`.
- Already-moved `power_web_os.application.live_radar_*` shims from new
  packages. Temporary imports from deferred legacy modules must stay documented
  in the compatibility map until their migration slices run.

## How to extend

1. Read the architecture document and this package README.
2. Pick the pipeline package that owns the behavior.
3. Use stable component contracts such as `Input`, `Result`, `Decision`,
   `Issue`, `Event`, and `Service`.
4. Add focused tests for the package boundary and behavior.
5. Do not create a new root-level `live_radar_*.py` module.
6. Prefer package-owned imports such as
   `power_web_os.application.radar.candidate_discovery.contracts`.
7. Do not add behavior tests or production imports through moved root shims;
   compatibility tests are the only allowed old-path assertions.
