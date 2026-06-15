# ADR: Canonical ICP Radar UX Contract

## Status

Accepted

## Context

Power Web OS now has more than one ICP Radar source:

- fixture-backed `ТОиР / SIBUR`;
- provider-backed `ТОиР Quick Live Radar`;
- configured or local draft radars without candidates yet.

The live radar initially drifted into a separate UI: different header attributes, different shortlist columns, a different preview, and a different detail layout. That makes the product harder to evolve because every new provider or fixture can accidentally invent its own review surface.

## Decision

All ICP Radar shortlist surfaces must render through a canonical view model and shared UX contract.

The frontend maps each data source into a canonical radar view model:

- radar: name, description, operational status, owner, tabs, runtime journal;
- candidate: identity, fit/intent/trigger/total slots, tier, evidence count, qualification rows, signal rows, source rows, journal rows.

Operational radar status shown in the header is limited to:

- `draft`;
- `active`;
- `stopped`.

Implementation-specific states such as local draft, modified locally, planned, or configured remain service labels and must not become new operational header statuses.

The shortlist table columns are canonical:

- company;
- total;
- fit;
- intent;
- trigger;
- tier;
- evidence;
- action.

If a radar does not have a value for a canonical score slot, the adapter returns `null` and the UI renders `—`. The UI must not invent a score to fill the column.

Inline preview always has four blocks:

- summary: why this candidate was selected and the main insight;
- tier: why the current tier was assigned;
- qualification: top qualification rows, capped at five;
- signals: top signal rows, capped at five.

Preview must not show source lists, provider runtime metadata, long rationale, or duplicated score/tier blocks.

Candidate detail is tabbed:

- overview;
- qualification;
- signals;
- sources;
- journal.

Runtime metadata, provider/model details, search queries, warnings, and structured model trace belong only in the `journal` tab. Do not show raw hidden chain-of-thought.

## Consequences

- New radar sources are data adapters, not separate visual products.
- Frontend tests should fail when a live/provider-backed radar uses standalone grid, split detail, provider-specific table columns, or preview sections outside the contract.
- UX changes to ICP Radar must update this ADR, the table-first ADR, and frontend contract tests together.
- Missing data is an explicit empty value, not a reason to create a custom layout.

## Alternatives Considered

- **Provider-specific UIs.** Rejected because they make each radar feel like a different product.
- **A single free-form detail page.** Rejected because dense evidence needs predictable navigation and table-first drilldown.
- **Runtime metadata above the shortlist.** Rejected for canonical screens; it belongs to the `journal` tab so the shortlist remains focused on candidate review.
