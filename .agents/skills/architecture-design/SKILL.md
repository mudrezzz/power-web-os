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

## Backend architecture rules

When the design touches backend, persistence, APIs, integrations, workflows, or
jobs, explicitly define ownership for:

- `api`: thin FastAPI routes, DTOs, dependency wiring.
- `application`: use cases, transactions, ports, orchestration.
- `domain`: business rules, scoring, validation, review semantics, handoff rules.
- `persistence`: SQLAlchemy models, sessions, repository implementations.
- `integrations`: provider, source, CRM, and external API adapters.
- `workflows`: LangGraph workflow wrappers and workflow state.
- `jobs`: worker and scheduler entrypoints.

Backend decisions must preserve this dependency direction:

```text
API / CLI / workers / scheduler
  -> application services
    -> domain services + ports
      -> persistence / integrations / job adapters
```

Do not design FastAPI routes, worker tasks, scheduler triggers, provider
adapters, SQLAlchemy models, or workflow wrappers as owners of domain scoring,
review semantics, or candidate state decisions. Record temporary exceptions and
required architecture contract tests in `ROADMAP.md`.

When a backend design introduces or materially changes a layer boundary, require
developer-facing ownership guidance close to the code, for example a local
`README.md` in the layer package plus concise module docstrings for key modules.
The guidance must explain allowed imports, forbidden imports, extension path,
transaction/runtime ownership where relevant, and the architecture contract
tests that protect the boundary.

## Complex LLM pipeline TDD rules

When the design touches a complex LLM-backed pipeline such as Radar planning,
retrieval, extraction, source-provider routing, evidence linking, scoring, or
workflow orchestration, require a fast TDD/preflight validation ladder before
long live runs:

- static/config preflight for active definitions, source policy, provider
  settings, source ids, and runtime wiring;
- recorded pipeline fixtures for planner, retrieval, source-provider,
  extraction, retry, verification, and scoring behavior;
- negative fixtures for malformed provider outputs, missing/unknown source refs,
  prose-first responses, schema mismatches, and evidence-linking failures;
- targeted live provider probes only after recorded fixtures are green;
- full live runs only as final smoke/benchmark steps or explicitly exploratory
  runs.

Do not design a workflow where a 20-30 minute live run is the first meaningful
validation signal. Record preflight commands, red tests, and accepted diagnostic
states in `ROADMAP.md` and ADRs.

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
- Backend boundaries are explicit when backend work is involved.
- Important trade-offs are documented.
- `ROADMAP.md` reflects architectural work.
- Follow-up tasks are small enough to implement as slices.
