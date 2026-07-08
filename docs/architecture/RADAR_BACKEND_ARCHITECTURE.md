# Radar Backend Architecture

This document is the backend-side map for Radar pipeline code. It complements
the product pipeline AS IS/TO BE documents under `docs/radar/` by answering a
different question: where backend code belongs and how new components should be
shaped.

Candidate-discovery execution has a dedicated procedural handbook:
`docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md`.
Use it together with this document before changing phase executors, execution
state, finalization, task running, or projection services.

Root-level Radar namespace debt has its own inventory:
`docs/architecture/radar/RADAR_ROOT_NAMESPACE_DEBT.md`. That file lists every
root `live_radar_*`, `radar_search_*`, `radar_work_scheduler*`, and
`signal_monitoring_*` file, its current status, target package, and owning
follow-up slice.

## Purpose

Radar backend code must remain understandable as candidate discovery, signal
monitoring, and future Power Web discovery grow. The current implementation is
functionally useful, but the backend package shape has become too flat. This
document records the current debt, the target package structure, and the
component contract that future slices must follow.

Runtime behavior is unchanged by this architecture slice.

## AS IS Inventory

Current candidate-discovery backend logic still has deferred behavior in
root-level `src/power_web_os/application/live_radar_*.py` modules, and the
root namespace also contains `radar_search_*`, `radar_work_scheduler*`, and
`signal_monitoring_*` pipeline files.

Measured baseline:

| Metric | Value |
|---|---:|
| Root-level `live_radar_*.py` files | 38 |
| Total lines in those files | 10 378 |
| Top-level functions | 332 |
| Top-level classes | 78 |
| Largest hotspot | `live_radar_staged_execution.py` |
| Service-facade hotspot | `live_radar_service.py` |
| Highest application import fan-out | `live_radar_staged_execution.py` |

The root-level files are temporary migration debt. They are not examples for new
backend work, and they are not the extension path for tests or production code
when behavior has already moved to `application/radar`.

### Hotspots

| Module | Current issue | Target treatment |
|---|---|---|
| `live_radar_staged_execution.py` | Former large phase executor with many helpers and high application import fan-out | Moved to candidate-discovery phase executors; root file is now a thin compatibility shim |
| `live_radar_service.py` | Former large service facade that shaped a full live run artifact | Moved to `radar/candidate_discovery/service.py`; root file is now a thin compatibility shim |

### Current Responsibility Map

| Current module group | Responsibility | Target package |
|---|---|---|
| `live_radar_contracts.py` | Provider-neutral DTOs and ports | `radar/shared/` and `radar/candidate_discovery/contracts.py` |
| `live_radar_definition.py` | Live mini Radar definition and search-plan builders | `radar/candidate_discovery/retrieval/definition.py` |
| `live_radar_definition_runtime.py` | Persisted definition runtime mapping | `radar/candidate_discovery/planning/definition_runtime.py` |
| `live_radar_discovery_planning.py`, `live_radar_plan_acceptance.py`, `live_radar_planning_pipeline.py`, `live_radar_execution_plan.py`, `live_radar_retrieval_plan.py` | Planning, validation, acceptance, and executable plan projection | `radar/candidate_discovery/planning/` |
| `live_radar_web_retrieval.py`, `live_radar_product_sources.py` | Provider-neutral retrieval/source material | `radar/candidate_discovery/retrieval/` |
| `live_radar_extraction_contract.py`, `live_radar_extraction_diagnostics.py` | Extraction schema validation, repair, diagnostics, and post-extraction salvage | `radar/candidate_discovery/extraction/contract.py`, `diagnostics.py`, and `recovery.py` |
| `live_radar_source_cards.py`, `radar_source_obligations.py`, connector/capability helpers | Source capability, source-card, and obligation rules | `radar/shared/sources/` and `radar/candidate_discovery/sources/` |
| `radar_source_providers.py`, registry lookup helpers, lookup term generators | Provider-neutral registry/source orchestration | `radar/candidate_discovery/sources/` |
| `live_radar_entity_resolution.py`, `live_radar_universe.py`, `live_radar_retrieved_candidates.py`, `live_radar_candidate_refs.py`, `live_radar_cross_disambiguation.py`, `radar_upstream_disambiguation.py` | Candidate universe, entity resolution, retrieved candidate extraction, upstream/cross-source disambiguation | `radar/candidate_discovery/universe/` |
| `live_radar_checkpoints.py`, `live_radar_checkpoint_actions.py`, `live_radar_checkpoint_execution.py` | Adaptive checkpoint decisions and action execution | `radar/candidate_discovery/checkpoints/` |
| `radar_search_expansion*.py`, `radar_work_scheduler*.py` | Search expansion, scheduler admission, and budget diagnostics | `radar/candidate_discovery/search_expansion/` |
| `live_radar_external_budget*.py` | Provider-level external-call budget settings, decisions, counters, source-verification budget accounting, retry records, and reserve metadata | `radar/shared/budgets/` |
| `live_radar_staged_execution.py`, `live_radar_staged_helpers.py`, `live_radar_staged_merge.py`, `live_radar_staged_support.py`, `live_radar_execution_budget.py`, `live_radar_useful_budget.py` | Candidate-discovery staged execution, task budgets, useful-result budgets, and phase helper logic | `radar/candidate_discovery/execution/` |
| `live_radar_normalization.py`, `live_radar_collection_utils.py`, `live_radar_pipeline_support.py`, diagnostics helpers | Candidate normalization, collection helpers, trace/event support, and product-safe projections | `radar/candidate_discovery/diagnostics/` |
| `live_radar_service.py` | One live run application facade | `radar/candidate_discovery/service.py` after migration |

