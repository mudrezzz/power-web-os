# ADR: Power Web Discovery Configuration Excludes Access Strategy

Date: 2026-07-21

Status: Accepted

## Context

The initial Playbook foundation combined product context, semantic buying roles
and access-route strategy. People discovery only needs to know what is sold and
which buying functions must be covered. Route constraints describe a later
engagement decision and can prematurely constrain discovery.

The original UI also exposed route policy as a required configuration area and
used simultaneous product and role side panels, leaving too little horizontal
space for role authoring.

## Decision

The canonical input to Power Web Discovery is an immutable product definition
plus semantic buying-role policy. New published definitions do not create or
reference an AccessPlaybook version.

Existing AccessPlaybook records remain immutable and readable. The API rejects
attempts to mutate them, and restoring an historical version does not reactivate
its routes. Access Planner remains an independent compatibility contour until a
future product decision defines Access Strategy.

Product configuration uses catalog-to-detail navigation. Product detail owns
the full workspace width, role details expand inline, and workspace sections
use the shared underline-tab component.

## Consequences

- Power Web Discovery can compile RoleDemand without route-policy coupling.
- Users author four basic role properties; search titles and evidence hints are
  generated later as reviewable account-specific hypotheses.
- Historical route data is preserved without driving new people searches.
- Access Planner behavior is retained, but no new access-policy authoring is
  exposed in the Playbook UI.
