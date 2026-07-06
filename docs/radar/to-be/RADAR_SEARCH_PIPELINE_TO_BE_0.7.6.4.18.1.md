# Radar Search Pipeline TO BE 0.7.6.4.18.1

Status: Implemented design input

Product area: Radar candidate discovery pipeline

Slice: 0.7.6.4.18.1 Candidate discovery and signal monitoring runtime split

Last updated: 2026-07-06

Generated PDF: `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_0.7.6.4.18.1.pdf`

## Goal

Candidate discovery becomes a producer/handoff pipeline. It finds and qualifies
candidate entities, records checkpoints, source obligations, budgets, coverage,
and candidate universe diagnostics, then projects signal-monitoring intent as
pending work. It no longer owns recurring signal evaluation as the normal
runtime path.

## Intended Runtime Split

Normal candidate discovery:

1. Planning and plan acceptance remain unchanged.
2. Discovery, retrieval, extraction, recovery, registry/entity resolution,
   checkpoints, coverage, expansion, and disambiguation remain unchanged.
3. The pre-signal checkpoint remains mandatory.
4. If the checkpoint continues, candidate discovery does not call providers for
   `signal_search`.
5. It projects one handoff status per configured signal task and candidate
   scope row:
   - `search_status="not_searched_pending_signal_monitoring"`;
   - `not_searched_reason="pending_signal_monitoring"`;
   - `signal_task_count=0`.
6. Final metadata exposes:
   - `signal_execution_mode`;
   - `signal_monitoring_handoff_status`;
   - `signal_monitoring_pending_count`.

Explicit compatibility mode:

- `signal_execution_mode="inline_compatibility"` preserves the old embedded
  `signal_search` execution for legacy tests and hidden callers.
- This mode may produce `searched` and searched-negative signal states because
  provider work actually ran.
- It is not the normal product runtime.

## Behavior Rules

- Unknown `signal_execution_mode` values fall back to `handoff`.
- `not_observed` is legal only when a signal was actually searched by signal
  monitoring or explicit inline compatibility.
- A blocked pre-signal checkpoint still produces existing
  `not_searched_policy_limited` / stopped-for-review statuses.
- Candidate discovery may keep signal task definitions in the execution plan as
  handoff intent, but it must not spend signal-monitoring budget.
- Candidate discovery must not import the `radar.signal_monitoring` runtime
  package.

## Validation Plan

- Focused tests prove default candidate discovery does not call provider stage
  `signal_search`.
- Compatibility tests explicitly opt into `inline_compatibility`.
- Adaptive/live/API regression tests prove candidate/source/checkpoint/dossier
  shape remains stable.
- Signal-monitoring recorded tests prove the separate pipeline still runs.
- AS IS Markdown/PDF is regenerated after implementation.
