---
name: radar-pipeline-as-is-sync
description: Use after a Radar search pipeline slice changes implemented behavior to update the AS IS Markdown/PDF documentation and keep diagrams, roles, context, budgets, diagnostic states, and tests current.
---

# Radar Pipeline AS IS Sync Skill

## Goal

Update the canonical AS IS Radar search pipeline documentation after an
implementation slice changes real behavior.

## Inputs

Read these sources in order:

1. User instructions and completed slice.
2. `ROADMAP.md`.
3. `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md`.
4. Any matching `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.md`.
5. Changed code, tests, docs, dossier/report examples, and validation output.

## Output

Update:

- `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md`
- `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.pdf`

Use:

```bash
python scripts/render_radar_pipeline_doc.py
```

## Required Checks

- The AS IS document describes actual implemented behavior, not intended
  future behavior.
- Mermaid blocks can remain in Markdown, but the PDF contains rendered diagrams
  and no raw diagram notation.
- Updated sections include roles, loops, context, budgets, failure semantics,
  source lifecycle, extension points, and tests when affected.
- The document contains no secrets, raw prompts, raw hidden reasoning, headers,
  tokens, or raw provider dumps.

## Completion Checklist

- Markdown and PDF are regenerated.
- Documentation contract tests pass.
- `ROADMAP.md` slice status and next task remain consistent.
- Any difference from TO BE is recorded in AS IS or roadmap notes.
