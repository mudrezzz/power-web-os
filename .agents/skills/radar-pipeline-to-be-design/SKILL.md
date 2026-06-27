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

Create both:

`docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.md`
`docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.pdf`

Use the slice id exactly, replacing characters only when required by the file
system.

Generate the PDF from the Markdown with:

```bash
python scripts/render_radar_pipeline_doc.py --source docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.md --output docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.pdf
```

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
- The Markdown may keep Mermaid source for GitHub readability, but the PDF must
  contain rendered diagrams/controlled diagram flowables, not raw Mermaid
  notation.

## Completion Checklist

- TO BE document exists under `docs/radar/to-be/`.
- TO BE PDF exists next to the Markdown.
- TO BE PDF was visually checked or rendered to preview images when layout
  changed.
- TO BE PDF does not expose raw Mermaid code, raw prompts, secrets, raw hidden
  reasoning, headers, tokens, or provider dumps.
- The user can review the intended algorithm without reading the codebase.
- Tests are specific to the changed logic.
- The next implementation slice can be generated from the TO BE.
