# ADR: Radar Pipeline Acceptance Evidence Loop

Status: Accepted

Date: 2026-07-10

## Context

Radar behavior was previously closed from code and regression tests even when a
persisted live run exposed a mismatch with the intended algorithm. AS IS, TO BE,
runtime diagnostics, DoD and Roadmap status could therefore drift apart.

## Decision

Every tracker slice marked `Pipeline` and `Behavior change: true` follows one
auditable loop:

1. Read the current pipeline AS IS.
2. Diagnose a product-safe persisted baseline run and record the RCA.
3. Create TO BE Markdown/PDF and an adjacent acceptance manifest.
4. Map stable mandatory requirement IDs to exact tests and runtime thresholds.
5. Implement and run fast, recorded, integration and required live checks.
6. Generate Markdown/JSON validation reports from tests and persisted reports.
7. Reconcile implemented behavior into AS IS and mark TO BE `Implemented`.
8. Rerun validation and permit Roadmap `Done` only for final `PASS`.

`RadarPipelineSliceValidator` owns evidence checking and report generation. The
Roadmap CLI owns the completion gate. Neither component owns pipeline product
semantics; those remain in each pipeline's package and acceptance manifest.

Autofix may make at most five local corrections that preserve the approved TO
BE. A change to the algorithm or DoD requires an explicit design revision.

## Consequences

- Tests alone no longer close behavior-changing Radar slices.
- Persisted live evidence is required only when declared by the manifest.
- Missing, failed or untraceable mandatory requirements keep a slice In Progress.
- Documentation-only and non-Radar slices are unaffected.
- AS IS becomes evidence-backed implemented truth rather than intended design.
