# Power Web Handoff Baseline Diagnostic 0.7.6.6.1

Status: Baseline before implementation.

## Current behavior

- Radar candidate discovery can persist evidence-complete accepted and review-needed candidates.
- Signal Monitoring can persist candidate-scoped signal results linked to a candidate-discovery run.
- Sales Playbook persists versioned products and semantic buying roles.
- Radar has no product binding policy.
- There is no account identity snapshot, role-demand compiler, handoff preflight, immutable handoff record, API, or UI.
- The existing future `RoleDemand` contract still contains aliases, expected evidence and a required reason, which contradicts the simplified product-policy boundary accepted in `0.7.6.6.0.2`.

## Gap

The three existing surfaces are disconnected. A candidate cannot be prepared for people discovery without manually reconstructing product versions, roles, provenance and signal lineage. Creating a Power Web run at this point would hide this missing boundary and would make later results irreproducible.

## Baseline safety

The slice must create no provider calls, candidate-discovery runs, signal-monitoring runs or Power Web discovery runs. Its runtime evidence is a persisted Docker/API/UI handoff assembled only from existing source-backed data.
