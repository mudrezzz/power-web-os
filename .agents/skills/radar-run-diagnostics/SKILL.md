---
name: radar-run-diagnostics
description: Diagnose a completed, failed, queued, or running Power Web OS Radar run from a provided run id. Use when the user gives a `radar-run-...` id and asks what happened, why results look wrong, whether the algorithm behaved according to the current ROADMAP, or what development correction should come next.
---

# Radar Run Diagnostics Skill

## Goal

Produce a critical run diagnosis anchored in persisted evidence, not generic
commentary. The output must explain what the Radar actually did, compare it to
the current roadmap/architecture expectations, and end with a verdict and next
engineering recommendation.

## Required Inputs

- A concrete `run_id`, normally shaped like `radar-run-...`.
- Repository workspace with the local database or API available.

If the run id is missing, ask for it. Do not invent one from recent context.

## Evidence Order

1. Read `ROADMAP.md` first and identify the current Radar slice status and next
   planned fixes.
2. Check `git status --short --branch` so the report can mention whether local
   code is dirty.
3. Find the database:
   - Prefer `POWER_WEB_OS_DATABASE_URL` from the environment when present.
   - Otherwise use `demo/output/power_web_os.sqlite3`.
4. Read persisted run state for the run id:
   - `radar_runs`: status, radar id, timestamps, requester, correlation id,
     idempotency key, run metadata, API/worker runtime config snapshots.
   - `radar_run_outputs`: artifact payload, candidates, sources, output
     metadata, execution results.
   - `radar_run_events`: journal events in sequence order.
   - `radar_run_technical_traces`: sanitized trace rows in sequence order.
   - `radar_review_decisions` when review overlays matter.
5. If the API is running, optionally compare persisted evidence with:
   - `GET /api/radar-runs/{run_id}`;
   - `GET /api/radar-runs/{run_id}/dossier`;
   - `GET /api/radar-runs/{run_id}/technical-trace`.

Use `inspect_radar_runs.py` only as a quick inventory. For RCA, query the
specific run and relevant JSON fields directly.

## What To Inspect

Focus on algorithm behavior, not only candidate counts:

- runtime config: API vs worker fingerprint, model routing, retrieval provider,
  web mode, DaData mode, budgets, verification mode;
- active definition: definition id/version, source policies, source obligations,
  qualification criteria, intent signals;
- plan and retrieval: discovery plan, retrieval plan, task cards, source scopes,
  source obligations, selected/skipped source bases;
- execution health: checkpoint decisions, adaptive actions, retry/revision caps,
  stopped-for-review reason, budget exhaustion;
- source lifecycle: retrieved, verified, extracted, linked, used,
  analyzed-only, skipped, risky, blocked, unavailable;
- extraction and evidence: schema validation, repair attempts, source-ref
  reconciliation, unresolved evidence refs, candidate universe gaps;
- entity resolution: legal entity vs production site/project/asset, linked facts,
  rejected account candidates;
- scoring semantics: distinguish `not_observed` from `not_searched_*`,
  review-needed, weak/risky evidence, zero scores;
- trace quality: whether technical trace explains prompts, provider calls,
  parsed outputs, validation and redaction without leaking secrets.

When counts appear contradictory, explain the surfaces separately instead of
collapsing them into one "candidate count":

- benchmark matches: baseline entities recognized anywhere in dossier/evidence;
- candidate universe: broad upstream raw/review entities retained for recall;
- public candidates: capped/scored candidate rows shown to users;
- product candidates: strict downstream accepted accounts;
- signal rows: signal-monitoring or compatibility signal states.

If a run found many upstream/review entities but public candidates are still
`Monitor` or `product_candidate_count=0`, treat that as a semantic/product
surface mismatch that needs roadmap or implementation action.

## RCA Format

Answer in Russian unless the user asks otherwise. Keep the report readable:

1. **Verdict**: one paragraph with the main diagnosis.
2. **Observed facts**: run status, candidate/source counts, runtime config,
   key timestamps, and whether API/worker config matched.
3. **Pipeline timeline**: what stages executed and where it stopped or degraded.
4. **Root causes**: ordered by impact, each tied to persisted evidence.
5. **Roadmap match**: whether the behavior is already expected/covered by
   current slices or indicates a gap.
6. **Retrospective**: if behavior contradicts a completed slice, name the
   completed slice, the failed assumption, and the missing process guardrail
   such as a test, linter, skill instruction, ADR, documentation rule, or
   acceptance gate.
7. **Recommended next action**:
   - continue according to roadmap;
   - adjust current implementation;
   - add a new corrective slice;
   - run a shorter targeted probe before another full live run.

Avoid dumping large JSON. Quote only compact field names, counts, status values,
and short snippets needed to support the conclusion.

For a pipeline slice with an acceptance manifest, map every material finding to
its requirement ID. Distinguish a code defect from a failed planning/testing
assumption, and propose changes to tests, skills, ADRs or tracker gates when the
same process could allow the defect again.

## Safety

- Never print `.env`, API keys, tokens, bearer strings, authorization headers,
  full provider headers, or raw hidden chain-of-thought.
- Treat trace payloads as sanitized but still inspect for accidental leakage.
- If evidence is missing or stale, say exactly which table/API payload was
  unavailable.