## TO BE Package Map

Target package root:

```text
src/power_web_os/application/radar/
  shared/
  candidate_discovery/
    planning/
    retrieval/
    extraction/
    sources/
    universe/
    checkpoints/
    search_expansion/
    execution/
    diagnostics/
  signal_monitoring/
  power_web_discovery/
```

## Package Skeleton Status

As of slice `0.7.6.4.8`, the target package skeleton exists at:

```text
src/power_web_os/application/radar/
```

The local package contract starts at
`src/power_web_os/application/radar/README.md`. Each meaningful package has its
own README with ownership, allowed imports, forbidden imports, and extension
rules.

Compatibility currently means:

- old root-level import paths remain available only as compatibility shims for
  moved modules;
- production code should import moved behavior from package-owned paths;
- behavior tests should import moved behavior from package-owned paths;
- old imports for moved modules are allowed only in explicit compatibility
  assertions, currently `tests/test_radar_backend_package_contract.py`;
- new packages do not re-export legacy symbols through broad compatibility
  layers;
- `src/power_web_os/application/radar/candidate_discovery/compatibility.py`
  stores a declarative migration map from legacy modules to target packages;
- future migration slices will move code behind package-owned contracts
  deliberately, one phase at a time.

This is a skeleton milestone, not a behavior migration.

As of slice `0.7.6.4.9`, the first candidate-discovery layer has moved. These
modules now have package-owned source of truth and root-level compatibility
shims:

| Legacy module | Source of truth |
|---|---|
| `live_radar_source_cards.py` | `radar/shared/source_cards.py` |
| `live_radar_contracts.py` | `radar/candidate_discovery/contracts.py` |
| `live_radar_definition_runtime.py` | `radar/candidate_discovery/planning/definition_runtime.py` |
| `live_radar_discovery_planning.py` | `radar/candidate_discovery/planning/discovery_planning.py` |
| `live_radar_plan_acceptance.py` | `radar/candidate_discovery/planning/plan_acceptance.py` |
| `live_radar_planning_pipeline.py` | `radar/candidate_discovery/planning/planning_pipeline.py` |
| `live_radar_execution_plan.py` | `radar/candidate_discovery/planning/execution_plan.py` |
| `live_radar_retrieval_plan.py` | `radar/candidate_discovery/planning/retrieval_plan.py` |
| `live_radar_product_sources.py` | `radar/candidate_discovery/retrieval/product_sources.py` |

As of slice `0.7.6.4.10`, staged candidate-discovery execution has also moved.
The old root-level files are compatibility shims, while the package-owned
source of truth is split into phase executors:

