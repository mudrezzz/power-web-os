---
name: radar-pipeline-as-is-sync
description: Use after a Radar search pipeline slice changes implemented behavior to update the AS IS Markdown/PDF documentation and keep diagrams, roles, context, budgets, diagnostic states, and tests current.
---

# Radar Pipeline AS IS Sync Skill

## Goal

Update the canonical AS IS Radar pipeline documentation after an implementation
slice changes real behavior. The skill is pipeline-aware; the caller may specify
`pipeline=<pipeline_id>`.

Supported pipeline ids:

- `candidate-discovery`
- `signal-monitoring`
- `power-web-discovery`

## Inputs

Read these sources in order:

1. User instructions and completed slice.
2. `ROADMAP.md`.
3. `docs/radar/pipelines/README.md`.
4. The selected pipeline AS IS document.
5. Any matching TO BE document for the selected pipeline.
6. Changed code, tests, docs, dossier/report examples, and validation output.

## Output

Choose AS IS paths from the requested pipeline id.

For `candidate-discovery`, keep the current legacy AS IS paths until the
candidate-discovery migration slice:

- `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md`
- `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.pdf`

For `signal-monitoring`, after runtime exists:

- `docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md`
- `docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.pdf`

For `power-web-discovery`, after runtime exists:

- `docs/radar/pipelines/power-web-discovery/RADAR_POWER_WEB_DISCOVERY_AS_IS.md`
- `docs/radar/pipelines/power-web-discovery/RADAR_POWER_WEB_DISCOVERY_AS_IS.pdf`

Use selected paths:

```bash
python scripts/render_radar_pipeline_doc.py --source <selected-as-is.md> --output <selected-as-is.pdf>
```

For legacy `candidate-discovery`, `python scripts/render_radar_pipeline_doc.py`
without arguments still renders the current AS IS document.

## Required Checks

- The AS IS document describes actual implemented behavior, not intended
  future behavior.
- Mermaid blocks can remain in Markdown, but the PDF contains rendered diagrams
  and no raw diagram notation.
- Updated sections include roles, loops, context, budgets, failure semantics,
  source lifecycle, extension points, and tests when affected.
- The document contains no secrets, raw prompts, raw hidden reasoning, headers,
  tokens, or raw provider dumps.
- Every mandatory acceptance requirement ID appears in the finalized AS IS
  change record and in the validation report for the slice.

## Completion Checklist

- Markdown and PDF are regenerated.
- Documentation contract tests pass.
- `ROADMAP.md` slice status and next task remain consistent.
- Any difference from TO BE is recorded in AS IS or roadmap notes.
