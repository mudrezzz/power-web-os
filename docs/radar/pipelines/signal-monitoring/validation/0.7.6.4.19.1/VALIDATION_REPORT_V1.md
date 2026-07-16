# Validation Report: 0.7.6.4.19.1

Validation status: `FAIL`

Pipeline: `signal-monitoring`
First live run: `signal-run-8eb6d673-a6f6-417a-8519-8cc50e7e94f8`
Second live run: `signal-run-6754eba6-a43a-4594-8236-d7ed60f6d2c5`
Initial live runs: `signal-run-8eb6d673-a6f6-417a-8519-8cc50e7e94f8, signal-run-6754eba6-a43a-4594-8236-d7ed60f6d2c5`
Incremental live run: `missing`
Restart verified: `False`

## Requirement Results

| Requirement | Status | Evidence |
|---|---|---|
| `SM-REP-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.19.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; manifest_sha256=9dfab1ee6a2a449109d35b8cf53b097cae3a4b48797bfedfb4c7214df2d6d82e |
| `SM-REP-02` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.19.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; initial_runs=2; series=sm-46065b891e37-a,sm-46065b891e37-b5; previous_source_keys=0,0 |
| `SM-REP-03` | `FAIL` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.19.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; {"signal-run-6754eba6-a43a-4594-8236-d7ed60f6d2c5": {"negative": {"matched": 4, "matched_ids": ["voronezh-old-abireg-repair", "kzsk-old-kommersant-modernization", "khimprom-old-interfax-investment", "voronezh-conflicting-smotrim-date"], "missing": []}, "positive": {"matched": 3, "matched_ids": ["voronezh-commissioning-2026", "voronezh-special-component-2026", "voronezh-kommersant-plant-2026"], "missing": ["khimprom-modernization-automation-2025"]}, "unknown": {"matched": 1, "matched_ids": ["khimprom-official-turnaround-date-unknown"], "missing": []}}, "signal-run-8eb6d673-a6f6-417a-8519-8cc50e7e94f8": {"negative": {"matched": 4, "matched_ids": ["voronezh-old-abireg-repair", "kzsk-old-kommersant-modernization", "khimprom-old-interfax-investment", "voronezh-conflicting-smotrim-date"], "missing": []}, "positive": {"matched": 4, "matched_ids": ["khimprom-modernization-automation-2025", "voronezh-commissioning-2026", "voronezh-special-component-2026", "voronezh-kommersant-plant-2026"], "missing": []}, "unknown": {"matched": 1, "matched_ids": ["khimprom-official-turnaround-date-unknown"], "missing": []}}} |
| `SM-QUERY-02` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.19.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; obligations_ok=True |
| `SM-XCRIT-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.19.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; cross_records=130 |
| `SM-XCRIT-02` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.19.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; invalid_cross_criterion=0 |
| `SM-CAP-03` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.19.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; identity_confirmed=0 |
| `SM-URL-01` | `FAIL` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.19.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; control URLs matched by canonical identity |
| `SM-DED-03` | `FAIL` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.19.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; incremental_series=; previous_source_keys=0; republished=0 |
| `SM-PROC-03` | `FAIL` | initial_run_ids=signal-run-8eb6d673-a6f6-417a-8519-8cc50e7e94f8,signal-run-6754eba6-a43a-4594-8236-d7ed60f6d2c5; incremental_run_id=; restart_verified=False |

## Runtime Summary