| Legacy module | Source of truth |
|---|---|
| `live_radar_staged_execution.py` | `radar/candidate_discovery/execution/orchestrator.py` |
| `live_radar_staged_helpers.py` | `radar/candidate_discovery/execution/task_runner.py` |
| `live_radar_staged_merge.py` | `radar/candidate_discovery/execution/merge.py` |
| `live_radar_staged_support.py` | `radar/candidate_discovery/execution/projection.py` |

Execution phase map:

| Module | Responsibility |
|---|---|
| `context.py` | Define `CandidateDiscoveryExecutionContext` and `PhaseResult`. |
| `state.py` | Define `CandidateDiscoveryExecutionState`, the mutable cross-phase state object. |
| `orchestrator.py` | Preserve the public `run_staged_radar_execution` entrypoint and run `CandidateDiscoveryOrchestrator`. |
| `discovery.py` | `DiscoveryPhaseExecutor`: run discovery tasks, retrieved-candidate extraction, cross-source disambiguation, first checkpoint, and gate pass. |
| `gates.py` | `GatePhaseExecutor`: own the qualification gate phase wrapper reused by discovery and coverage. |
| `coverage.py` | `CoveragePhaseExecutor`: run iterative coverage checks and after-coverage checkpoint recovery. |
| `expansion.py` | `ExpansionPhaseExecutor`: execute search expansion tasks under scheduler/admission and budget guards. |
| `expansion_diagnostics.py` | Build expansion summaries, target coverage, and guarantee diagnostics. |
| `signals.py` | `CandidateDiscoverySignalHandoffProjector`: normal signal-monitoring handoff projection; `SignalCompatibilityPhaseExecutor`: explicit legacy inline signal-search compatibility. |
| `finalization.py` | `FinalizationProjector`: build final `WebSearchProviderResult`, event list, and dossier/report metadata. |
| `finalization_universe.py` | Add review-needed upstream entities and upstream disambiguation events. |
| `reconciliation.py` | `CandidateDiscoveryOutcomeReconciler`: reconcile public candidates, universe-only leads, diagnostic gaps, product acceptance, and projection reasons. |
| `task_runner.py` | `TaskExecutionService`: provider-neutral task execution, gate pass, retries, and candidate task utilities. |
| `merge.py` | `ExecutionResultMerger`: source/observation/provider metadata merge and universe entity metadata projection. |
| `projection.py` | `CandidateProjectionService` and `PipelineEventFactory`: candidate projection and product-safe event payloads. |
| `finalization_metadata.py`, `task_runner_payloads.py` | Private small payload/summary helpers used by service classes. |

As of slices `0.7.6.4.11`, `0.7.6.4.11.1`, and `0.7.6.4.11.2`,
candidate-discovery execution follows an explicit service contract. The
authoritative class-by-class contract is maintained in
`docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md`:

- `CandidateDiscoveryExecutionContext` carries run-level dependencies and
  limits: radar payload, execution/retrieval plans, provider port, task and
  external budgets, useful-result budget, checkpoint services, expansion
  service, work scheduler, verification cache, source policy decisions, and
  phase limits.
- `CandidateDiscoveryExecutionState` carries mutable cross-phase data:
  sources, observations, provider metadata, events, executed task ids,
  candidate scope, coverage records, checkpoint decisions, adaptive actions,
  review-stop reason, signal statuses, and finalization counters.
- `PhaseResult` is a small phase-status record. It must not duplicate the full
  state payload.
- `CandidateDiscoveryOrchestrator` owns only phase order. It must not become a
  hidden place for discovery, expansion, scoring, checkpoint, or finalization
  rules.
- Phase behavior belongs to service/projector methods:
  `DiscoveryPhaseExecutor.run`, `GatePhaseExecutor.run`,
  `CoveragePhaseExecutor.run`, `ExpansionPhaseExecutor.run`,
  `CandidateDiscoverySignalHandoffProjector.run`,
  `SignalCompatibilityPhaseExecutor.run`, and `FinalizationProjector.project`.
  Normal candidate discovery uses `signal_execution_mode="handoff"` and does
  not call provider `signal_search` tasks. Inline signal search remains only as
  explicit `inline_compatibility` behavior until closure.
- Helper behavior is also service-owned:
  `TaskExecutionService`, `ExecutionResultMerger`,
  `CandidateProjectionService`, `PipelineEventFactory`,
  `SmokeLimitPolicy`, and `ExecutionMetadataFactory`.
