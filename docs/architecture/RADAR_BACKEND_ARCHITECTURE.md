# Radar Backend Architecture

This document is the backend-side map for Radar pipeline code. It complements
the product pipeline AS IS/TO BE documents under `docs/radar/` by answering a
different question: where backend code belongs and how new components should be
shaped.

Candidate-discovery execution has a dedicated procedural handbook:
`docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md`.
Use it together with this document before changing phase executors, execution
state, finalization, task running, or projection services.

## Purpose

Radar backend code must remain understandable as candidate discovery, signal
monitoring, and future Power Web discovery grow. The current implementation is
functionally useful, but the backend package shape has become too flat. This
document records the current debt, the target package structure, and the
component contract that future slices must follow.

Runtime behavior is unchanged by this architecture slice.

## AS IS Inventory

Current candidate-discovery backend logic lives mostly in root-level
`src/power_web_os/application/live_radar_*.py` modules.

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
backend work.

### Hotspots

| Module | Current issue | Target treatment |
|---|---|---|
| `live_radar_staged_execution.py` | Former large phase executor with many helpers and high application import fan-out | Moved to candidate-discovery phase executors; root file is now a thin compatibility shim |
| `live_radar_service.py` | Former large service facade that shaped a full live run artifact | Moved to `radar/candidate_discovery/service.py`; root file is now a thin compatibility shim |
| `live_radar_search_expansion_execution.py` | Expansion execution imports many phase helpers | Move under candidate-discovery expansion/execution package |
| `live_radar_checkpoint_actions.py` | Checkpoint action and recovery logic mixes phase execution concerns | Move under candidate-discovery checkpoint package |

### Current Responsibility Map

| Current module group | Responsibility | Target package |
|---|---|---|
| `live_radar_contracts.py` | Provider-neutral DTOs and ports | `radar/shared/` and `radar/candidate_discovery/contracts.py` |
| `live_radar_definition*.py` | Legacy live definition and persisted definition runtime mapping | `radar/shared/definition/` or candidate-discovery runtime adapters |
| `live_radar_discovery_planning.py`, `live_radar_plan_acceptance.py`, `live_radar_planning_pipeline.py`, `live_radar_execution_plan.py`, `live_radar_retrieval_plan.py` | Planning, validation, acceptance, and executable plan projection | `radar/candidate_discovery/planning/` |
| `live_radar_web_retrieval.py`, `live_radar_product_sources.py` | Provider-neutral retrieval/source material | `radar/candidate_discovery/retrieval/` |
| `live_radar_extraction_contract.py`, `live_radar_extraction_diagnostics.py` | Extraction schema validation, repair, and diagnostics | `radar/candidate_discovery/extraction/` |
| `live_radar_source_cards.py`, `radar_source_obligations.py`, connector/capability helpers | Source capability, source-card, and obligation rules | `radar/shared/sources/` and `radar/candidate_discovery/sources/` |
| `radar_source_providers.py`, registry lookup helpers, lookup term generators | Provider-neutral registry/source orchestration | `radar/candidate_discovery/sources/` |
| `live_radar_entity_resolution.py`, `live_radar_universe.py`, `live_radar_retrieved_candidates.py`, `live_radar_candidate_refs.py`, `radar_upstream_disambiguation.py` | Candidate universe, entity resolution, retrieved candidate extraction | `radar/candidate_discovery/universe/` |
| `live_radar_checkpoints.py`, `live_radar_checkpoint_actions.py`, `live_radar_checkpoint_execution.py` | Adaptive checkpoint decisions and action execution | `radar/candidate_discovery/checkpoints/` |
| `radar_search_expansion*.py`, `radar_work_scheduler*.py`, external budget helpers | Search expansion, scheduler admission, and budget diagnostics | `radar/candidate_discovery/execution/` and `radar/shared/budgets/` |
| `live_radar_staged_execution.py`, `live_radar_staged_helpers.py`, `live_radar_staged_merge.py`, `live_radar_staged_support.py`, `live_radar_cross_disambiguation.py`, `live_radar_useful_budget.py` | Candidate-discovery staged execution and phase helper logic | `radar/candidate_discovery/execution/` |
| `live_radar_normalization.py`, `live_radar_collection_utils.py`, `live_radar_pipeline_support.py`, diagnostics helpers | Artifact shaping and product-safe projections | `radar/candidate_discovery/diagnostics/` or phase-owned projection modules |
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
| `signals.py` | `SignalCompatibilityPhaseExecutor`: preserve the compatibility signal-search stage and `not_searched_*` projection. |
| `finalization.py` | `FinalizationProjector`: build final `WebSearchProviderResult`, event list, and dossier/report metadata. |
| `finalization_universe.py` | Add review-needed upstream entities and upstream disambiguation events. |
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
  `SignalCompatibilityPhaseExecutor.run`, and `FinalizationProjector.project`.
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
`radar/candidate_discovery/diagnostics/live_run_artifact.py`. Service-adjacent
runtime policies are named package-owned components:
`LiveRadarTaskContextReader` owns typed task-context access for staged execution
options, `ExternalBudgetMetadataMerger` owns planner/execution budget metadata
merging, and `LiveRadarEventStateProjector` owns event-list projection. The old
root-level `live_radar_service.py` file is a compatibility shim for existing
imports and must not regain behavior.

