---
name: roadmap-slice-planning
description: Use when turning requirements, user ideas, or architecture into ROADMAP.md iterations, slices, backlog items, and next actions. Optimizes for small complete increments and concentric product growth.
---

# Roadmap Slice Planning Skill

## Goal

Maintain `ROADMAP.md` as the project control center.

## Process

1. Read the requirements source.
2. Read current `ROADMAP.md`.
3. Read architecture docs if present.
4. Identify the smallest useful product perimeter.
5. Break work into iterations.
6. Break iterations into small slices.
7. Ensure every slice has:
   - user value
   - implementation scope
   - documentation impact
   - test expectations
   - demo impact when applicable
   - clear completion criteria

## Slice format

Use this format in `ROADMAP.md`:

```markdown
### Slice <number>: <title>

- Status: Backlog | Ready | In Progress | Blocked | Done
- Goal:
- User value:
- Scope:
- Out of scope:
- Implementation notes:
- Tests:
- Docs:
- Demo impact:
- Acceptance criteria:
- Risks:
```

## Planning rules

- Prefer small working increments.
- Avoid large vague tasks.
- Avoid module-by-module waterfall plans.
- Ensure each iteration can leave the product demonstrable.
- Keep blocked questions explicit.
- Always identify the next recommended task.
- For complex LLM-backed pipelines, plan TDD/preflight slices before expensive
  live-provider or benchmark slices. The roadmap should name the fast red tests,
  recorded fixtures, negative provider-output fixtures, targeted live probes,
  and explicit diagnostic states needed before full live runs.
- Do not schedule a benchmark or broad live quality claim as the next task if
  known pipeline wiring, source-provider selection, extraction schema, or
  evidence-linking failures do not yet have fast tests.
- Mark every behavior-changing Radar slice with tracker sections `Pipeline`,
  `Behavior change: true`, `Acceptance manifest`, and `Validation report`.
  Its DoD must follow AS IS -> run RCA -> TO BE/manifest -> tests/live evidence
  -> validation PASS -> finalized AS IS. Plan process/tooling corrections when
  observed behavior contradicts a previously completed slice.

## Completion checklist

Before finishing:

- `ROADMAP.md` is updated.
- The next task is clearly marked.
- Slices are small enough to implement independently.
- Testing and docs are included in each slice.
