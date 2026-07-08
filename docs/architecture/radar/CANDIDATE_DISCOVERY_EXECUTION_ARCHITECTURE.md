# Candidate Discovery Execution Architecture

This handbook is the procedural architecture contract for
`src/power_web_os/application/radar/candidate_discovery/execution`.
The broader product pipeline remains documented in
`docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md`; this file explains how the backend
execution components are organized so future changes do not recreate another
large procedural module.

## Purpose

Candidate discovery execution turns an accepted Radar execution plan into:

- retrieved sources;
- candidate observations;
- review-needed upstream universe rows;
- upstream discovery outcomes and product acceptance statuses;
- checkpoint decisions;
- search expansion diagnostics;
- signal-monitoring handoff statuses;
- final provider result, events, and metadata used by dossier/report mappers.

The package is an application-layer use case. It may depend on provider ports
and application services, but it must not import FastAPI, SQLAlchemy, Celery,
Redis, direct HTTP clients, provider SDKs, or dotenv.

## Read This First

Before changing candidate-discovery execution, read these files in order:

1. `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md` for product-level pipeline
   behavior.
2. `docs/architecture/RADAR_BACKEND_ARCHITECTURE.md` for package boundaries.
3. This handbook for execution services, contracts, and ownership.
4. `src/power_web_os/application/radar/candidate_discovery/execution/README.md`
   for local package rules.

The behavior rule is strict: refactors inside this package must preserve stage
order, checkpoint semantics, expansion diagnostics, budget counters, candidate
universe shape, signal `not_searched_*` projection, and compatibility wrapper
return shape unless a dedicated product slice explicitly changes them.

## Execution Flow

```text
run_staged_radar_execution compatibility wrapper
  -> normalizes legacy kwargs or named CandidateDiscoveryExecutionOptions
  -> builds CandidateDiscoveryExecutionContext
  -> creates CandidateDiscoveryExecutionState
  -> CandidateDiscoveryOrchestrator.run
       -> DiscoveryPhaseExecutor.run
       -> CoveragePhaseExecutor.run
       -> ExpansionPhaseExecutor.run
       -> CoveragePhaseExecutor.recover_after_coverage
       -> DiscoveryPhaseExecutor.extract_retrieved_candidates
       -> universe cross-source disambiguation service
       -> SignalCompatibilityPhaseExecutor.review_before_search
       -> CandidateDiscoverySignalHandoffProjector.run
          or explicit inline_compatibility SignalCompatibilityPhaseExecutor.run
       -> FinalizationProjector.project
```

The orchestrator owns the order only. Phase services own their stage behavior.
Shared dependencies live in context. Cross-phase mutable data lives in state.

## Service Interface Contract

### Phase Executor

A phase executor is a class with a stable `phase_name` and a `run(context,
state, ...)` method. It may mutate `CandidateDiscoveryExecutionState`. It must
not return another copy of sources, observations, metadata, budgets, and events.
Use `PhaseResult` only for compact phase status and reason.

Interface marker: `CandidateDiscoveryPhaseExecutor`.

### Projector

A projector converts completed state to product-safe artifacts. It should not
run provider tasks or change checkpoint decisions.

Interface marker: `CandidateDiscoveryProjector`.

### Policy

A policy returns deterministic decisions from explicit inputs. It does not call
providers and does not mutate state.

Interface marker: `CandidateDiscoveryPolicy`.

### Factory

A factory builds payloads, summaries, DTO-like records, or service instances
from explicit inputs. It does not perform provider execution or budget
admission.

Interface marker: `CandidateDiscoveryFactory`.

### Public API Rules

Public classes are allowed. Public top-level execution functions are not
allowed, except the compatibility wrapper `run_staged_radar_execution`.

Private helper functions are acceptable only for small local transformations,
payload builders, or summaries. A service method that only delegates to one
large private function violates this contract.

## Component Map

### `CandidateDiscoveryExecutionContext`

Owns immutable-ish dependencies and limits for one run: radar payload,
execution plan, retrieval plan, provider port, task budget, external-call
budget, checkpoint services, expansion service, work scheduler, verification
cache, source policy decisions, and hard execution limits.

Does not own mutable sources, observations, provider metadata, events, candidate
scope, or checkpoint records.

