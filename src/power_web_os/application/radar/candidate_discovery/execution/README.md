# Candidate Discovery Execution

## Ownership

Owns candidate-discovery phase orchestration, scheduler admission, search
expansion execution, budget-sensitive execution order, and migration of staged
executor behavior.

## Phase map

- `context.py`: `CandidateDiscoveryExecutionContext` and `PhaseResult`.
- `state.py`: `CandidateDiscoveryExecutionState`, the mutable cross-phase state.
- `orchestrator.py`: public `run_staged_radar_execution` wrapper and
  `CandidateDiscoveryOrchestrator` phase order only.
- `discovery.py`: `DiscoveryPhaseExecutor` for discovery tasks,
  retrieved-candidate extraction, cross-source disambiguation, first checkpoint
  recovery, and gate pass.
- `gates.py`: `GatePhaseExecutor` for qualification gate execution used by
  discovery and coverage.
- `coverage.py`: `CoveragePhaseExecutor` for iterative coverage tasks and
  after-coverage checkpoint recovery.
- `expansion.py`: `ExpansionPhaseExecutor` for search expansion execution
  through scheduler/admission and budget guards.
- `expansion_diagnostics.py`: expansion target summaries, guarantee state, and
  report-safe diagnostics.
- `signals.py`: `SignalCompatibilityPhaseExecutor` for the legacy
  candidate-discovery signal-search projection.
- `finalization.py`: `FinalizationProjector` for final provider result,
  events, candidate universe, budget metadata, source obligations, and
  dossier/report payload.
- `finalization_universe.py`: review-needed upstream entity projection.
- `task_runner.py`, `merge.py`, `projection.py`: provider-neutral task
  execution helpers, result merging, and artifact projection.

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

## Allowed imports

- `power_web_os.application.radar.shared`.
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

Do not add public top-level phase functions. Public execution behavior belongs
to `CandidateDiscoveryOrchestrator`, `DiscoveryPhaseExecutor`,
`GatePhaseExecutor`, `CoveragePhaseExecutor`, `ExpansionPhaseExecutor`,
`SignalCompatibilityPhaseExecutor`, or `FinalizationProjector`. Private
`_helper` functions are acceptable for local pure transformations or preserved
implementation details during migration.
