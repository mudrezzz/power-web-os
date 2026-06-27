---
name: radar-pipeline-to-as-is-finalize
description: Use after implementing a Radar pipeline TO BE slice to compare planned behavior with actual behavior, record deviations, update AS IS Markdown/PDF, and close the documentation loop.
---

# Radar Pipeline TO BE To AS IS Finalize Skill

## Goal

Finalize a Radar pipeline slice by reconciling the reviewed TO BE design with
the implemented AS IS behavior.

## Inputs

Read these sources in order:

1. Target slice and user instructions.
2. `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.md`.
3. `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md`.
4. Changed implementation and tests.
5. Validation output, benchmark/evaluation reports, or RCA notes when relevant.

## Process

1. Compare the TO BE intended behavior with implemented behavior.
2. Identify exact matches, deliberate deviations, and incomplete behavior.
3. Update AS IS with implemented behavior only.
4. Record unresolved deviations as roadmap follow-up items instead of hiding
   them in prose.
5. Regenerate PDF.
6. Run documentation contract tests.

## Rules

- Do not mark a TO BE behavior as AS IS unless it is implemented and validated.
- Do not silently convert benchmark or RCA findings into product truth.
- Do not include secrets, raw prompts, hidden reasoning, headers, tokens, or raw
  provider dumps.

## Completion Checklist

- AS IS Markdown/PDF match implemented behavior.
- TO BE deviations are visible.
- Roadmap next task reflects remaining work.
- Documentation contract tests pass.
