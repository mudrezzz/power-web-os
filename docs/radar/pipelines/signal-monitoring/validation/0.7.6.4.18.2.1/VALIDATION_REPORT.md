# Validation Report: 0.7.6.4.18.2.1

Validation status: `PASS`

Pipeline: `signal-monitoring`
First live run: `signal-run-9d018757-a96c-4902-92ac-b0bdb4d3bb50`
Second live run: `signal-run-863de7ce-cdab-456f-91f8-917c0a875452`

## Requirement Results

| Requirement | Status | Evidence |
|---|---|---|
| `SM-PLAN-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; orphan_decisions=0 |
| `SM-SRC-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; opaque_known_tasks=0 |
| `SM-SRC-02` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; unrestricted_official_tasks=0 |
| `SM-SRC-03` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; open_web_tasks=4 |
| `SM-AUD-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; receipt_gap_count=0 |
| `SM-OBS-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; false_not_observed=0 |
| `SM-WIN-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; initial_lookback_days=365 |
| `SM-WIN-02` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; incremental_windows=14 |
| `SM-WIN-03` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; failed_watermark_advances=0 |
| `SM-VAL-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; observed_count=4 |
| `SM-VAL-02` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; rejected_observed_count=0; negative_controls_tested=1; negative_control_false_positives=0 |
| `SM-DED-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md; previous_source_keys=35; duplicates_suppressed=2; previous_sources_republished=0 |
| `SM-ARCH-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md |
| `SM-PROC-01` | `PASS` | docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md; docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md |

## Runtime Summary

```json
{
  "first_live": {
    "candidate_count": 2,
    "signal_rule_count": 2,
    "orphan_decisions": 0,
    "opaque_known_tasks": 0,
    "unrestricted_official_tasks": 0,
    "open_web_task_count": 4,
    "receipt_gap_count": 0,
    "false_not_observed_count": 0,
    "initial_lookback_days": 365,
    "incremental_window_count": 0,
    "failed_watermark_advances": 2,
    "observed_count": 4,
    "rejected_observed_count": 0,
    "entity_mismatch_rejection_count": 0,
    "negative_control_tested_count": 1,
    "negative_control_false_positive_count": 0,
    "duplicate_count": 0,
    "previous_source_key_count": 0,
    "republished_previous_source_count": 0
  },
  "second_live": {
    "candidate_count": 2,
    "signal_rule_count": 2,
    "orphan_decisions": 0,
    "opaque_known_tasks": 0,
    "unrestricted_official_tasks": 0,
    "open_web_task_count": 4,
    "receipt_gap_count": 0,
    "false_not_observed_count": 0,
    "initial_lookback_days": 90,
    "incremental_window_count": 14,
    "failed_watermark_advances": 0,
    "observed_count": 0,
    "rejected_observed_count": 0,
    "entity_mismatch_rejection_count": 0,
    "negative_control_tested_count": 1,
    "negative_control_false_positive_count": 0,
    "duplicate_count": 2,
    "previous_source_key_count": 35,
    "republished_previous_source_count": 0
  }
}
```

## Process Retrospective

- `LIVE-SCHEMA-01`: Live provider confidence aliases were broader than the application contract. Resolution: Normalize provider confidence values before contract validation and cover aliases with adapter tests.
- `LIVE-LANE-01`: A broad OpenRouter capability card could collapse official and open-web routing. Resolution: Compile explicit lane tasks and require a terminal ledger entry for every selected decision.
- `LIVE-ENTITY-01`: Known-source retrieval could return evidence for another SIBUR entity. Resolution: Validate candidate identity and enforce the requested known-source URL family before accepting evidence.
- `LIVE-DED-01`: Summary-based fingerprints were unstable across incremental provider responses. Resolution: Persist candidate-signal-source URL keys and suppress overlap matches independently of generated wording.
- `PROCESS-IMAGE-01`: One verification run used a stale API image after a worker-only rebuild. Resolution: Rebuild the complete Docker stack before final live evidence and inspect the queued input snapshot before acceptance.
