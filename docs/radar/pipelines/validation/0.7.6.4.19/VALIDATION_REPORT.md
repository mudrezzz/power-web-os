# Radar Namespace Closure Validation

Validation status: **PASS**

## Runs

- candidate_baseline: radar-run-3bbf9c0f-330e-4468-8901-966a751234a8
- candidate_live: radar-run-b03fac86-7307-448f-8deb-c1ea1794956c
- signal_baseline_initial: signal-run-010ef75d-c626-44e3-a025-56c95522c1a8
- signal_baseline_incremental: signal-run-df00b3b8-267c-4091-a4dd-8167434e2cf3
- signal_live_initial: signal-run-8eb6d673-a6f6-417a-8519-8cc50e7e94f8
- signal_live_incremental: signal-run-47e29772-8cbf-421e-8072-7c2d951ba611

## Requirements

| Requirement | Status |
|---|---|
| NS-ROOT-01 | PASS |
| NS-CAND-01 | PASS |
| NS-TRACE-01 | PASS |
| NS-SIGNAL-01 | PASS |
| NS-SIGNAL-02 | PASS |
| NS-LINEAGE-01 | PASS |
| NS-NO-RERUN-01 | PASS |
| NS-RESTART-01 | PASS |

## Candidate Discovery

- Strict recall: 1.0
- Visible recall: 0.8889
- Visible candidates: 91
- Retained upstream leads: 110
- Quality scope: 6 candidates

## Trace Comparison

- Classification: provider_drift
- Phase order preserved: True
- Behavior regressions: []
- Provider drift: ['provider_trace_count:172->190']

## Signal Monitoring

- Initial pass: True
- Incremental pass: True
- Lineage pass: True
- Positive controls: 4
- Negative controls: 4

## Retrospective

Root namespace closure is proven by fresh live evidence.
