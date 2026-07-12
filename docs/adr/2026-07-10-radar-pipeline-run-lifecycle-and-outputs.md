# ADR: Shared Radar Run Lifecycle And Pipeline-Specific Outputs

## Status

Accepted

## Context

Candidate discovery and signal monitoring need the same durable queued/running/
terminal lifecycle, journal, correlation, and worker polling behavior. Their
artifacts, budgets, inputs, and read APIs are different. Reusing the existing
candidate-discovery output record for signal monitoring would make empty
candidate/search-plan fields appear meaningful and would let signal runs replace
the latest candidate-discovery result in the Radar catalog.

## Decision

`radar_runs` remains the shared lifecycle table and gains an explicit
`pipeline_id` plus nullable `source_run_id`. Existing rows default to
`candidate_discovery`; signal monitoring uses `signal_monitoring` and links to
the completed candidate-discovery run that supplied its snapshot.

Each pipeline owns a separate output record, repository, application executor,
job entrypoint, and API report. Existing candidate-discovery catalog and history
queries filter by pipeline id. Shared lifecycle code does not interpret a
pipeline artifact.

## Consequences

- Queue/status/journal mechanics remain consistent without duplicating the run
  lifecycle table.
- Candidate and signal artifacts cannot be confused structurally.
- New pipelines can add output contracts without widening the candidate output
  table.
- Repository and API tests must prove that a newer signal run does not replace
  candidate-discovery latest-run counters.

## Alternatives considered

- Separate signal run table: rejected because lifecycle, idempotency, journal,
  and polling behavior would be duplicated.
- Store `pipeline_id` only in JSON metadata: rejected because filtering and
  lineage would be implicit and easy to omit.
- Reuse `radar_run_outputs`: rejected because its required sections are
  candidate-discovery-specific.
