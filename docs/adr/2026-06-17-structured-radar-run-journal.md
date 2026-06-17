# ADR: Structured Radar Run Journal And Reasoning Audit

## Status

Accepted.

## Context

Live Radar runs need a durable audit trail for planning, execution, evidence
extraction, scoring, and validation. Future planner/executor/evaluator
workflows must be able to add richer audit information without redesigning the
database every time the workflow shape changes.

The audit trail must not store or display raw hidden chain-of-thought. Product
users need explainable artifacts, not private model traces.

## Decision

Persist an append-only `radar_run_events` table owned by the backend
persistence layer and exposed through application records and ports.

Application services own event semantics. Persistence stores
`RadarRunEventRecord` values and does not decide scoring, review, provider, or
workflow meaning. API routes map records to transport DTOs. Frontend screens
display structured summaries from the API-backed journal and use artifact
metadata only as an offline fallback.

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

## Consequences

- `radar_runs` remains the authoritative durable run state.
- `radar_run_outputs` remains the immutable output snapshot.
- `radar_run_events` becomes the append-only reasoning/audit timeline.
- Celery and Redis remain execution infrastructure only; they do not own audit
  or product truth.
- Future planner/executor/evaluator nodes can emit the same event contract
  instead of requiring a schema rewrite.
- Debug visibility is allowed in the contract, but product UI should display
  user/operator audit summaries by default.
