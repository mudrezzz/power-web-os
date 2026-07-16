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
8. For the API/worker path, prefer the Docker dev API host port
   `http://127.0.0.1:8001`. Use `http://127.0.0.1:8000` only for a manual local
   uvicorn process after verifying `/health` and `/api/radars` belong to Power
   Web OS.
9. Before any Docker/API-backed run, rebuild the stack yourself:

   ```powershell
   docker compose up -d --build
   ```

   Do not ask the user whether to rebuild, and do not treat a run against a
   stale backend image as evidence for current workspace code. Mention Docker
   only when Docker is unavailable or the rebuild fails.

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
- If the result contradicts a slice already marked `Done`, treat that as a
  process defect, not just a product bug. Identify which assumption, test,
  guardrail, documentation, skill instruction, or roadmap acceptance criterion
  let the mismatch pass.

## Post-Slice Retrospective

For every Radar slice that changes candidate discovery, source routing,
extraction, admission, projection, checkpoints, budgets, signal monitoring, API
surface, or benchmark semantics, perform a retrospective after the run:

1. Compare observed behavior against each relevant completed slice, not only
   the current next slice.
2. Explain count surfaces in plain language: raw upstream entities,
   benchmark matched entities, public candidate rows, accepted product
   candidates, and signal-monitoring rows are different surfaces.
3. Flag contradictions, for example:
   - recall-first upstream is marked done but public candidates are all
     `Monitor`;
   - benchmark targets are present in source diagnostics but remain
     `present_not_projected`;
   - `product_candidate_count=0` appears while the run found source-backed
     upstream leads;
   - candidate discovery emits signal-like review flags after handoff mode.
4. Decide whether the response needs:
   - a small autofix;
   - a new corrective roadmap slice;
   - a skill/procedure update;
   - an architecture/ADR/test/guardrail update.
5. Do not close the loop with "continue roadmap" until the contradiction is
   either fixed, explicitly covered by the next slice, or recorded as a new
   corrective slice.

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

Autofix is limited to five corrective cycles. It may repair local defects that
preserve the approved TO BE, but it must not weaken acceptance thresholds,
remove mandatory requirement IDs, or rewrite the intended algorithm. A needed
TO BE/DoD change stops the loop for explicit design revision.

For migration-only slices with mandatory live regression proof, a local import
or wiring defect may be repaired within the five-cycle limit. The complete
candidate plus initial/incremental signal chain must then be repeated; passing
only the previously failed command is insufficient. Never weaken recall,
control, provenance, trace, or dedupe thresholds to obtain PASS.

For reproducibility gates with independent initial runs A and B plus incremental
run C, validate each initial run before queueing the next stage. A failed B must
not queue C. Record every superseded run and monitoring series in the frozen
acceptance session. Even when C is missing, the validator must write a machine
`FAIL` report with the available run IDs and control matrix instead of exiting
before evidence is persisted.

If the five-cycle limit proves that the approved DoD is measuring external
provider variance rather than a local pipeline defect, stop and request an
explicit design decision. A subsequently approved acceptance revision must
archive the original manifest, freeze and machine `FAIL`; create a new
versioned amendment and hash; keep controls, URLs, dates and semantic integrity
rules unchanged unless the design decision explicitly says otherwise; and add
the unresolved provider-stability work to the tracker. Never overwrite the
original failed evidence or describe it as a pass under the revised policy.

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