- Public top-level functions are forbidden across
  `candidate_discovery/execution`, except the compatibility wrapper
  `run_staged_radar_execution`. Private helpers are allowed only for small local
  payload/summary transformations.
- Execution functions and methods should stay under the architecture-test line
  threshold. A large private helper that hides phase behavior is treated as
  migration debt, not as a valid service boundary.
- Every public class in `candidate_discovery/execution` must document `Owns`,
  `Does not own`, and an `Architecture` link to the execution handbook. The
  handbook must mention every public class.

As of slice `0.7.6.4.12`, the live Radar run service facade has also moved:

| Legacy module | Source of truth |
|---|---|
| `live_radar_service.py` | `radar/candidate_discovery/service.py` |

`LiveRadarRunService` now owns only the provider-neutral use-case order:
planning, staged execution, and delegation to artifact projection. Product-safe
artifact shaping lives in
`radar/candidate_discovery/diagnostics/live_run_artifact.py`.
`LiveRadarRunServiceFactory` owns collaborator assembly for that facade:
provider wrapping through `SourceRegistryWebSearchProvider`, default planner
selection, artifact projector construction, budget/event services, and
task-context reader factory wiring. `LiveRadarRunComposition` carries the ready
collaborators into the facade so the facade does not act as its own composition
root. Service-adjacent runtime policies remain named package-owned components:
`LiveRadarTaskContextReader` adapts task context to staged execution options,
`ExternalBudgetMetadataMerger` owns planner/execution budget metadata merging,
and `LiveRadarEventStateProjector` owns event-list projection. The old
root-level `live_radar_service.py` file is a compatibility shim for existing
imports and must not regain behavior.

As of slice `0.7.6.4.15`, candidate-discovery checkpoints have moved:

| Legacy module | Source of truth |
|---|---|
| `live_radar_checkpoints.py` | `radar/candidate_discovery/checkpoints/models.py` and `policy.py` |
| `live_radar_checkpoint_execution.py` | `radar/candidate_discovery/checkpoints/recording.py` |
| `live_radar_checkpoint_actions.py` | `radar/candidate_discovery/checkpoints/recovery.py` |

The checkpoint package owns deterministic checkpoint policy, checkpoint
recording, and bounded recovery actions. The root files are compatibility
shims and must not regain behavior. The checkpoint package may temporarily call
deferred root budget/search-expansion modules until the owning migration slices
move those contracts, but it must not import provider SDKs, persistence, API
routes, or direct HTTP clients.

As of slice `0.7.6.4.16`, candidate-discovery search expansion has moved:

| Legacy module | Source of truth |
|---|---|
| `radar_search_expansion.py` | `radar/candidate_discovery/search_expansion/service.py` |
| `radar_search_expansion_models.py` | `radar/candidate_discovery/search_expansion/models.py` |
| `radar_search_expansion_selection.py` | `radar/candidate_discovery/search_expansion/selection.py` |
| `radar_search_expansion_scheduler.py` | `radar/candidate_discovery/search_expansion/scheduler.py` |
| `radar_search_expansion_support.py` | `radar/candidate_discovery/search_expansion/support.py` |
| `live_radar_search_expansion_payloads.py` | `radar/candidate_discovery/search_expansion/payloads.py` |
| `live_radar_search_expansion_execution.py` | `radar/candidate_discovery/search_expansion/targeted_execution.py` |
| `radar_work_scheduler.py` | `radar/candidate_discovery/search_expansion/work_scheduler.py` |
| `radar_work_scheduler_metadata.py` | `radar/candidate_discovery/search_expansion/work_scheduler_metadata.py` |

`ExpansionPhaseExecutor` still owns phase flow inside
`candidate_discovery/execution`; search-expansion planning, selection,
guaranteed-lane scheduling, checkpoint targeted expansion payloads, and
recall-expansion work admission now live in the search-expansion package.
Root files are compatibility shims and must not regain behavior.

As of slice `0.7.6.4.17.1`, live mini Radar definition builders and
provider-neutral web retrieval contracts have moved:

| Legacy module | Source of truth |
|---|---|
| `live_radar_definition.py` | `radar/candidate_discovery/retrieval/definition.py` |
| `live_radar_web_retrieval.py` | `radar/candidate_discovery/retrieval/web_retrieval.py` |

