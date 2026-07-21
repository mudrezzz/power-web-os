# Power Web TO BE 0.7.6.6.0.1

Status: Implemented.

AS IS: `../RADAR_POWER_WEB_DISCOVERY_AS_IS.md`
Acceptance manifest: `RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.0.1.acceptance.json`

## Problem and decision

Power Web Discovery has provider-neutral people and identity contracts, but no
authoritative owner for the product being sold or the semantic buying roles
that must be discovered. The current production Playbook screen is an
account-specific route analysis over a demo Access Plan artifact.

This slice creates shared, versioned sales configuration:

`product -> semantic buying-role policy -> access playbook -> sales playbook version`.

The Playbook workspace becomes global configuration. Account-specific route
analysis moves to Access Plans. No people search, LLM call or Power Web run is
introduced.

## Ownership and versioning

The sales-playbook application package owns product drafts, validation,
publication, activation, restore and archive use cases. Domain contracts and
ports remain independent from FastAPI, SQLAlchemy and frontend code.

Published `ProductDefinitionVersion`, `BuyingRolePolicyVersion` and
`AccessPlaybookVersion` snapshots are immutable. A published
`SalesPlaybookDefinitionVersion` references exactly one compatible version of
each. Editing occurs only in a mutable draft with optimistic `draft_revision`.

Publishing creates a new immutable version; activating changes the stable
product pointer, not historical content. Restoring a historical version creates
a new draft. Archiving prevents future selection but preserves all versions.

## Product and role contracts

A product definition contains stable code, name, short description, customer
problem, value proposition, use contexts and lifecycle state.

Each semantic role contains a stable role code, display name, business
responsibility, decision rights, required/optional state, priority, account
scope, reason, expected evidence and exclusions. Roles describe functions in a
buying process, not account-specific job titles or people.

An access route contains a stable route code, source and target semantic role
IDs, allowed channels, required assets, human-review policy and rationale.
Dangling role references are invalid.

`AccountRoleTitleHypothesis` is a future run output. It may propose title and
query variants for an existing semantic role, but cannot create, remove,
reprioritize or confirm role requirements.

## UI contract

The existing Playbook navigation item opens a backend-backed global workspace.
The top bar no longer presents an account as the owner of this screen.

The desktop layout has a searchable product rail and one bounded workspace.
The workspace header shows product, lifecycle, version and update time. It has
four tabs: Product, Buying roles, Access rules and Versions.

The Product tab edits product context. The Buying roles tab uses a dense table
and a right-side inspector. There are no title, person, URL or query fields. The
Access rules tab references semantic role IDs through controlled selectors and
keeps routes, blocked channels, assets and review requirements separate from
Radar signal settings. The Versions tab is read-only for published snapshots
and supports activation and restore-as-draft.

There is no hidden autosave or browser-local source of truth. Explicit draft
save and publish commands are used. Loading is never rendered as an empty
configuration. A stale `draft_revision` produces an explicit conflict without
discarding local changes.

The existing account-specific Playbook Analysis is available under Access
Plans as the `Rule analysis` tab. It continues to explain route decisions,
alternatives, evidence, risks and required review.

The workspace uses design-system tokens, Lucide icons, RU/EN resources and
owned scrolling. It must remain usable at 1280x720 and 1366x768 without body
scrolling or overlapping text.

## API and persistence

The public API supports lightweight product listing, stable product creation,
draft read/update, atomic publication, version history, historical read,
activation, restore-as-draft and archive.

Draft writes require `draft_revision`; stale writes return HTTP 409. Published
versions cannot be updated. API mode never falls back to demo configuration.

Persistence uses separate stable product, draft and immutable version records.
The SmartDiagnostics seed is idempotent and creates an active version with at
least eight semantic roles and valid access routes.

## Compatibility and benchmark

The existing `Playbook` contract remains a compatibility projection of active
access-playbook settings. Access Planner scoring, Power Web Board behavior and
existing artifacts do not change.

The accepted SIBUR benchmark receives a versioned amendment containing only the
SmartDiagnostics product and role-policy version references. People, profile
URLs, pair labels and expected answers remain evaluator-only. Blind leakage
must remain zero.

## Requirement traceability

- `PWF-PROD-01`: product draft, publish, activate, restore and archive are persisted.
- `PWF-ROLE-01`: every published role is complete and semantic rather than title-specific.
- `PWF-ROLE-02`: title hypotheses cannot mutate semantic role requirements.
- `PWF-ACCESS-01`: access routes reference only existing semantic role IDs.
- `PWF-VERS-01`: published versions are immutable and stale drafts return conflict.
- `PWF-API-01`: API and DB survive restart without local fallback.
- `PWF-UI-01`: Product, Buying roles, Access rules and Versions are separate usable views.
- `PWF-UI-02`: account-specific rule analysis is preserved under Access Plans.
- `PWF-DEMO-01`: SmartDiagnostics has an accepted active configuration with eight roles.
- `PWF-BENCH-01`: benchmark amendment preserves blind leakage zero.
- `PWF-COMPAT-01`: existing Access Planner and Power Web Board behavior remains green.
- `PWF-NET-01`: provider calls and Power Web/Radar runs equal zero.
- `PWF-PROC-01`: TO BE, tests, validation and finalized AS IS are traceable.

## Acceptance

The slice is accepted only after backend, migration, API, UI and Playwright
tests pass; Docker proves UI -> API -> DB -> restart -> UI persistence; the
validation report is PASS; and this design is reconciled into AS IS.

## Implementation reconciliation

The implemented slice matches this design. Product, semantic buying-role and
access-rule drafts are persisted independently from account artifacts;
publication creates immutable compatible snapshots; activation changes only
the product pointer. The Playbook workspace is backend-backed, while the former
account-specific rule analysis is available under Access Plans.

No provider, Radar or Power Web run is created by this slice. The future
`AccountRoleTitleHypothesis` remains a provider-neutral contract and does not
alter the accepted semantic-role policy.
