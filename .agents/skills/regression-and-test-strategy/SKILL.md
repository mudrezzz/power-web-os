---
name: regression-and-test-strategy
description: Use when deciding which tests to add or run for a slice, when a change may affect existing functionality, or when planning/running full regression. Covers unit, integration, smoke, and e2e testing.
---

# Regression and Test Strategy Skill

## Goal

Choose and execute the right validation scope for the current change.

## Test layers

Consider:

- Unit tests for isolated logic.
- Integration tests for collaboration between components.
- Smoke tests for critical startup and happy-path behavior.
- E2E tests for important user-facing flows.

For complex LLM-backed pipelines, also consider:

- static/config preflight tests for active definitions, provider settings,
  source ids, runtime wiring, and policy references;
- recorded pipeline fixtures for planner, retrieval, source-provider,
  extraction, verification, retries, and scoring;
- negative fixtures for malformed provider output, missing source refs,
  unknown evidence refs, schema shape mismatches, prose-first responses, and
  provider errors;
- targeted live provider probes for a single bounded lookup/retrieval/extraction
  path;
- full live runs only as final smoke/benchmark validation.

## Process

All execution uses one announced remote session through
`scripts/remote_dev.ps1`. Use `backend`, `frontend`, or `playwright` runners;
never run project tests or Docker locally and never silently fall back when the
remote contour is unavailable.

1. Inspect the current slice or change.
2. Identify affected components.
3. Identify existing tests.
4. Add or update tests for changed behavior.
5. Select validation scope:
   - targeted tests for local changes
   - smoke tests for user-visible flows
   - integration tests for cross-component changes
   - full regression when risk is broad
6. Sync once, execute selected layers in isolated remote containers, collect the
   manifest/evidence, and clean only that validation session.
   - for LLM pipelines, prefer fast preflight/recorded/negative tests before
     running expensive live-provider flows
6. Run the selected commands if available.
7. Report results clearly.

## Full regression triggers

Run or recommend full regression when:

- core domain behavior changed
- shared infrastructure changed
- public APIs changed
- persistence or migration logic changed
- authentication, authorization, payments, security, or data integrity paths changed
- demo-critical flows changed
- many modules were touched
- complex LLM pipeline semantics changed and preflight/recorded fixtures were
  added or repaired

## Completion checklist

Before finishing:

- Test coverage matches the slice.
- Relevant tests were run.
- Any skipped tests are explained.
- Failures are either fixed or documented as blockers.
- `ROADMAP.md` reflects test-related follow-up work.
