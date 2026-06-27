---
name: radar-pipeline-to-be-design
description: Use before substantial Radar search pipeline changes to create a TO BE design document from the current AS IS pipeline, ROADMAP slice, and implementation evidence. Applies when changing planner, retrieval, extraction, source routing, registry lookup, candidate universe, checkpoints, budgets, signal search, dossier projection, or evaluation.
---

# Radar Pipeline TO BE Design Skill

## Goal

Create a reviewable TO BE design before implementing a substantial Radar search
pipeline change.

## Inputs

Read these sources in order:

1. User instructions and target slice.
2. `ROADMAP.md`.
3. `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md`.
4. Relevant architecture docs and ADRs.
5. Relevant tests and implementation modules for the changed pipeline area.

## Output

Create:

`docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.md`

Use the slice id exactly, replacing characters only when required by the file
system.

## Required TO BE Sections

- Slice and decision context.
- AS IS problem statement.
- Intended pipeline behavior.
- Roles changed.
- Context passed between roles.
- Source, budget, and checkpoint semantics.
- Dossier/trace/evaluation visibility.
- Diagrams for changed flows.
- Test plan mapped to changed logic, not only end-to-end smoke.
- Acceptance criteria.
- Explicit out of scope.
- Open questions.

## Rules

- Do not implement production code in this skill.
- Do not invent behavior that conflicts with the current AS IS without calling
  it out as a deliberate change.
- Do not pass or print secrets, raw prompts, raw hidden reasoning, or provider
  dumps.
- Keep the design slice-sized. Large redesigns should be split into smaller
  TO BE documents and roadmap slices.

## Completion Checklist

- TO BE document exists under `docs/radar/to-be/`.
- The user can review the intended algorithm without reading the codebase.
- Tests are specific to the changed logic.
- The next implementation slice can be generated from the TO BE.