```json
{
  "initial_live": [
    {
      "candidate_count": 6,
      "accepted_candidate_count": 3,
      "review_candidate_count": 3,
      "signal_rule_count": 2,
      "candidate_signal_pair_count": 12,
      "task_count": 36,
      "orphan_decisions": 0,
      "opaque_known_tasks": 0,
      "unrestricted_official_tasks": 0,
      "open_web_task_count": 24,
      "receipt_gap_count": 0,
      "false_not_observed_count": 0,
      "initial_lookback_days": 365,
      "incremental_window_count": 0,
      "failed_watermark_advances": 9,
      "observed_count": 7,
      "zero_score_observed_count": 0,
      "rejected_observed_count": 2,
      "entity_mismatch_rejection_count": 0,
      "negative_control_tested_count": 4,
      "negative_control_false_positive_count": 0,
      "retrieved_at_as_fresh_count": 0,
      "unknown_date_review_count": 15,
      "out_of_window_confirmed_count": 0,
      "sources_without_capability_count": 0,
      "cross_entity_known_task_count": 0,
      "identity_confirmed_signal_count": 0,
      "alternate_query_count": 36,
      "transport_retry_proven": 0,
      "unretried_transport_error_count": 0,
      "duplicate_review_count": 0,
      "unreasoned_retained_item_count": 0,
      "duplicate_count": 0,
      "previous_source_key_count": 0,
      "republished_previous_source_count": 0
    },
    {
      "candidate_count": 6,
      "accepted_candidate_count": 3,
      "review_candidate_count": 3,
      "signal_rule_count": 2,
      "candidate_signal_pair_count": 12,
      "task_count": 42,
      "orphan_decisions": 0,
      "opaque_known_tasks": 0,
      "unrestricted_official_tasks": 0,
      "open_web_task_count": 30,
      "receipt_gap_count": 0,
      "false_not_observed_count": 0,
      "initial_lookback_days": 365,
      "incremental_window_count": 0,
      "failed_watermark_advances": 8,
      "observed_count": 7,
      "zero_score_observed_count": 0,
      "rejected_observed_count": 5,
      "entity_mismatch_rejection_count": 0,
      "negative_control_tested_count": 4,
      "negative_control_false_positive_count": 0,
      "retrieved_at_as_fresh_count": 0,
      "unknown_date_review_count": 16,
      "out_of_window_confirmed_count": 0,
      "sources_without_capability_count": 0,
      "cross_entity_known_task_count": 0,
      "identity_confirmed_signal_count": 0,
      "alternate_query_count": 42,
      "transport_retry_proven": 2,
      "unretried_transport_error_count": 0,
      "duplicate_review_count": 0,
      "unreasoned_retained_item_count": 0,
      "duplicate_count": 0,
      "previous_source_key_count": 0,
      "republished_previous_source_count": 0
    }
  ],
  "incremental_live": {
    "candidate_count": 0,
    "accepted_candidate_count": 0,
    "review_candidate_count": 0,
    "signal_rule_count": 0,
    "candidate_signal_pair_count": 0,
    "task_count": 0,
    "orphan_decisions": 0,
    "opaque_known_tasks": 0,
    "unrestricted_official_tasks": 0,
    "open_web_task_count": 0,
    "receipt_gap_count": 0,
    "false_not_observed_count": 0,
    "initial_lookback_days": 0,
    "incremental_window_count": 0,
    "failed_watermark_advances": 0,
    "observed_count": 0,
    "zero_score_observed_count": 0,
    "rejected_observed_count": 0,
    "entity_mismatch_rejection_count": 0,
    "negative_control_tested_count": 4,
    "negative_control_false_positive_count": 0,
    "retrieved_at_as_fresh_count": 0,
    "unknown_date_review_count": 0,
    "out_of_window_confirmed_count": 0,
    "sources_without_capability_count": 0,
    "cross_entity_known_task_count": 0,
    "identity_confirmed_signal_count": 0,
    "alternate_query_count": 0,
    "transport_retry_proven": 0,
    "unretried_transport_error_count": 0,
    "duplicate_review_count": 0,
    "unreasoned_retained_item_count": 0,
    "duplicate_count": 0,
    "previous_source_key_count": 0,
    "republished_previous_source_count": 0
  },
  "restart_verified": false
}
```

## Process Retrospective

- `SM-REP-RCA-01`: One accepted initial run did not prove live-search reproducibility and its accepted URL set was adjusted after output inspection. Resolution: Freeze controls before execution and require two independent initial runs plus a separate incremental proof.
- `SM-XCRIT-RCA-01`: Two missing S2 controls were present in the failed artifact under S1 receipts. Resolution: Revalidate product-safe evidence across configured criteria with explicit origin provenance.
- `SM-CAP-RCA-01`: A mixed provider response allowed an identity-only XLSX to participate in a confirmed signal. Resolution: Apply capability eligibility to each confirmed evidence ref.
