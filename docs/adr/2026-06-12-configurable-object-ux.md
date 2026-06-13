# ADR: Configurable Object UX

## Status

Accepted

## Context

Power Web OS has configurable product objects: ICP Radars, playbooks, future source setups, scoring models, and monitoring rules. These objects can exist in parallel, and users need to understand what is configured, what is active, what is only planned, and what produced the current output.

The ICP Radar UI initially looked like a single radar existed by nature. We decided to model radars as a catalog of configured objects, then open one object into shortlist and settings modes.

## Decision

Configurable product objects should use catalog-first navigation.

- When the product has many configured objects, start with a catalog view before opening one object.
- Catalogs for dense operational objects should use list-first rows rather than narrow multi-column cards when users need to compare status, cadence, last run, owner, and output counts.
- Catalog rows should show the object name, status, owner, cadence or run mode, last activity, output counts, and whether the object is active, configured, or planned.
- Catalog row columns must be stable across rows. Status, metrics, run mode, and primary action should occupy predictable columns instead of floating based on content width.
- Stable columns must still shrink, wrap, or ellipsize inside the bounded workspace. Do not use fixed minimum column widths that create page-level horizontal overflow on laptop screens.
- A selected object should use in-shell navigation such as tabs or segmented controls.
- For ICP Radar the accepted baseline is `Shortlist` / `Settings`.
- Settings screens may be read-only in early slices, but they must be visibly read-only.
- Read-only settings must not include save actions or imply persistence.
- Editable settings may be introduced as a local demo loop before production persistence, but the persistence boundary must be visible in the UI.
- Local editable loops must label created or modified objects as local drafts or locally modified state.
- Save, discard, duplicate, reset-one-object, and reset-all-demo-changes actions should be explicit for configurable objects.
- Complex configuration screens should prefer block-level editing. Each block owns its own edit/save/discard lifecycle so users can change sources, rules, signals, monitoring, or scoring without putting the whole object into one broad edit mode.
- Generated artifacts remain the reset source of truth until backend persistence exists.
- Editing configuration must not imply live execution, scheduling, connector setup, or output recalculation unless that behavior is implemented.
- Constrained controls are preferred for settings such as cadence, run mode, thresholds, source definitions, source policies, rule groups, signal detection rules, and scoring rubrics.
- Scoring setup should offer named presets first. Custom formula text is acceptable only as an explicit advanced mode that shows generated rule ids or signal codes as a reference.
- User-facing rule editors should collect names, natural-language descriptions, requirement level, and source policy. Internal field/operator/value triples may be generated for future agent execution, but they must not be the primary UX.
- Planned, configured, active, fixture-backed, and live states must be explicit.
- Demo fixtures must not imply live jobs, persistence, scheduling, connectors, or production state.

## Consequences

- Future configuration work can evolve from read-only settings to editable controls without changing the navigation model.
- Product screens can support multiple radars/playbooks/rulesets instead of hardcoding one global object.
- UI copy must be precise about what is active versus planned.
- Frontend-local configuration is useful for PoC learning, but it must not blur into production persistence or durable workflow state.

## Alternatives considered

- **Single implicit configuration screen.** Rejected because multiple radars and playbooks can run in parallel.
- **Editable-looking read-only forms.** Rejected because they create false expectations and can make demos misleading.
- **Hide planned objects until implemented.** Rejected for navigation areas where showing planned capability helps explain the product map, as long as the state is explicit.