Deferred modules, including `live_radar_definition.py`,
`live_radar_pipeline_support.py`, checkpoints, extraction, universe, and
diagnostics helpers, remain legacy migration debt until their own slices move
them. `live_radar_search_expansion_execution.py` and
`live_radar_checkpoint_actions.py` are the remaining documented Radar
application hotspots; they are not examples for new backend work.

### `radar/shared`

Owns contracts and utilities that are genuinely common across Radar pipelines:

- source capability cards and source eligibility primitives;
- model/runtime profile summaries;
- budget records that are not candidate-discovery-specific;
- product-safe event/issue shapes reused by multiple pipelines.

It must not import candidate discovery, signal monitoring, or Power Web
discovery packages.

### `radar/candidate_discovery`

Owns the upstream search pipeline: finding and qualifying legal entities,
review-needed sites, branches, assets, and other candidate-universe entities.

Expected subpackages:

- `planning`: planner input, validation, acceptance, execution-plan projection;
- `retrieval`: retrieval task cards and retrieved source material;
- `extraction`: structured extraction validation, repair, and diagnostics;
- `sources`: source obligations, registry/source orchestration, lookup terms;
- `universe`: candidate universe, entity resolution, retrieved candidates;
- `checkpoints`: adaptive checkpoint policies and recovery actions;
- `execution`: phase executors, search expansion, scheduler admission;
- `diagnostics`: dossier/trace/journal-ready projection helpers.

### `radar/signal_monitoring`

Owns recurring checks over known candidates. It must stay separate from
candidate discovery because it has different cadence, budgets, source strategy,
model profile, and output states.

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
- large/high-fan-out legacy modules must be documented as migration debt, and
  moved modules such as `live_radar_service.py` and
  `live_radar_staged_execution.py` must stay thin compatibility shims;
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
11. Product corrective work resumes after that, starting with the already
    planned `0.7.6.3.6.6` post-extraction fallback materialization and
    `0.7.6.3.7` model-role evaluation slices, unless a blocking architecture
    regression appears.
12. `0.7.6.4.15` moves checkpoint decision/action ownership into
    `radar/candidate_discovery/checkpoints`.
13. `0.7.6.4.16` moves search-expansion execution/payload ownership into the
    candidate-discovery package.
14. `0.7.6.4.17` assesses shared budget contracts and extracts only genuinely
    shared budget records/services to `radar/shared/budgets`.

## Remaining Migration Debt

The architecture rescue for staged execution and the service facade is complete,
but not every root-level `live_radar_*` module has moved. Deferred legacy
modules must be migrated through their own slices when their behavior changes or
when their target package becomes mature enough. Until then, they remain
explicit migration debt and must not be copied as patterns for new code.
