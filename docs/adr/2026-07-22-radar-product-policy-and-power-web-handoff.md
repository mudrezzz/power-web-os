# ADR: Radar Product Policy And Immutable Power Web Handoff

Date: 2026-07-22

Status: Accepted

## Context

Candidate Discovery and Signal Monitoring are Radar-owned, while semantic
buying roles are product-owned. A Radar may serve several products, and one
product may be reused by several Radars. Coupling product bindings to the large
Radar definition would allow unrelated settings updates to overwrite them.
Starting people retrieval directly from mutable UI state would also make old
results impossible to explain.

## Decision

Store Radar-product bindings as a separate ordered, immutable-versioned
many-to-many policy. Prepare one immutable `power_web_handoff.v1` per account
before people retrieval. The handoff freezes candidate lineage, account
identity, selected product/version snapshots, product-scoped semantic role
demands, optional linked signal context and review acknowledgement.

The handoff is not a Power Web run and performs no retrieval. Accepted
candidates are admitted directly; review-needed candidates require explicit
acknowledgement. Signal context is optional and must match Radar, source run and
candidate scope. Similar roles from different products remain separate.

## Consequences

- Product and Radar configuration can evolve without rewriting old handoffs.
- Future people-search runs receive a deterministic, auditable input brief.
- Account identity can be stable by INN/OGRN or explicitly provisional.
- Access strategy is not a discovery input.
- The UI can show readiness honestly before any person is found.
- A later runtime owns title/query hypotheses, retrieval and identity resolution.
