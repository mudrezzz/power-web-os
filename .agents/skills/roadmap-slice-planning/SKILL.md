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

## Completion checklist

Before finishing:

- `ROADMAP.md` is updated.
- The next task is clearly marked.
- Slices are small enough to implement independently.
- Testing and docs are included in each slice.
