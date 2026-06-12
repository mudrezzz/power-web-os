# ADR: Evidence-First Review UX

## Status

Accepted

## Context

Power Web OS must explain why an account, signal, criterion, route, or action was scored or recommended. The user should be able to inspect the evidence, decide what to trust, and eventually accept, reject, correct, or comment on the system's interpretation.

Early criterion breakdowns looked like fully expanded evidence cards by default. They were hard to scan and gave too much space to low-value metadata while hiding the review workflow.

## Decision

Evidence-backed review surfaces must be scan-first and evidence-first.

- Scores, tiers, confidence, and counts stay near their rationale.
- Evidence-backed detail starts as a table or compact list with status, score, confidence, facts count, and review status.
- Users expand a row only when they want rationale, facts, source refs, links, or review controls.
- Expanded detail prioritizes:
  - rationale;
  - facts;
  - source refs and URLs;
  - review controls;
  - reviewer comments.
- Metadata such as origin or confidence should be compact tags, not large content blocks.
- Criterion review controls may include accept, reject, and score edit with comment, but until persistence exists they must be clearly labelled as local/non-persistent demo state.
- Breadcrumbs and compact object headers must remain sticky in long detail views. The user should not lose which account, candidate, radar, or rule set they are inspecting.

## Consequences

- Future score explanations need structured evidence payloads, not only aggregate numbers.
- UI should avoid turning evidence into prose-only walls of text.
- Production validation will need persistence and score recalculation, but the UI can prototype local review state first when clearly labelled.

## Alternatives considered

- **Show all evidence cards expanded by default.** Rejected because it prevents scanning and makes important review targets harder to find.
- **Show scores without evidence.** Rejected because transparent ABM scoring is a core product requirement.
- **Make confidence/origin large content panels.** Rejected because they are supporting metadata, not the review task.
