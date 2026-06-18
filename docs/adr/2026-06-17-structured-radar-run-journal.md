# ADR: Structured Radar Run Journal And Reasoning Audit

## Status

Accepted.

## Context

Live Radar runs need a durable audit trail for planning, execution, evidence
extraction, scoring, and validation. Future planner/executor/evaluator
workflows must be able to add richer audit information without redesigning the
database every time the workflow shape changes.

The audit trail must not store or display raw hidden chain-of-thought. Product
users need explainable artifacts, not private model traces. Developers also need
sanitized technical traces for debugging provider requests, responses,
normalization, and validation before broader benchmark runs.

## Decision

Persist an append-only `radar_run_events` table owned by the backend
persistence layer and exposed through application records and ports.

Application services own event semantics. Persistence stores
`RadarRunEventRecord` values and does not decide scoring, review, provider, or
workflow meaning. API routes map records to transport DTOs. Frontend screens
display structured summaries from the API-backed journal and use artifact
metadata only as an offline fallback.

Live Radar execution emits journal-ready events from explicit application
pipeline phases: planning, provider collection, source normalization, candidate
extraction, candidate evaluation, validation, and artifact shaping. Workflow
wrappers map optional LangGraph nodes onto those phases; they do not own the
event semantics. Artifact-derived journal events remain a compatibility fallback
for older snapshots and fake executors.

Allowed audit payloads include:

- lifecycle events such as `run_queued`, `run_started`, `run_completed`, and
  `run_failed`;
- planning summaries and search query plans;
- provider/source collection outcomes;
- candidate extraction summaries;
- qualification, signal, and score explanation summaries;
- validation warnings and self-check summaries;
- source and candidate references.

Forbidden payloads include raw hidden reasoning keys such as
`chain_of_thought`, `hidden_reasoning`, and `internal_thoughts`.

Product run inspection and developer trace are separate projections:

- `radar_run_events` and `/journal` provide ordered product/operator audit
  summaries.
- `/dossier` composes run context, definition snapshot, search plan, source
  usage, validation, and non-debug events into a product-readable run dossier.
- `radar_run_technical_traces` and `/technical-trace` store sanitized
  developer/admin trace records for pipeline inputs/outputs,
  provider-request/response/error payloads, normalization results, and
  validation results.

Technical trace payloads are redacted before persistence. Secret-like keys and
values are masked, long strings are capped with a redaction report, and raw
hidden reasoning keys are rejected. The trace surface is visible in local/dev UI
for now and should be authorization-gated later.

## Consequences

- `radar_runs` remains the authoritative durable run state.
- `radar_run_outputs` remains the immutable output snapshot.
- `radar_run_events` becomes the append-only reasoning/audit timeline.
- `radar_run_technical_traces` becomes the append-only sanitized developer trace
  timeline.
- Celery and Redis remain execution infrastructure only; they do not own audit
  or product truth.
- Future planner/executor/evaluator nodes can extend the same application phase
  and event contracts instead of requiring a schema rewrite.
- Debug visibility is allowed in the contract, but product UI should display
  user/operator audit summaries by default.
