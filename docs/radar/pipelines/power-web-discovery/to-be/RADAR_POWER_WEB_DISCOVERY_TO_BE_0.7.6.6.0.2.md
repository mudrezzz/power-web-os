# Power Web TO BE 0.7.6.6.0.2

Status: Implemented.

Implemented result: new definitions contain product and semantic-role snapshots
only; AccessPlaybook is frozen compatibility data. Docker validation measured
99.8% detail/workspace width, a 2 px inline-editor width delta, four basic role
fields and no overflow in RU/EN at 1280x720 and 1366x768.

AS IS: `../RADAR_POWER_WEB_DISCOVERY_AS_IS.md`
Baseline diagnostic: `../validation/0.7.6.6.0.2/BASELINE_DIAGNOSTIC.md`
Acceptance manifest: `RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.0.2.acceptance.json`

## Problem and decision

Slice `0.7.6.6.0.1` established versioned product, semantic-role and access
configuration, but made the downstream access strategy part of the mandatory
Power Web Discovery input. It also combined a persistent product rail, a dense
role table and a right-side editor inside the bounded application workspace.

The corrected discovery configuration is:

`product definition -> semantic buying-role policy -> future account handoff`.

Access rules are frozen compatibility data. They do not constrain publication,
role deletion, RoleDemand compilation or people-search planning. Existing
versions and the existing Access Planner remain readable and unchanged.

## Semantic-role authoring

A role requires only a stable generated code, display name, business
responsibility, requiredness and organizational scope. New required roles
default to high priority; optional roles default to normal priority.

Decision rights, a priority override and exclusions are optional advanced
guidance. Historical reason and expected-evidence values remain readable, but
new configuration does not require or edit them. Expected evidence, title
variants, aliases and queries belong to auditable account-specific planning in
slice `0.7.6.6.2`, not to product policy.

Publication requires complete product context, at least one role and at least
one required role. Empty advanced guidance is valid.

## Access-strategy compatibility

`access_playbook_version_id` becomes nullable. New publications create product
and buying-role snapshots only and expose `access_playbook=null`. Historical
versions with access snapshots continue to return the original data.

The draft API accepts an omitted access field. A supplied value is accepted
only when it is identical to the frozen stored value; mutation returns the
explicit conflict `access_playbook_frozen`. Restoring an historical version
restores product and roles only. No access snapshot is reactivated or created.

## Workspace contract

Playbook uses two states: a full-width product catalog and a full-width product
detail. The detail contains a back command and compact product switcher; it has
no persistent product rail.

Product detail has Product, Buying roles and Versions tabs. Access rules are
absent from the primary workspace. Historical access data is visible only in
read-only version detail and is labelled as compatibility data not used by
Power Web Discovery.

Selecting a role expands its editor below the selected table row. The editor
spans the same width as the table; there is no right inspector. The four basic
business controls are name, responsibility, requiredness and scope. Advanced
guidance is collapsed by default.

A shared underline `WorkspaceTabs` component owns section navigation in
Playbook, Radar detail, candidate detail, run diagnostics and Access Plans.
Pill controls remain reserved for filters and mode switches.

URL state preserves `productId` and the active tab. Loading, API failure,
optimistic conflict and browser navigation never fall back to local demo data.

## Role-demand ownership correction

Slice `0.7.6.6.1` snapshots ProductDefinition and BuyingRolePolicy versions and
compiles role responsibility, requiredness, scope and effective priority. It
does not snapshot AccessPlaybook and does not require authored expected
evidence or route constraints.

Slice `0.7.6.6.2` owns accepted account-specific title, query, alias,
expected-evidence and exclusion hypotheses. These proposals cannot add, remove
or reprioritize semantic roles.

## Requirement traceability

- `PWS-CFG-01`: product and role policy form the complete discovery configuration.
- `PWS-ROLE-01`: a role publishes with only the four basic business controls.
- `PWS-ROLE-02`: priority defaults are deterministic and advanced guidance is optional.
- `PWS-PLAN-01`: expected evidence and title/query variants are planning-owned.
- `PWS-ACCESS-01`: new publication creates no access snapshot or dependency.
- `PWS-ACCESS-02`: historical access data remains readable and immutable.
- `PWS-API-01`: API and persistence survive migration and restart.
- `PWS-UI-01`: catalog and product detail are separate full-width states.
- `PWS-UI-02`: role detail expands inline at the table width.
- `PWS-TABS-01`: section navigation uses shared underline tabs.
- `PWS-COMPAT-01`: Access Planner, Power Web Board and historical versions do not regress.
- `PWS-BENCH-01`: the accepted benchmark remains blind and unchanged.
- `PWS-NET-01`: the slice performs no provider calls or pipeline runs.
- `PWS-PROC-01`: TO BE, tests, validation and finalized AS IS are traceable.

## Hard acceptance

The slice is accepted only after backend, migration, API, frontend and Docker
tests pass; the product detail occupies at least 95 percent of the available
workspace; inline role detail matches the table width within two pixels at
1280x720 and 1366x768 in RU and EN; persisted state survives API restart; all
mandatory requirements pass; and this design is reconciled into AS IS.
