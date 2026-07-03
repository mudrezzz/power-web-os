---
name: slice-implementation
description: Use when implementing a selected ROADMAP.md slice. Keeps the increment small, updates tests, docs, demo, and roadmap, and preserves a working product after the slice.
---

# Slice Implementation Skill

## Goal

Implement one small, complete, tested, documented product increment.

## Process

1. Read `AGENTS.md`.
2. Read `ROADMAP.md`.
3. Identify the active or next slice.
4. Read relevant requirements, architecture docs, ADRs, and existing code.
5. Confirm the slice scope.
6. Implement only the selected slice.
7. Add or update tests.
8. Update documentation.
9. Update demo if user-visible behavior changed.
10. Run relevant validation.
11. Update `ROADMAP.md`.

## Implementation rules

- Keep changes localized.
- Preserve existing functionality.
- Follow OOP and single-responsibility principles.
- For backend work, keep API routes, application services, domain rules,
  persistence adapters, integrations, workflows, and jobs in their documented
  ownership boundaries.
- Do not put SQLAlchemy queries in FastAPI routes, provider calls in domain
  services, or scoring/review semantics in worker tasks or scheduler triggers.
- Add or update architecture contract tests when a slice introduces a new
  backend boundary, dependency, persistence mechanism, integration, workflow, or
  job entrypoint.
- For backend layers, add or update local README guidance and concise module
  docstrings so future developers can extend the layer without reading every
  implementation file first.
- For Radar backend work, read
  `docs/architecture/RADAR_BACKEND_ARCHITECTURE.md` before adding or moving
  application code. Do not add new root-level
  `src/power_web_os/application/live_radar_*.py` modules; use the package
  contract under `src/power_web_os/application/radar/...` as it is introduced.
- For complex LLM pipelines, implement TDD/preflight coverage before relying on
  full live provider runs. Add or update static/config checks, recorded
  fixtures, malformed-output negative fixtures, and targeted provider probes
  where relevant. A long live run is a final smoke/benchmark step, not the first
  validation signal.
- Do not normalize broken LLM/provider output into apparently successful
  product states. Missing source refs, invalid schemas, evidence-linking
  failures, and budget/policy skips should become explicit diagnostic states and
  tests.
- Comment non-obvious code and tests.
- Do not expand scope unless required for the slice to work.
- Record follow-up work in `ROADMAP.md` instead of silently doing it.

## Completion checklist

Before finishing:

- Slice behavior works.
- Tests were added or updated.
- For complex LLM pipelines, fast preflight/recorded/negative tests were added
  or explicitly documented as out of scope for the slice.
- Relevant tests were run.
- Backend architecture contract tests were run when backend boundaries changed.
- Docs were updated.
- Demo was updated if needed.
- `ROADMAP.md` status was updated.
- Remaining risks and next tasks are documented.
