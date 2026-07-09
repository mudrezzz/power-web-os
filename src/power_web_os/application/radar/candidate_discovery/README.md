# Radar Candidate Discovery

This package is the target home for the upstream Radar pipeline: finding and
qualifying companies, legal entities, and review-needed upstream entities.

## Ownership

Candidate discovery owns planning, retrieval, extraction, source routing,
candidate universe construction, checkpoints, execution, and diagnostics for
the "who should we monitor" pipeline.

Moved candidate-discovery behavior is package-owned here, not in the old
root-level shims. Remaining root `live_radar_*` and `radar_search_*` files are
tracked in `docs/architecture/radar/RADAR_ROOT_NAMESPACE_DEBT.md` and must move
through their owning slices before the root namespace can close.

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
- Behavior-test imports through moved root shims. Use package-owned paths unless
  the test explicitly asserts compatibility.

## How to extend

Choose the smallest phase package that owns the behavior. If a change crosses
multiple phases, introduce a narrow `Service` or `Decision` contract instead of
adding broad helper functions or a new root-level module.

If the code you need still lives in a deferred root module, keep the behavior
move as a dedicated migration slice rather than copying root namespace patterns
into new code.

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
- `retrieval/definition.py`: live mini Radar definition, execution/search-plan
  builders, and artifact projection for candidate-discovery runs.
- `retrieval/web_retrieval.py`: provider-neutral web retrieval request/result
  contracts and recorded retrieval provider used by tests and demos.
- `retrieval/product_sources.py`: strict product-source projection for
  candidate rows.
- `universe/`: recall-first upstream admission, candidate identity, metadata
  merge, gap payloads, coverage helpers, entity resolution,
  retrieved-candidate extraction, final universe projection, and
  upstream/cross-source disambiguation.
- `extraction/`: provider payload validation, deterministic extraction repair,
  post-extraction salvage from product-safe source diagnostics, extraction
  validation states, and validation event projection.
- `diagnostics/`: live artifact shaping, candidate normalization, upstream
  admission projection, contract validation, collection helpers, and trace/event
  support.
- `sources/risk.py`: source verification-risk helpers used by evidence
  projection.
- `checkpoints/`: checkpoint models, deterministic policy, execution-state
  recording, and bounded recovery actions for candidate discovery.
- `search_expansion/`: recall-first expansion target/variant planning,
  protected benchmark target merge, selection, scheduling, targeted checkpoint
  expansion execution, and work-admission contracts.
- `execution/reconciliation.py`: final product-safe accounting between public
  candidate rows, universe-only upstream leads, diagnostic gaps, product
  acceptance, and projection reasons.
- `execution/public_surface.py`: user-visible candidate surface projection:
  accepted product candidates plus review-needed legal candidates with strict
  product acceptance kept as a separate subset.
- `execution/task_budget.py`: candidate-discovery task budget settings,
  semantic task reserve decisions, counters, warnings, and exhaustion events.
- `execution/useful_budget.py`: useful-result retry budget and retry task
  shaping for candidate-discovery discovery/coverage tasks.
