---
name: radar-pipeline-to-as-is-finalize
description: Use after implementing a Radar pipeline TO BE slice to compare planned behavior with actual behavior, record deviations, update AS IS Markdown/PDF, and close the documentation loop.
---

# Radar Pipeline TO BE To AS IS Finalize Skill

## Goal

Finalize a Radar pipeline slice by reconciling the reviewed TO BE design with
the implemented AS IS behavior. The skill is pipeline-aware; the caller may
specify `pipeline=<pipeline_id>`.

Supported pipeline ids:

- `candidate-discovery`
- `signal-monitoring`
- `power-web-discovery`

## Inputs

Read these sources in order:

1. Target slice and user instructions.
2. `docs/radar/pipelines/README.md`.
3. The matching TO BE document for the selected pipeline.
4. The selected pipeline AS IS document.
5. Changed implementation and tests.
6. Validation output, benchmark/evaluation reports, or RCA notes when relevant.

## Process

1. Compare the TO BE intended behavior with implemented behavior.
2. Identify exact matches, deliberate deviations, and incomplete behavior.
3. Update AS IS with implemented behavior only.
4. Record unresolved deviations as roadmap follow-up items instead of hiding
   them in prose.
5. Regenerate PDF.
6. Run documentation contract tests.
7. Read the acceptance manifest and generated Markdown/JSON validation report.
8. Record the slice ID and any accepted deviations in AS IS, set the TO BE
   status to `Implemented`, rerun the pipeline validator, and require final
   `validation_status=PASS` before roadmap closeout.

Path rules:

- `candidate-discovery` keeps the legacy AS IS path
  `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md` until the migration slice.
- `signal-monitoring` AS IS belongs under
  `docs/radar/pipelines/signal-monitoring/` after runtime exists.
- `power-web-discovery` AS IS belongs under
  `docs/radar/pipelines/power-web-discovery/` after runtime exists.

## Rules

- Do not mark a TO BE behavior as AS IS unless it is implemented and validated.
- Do not silently convert benchmark or RCA findings into product truth.
- Do not include secrets, raw prompts, hidden reasoning, headers, tokens, or raw
  provider dumps.
- Do not finalize AS IS from unit tests alone when the manifest requires
  persisted live evidence.

## Completion Checklist

- AS IS Markdown/PDF match implemented behavior.
- TO BE deviations are visible.
- Roadmap next task reflects remaining work.
- Documentation contract tests pass.