Definition builders stay candidate-discovery-owned because they compile the
live mini Radar payload, execution plan, retrieval plan, and artifact shape for
this pipeline. Web retrieval records remain provider-neutral application
contracts, while provider HTTP/SDK adapters stay outside `application/radar`.

As of slice `0.7.6.4.17.2`, candidate-universe behavior has moved:

| Legacy module | Source of truth |
|---|---|
| `live_radar_candidate_refs.py` | `radar/candidate_discovery/universe/identity.py` |
| `live_radar_universe.py` | `radar/candidate_discovery/universe/` split helpers |
| `live_radar_retrieved_candidates.py` | `radar/candidate_discovery/universe/retrieved_candidates.py` |
| `live_radar_entity_resolution.py` | `radar/candidate_discovery/universe/entity_resolution.py` |
| `live_radar_cross_disambiguation.py` | `radar/candidate_discovery/universe/cross_source_disambiguation.py` |
| `radar_upstream_disambiguation.py` | `radar/candidate_discovery/universe/upstream_disambiguation.py` |

The universe package owns candidate identity/source refs, provider metadata
merge keys, gap payloads, coverage risk helpers, candidate-universe projection,
retrieved-source candidate extraction, entity resolution, and upstream/cross-
source disambiguation. Execution phases may invoke these services, but they do
not own the candidate-universe rules.

As of slice `0.7.6.4.17.3`, candidate extraction and diagnostics behavior has
moved:

| Legacy module | Source of truth |
|---|---|
| `live_radar_extraction_contract.py` | `radar/candidate_discovery/extraction/contract.py` |
| `live_radar_extraction_diagnostics.py` | `radar/candidate_discovery/extraction/diagnostics.py` |
| `live_radar_normalization.py` | `radar/candidate_discovery/diagnostics/normalization.py` |
| `live_radar_collection_utils.py` | `radar/candidate_discovery/diagnostics/collections.py` |
| `live_radar_pipeline_support.py` | `radar/candidate_discovery/diagnostics/pipeline_support.py` |
| `live_radar_source_risk.py` | `radar/candidate_discovery/sources/risk.py` |

The extraction package owns provider payload validation, deterministic repair,
post-extraction salvage from product-safe source diagnostics, and extraction
diagnostic states. The diagnostics package owns candidate normalization,
collection helpers, and trace/event support used by product-safe artifact
projection. The sources package owns source verification-risk helpers.
Root files are compatibility shims and must not regain behavior.

As of slice `0.7.6.4.18`, recorded/no-network signal-monitoring behavior has
moved:

| Legacy module | Source of truth |
|---|---|
| `signal_monitoring_contracts.py` | `radar/signal_monitoring/contracts.py` |
| `signal_monitoring_executor.py` | `radar/signal_monitoring/executor.py` |
| `signal_monitoring_source_strategy.py` | `radar/signal_monitoring/source_strategy.py` |

The signal-monitoring package owns contracts, source-lane strategy, task
planning, signal-specific budget counters, payload parsing/repair, observation
projection, and the recorded executor. Root files are compatibility shims and
must not regain behavior. This migration does not add live providers,
persistence, API/job lifecycle, or UI scheduling.

As of slice `0.7.6.4.18.1`, candidate discovery and signal monitoring are split
at runtime. Candidate discovery records the pre-signal checkpoint and projects
`not_searched_pending_signal_monitoring` handoff rows by default. The
signal-monitoring package owns actual signal evaluation semantics and budgets;
candidate discovery keeps only explicit inline compatibility for old callers.

As of slice `0.7.6.4.14.1`, the flat namespace closure policy is explicit:
`docs/architecture/radar/RADAR_ROOT_NAMESPACE_DEBT.md` is the reviewable debt
inventory, behavior tests for moved modules use package-owned imports, and
architecture tests fail when production code or non-compatibility tests import
already moved legacy paths. Deferred root behavior remains honest debt, not a
normal API.

### `radar/shared`

Owns contracts and utilities that are genuinely common across Radar pipelines:

- source capability cards and source eligibility primitives;
- model/runtime profile summaries;
- provider-level external-call budget records under `shared/budgets`, including
  settings, decisions, counters, exhaustion records, source-verification budget
  accounting, retry records, and reserve metadata;
