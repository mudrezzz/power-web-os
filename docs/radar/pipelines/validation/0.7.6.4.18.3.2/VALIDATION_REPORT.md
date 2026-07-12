# Validation Report: 0.7.6.4.18.3.2

Validation status: **PASS**

## Persisted Evidence

- Radar: `benchmark-sibur-holding-contour`.
- Candidate run: `radar-run-3bbf9c0f-330e-4468-8901-966a751234a8`.
- Initial signal run: `signal-run-010ef75d-c626-44e3-a025-56c95522c1a8`.
- Incremental signal run: `signal-run-df00b3b8-267c-4091-a4dd-8167434e2cf3`.
- Public candidate surface: 74 unique candidates.
- Monitoring scope: 6 candidates, 2 criteria, 12 checks.
- Candidates outside scope: 68, all explicitly marked not monitored.

## Semantic Results

The initial run renders exactly 4 confirmed fresh outcomes, 3 review outcomes
and 5 searched-negative outcomes. Every confirmed or retained review outcome
has resolved product-safe provenance.

The incremental run renders 0 new confirmed outcomes while preserving 4
previously confirmed outcomes and their originating run. It renders 4 current
review outcomes and 8 current searched-negative outcomes. No prior confirmed
state is presented as zero merely because the selected run is incremental.

The UI says "6 candidates x 2 criteria = 12 checks". It does not claim that 12
signals were found. All 12 checks are rendered without hidden truncation.

## Product Surface Results

- The signal report displays current and cumulative status separately.
- Source links, temporal basis and origin run are visible.
- The main candidate table and candidate detail use the selected monitoring
  surface while candidate discovery identity and qualification stay unchanged.
- API mode does not use the static recorded report.
- English 1280x720 and Russian 1366x768 browser gates passed.

## Process Retrospective

The previous split-UI gate checked panel presence, lineage and row counts but
did not assert semantic values, cumulative state or evidence links. The DoD
script now validates all 12 pair outcomes, exact initial/incremental counts,
resolved evidence and the candidate-list overlay. This closes the procedural
gap that allowed a technically correct runtime report to remain misleading in
the product.
