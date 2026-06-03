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
- Comment non-obvious code and tests.
- Do not expand scope unless required for the slice to work.
- Record follow-up work in `ROADMAP.md` instead of silently doing it.

## Completion checklist

Before finishing:

- Slice behavior works.
- Tests were added or updated.
- Relevant tests were run.
- Docs were updated.
- Demo was updated if needed.
- `ROADMAP.md` status was updated.
- Remaining risks and next tasks are documented.