- product-safe event/issue shapes reused by multiple pipelines.

It must not import candidate discovery, signal monitoring, or Power Web
discovery packages.

Shared budget ownership is intentionally narrow. Candidate-discovery task
budgets and useful-result retry budgets stay in
`radar/candidate_discovery/execution` because they depend on
`RadarExecutionTask`, candidate-discovery stages, semantic task reserves, and
discovery/coverage usefulness thresholds. Signal monitoring keeps its own
signal task, provider-call, retry, and lookback counters in
`radar/signal_monitoring/budgets.py` until a later runtime slice proves a shared
provider-level budget is needed there.

### `radar/candidate_discovery`

Owns the upstream search pipeline: finding and qualifying legal entities,
review-needed sites, branches, assets, and other candidate-universe entities.

Expected subpackages:

- `planning`: planner input, validation, acceptance, execution-plan projection;
- `retrieval`: live mini Radar definition builders, provider-neutral web
  retrieval contracts, retrieval task cards, and retrieved source material;
- `extraction`: structured extraction validation, repair, and diagnostics;
- `sources`: source obligations, registry/source orchestration, lookup terms;
- `universe`: recall-first upstream admission, candidate universe, entity
  resolution, retrieved candidates, candidate refs, gap payloads, and
  upstream/cross-source disambiguation;
- `checkpoints`: adaptive checkpoint policies and recovery actions;
- `search_expansion`: recall-first expansion planning, protected benchmark
  target metadata merge, selection, scheduling, targeted checkpoint expansion
  execution, payloads, and work admission;
- `execution`: phase executors and phase order;
- `diagnostics`: dossier/trace/journal-ready projection helpers.

### `radar/signal_monitoring`

Owns recurring checks over known candidates. It must stay separate from
candidate discovery because it has different cadence, budgets, source strategy,
model profile, and output states.

Current package-owned submodules:

- `contracts`: monitoring input/plan/task/observation/outcome records and the
  provider port.
- `source_strategy`: source-lane decisions for known, official, signal-specific,
  and open-web evidence lanes.
- `planning`, `budgets`, `payloads`, and `projection`: executor support
  components for task construction, bounded counters, payload repair, and
  product-safe observation shaping.
- `executor`: recorded/no-network orchestration facade.

It must not import candidate-discovery internals; data shared between candidate
discovery and signal monitoring must cross through shared contracts or explicit
source/candidate records.

### `radar/power_web_discovery`

Reserved for future account-access discovery: people, roles, relationships,
partner paths, influence structure, and buying-committee context.

## Component Contract

New Radar backend components should use stable names and responsibilities.

| Contract name | Meaning |
|---|---|
| `Input` | Immutable or value-like input record for one service or phase |
| `Result` | Successful service or phase output |
| `Decision` | Policy, admission, validation, capability, or checkpoint decision |
| `Issue` | Validation, schema, evidence-linking, policy, or budget problem |
| `Event` | Product-safe event for journal, dossier, trace, or report projection |
| `Service` | Component that owns a use-case decision or phase operation |

Pure helpers are allowed only when they stay local and obvious:

- private helpers such as `_normalize_name`;
- explicit projection helpers such as `source_summary` or `issue_payload`;
- small pure functions covered by targeted tests.

Public top-level functions should not become a hidden API between phases. If a
function carries phase state, budget state, source policy, or candidate-universe
mutation, it should become part of a service or a phase executor contract.

## Import Rules

The existing backend direction remains:

```text
API / CLI / workers / scheduler
  -> application services
    -> domain services + ports
      -> persistence / integrations / job adapters
```

Inside `application/radar`:

- `radar/shared` may be imported by pipeline packages;
- `radar/shared` must not import pipeline packages;
- candidate discovery must not import signal monitoring or Power Web discovery;
- signal monitoring must not import candidate-discovery internals except through
  shared records or explicit known-candidate/source references;
- provider SDKs and HTTP clients stay in `integrations`;
- SQLAlchemy and persistence adapters stay in `persistence`;
- FastAPI stays in `api`;
- Celery and scheduler entrypoints stay in `jobs`.

## Guardrails

Architecture tests enforce this rescue plan:

- no new root-level `src/power_web_os/application/live_radar_*.py` files outside
  the explicit migration allowlist;