### `CandidateDiscoveryExecutionOptions`

Owns provider-neutral staged execution options for one run: task-context
overrides, semantic task budget limits, useful-result retry limits, checkpoint
limits, external-call budget settings, smoke caps, reserve maps, run profile,
and source policy decisions.

Does not own provider ports, phase order, mutable execution state, budget
counters, checkpoint decisions, or final artifact projection.

The default `signal_execution_mode` is `handoff`. Candidate discovery therefore
projects `not_searched_pending_signal_monitoring` statuses after the pre-signal
checkpoint instead of executing signal provider tasks. The legacy
`inline_compatibility` mode is explicit and exists only for old callers and
tests while runtime split closure continues.

### `RadarExecutionBudgetSettings`

Owns candidate-discovery hard task limits and semantic task reserve limits for
one staged run.

Does not own provider-level external-call settings or signal-monitoring budget
policy.

### `RadarBudgetDecision`

Owns candidate-discovery task admission state: accepted/rejected result,
budget key, limit, current count, reason, message, reserve key, and semantic
reserve flag.

Does not own provider-call counters, checkpoint decisions, or final artifact
projection.

### `RadarExecutionBudget`

Owns candidate-discovery task admission, semantic task reserve decisions,
per-stage/per-subject counters, budget warnings, and exhaustion event payloads.
It lives in `execution/task_budget.py` because its keys are derived from
`RadarExecutionTask` stages and candidate-discovery candidate scope.

Does not own provider-level external-call accounting, source-verification
request accounting, retry records, or reserve metadata. Those live in
`radar/shared/budgets`.

### `SubjectTaskBudget`

Owns compatibility construction of candidate-discovery task budgets from the
old single subject limit.

Does not own new task-budget policy, external budgets, or signal-monitoring
budgets.

### `UsefulResultBudget`

Owns discovery/coverage useful-result thresholds and bounded retry task
shaping for candidate-discovery provider results.

Does not own hard task admission, external-call limits, checkpoint recovery, or
signal-monitoring budgets.

### `CandidateDiscoveryExecutionState`

Owns mutable cross-phase data: sources, observations, provider metadata, events,
executed task ids, completed qualification ids, gate results, candidate scope,
coverage checks, unresolved gaps, warnings, checkpoint decisions, expansion
diagnostics, and signal statuses.

Does not own dependencies, provider ports, budgets, services, or immutable run
limits.

### `PhaseResult`

Owns compact phase status: phase name, status, and reason. It intentionally does
not transport full execution state.

### `CandidateDiscoveryOrchestrator`

Owns phase order and compatibility flow. It wires phase services together and
hands completed state to finalization.

Does not own provider calls, checkpoint internals, expansion scheduling,
coverage iteration, candidate projection, or event payload creation.

### `DiscoveryPhaseExecutor`

Owns the beginning of candidate discovery: discovery tasks, useful-result
retries, invocation of universe-owned retrieved-candidate extraction and
cross-source disambiguation services, first checkpoint recovery, initial
qualification gates, and smoke candidate-scope capping.

It does not own recall-first upstream admission rules. Those live in
`radar/candidate_discovery/universe/admission.py` and are applied during
candidate normalization/final projection.

### `GatePhaseExecutor`

Owns qualification gate execution for an explicit task list and candidate scope.
It delegates provider task running and merge details to `TaskExecutionService`.

### `CoveragePhaseExecutor`

Owns iterative coverage tasks, gap observation merge, coverage records, gates
for newly discovered names, candidate-scope refresh, and after-coverage
checkpoint recovery.

### `ExpansionPhaseExecutor`

Owns the candidate-discovery expansion phase flow after weak
discovery/coverage: request an expansion plan, persist diagnostics, schedule
approved variants, ask the work scheduler for admission, execute admitted
provider tasks, merge returned sources/observations, and emit expansion events.

Does not own search-expansion planning, target/variant records, deterministic
selection, lane scheduling rules, targeted checkpoint expansion execution, or
work-admission contracts. Those live in
`radar/candidate_discovery/search_expansion`.

### `SignalCompatibilityPhaseExecutor`

