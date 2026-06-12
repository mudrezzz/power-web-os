# ADR: Configurable Object UX

## Status

Accepted

## Context

Power Web OS has configurable product objects: ICP Radars, playbooks, future source setups, scoring models, and monitoring rules. These objects can exist in parallel, and users need to understand what is configured, what is active, what is only planned, and what produced the current output.

The ICP Radar UI initially looked like a single radar existed by nature. We decided to model radars as a catalog of configured objects, then open one object into shortlist and settings modes.

## Decision

Configurable product objects should use catalog-first navigation.

- When the product has many configured objects, start with a catalog/cards view before opening one object.
- Cards should show the object name, status, owner, cadence or run mode, last activity, output counts, and whether the object is active, configured, or planned.
- A selected object should use in-shell navigation such as tabs or segmented controls.
- For ICP Radar the accepted baseline is `Shortlist` / `Settings`.
- Settings screens may be read-only in early slices, but they must be visibly read-only.
- Read-only settings must not include save actions or imply persistence.
- Planned, configured, active, fixture-backed, and live states must be explicit.
- Demo fixtures must not imply live jobs, persistence, scheduling, connectors, or production state.

## Consequences

- Future configuration work can evolve from read-only settings to editable controls without changing the navigation model.
- Product screens can support multiple radars/playbooks/rulesets instead of hardcoding one global object.
- UI copy must be precise about what is active versus planned.

## Alternatives considered

- **Single implicit configuration screen.** Rejected because multiple radars and playbooks can run in parallel.
- **Editable-looking read-only forms.** Rejected because they create false expectations and can make demos misleading.
- **Hide planned objects until implemented.** Rejected for navigation areas where showing planned capability helps explain the product map, as long as the state is explicit.
