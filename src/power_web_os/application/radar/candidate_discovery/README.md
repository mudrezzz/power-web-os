# Radar Candidate Discovery

This package is the target home for the upstream Radar pipeline: finding and
qualifying companies, legal entities, and review-needed upstream entities.

## Ownership

Candidate discovery owns planning, retrieval, extraction, source routing,
candidate universe construction, checkpoints, execution, and diagnostics for
the "who should we monitor" pipeline.

## Allowed imports

- Python standard library.
- `power_web_os.application.radar.shared`.
- Candidate-discovery subpackages following phase ownership.
- Provider-neutral application/domain records.

## Forbidden imports

- `power_web_os.application.radar.signal_monitoring`.
- `power_web_os.application.radar.power_web_discovery`.
- FastAPI, SQLAlchemy, Celery, Redis, HTTP clients, provider SDKs, and dotenv.
- Already-moved legacy shims from new package code. Deferred legacy imports are
  temporary migration debt and must be visible in `compatibility.py`.

## How to extend

Choose the smallest phase package that owns the behavior. If a change crosses
multiple phases, introduce a narrow `Service` or `Decision` contract instead of
adding broad helper functions or a new root-level module.

Current package-owned source-of-truth modules:

- `contracts.py`: candidate-discovery DTOs, provider-neutral records, and
  ports.
- `service.py`: `LiveRadarRunService`, the provider-neutral live run use-case
  facade used by workflow wrappers and legacy compatibility imports.
- `service_factory.py`: `LiveRadarRunServiceFactory` and
  `LiveRadarRunComposition`, the package-owned collaborator assembly boundary
  for the live run facade.
- `service_context.py`: `LiveRadarTaskContextReader`, typed task-context
  access that adapts live-run task context into
  `CandidateDiscoveryExecutionOptions`.
- `service_budget.py`: `ExternalBudgetMetadataMerger`, budget metadata merge
  policy for planner-node and staged-execution snapshots.
- `service_events.py`: `LiveRadarEventStateProjector`, product-safe event state
  projection for the live run facade.