Owns the legacy signal-search stage still embedded inside candidate discovery
for explicit `inline_compatibility` runs. It records the pre-signal checkpoint,
runs compatibility signal tasks when allowed, and projects `not_searched_*`
statuses when candidate discovery is stopped or policy-limited.

It does not own the standalone `signal-monitoring` pipeline.

### `CandidateDiscoverySignalHandoffProjector`

Owns normal candidate-discovery signal handoff projection after the pre-signal
checkpoint. It sets `signal_task_count` to zero, preserves candidate/signal
scope visibility, and projects `not_searched_pending_signal_monitoring` records
for signal tasks that must be evaluated by a separate signal-monitoring run.

It does not call providers, count signal-monitoring budgets, or project
`not_observed`. If the pre-signal checkpoint blocks the run, it preserves the
existing policy-limited/stopped-for-review not-searched status.

### `FinalizationProjector`

Owns final artifact projection: warnings, extraction issues, smoke promotion
cap metadata, candidate universe, source obligations, checkpoint metadata,
budget/cache metadata, expansion/work scheduler metadata, registry metadata,
coverage metadata, final `WebSearchProviderResult`, and events.

It does not own provider task execution, checkpoint decisions, or expansion
target selection.

For benchmark runs, finalization may project benchmark-present source
diagnostics into review-needed upstream universe rows. It must use only
product-safe source diagnostics and must not inspect prompts or hidden provider
text.

### `CandidateDiscoveryOutcomeReconciler`

Owns the product-safe ledger that reconciles raw upstream leads, public
candidate rows, candidate-universe-only rows, diagnostic gaps, product
acceptance status, and public projection reasons. Every retained upstream lead
must have a `public_result_status`, `public_projection_reason`, and
`product_acceptance_reason`; `unexplained_drop_count` must stay zero for a run
to satisfy the candidate-discovery DoD.

It does not own retrieval, extraction, admission, product acceptance policy,
signal monitoring, or benchmark scoring. It only makes the already projected
candidate-discovery output auditable.

### `CandidateDiscoveryUpstreamAdmissionPolicy`

Owns deterministic recall-first upstream retention:
source-backed retrieved candidates, official-domain promotion, concrete
registry identity retention, and the split between upstream discovery and
strict product acceptance.

It does not own signal-monitoring execution, provider calls, or manual product
account approval. Normal candidate discovery must not require observed signal
evidence to retain upstream leads.

Extraction validation and diagnostic-state rules live in
`radar/candidate_discovery/extraction`. Candidate normalization, collection
helpers, and product-safe pipeline trace/event helpers live in
`radar/candidate_discovery/diagnostics`. Source verification-risk helpers live
in `radar/candidate_discovery/sources/risk.py`. Execution services invoke these
contracts but should not recreate extraction repair, normalization, or source
risk policy inline.

### `ExtractionFailureClassifier`

Owns provider-neutral extraction failure categories used by checkpoint recovery:
schema-invalid empty output, schema-invalid output with usable source
diagnostics, unlinked source refs, backup schema invalid, retry budget
exhaustion, and unrecoverable no-source-text cases.

It does not own provider retries, backup model choice, checkpoint decision
selection, or candidate projection.

### `PostExtractionSalvageService`

Owns deterministic post-extraction salvage after bounded extraction recovery
fails. It may materialize review-needed upstream observations only from
product-safe source title/snippet/URL diagnostics with source refs, and it
records explicit recovered or unrecovered metadata.

It does not own OpenRouter calls, raw provider payload inspection, hidden
reasoning, signal monitoring, or downstream product acceptance.

### `TaskExecutionService`

Owns provider-port task execution, task budget reservation, schema-invalid
provider retry loop, gate pass execution, candidate task utilities, and
candidate/source dedupe utilities.

It does not own phase order, checkpoint policy, expansion target selection, or
final dossier projection.

### `ExecutionResultMerger`

Owns source dedupe, provider metadata merge, entity-resolution merge, candidate
observation consolidation, and candidate-universe metadata enrichment.

It delegates entity-resolution rules and provider metadata merge semantics to
`radar/candidate_discovery/universe`; it does not classify entity types itself.

### `CandidateProjectionService`

Owns conversion from merged observations to normalized candidates, gate
summaries, rejected candidate summaries, and signal-status enrichment for
candidate universe rows.

