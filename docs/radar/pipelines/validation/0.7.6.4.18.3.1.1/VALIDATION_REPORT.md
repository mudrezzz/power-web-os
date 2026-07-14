# Validation Report: 0.7.6.4.18.3.1.1

Validation status: **PASS**

## Persisted Counter Evidence

| Radar | Basis run | Visible | Accepted | Review needed |
|---|---|---:|---:|---:|
| Benchmark / SIBUR holding contour | `radar-run-3aa622ff-e137-48aa-9f2c-15e74f594bfc` | 10 | 3 | 7 |
| TOIR Quick Live Radar | `radar-run-ef74d8c0-8e19-43eb-9936-cfc0a44c383b` | 2 | 0 | 2 |
| TOIR / SIBUR demo fixture | static fixture | 33 | 0 | 33 |

For both persisted runs, catalog counts and run summaries matched the
candidate rows returned by `/api/radar-runs/{run_id}/candidates`. The catalog
used the latest completed candidate-discovery output. Signal runs and newer
non-completed runs did not replace this basis.

The final reconciliation pass scanned 65 outputs: 0 updated, 65 unchanged and
0 invalid. This proves that the reconciled state survived the repeated API
container restarts. Automated persistence tests separately corrupt and repair
stored summaries, then prove that a second reconciliation pass is idempotent.

## Browser Recovery Evidence

- Docker stack rebuilt before validation.
- Cold opens with an already-ready backend: `10/10 PASS`.
- Frontend-before-backend recovery cycles: `10/10 PASS`.
- Every recovery reached the Backend API state without page reload.
- Catalog detail or artifact requests before opening a Radar: `0` in every
  cold open.
- Viewports alternated between `1280x720` and `1366x768`.
- API container was running after the gate.
- No Radar or provider run was started; no provider tokens were spent.

## Process Retrospective

The previous clean-start stability gate was insufficient in two ways. It did
not test the frontend opening before the API, and it compared catalog counts
with persisted scalar summaries instead of independently checking the
candidates endpoint. The new gate exercises the failure ordering and compares
both read surfaces.

Implementation validation also exposed two concrete defects before PASS:

1. `normalizeRadarCatalogItem` reconstructed the summary using an older shape
   and silently discarded the counter basis and basis run ID received from the
   API. The normalizer now preserves both fields and the catalog renders the
   run ID.
2. The first recovery test treated expected `connection refused` and empty
   response browser messages during the intentional API outage as product
   errors. The gate now permits only those availability errors in recovery
   mode; all other browser and page errors still fail validation.

No pipeline algorithm correction or provider validation is required. The
remaining work belongs to subsequent product slices, not this read-model and
frontend lifecycle correction.
