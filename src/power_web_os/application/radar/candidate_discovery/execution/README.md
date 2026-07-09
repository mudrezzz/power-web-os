# Candidate Discovery Execution

## Ownership

Owns candidate-discovery phase orchestration, scheduler admission, search
expansion execution, budget-sensitive execution order, and migration of staged
executor behavior.

Detailed architecture handbook:
`docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md`.
Read it before changing this package.

## Phase map

- `context.py`: `CandidateDiscoveryExecutionContext` and `PhaseResult`.
- `options.py`: `CandidateDiscoveryExecutionOptions`, the named staged
  execution option contract used by the compatibility wrapper and live service.
- `signal_modes.py`: private normalization and type contract for candidate
  discovery signal execution mode (`handoff` or explicit inline compatibility).
- `state.py`: `CandidateDiscoveryExecutionState`, the mutable cross-phase state.
- `task_budget.py`: candidate-discovery task budget settings, semantic task
  reserve admission, counters, warnings, and exhaustion event payloads.
- `useful_budget.py`: useful-result retry budget, result assessment, and retry
  task shaping for discovery/coverage tasks.
- `orchestrator.py`: public `run_staged_radar_execution` wrapper and
  `CandidateDiscoveryOrchestrator` phase order only.
- `discovery.py`: `DiscoveryPhaseExecutor` for discovery tasks,
  retrieved-candidate extraction, cross-source disambiguation, first checkpoint
  recovery, and gate pass.
- `gates.py`: `GatePhaseExecutor` for qualification gate execution used by
  discovery and coverage.
- `coverage.py`: `CoveragePhaseExecutor` for iterative coverage tasks and
  after-coverage checkpoint recovery.
- `expansion.py`: `ExpansionPhaseExecutor` for expansion phase flow and
  execution of admitted expansion tasks through package-owned
  `search_expansion` planning, scheduling, payload, and admission services.
- `expansion_diagnostics.py`: expansion target summaries, guarantee state, and
  report-safe diagnostics.
- `signals.py`: `CandidateDiscoverySignalHandoffProjector` for normal
  signal-monitoring handoff projection and `SignalCompatibilityPhaseExecutor`
  for explicit legacy inline signal-search compatibility.
- `finalization.py`: `FinalizationProjector` for final provider result,
  events, candidate universe, budget metadata, source obligations, and
  dossier/report payload.
- `finalization_metadata.py`: private small summary helpers used by finalization.
- `finalization_signals.py`: private signal handoff metadata helpers used by
  finalization.
- `finalization_universe.py`: review-needed upstream entity projection.
- `reconciliation.py`: `CandidateDiscoveryOutcomeReconciler` for public
  candidate, universe-only lead, diagnostic gap, product-acceptance, and
  projection-reason ledger output.
- `public_surface.py`: `CandidateDiscoveryPublicSurfaceProjector` and
  `CandidateDiscoveryProductAcceptancePromoter` for the `user_visible_candidates`
  surface. It shows accepted product candidates and review-needed legal
  candidates separately from universe-only diagnostics, and promotes only
  already selected source-backed legal public rows.
- `task_runner.py`: `TaskExecutionService` for provider-neutral task execution,
  gate passes, retries, and candidate task utilities.
- `task_runner_payloads.py`: private small payload/schema helpers used by task execution.
- `service_contracts.py`: protocol-level service interfaces for phase executors,
  projectors, deterministic policies, and payload factories.
- `merge.py`: `ExecutionResultMerger` for result merge and entity metadata projection.
- `projection.py`: `CandidateProjectionService` and `PipelineEventFactory`.

## Service Contract

Every stateful phase operation should be a method on a service/projector class.
The normal signature is:

```python
executor.run(context: CandidateDiscoveryExecutionContext, state: CandidateDiscoveryExecutionState, ...)
```

Use `context` for dependencies and limits that should not be mutated by a phase.
Use `state` for shared execution data that phases intentionally mutate. Return
`PhaseResult` only for compact status/reason reporting; do not return another
copy of all sources, observations, events, budgets, and metadata.

`run_staged_radar_execution` remains the public compatibility wrapper for old
callers, but package-owned code should pass a
`CandidateDiscoveryExecutionOptions` instance instead of broad execution kwargs.
The default `signal_execution_mode` is `handoff`; old inline signal-search
execution must be requested explicitly with `inline_compatibility`.

Every public class must have a docstring that states:

- `Owns:`
- `Does not own:`
- `Architecture:`
- a link to
  `docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#...`

## Allowed imports

- `power_web_os.application.radar.shared`.
- `power_web_os.application.radar.shared.budgets` for provider-level
  external-call budget accounting.
- Candidate-discovery phase packages.
- Provider ports and provider-neutral task/result records.

## Forbidden imports

- FastAPI routes, SQLAlchemy models/sessions, Celery entrypoints, Redis
  clients, direct HTTP clients, provider SDKs, dotenv, and legacy
  `live_radar_*` modules from new package code.

## How to extend

Keep orchestration thin and explicit. If logic belongs to planning, sources,
extraction, universe, or diagnostics, add it to that phase package instead of
growing the executor.

When changing staged execution, prefer adding a method or helper inside the
phase that owns the behavior. Do not add new logic to root-level
`live_radar_staged_*.py`; those files are compatibility shims only.

Search-expansion strategy, target/variant records, deterministic selection,
guaranteed-lane scheduling, checkpoint targeted expansion execution, payload
helpers, and work admission belong in
`candidate_discovery/search_expansion`, not in root-level `radar_search_*` or
`radar_work_scheduler*` modules.

Do not add public top-level phase functions. Public execution behavior belongs
to `CandidateDiscoveryOrchestrator`, `DiscoveryPhaseExecutor`,
`GatePhaseExecutor`, `CoveragePhaseExecutor`, `ExpansionPhaseExecutor`,
`CandidateDiscoverySignalHandoffProjector`,
`SignalCompatibilityPhaseExecutor`, `FinalizationProjector`,
`CandidateDiscoveryOutcomeReconciler`,
`CandidateDiscoveryPublicSurfaceProjector`, `TaskExecutionService`,
`ExecutionResultMerger`, `CandidateProjectionService`,
`PipelineEventFactory`, `SmokeLimitPolicy`, or
`ExecutionMetadataFactory`. Private `_helper` functions are acceptable only for
small local pure transformations and product-safe payload/summary builders.
Do not hide phase behavior inside a large private function called by a service
method; architecture tests should catch that pattern.
