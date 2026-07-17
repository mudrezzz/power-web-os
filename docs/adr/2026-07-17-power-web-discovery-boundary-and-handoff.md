# ADR: Power Web discovery boundary and Access Planner handoff

## Status

Accepted

## Context

Power Web OS currently displays supplied roles and plans access routes but has
no runtime that discovers and validates people. Candidate Discovery and Signal
Monitoring already have independent ownership and must not absorb this work.

## Decision

Create `power-web-discovery` as a third independent Radar pipeline. It owns role
demand, people-source planning, source-native profiles, reversible identity
decisions, employment and relationship claims, graph projection, gaps and
diagnostics.

It receives an account lineage snapshot and later emits an evidence-backed,
reviewable graph. A separate adapter may project approved states to the existing
`PowerWebRole` read model consumed by `PowerWebBoard` and Access Planner.

The application package is provider-neutral and imports neither other pipeline
internals nor transport, persistence, job or integration frameworks.

## Consequences

- Three pipeline histories, budgets and artifacts remain independent.
- Access Planner does not own identity or employment truth.
- Existing Board/Planner contracts remain compatible.
- Runtime, persistence and UI are delivered by later slices.

## Alternatives considered

- Extend Candidate Discovery: rejected because company and person identity have
  different evidence, privacy and review semantics.
- Put people search inside Access Planner: rejected because route planning must
  consume reviewed evidence rather than create it.
