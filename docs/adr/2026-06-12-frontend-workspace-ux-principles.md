# ADR: Frontend Workspace UX Principles

## Status

Accepted

## Context

Power Web OS is a sales and ABM workspace, not a landing page or a static report. During the ICP Radar, Accounts, Account Map, Access Plans, and Playbook slices we repeatedly corrected the same UX risks around shell behavior, dense data scanning, sticky object identity, evidence review, read-only configuration, bilingual UI, and small-screen use.

This ADR is the umbrella entry for the frontend workspace UX decision family. Detailed decisions live in narrower ADRs so future changes can be evaluated independently.

## Decision

Use the following ADRs as the durable UX contract for product screens:

- `2026-06-12-bounded-spa-workspace-shell.md` - viewport-bounded shell, scroll ownership, and persistent workspace context.
- `2026-06-12-table-first-dense-data-ux.md` - table-first scanning, sticky identity columns, inline previews, and detail drilldown.
- `2026-06-12-evidence-first-review-ux.md` - score/rationale/evidence layout and criterion review behavior.
- `2026-06-12-configurable-object-ux.md` - catalog-first navigation, settings views, and read-only configuration states.
- `2026-06-12-bilingual-responsive-frontend-baseline.md` - EN/RU i18n and small-screen/mobile constraints.

Future frontend slices should cite the specific ADR that governs the behavior being changed. This umbrella ADR should only change when the decision family changes.

## Consequences

- UX decisions are discoverable from one index file without turning one ADR into a checklist dump.
- Teams can revise one UX area without reopening unrelated decisions.
- Developer guidance can reference this ADR family while implementation discussions cite the narrower ADRs.

## Alternatives considered

- **Keep all UX requirements in one ADR.** Rejected because it mixes shell architecture, data presentation, evidence review, configuration UX, localization, and responsive requirements into one hard-to-maintain decision.
- **Move all rules into `AGENTS.md` only.** Rejected because agent instructions help execution, but ADRs are the architectural record for why the project behaves this way.
