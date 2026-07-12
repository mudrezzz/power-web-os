# Validation Report: 0.7.6.4.18.3

Validation status: **PASS**

## Persisted Evidence

- Radar: `benchmark-sibur-holding-contour`
- Candidate run: `radar-run-3bbf9c0f-330e-4468-8901-966a751234a8`
- Selected signal run: `signal-run-df00b3b8-267c-4091-a4dd-8167434e2cf3`
- Second signal history run: `signal-run-010ef75d-c626-44e3-a025-56c95522c1a8`
- Signal scope: 6 candidates
- Signal observations: 12

## Results

The Docker-backed UI rendered candidate discovery and signal monitoring as
separate panels with separate histories, controls, budgets and reports. Direct
opening by `signalRunId` selected the linked candidate run and normalized the
URL to the run pair. Selecting the second signal run preserved lineage. Static
recorded fallback was absent in API mode, and a missing signal run produced a
visible error instead of opening latest candidate data.

The browser DoD passed at 1280x720 in English and 1366x768 in Russian. It also
checked horizontal overflow and panel intersection. API restart retained both
histories and reports.

## Process Retrospective

The first browser pass exposed a presentation defect: candidate budget counters
were separate in data but the section name existed only as an ARIA label. The
UI was corrected to show explicit `Candidate discovery budget` and `Signal
monitoring budget` headings. This is why cross-pipeline acceptance must inspect
visible explanations, not only transport payloads.

No pipeline semantic correction or new roadmap slice is required. Per-signal
settings and human evidence wording remain in `0.7.6.4.18.3.1` and
`0.7.6.4.18.3.2`.
