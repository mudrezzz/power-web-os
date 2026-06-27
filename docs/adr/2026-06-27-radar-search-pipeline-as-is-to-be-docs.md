# ADR: Radar Search Pipeline AS IS/TO BE Documentation System

## Status

Accepted

## Context

Radar candidate and signal search has become the central product mechanism. Its
behavior now spans active Radar definitions, connector profiles, source cards,
planner validation, retrieval, extraction recovery, structured registry lookup,
candidate universe retention, adaptive checkpoints, signal search, dossier
projection, and benchmark evaluation.

Before this decision, the real algorithm was understandable only by combining
ROADMAP slices, RCA notes, tests, implementation files, and run diagnostics.
That made substantial pipeline changes risky: a developer or agent could change
one part of the pipeline without understanding how context, budgets,
observability, and review semantics flow across stages.

## Decision

Maintain a dedicated Radar search pipeline documentation system:

- `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md` is the canonical current
  implementation description.
- `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.pdf` is the generated review artifact.
- Substantial future pipeline changes must create a TO BE document under
  `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.md` before
  implementation.
- After implementation, the accepted behavior is merged back into AS IS and the
  PDF is regenerated.
- PDF diagrams must be rendered diagrams, not raw Mermaid notation.
- A documentation contract test guards the existence and basic safety of the
  AS IS Markdown/PDF and related agent skills.

Three project skills support the workflow:

- `radar-pipeline-to-be-design`
- `radar-pipeline-as-is-sync`
- `radar-pipeline-to-as-is-finalize`

## Consequences

Positive consequences:

- New developers and agents get one current entry point for the Radar search
  algorithm.
- Major pipeline changes start from a reviewed algorithm design instead of
  ad hoc code edits.
- AS IS drift becomes test-visible.
- Dossier, benchmark, and execution semantics can be understood without reading
  the full backend implementation.

Trade-offs:

- Each substantial pipeline slice has an additional documentation step.
- The PDF generation script is now part of the documentation toolchain.
- The AS IS document is descriptive; it must not replace tests or RCA evidence.

## Alternatives Considered

- Keep using only `ROADMAP.md`.
  - Rejected because the roadmap is a backlog and delivery tracker, not a
    current algorithm specification.
- Put all details in the architecture overview.
  - Rejected because the Radar search pipeline is detailed enough to deserve its
    own operational specification.
- Require only TO BE docs and no AS IS.
  - Rejected because future agents need a current implementation map before
    designing changes.
