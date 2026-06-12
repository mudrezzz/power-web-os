# ADR: Table-First Dense Data UX

## Status

Accepted

## Context

Power Web OS shows dense operational data: radar candidates, accepted accounts, criteria, evidence rows, validation queues, routes, and configured radar objects. Users need to scan, compare, and prioritize before drilling into detail.

Card-heavy or split-panel layouts made the ICP Radar experience hard to scan on small monitors. Always-visible detail panels consumed table width, while global horizontal scroll hid the identity of the candidate being reviewed.

## Decision

Dense operational data should start table-first.

- Dense lists start as compact scan surfaces, usually tables or similarly structured rows.
- Details open only after user intent:
  - inline preview for lightweight context;
  - separate in-shell detail view for full evidence, review, or editing workflows.
- Avoid always-visible side detail panels for primary scan surfaces unless a slice explicitly validates that layout on small desktop and mobile.
- Horizontal overflow belongs to the table or board wrapper, not to the browser page or whole workspace.
- The first identity column should stay sticky where horizontal comparison would otherwise hide the object being reviewed.
- Tables must use `min-width: 0`, explicit column policies, wrapping/ellipsis, and owned overflow so text never overlaps adjacent columns.
- Inline previews must stay bounded and short. For ICP Radar previews the accepted baseline is:
  - main signal;
  - short recommendation/comment;
  - top-5 evidence refs;
  - top-5 criteria.
- Inline previews in horizontally scrollable tables must not inherit the table's horizontal scroll position. Table columns may scroll, but the expanded preview content should stay anchored to the visible workspace and use its own responsive layout.
- Inline preview actions should sit after the preview content, not in a separate left rail that consumes scan width on laptop screens.
- Do not create nested vertical scrolls inside expanded previews. Prefer one scroll owner for the whole expanded block.
- Do not duplicate score/tier blocks inside previews when those values already exist in the row. Emphasize the existing row values when expanded.

## Consequences

- Future dense screens should define row, preview, and detail modes explicitly.
- Some screens need separate desktop and mobile representations instead of trying to make a wide table usable everywhere.
- Contract tests and visual smoke should cover scroll ownership, sticky identity, and no text overlap.

## Alternatives considered

- **Always-visible split detail panels.** Rejected as the default because they reduce table width and break small-monitor scanning.
- **Global horizontal page scroll.** Rejected because it hides navigation/context and makes sticky identity unreliable.
- **Fully expanded rows by default.** Rejected because users need to scan first and drill down selectively.
