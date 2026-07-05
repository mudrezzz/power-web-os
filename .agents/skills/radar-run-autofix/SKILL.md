---
name: radar-run-autofix
description: Run a Power Web OS Radar self-test, diagnose it, compare the result with ROADMAP expectations, and perform bounded corrective implementation loops when defects are small implementation gaps. Use when the user asks for "сам запусти и почини", "прогони, продиагностируй и исправь", "self-healing Radar run", "run diagnose fix loop", or wants Codex to run Radar, decide whether behavior matches the roadmap, patch non-architectural defects, and rerun without making the user be the tester.
---

# Radar Run Autofix Skill

## Goal

Run a bounded Radar test, diagnose the persisted result, compare it with the
current `ROADMAP.md`, and either report the result or perform a limited
corrective implementation loop.

This skill orchestrates the existing `radar-run-self-test`,
`radar-run-diagnostics`, `roadmap-slice-planning`, `slice-implementation`, and
`docs-sync` workflows. It does not replace them.

## Loop Limit

Run at most 5 corrective cycles.

A cycle is:

1. run Radar;
2. diagnose persisted dossier, trace, journal, and metadata;
3. compare with current roadmap expectations;
4. classify the mismatch;
5. optionally patch, document, test, and rerun.

Stop immediately when the result matches expectations, when the mismatch is
already covered by the upcoming roadmap, when the fix requires an architectural
shift, or when 5 corrective cycles have been used.

## Preconditions

Before the first run:

1. Read `ROADMAP.md` and identify the current Radar slice, next recommended
   task, and known blocking defects.
2. Run `git status --short --branch`.
3. If the worktree is dirty, identify whether current changes are related to the
   requested self-test. Do not revert unrelated changes.
4. Prefer the smoke/API/worker path unless the user explicitly asks for a full
   benchmark.
5. Run static/offline preflight when available.
6. Never print `.env`, secrets, request headers, bearer tokens, provider API
   keys, or raw hidden reasoning fields.
7. For local OpenRouter live probes and runs, use repository `.env` as the
   credential source of truth. Do not trust an inherited `OPENROUTER_API_KEY`
   process variable when diagnosing provider auth failures.

## Run And Diagnose

Use `radar-run-self-test` to start and poll the run. Then use
`radar-run-diagnostics` on the produced run id.

The diagnosis must inspect:

- runtime config and API/worker parity;
- active Radar definition and source obligations;
- discovery plan, retrieval plan, source cards, and capability validation;
- candidate universe, materialization, entity resolution, and registry lookup
  inputs;
- source lifecycle and evidence linking;
- checkpoint decisions and adaptive actions;
- external-call budgets, provider retries, and not-executed states;
- product vs diagnostic source/candidate projection.

Use the dossier outcome as the primary truth for semantic success or failure.
Top-level run status `completed` is not enough.

## Roadmap Comparison

After diagnosis, compare the observed behavior with `ROADMAP.md`:

- If the result matches the current slice acceptance criteria, report success.
- If the result fails, but the failure is already explicitly covered by the next
  planned slice, report the failure and recommend continuing with that slice.
- If the result fails and the failure is not covered by the roadmap, classify
  the required change before editing.

## Mismatch Classification

### Small implementation defect

Treat as a small implementation defect when the fix is local and preserves the
current architecture, for example:

- missing data handoff between existing stages;
- missing dossier or trace projection;
- incorrect budget counter persistence;
- source capability validation not wired into one existing path;
- malformed fixture or test gap;
- docs missing for already implemented behavior.
- stale inherited provider credentials when `.env` contains the intended local
  key and the runtime loader should prefer `.env`;

For small defects:

1. Add or update a narrow corrective slice in `ROADMAP.md` if the work is not
   already named.
2. Add failing or regression tests first when practical.
3. Implement the smallest patch.
4. Update docs affected by behavior, setup, diagnostics, or roadmap status.
5. Run targeted tests and the relevant smoke/preflight checks.
6. Rerun the Radar smoke if the patch affects runtime behavior.
7. Continue the loop until the result matches expectations, is covered by the
   next roadmap task, or the loop limit is reached.

### Architectural shift

Treat as an architectural shift when the fix changes ownership boundaries,
public contracts, provider architecture, persistence model, UI/product flow, or
long-term roadmap direction, for example:

- new connector/plugin architecture;
- new normalized database tables;
- replacing the provider abstraction;
- changing source obligation semantics;
- adding a new UI configuration model;
- changing benchmark acceptance strategy.

For architectural shifts:

1. Do not implement the change inside the autofix loop.
2. Prepare a report explaining the mismatch, evidence, impact, and options.
3. Propose a roadmap correction or architecture slice.
4. Stop and wait for explicit user direction.

## Patch Discipline

When patching:

- Keep edits scoped to the diagnosed defect.
- Do not start a broad refactor.
- Do not change scoring or source policy semantics unless the roadmap already
  requires it.
- Do not hardcode SIBUR-specific or DaData-specific behavior when connector
  capability or source policy should own the decision.
- Keep product sources evidence-bearing only; diagnostics may show analyzed,
  skipped, unlinked, and rejected sources.
- Keep raw hidden chain-of-thought, secrets, request headers, and raw provider
  dumps out of product dossier and final reports.

## Validation

Each corrective patch must run the narrowest meaningful tests first, then
broader tests when risk is meaningful. Prefer:

```powershell
python -m pytest tests/test_radar_adaptive_execution.py -q
python -m pytest tests/test_live_icp_radar.py tests/test_radar_preflight.py -q
python -m pytest tests/test_backend_api.py tests/test_radar_jobs.py -q
python -m pytest tests/test_backend_architecture_contract.py -q
```

Run additional tests when the changed files require them. If frontend files are
changed, use the frontend design system skill and run frontend contracts/build.

## Final Report

Return a concise Russian report:

1. final run id and terminal status;
2. whether the result matches the roadmap expectation;
3. what was fixed automatically, if anything;
4. tests and smoke runs performed;
5. remaining risks;
6. whether to continue roadmap, run another smoke, or plan an architecture
   correction.

If the loop limit is reached, stop with the latest evidence and recommend the
next manual decision.
