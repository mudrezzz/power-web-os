# ADR: Product, semantic buying roles and access playbook ownership

## Status

Accepted

## Context

Power Web Discovery needs an authoritative answer to two different questions:
what is being sold, and which business functions must be represented in the
buying committee. The former Playbook UI explained account-specific route
decisions but did not own either answer. Asking an LLM to invent required roles
per account would make coverage unstable and impossible to benchmark.

## Decision

Create a backend-owned, versioned sales-playbook aggregate composed of three
independent snapshots:

- product definition;
- semantic buying-role policy;
- access playbook.

A published sales-playbook version atomically references one compatible version
of each snapshot. Edits occur only in an optimistic mutable draft. Published
snapshots are immutable; activation changes a product pointer and restore
creates a new draft.

Semantic roles describe buying functions and decision responsibility. They do
not contain job titles, people, benchmark controls or source URLs. Future
account-specific title hypotheses may expand retrieval terms but cannot add,
remove, reprioritize or confirm semantic roles.

Global configuration remains in Playbook. The explanation of how rules apply
to a concrete account belongs to Access Plans.

## Consequences

- Power Web Discovery can receive a reproducible immutable role-demand source.
- Benchmark planning can reference a version without leaking people controls.
- Access rules cannot silently reference missing roles.
- Existing `Playbook`, Access Planner and Power Web Board remain compatibility
  consumers until later migration slices.
- Multi-product opportunity composition and account title generation remain
  future work.

## Alternatives considered

- Hardcode a universal buying committee: rejected because products and buying
  motions differ.
- Let the LLM choose mandatory roles: rejected because it makes recall and
  benchmark coverage nondeterministic.
- Keep browser-local Playbook settings: rejected because runs need persisted,
  immutable configuration lineage.
