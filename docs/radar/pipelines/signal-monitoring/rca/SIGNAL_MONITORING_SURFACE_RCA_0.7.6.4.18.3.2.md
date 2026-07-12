# Signal Monitoring Surface RCA: 0.7.6.4.18.3.2

## Evidence

- Source candidate run: `radar-run-3bbf9c0f-330e-4468-8901-966a751234a8`.
- Initial signal run: `signal-run-010ef75d-c626-44e3-a025-56c95522c1a8`.
- Incremental signal run: `signal-run-df00b3b8-267c-4091-a4dd-8167434e2cf3`.
- Scope: 6 candidates, 2 criteria and 12 candidate-criterion checks.

## Root Causes

The runtime report stored task outcomes correctly, but the product surface did
not preserve their meaning:

1. The UI called 12 checks "results" and rendered only the first six rows.
2. Evidence lived in heterogeneous source collections while the report view
   inspected only one legacy evidence field. Valid `source_refs` therefore
   appeared as zero evidence.
3. The incremental report was a delta. Duplicate states correctly meant
   "already retained", but the UI did not join them to the originating run and
   made four previously confirmed signals disappear.
4. Candidate discovery correctly contained no signal scores after the pipeline
   split, but the main candidate table still displayed those zero values as if
   they were current monitoring results.

## Correction

The application-owned cumulative surface joins only completed signal runs with
the same Radar and source candidate run. It resolves product-safe evidence,
preserves origin lineage and returns both current-run and cumulative status.
The frontend renders all checks and overlays the selected monitoring surface
onto the candidate list without mutating the candidate-discovery artifact.

## Preserved Boundaries

No search, provider, budget, scoring, candidate-universe or persistence
semantics changed. The correction is a read model and product-language change.
Candidates outside the selected signal scope are explicitly "not monitored".