- all root-level `live_radar_*`, `radar_search_*`, and `signal_monitoring_*`
  files must appear in
  `docs/architecture/radar/RADAR_ROOT_NAMESPACE_DEBT.md`;
- large/high-fan-out legacy modules must be documented as migration debt, and
  moved modules such as `live_radar_service.py` and
  `live_radar_staged_execution.py` must stay thin compatibility shims;
- production code and behavior tests must not import moved legacy paths; the
  failure message names the legacy import and the package-owned replacement;
- target Radar packages and the component contract must be named in this
  document;
- new backend Radar work should start from the package contract before adding
  modules or helpers.

The first guardrail intentionally does not move existing files. It prevents the
debt from growing while follow-up slices migrate code safely.

## Migration Slices

The roadmap tracks this rescue as several small slices:

1. `0.7.6.4.7` defines this package contract and guardrails.
2. `0.7.6.4.8` creates the package skeleton, local README files, and the
   declarative compatibility map.
3. `0.7.6.4.9` moves contracts, planning, source-card, retrieval-plan, and
   product-source modules behind compatibility shims.
4. `0.7.6.4.10` splits staged execution into phase executors.
5. `0.7.6.4.11` hardens validators and agent rules.
6. `0.7.6.4.11.1` decomposes execution helper debt and enforces the strict
   service API across the whole execution package.
7. `0.7.6.4.11.2` adds the execution architecture handbook, class docstring
   contract, and protocol-level service interface guardrails.
8. `0.7.6.4.12` removes the migrated staged-execution/service facade from the
   legacy allowlist and compatibility debt.

The rescue is complete, but the post-rescue refactor plan continues as small
bounded slices:

9. `0.7.6.4.13` replaces the broad `run_staged_radar_execution` kwargs
   boundary with a named `CandidateDiscoveryExecutionOptions` contract.
10. `0.7.6.4.14` moves `LiveRadarRunService` collaborator assembly into a
    package-owned composition/factory component so the facade stays a use-case
    boundary.
11. `0.7.6.4.14.1` records the full root namespace debt inventory, migrates
    behavior-test imports for moved modules, and adds guardrails against new
    usage of moved root paths.
12. Product corrective work stays deferred until the root namespace cleanup
    corridor is complete.
13. `0.7.6.4.15` moved checkpoint decision/action ownership into
    `radar/candidate_discovery/checkpoints`.
14. `0.7.6.4.16` moved search-expansion execution/payload/work-admission
    ownership into the candidate-discovery package.
15. `0.7.6.4.17` moved provider-level external-call budgets to
    `radar/shared/budgets` and kept candidate-discovery task/useful budgets
    pipeline-owned under `radar/candidate_discovery/execution`.
16. `0.7.6.4.17.1` moves live mini definition builders and web retrieval
    contracts into package-owned candidate-discovery retrieval modules.
17. `0.7.6.4.17.2` moves candidate universe, retrieved-candidate extraction,
    entity resolution, candidate refs, and upstream/cross-source
    disambiguation into package-owned universe modules.
18. `0.7.6.4.17.3` moved extraction, diagnostics, normalization,
    collection/pipeline support, and source-risk helpers.
19. `0.7.6.4.18` moved root-level signal-monitoring behavior into
    `radar/signal_monitoring`.
20. `0.7.6.4.18.1` split candidate discovery and signal monitoring runtime:
    discovery now emits handoff statuses by default.
21. `0.7.6.4.19` closes or sunsets remaining root Radar-prefixed files.
22. `0.7.6.4.18.1.2` merges the older `0.7.6.3.6.6` fallback scope into
    current candidate-discovery recovery and adds deterministic
    post-extraction salvage before signal-monitoring live runtime resumes.
23. Product corrective work resumes with signal-monitoring live runtime and
    model-role evaluation only after live candidate-discovery smoke reaches
    expansion and benchmark target-funnel diagnostics.

## Remaining Migration Debt

The architecture rescue for staged execution and the service facade is complete,
but not every root-level `live_radar_*` module has moved. Deferred legacy
modules must be migrated through their own slices when their behavior changes or
when their target package becomes mature enough. Until then, they remain
explicit migration debt and must not be copied as patterns for new code.
