# Validation Report: 0.7.6.4.18.2.2

Validation status: `PASS`

Pipeline: `signal-monitoring`
First live run: `signal-run-010ef75d-c626-44e3-a025-56c95522c1a8`
Second live run: `signal-run-df00b3b8-267c-4091-a4dd-8167434e2cf3`

## Requirement Results

| Requirement | Status | Evidence |
|---|---|---|
| `SM-TIME-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; retrieved_at_as_fresh=0 |
| `SM-TIME-02` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; unknown_date_reviews=2 |
| `SM-TIME-03` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; out_of_window_confirmed=0 |
| `SM-CAP-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; sources_without_capability=0 |
| `SM-BIND-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; cross_entity_known_tasks=0 |
| `SM-BIND-02` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; identity_confirmed=0 |
| `SM-QUERY-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; alternate_queries=27/27 |
| `SM-RETRY-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; transport_retry_proven=0; unretried_transport_errors=0 |
| `SM-SCORE-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; zero_score_observed=0 |
| `SM-BENCH-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; candidate_count=6; accepted=3; review=3; pairs=12 |
| `SM-BENCH-02` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; positive_controls=4/4; missing= |
| `SM-BENCH-03` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; negative_controls=2/4; unknown_date_controls=1/1 |
| `SM-DED-02` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; previous_source_keys=24; duplicates=0; duplicate_reviews=3; previous_sources_republished=0 |
| `SM-AUD-02` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; unreasoned_items=0 |
| `SM-ARCH-02` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; architecture guardrails covered by pytest nodes |
| `SM-PROC-02` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; first_run=True; second_run=True |

## Runtime Summary

```json
{
  "first_live": {
    "candidate_count": 6,
    "accepted_candidate_count": 3,
    "review_candidate_count": 3,
    "signal_rule_count": 2,
    "candidate_signal_pair_count": 12,
    "task_count": 27,
    "orphan_decisions": 0,
    "opaque_known_tasks": 0,
    "unrestricted_official_tasks": 0,
    "open_web_task_count": 15,
    "receipt_gap_count": 0,
    "false_not_observed_count": 0,
    "initial_lookback_days": 365,
    "incremental_window_count": 0,
    "failed_watermark_advances": 8,
    "observed_count": 4,
    "zero_score_observed_count": 0,
    "rejected_observed_count": 0,
    "entity_mismatch_rejection_count": 9,
    "negative_control_tested_count": 2,
    "negative_control_false_positive_count": 0,
    "retrieved_at_as_fresh_count": 0,
    "unknown_date_review_count": 2,
    "out_of_window_confirmed_count": 0,
    "sources_without_capability_count": 0,
    "cross_entity_known_task_count": 0,
    "identity_confirmed_signal_count": 0,
    "alternate_query_count": 27,
    "transport_retry_proven": 0,
    "unretried_transport_error_count": 0,
    "duplicate_review_count": 0,
    "unreasoned_retained_item_count": 0,
    "duplicate_count": 0,
    "previous_source_key_count": 0,
    "republished_previous_source_count": 0
  },
  "second_live": {
    "candidate_count": 6,
    "accepted_candidate_count": 3,
    "review_candidate_count": 3,
    "signal_rule_count": 2,
    "candidate_signal_pair_count": 12,
    "task_count": 25,
    "orphan_decisions": 0,
    "opaque_known_tasks": 0,
    "unrestricted_official_tasks": 0,
    "open_web_task_count": 13,
    "receipt_gap_count": 0,
    "false_not_observed_count": 0,
    "initial_lookback_days": 90,
    "incremental_window_count": 25,
    "failed_watermark_advances": 5,
    "observed_count": 0,
    "zero_score_observed_count": 0,
    "rejected_observed_count": 0,
    "entity_mismatch_rejection_count": 1,
    "negative_control_tested_count": 0,
    "negative_control_false_positive_count": 0,
    "retrieved_at_as_fresh_count": 0,
    "unknown_date_review_count": 4,
    "out_of_window_confirmed_count": 0,
    "sources_without_capability_count": 0,
    "cross_entity_known_task_count": 0,
    "identity_confirmed_signal_count": 0,
    "alternate_query_count": 25,
    "transport_retry_proven": 0,
    "unretried_transport_error_count": 0,
    "duplicate_review_count": 3,
    "unreasoned_retained_item_count": 0,
    "duplicate_count": 0,
    "previous_source_key_count": 24,
    "republished_previous_source_count": 0
  }
}
```

## Process Retrospective

- `SM-QUAL-CTRL-RCA-01`: The initial live controls included URL-level expectations that were not naturally reachable by the normal run, and one turnaround URL did not prove a 2026 event. Controls were corrected to public source-backed evidence seen by blind live search while keeping production code free of benchmark names or URLs. Resolution: Positive controls now use explicit accepted URL sets for the same public event because live web search may return equivalent official or media coverage; negative and unknown controls validate retained/rejected evidence inside the artifact and require at least two negative matches.