### `PipelineEventFactory`

Owns product-safe event payloads: task execution events, candidate filtered
events, signal planned events, budget warnings, source obligation events, and
not-searched signal observations.

### `SmokeLimitPolicy`

Owns smoke-profile truncation for candidate and signal lists. It is deliberately
small and deterministic.

### `ExecutionMetadataFactory`

Owns initial provider metadata derived from product-safe benchmark task context.
It does not project final metadata.

### `CandidateDiscoveryPhaseExecutor`

Protocol for stateful phase services. Implementations have `phase_name` and
`run(context, state, ...)`.

### `CandidateDiscoveryProjector`

Protocol for final projectors. Implementations have `project(context, state)`.

### `CandidateDiscoveryPolicy`

Protocol for deterministic policies. Implementations expose a narrow decision
method and must not call providers or mutate state.

### `CandidateDiscoveryFactory`

Protocol for product-safe factories and payload builders.

## Extension Recipes

### Add A New Execution Phase

1. Add a service class in the owning phase module or a new small module.
2. Give it a `phase_name`.
3. Add a class docstring with `Owns`, `Does not own`, and an `Architecture`
   link to this handbook.
4. Accept `CandidateDiscoveryExecutionContext` and
   `CandidateDiscoveryExecutionState`.
5. Mutate state intentionally; return `PhaseResult` only for status.
6. Wire it in `CandidateDiscoveryOrchestrator`.
7. Add tests for behavior and architecture guardrails.

### Change Expansion Behavior

Change `ExpansionPhaseExecutor` only when the behavior is phase flow or
execution of already planned expansion work. Source-profile strategy, target
generation, variant selection, guaranteed-lane scheduling, checkpoint targeted
expansion execution, and work admission live in
`radar/candidate_discovery/search_expansion`. Evaluation matching lives outside
this phase.

### Change Candidate Universe Projection

Projection changes belong in `FinalizationProjector`,
`CandidateProjectionService`, `ExecutionResultMerger`, or the universe package.
Do not hide candidate-universe changes in discovery, coverage, or expansion.

### Change Budget Behavior

Task execution budget reservation belongs in `TaskExecutionService`. Work
ordering and admission belong in the scheduler. Final budget reporting belongs
in `FinalizationProjector`.

### Change Checkpoint Behavior

Checkpoint policy stays in `radar/candidate_discovery/checkpoints`.
`models.py` owns checkpoint records, `policy.py` owns deterministic review
decisions, `recording.py` owns checkpoint event/state recording, and
`recovery.py` owns bounded adaptive action execution. `recovery_salvage.py`
owns the checkpoint-specific integration between extraction salvage and recovery
state. Execution phases may call checkpoint recovery/recording and persist the
resulting decisions, but they should not invent new checkpoint policy inline or
import root checkpoint shims.

### Change Extraction Or Diagnostics Behavior

Extraction payload validation and deterministic repair belong in
`radar/candidate_discovery/extraction`. Post-extraction salvage also belongs
there; checkpoint code may invoke it but must not reimplement source scanning or
upstream-admission decisions. Candidate normalization, collection helpers,
trace/event support, and product-safe artifact helpers belong in
`radar/candidate_discovery/diagnostics`. Source verification-risk helpers belong
in `radar/candidate_discovery/sources/risk.py`. Do not import root `live_radar_*`
shims from execution code.

## Documentation Rules

Every public class in this package must have a docstring with:

- `Owns:`
- `Does not own:`
- `Architecture:`
- a link to this handbook section for the class.

The handbook must mention every public execution class. This is enforced by
architecture tests.

## Validation Rules

Relevant guards live in `tests/test_backend_architecture_contract.py` and
`tests/test_radar_backend_package_contract.py`.

They must catch:

- a new root-level `application/live_radar_*.py`;
- a public top-level execution function other than the compatibility wrapper;
- long helper functions that should be decomposed;
- public execution classes without handbook docstrings;
- phase executors without `phase_name`;
- missing service protocol exports;
- forbidden infrastructure imports in `application/radar/...`.

For behavior preservation during refactor slices, run the adaptive/live/budget
tests listed in the active roadmap slice.
