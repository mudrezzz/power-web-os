# Validation Report: 0.7.6.4.18.3.1

Validation status: `PASS`

Pipeline: `signal-monitoring`

## Runtime Evidence

- Docker stack rebuilt with migration `202607120719`.
- Benchmark Radar cold opens: `10/10` PASS, alternating `1280x720` and `1366x768`.
- Settings on every open: `2` qualification rules, `3` signals, `3` sources.
- Detail payload: `16,313` bytes, down from the observed `33.3 MB` and below `250 KB`.
- Twenty-run history: `17,367` bytes, below `250 KB`.
- Radar detail requests before catalog selection: `0`.
- Persisted definition version after API restart: `0.7.6.4.18.3.1`.
- Per-signal policies survived API -> DB -> restart -> API round-trip.

## Requirement Results

| Requirement | Status | Evidence |
|---|---|---|
| `SM-CFG-01` | PASS | Three policies persisted and reloaded after API restart. |
| `SM-CFG-02` | PASS | Effective values and basis are present in preflight and artifact contracts. |
| `SM-CFG-03` | PASS | Planner excludes criterion-disabled source lanes. |
| `SM-WIN-04` | PASS | Criterion overlap controls incremental window. |
| `RADAR-API-01` | PASS | 16,313-byte detail; 17,367-byte history. |
| `RADAR-LAZY-01` | PASS | No catalog fanout; diagnostics and full report load on interaction. |
| `RADAR-UI-01` | PASS | 10/10 cold opens showed complete 2/3/3 definition. |
| `RADAR-UI-02` | PASS | Loading/error/stale/dirty states are explicit; no silent fallback. |
| `SM-PROC-03` | PASS | TO BE, manifest, tests, validation and AS IS are linked. |

## Process Retrospective

The first Docker browser run exposed a permanent-loading race. The definition
loader callback depended on its own state; every state transition launched a
new request and invalidated the previous response. Unit/build gates did not
detect it. The ten-cold-open gate did, and the loader now uses stable callback
identity, request identity and a dedicated loaded-definition cache. Future
configuration slices must keep repeated cold browser opens in their DoD.
