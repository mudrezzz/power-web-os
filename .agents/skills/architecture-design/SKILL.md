---
name: architecture-design
description: Use when designing or revising project architecture based on user input, requirements documents, ROADMAP.md, and files in the repository root. Applies object-oriented design, clear component boundaries, ADRs, and iterative slice-based architecture planning. Do not use for ordinary small code edits.
---

# Architecture Design Skill

## Goal

Design or revise the architecture so the project can grow iteratively through small, working slices.

## Inputs

Use the following sources, in this order:

1. User instructions in the current task.
2. The source requirements document specified by the user.
3. If no requirements file was specified, search the repository root for likely requirements files:
   - `SPEC.md`
   - `SPECIFICATION.md`
   - `REQUIREMENTS.md`
   - `PRD.md`
   - `TASK.md`
   - `TZ.md`
   - `ТЗ.md`
   - files containing "requirements", "spec", "prd", "task", "тз", or "задание".
4. `ROADMAP.md`.
5. Existing architecture docs.
6. Existing code structure.

## Process

1. Identify the product goal and primary user value.
2. Identify the smallest closed product perimeter that can work end-to-end.
3. Define the first architectural circle: the minimal complete product.
4. Define later expansion circles.
5. Propose module boundaries using OOP and single-responsibility principles.
6. Separate domain, application, infrastructure, UI, persistence, integration, and testing concerns where applicable.
7. Identify architectural risks.
8. Record meaningful decisions as ADRs.

## Required outputs

Update or create:

- `docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md`
- relevant ADR files under `docs/adr/`
- `ROADMAP.md` if architecture affects iterations or slices

## Architecture document should include

- Product context
- Major components
- Responsibilities of each component
- Data flow
- Dependency direction
- Extension points
- Testing strategy
- Demo implications
- Known trade-offs
- Open questions

## ADR format

Use this filename pattern:

`docs/adr/YYYY-MM-DD-short-decision-title.md`

Use this structure:

```markdown
# ADR: <Decision title>

## Status

Proposed | Accepted | Superseded

## Context

## Decision

## Consequences

## Alternatives considered
```

## Completion checklist

Before finishing:

- Architecture supports iterative slice delivery.
- No component has unclear ownership.
- Important trade-offs are documented.
- `ROADMAP.md` reflects architectural work.
- Follow-up tasks are small enough to implement as slices.
