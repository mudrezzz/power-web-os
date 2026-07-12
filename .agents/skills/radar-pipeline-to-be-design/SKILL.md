---
name: radar-pipeline-to-be-design
description: Use before substantial Radar search pipeline changes to create a TO BE design document from the current AS IS pipeline, ROADMAP slice, and implementation evidence. Applies when changing planner, retrieval, extraction, source routing, registry lookup, candidate universe, checkpoints, budgets, signal search, dossier projection, or evaluation.
---

# Radar Pipeline TO BE Design Skill

## Goal

Create a reviewable TO BE design before implementing a substantial Radar search
pipeline change. The skill is pipeline-aware; the caller may specify
`pipeline=<pipeline_id>`.

Supported pipeline ids:

- `candidate-discovery`
- `signal-monitoring`
- `power-web-discovery`

## Inputs

Read these sources in order:

1. User instructions and target slice.
2. `ROADMAP.md`.
3. `docs/radar/pipelines/README.md`.
4. The pipeline AS IS document, when it exists.
5. Relevant architecture docs and ADRs.
6. Relevant tests and implementation modules for the changed pipeline area.

## Output

Choose output paths from the requested pipeline id.

For `candidate-discovery`, keep the current legacy paths until the migration
slice moves the candidate-discovery AS IS document:

- AS IS source: `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md`
- TO BE Markdown: `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.md`
- TO BE PDF: `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.pdf`

For `signal-monitoring`:

- AS IS source: none until the first runtime implementation creates it
- TO BE Markdown: `docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_<slice>.md`
- TO BE PDF: `docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_<slice>.pdf`

For `power-web-discovery`:

- AS IS source: none until the first runtime implementation creates it
- TO BE Markdown: `docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_<slice>.md`
- TO BE PDF: `docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_<slice>.pdf`

Use the slice id exactly, replacing characters only when required by the file
system.

Generate the PDF from the Markdown with the selected paths:

```bash
python scripts/render_radar_pipeline_doc.py --source <selected-to-be.md> --output <selected-to-be.pdf>
```

Example invocation:

```text
Сделай TO BE для signal-monitoring по слайсу 0.7.6.4.1
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

For every slice marked `Pipeline` and `Behavior change: true`, also create an
adjacent `.acceptance.json`. It must list stable requirement IDs, mandatory
flags, exact pytest node IDs, runtime acceptance thresholds, AS IS/TO BE paths,
and validation-report paths. Register the manifest in the roadmap tracker.
Derive the TO BE from the current AS IS plus persisted run RCA; do not start
from the desired code structure alone.

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

- TO BE document exists under the selected pipeline path.
- TO BE PDF exists next to the Markdown.
- TO BE PDF was visually checked or rendered to preview images when layout
  changed.
- TO BE PDF does not expose raw Mermaid code, raw prompts, secrets, raw hidden
  reasoning, headers, tokens, or provider dumps.
- The user can review the intended algorithm without reading the codebase.
- Tests are specific to the changed logic.
- The next implementation slice can be generated from the TO BE.
