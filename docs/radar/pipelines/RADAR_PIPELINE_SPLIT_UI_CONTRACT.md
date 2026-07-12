# Radar Pipeline Split UI Contract

Status: Implemented by slice `0.7.6.4.18.3`.

## Purpose

The Radar workspace presents candidate discovery and signal monitoring as two
separate pipelines. Candidate discovery finds and qualifies companies. Signal
monitoring checks configured signals only for candidates from one completed
candidate-discovery run.

## Invariants

- Candidate history contains only `pipeline_id=candidate_discovery` runs.
- Signal history contains only `pipeline_id=signal_monitoring` runs.
- Every signal run exposes `source_run_id`; its report exposes the same value as
  `source_candidate_run_id`.
- Selecting a signal run also selects its source candidate run. The UI never
  renders a signal report next to an unrelated candidate snapshot.
- Candidate tables, dossier, diagnostics and review actions continue to use the
  selected candidate run only.
- Signal status, report and budget data come only from the selected signal run.
- The product-facing monitoring surface is a cumulative application read model.
  It joins only completed signal runs with the same Radar and source candidate
  run, while keeping current-run delta and retained state separate.
- A signal report names candidate count, criterion count and check count. A
  candidate-criterion check is never presented as a found signal.
- Every retained or confirmed outcome resolves to product-safe evidence and its
  origin run. Candidates outside the selected monitoring scope are explicitly
  marked not monitored.
- Candidate and signal budget counters are rendered in separately labelled
  sections and are never added together.
- Signal runs never replace the latest candidate run or change candidate catalog
  counters.
- In API mode the committed recorded report is not used as a backend result. It
  is available only in visibly labelled offline/demo fallback mode.

## UI Flow

The Radar `Runs` tab contains two panels. `Candidate discovery` owns its run
action, preflight, diagnostics and budget. `Signal monitoring` owns its own
preflight, run action, history, budget and report, and names the source candidate
run.

Normal Signal Monitoring UI execution uses the selected completed candidate
run, `accepted_and_review_needed` scope, all configured signal rules, Radar-owned
lookback settings, and `signal_monitoring_smoke` budget profile.

Direct inspection uses:

```text
?runId=radar-run-...&signalRunId=signal-run-...
```

When only `signalRunId` is supplied, the UI resolves its lineage and normalizes
the URL to the linked pair. Missing or wrong-radar runs produce an explicit
error; there is no silent latest-run fallback.

## Deferred Product Work

- Per-signal depth, cadence and source controls belong to `0.7.6.4.18.3.1`.
- Human evidence wording and cumulative monitoring projection were implemented
  by `0.7.6.4.18.3.2`.
- Candidate projection strictness belongs to `0.7.6.5.1`.

## Validation

The contract is covered by backend pipeline-history tests, frontend static
contracts, TypeScript build and `radar:pipeline-split-ui-dod`. The Docker UI gate
checks linked persisted runs at 1280x720 and 1366x768 in English and Russian,
including direct URL synchronization, separate budgets and explicit missing-run
errors. Slice `0.7.6.4.18.3.2` extends the same gate with semantic assertions
for all 12 checks, evidence links, initial versus incremental counts and the
candidate-list overlay.
