---
name: radar-run-self-test
description: Start a Power Web OS Radar run independently, poll it to a terminal state, then diagnose it using the Radar run diagnostics workflow. Use when the user asks Codex to run the Radar itself, perform an end-to-end manual smoke, "самостоятельный прогон", "запусти и проверь", or run then diagnose without making the user be the tester.
---

# Radar Run Self-Test Skill

## Goal

Run a bounded Radar smoke test end to end, wait for completion or timeout, and
then perform the same critical diagnosis as `radar-run-diagnostics`.

## Preconditions

Before starting a full run:

1. Read `ROADMAP.md` and identify whether the current next slice recommends
   avoiding long live runs.
2. Run `git status --short --branch`.
3. Run static/offline preflight when possible:

   ```powershell
   python -m power_web_os.demo preflight-radar --radar-id toir-quick-live --json --show-runtime-config
   ```

4. If preflight reports blocking errors, do not start a long run unless the user
   explicitly asked to run despite the failure. Report the blocking checks.
5. Never print `.env` or secrets. Only report secret presence/missing from
   redacted runtime config.
6. For local OpenRouter live probes and runs, treat repository `.env` as the
   credential source of truth. Do not rely on an inherited
   `OPENROUTER_API_KEY` process variable; the runtime loader should read
   `.env` and let it override stale process credentials.

## Preferred Run Path

Use the remote API/worker path because it matches the UI. Read API and frontend
URLs from `deploy/remote-dev.env`; never use a loopback URL for Codex runtime
validation.

Before any API-backed Radar self-test, deploy the current workspace:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/remote_dev.ps1 -Action Deploy -SessionId <id>
```

If remote SSH/Docker is unavailable, report a blocker. Do not use local Docker
or a stale release.

1. Verify API health:

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/remote_dev.ps1 -Action Exec -SessionId <id> -Runner stack -Command "curl -fsS `$POWER_WEB_OS_REMOTE_API_URL/health"
   ```

2. Verify Radar catalog:

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/remote_dev.ps1 -Action Exec -SessionId <id> -Runner stack -Command "curl -fsS `$POWER_WEB_OS_REMOTE_API_URL/api/radars"
   ```

3. Queue a run:

   ```powershell
   $body = @{
     live = $true
     requester = "codex-self-test"
     task_context = @{ source = "codex_self_test" }
   } | ConvertTo-Json -Depth 5
   powershell -ExecutionPolicy Bypass -File scripts/remote_dev.ps1 -Action Exec -SessionId <id> -Runner stack -AllowProviderCalls -Command "<announced bounded API run command>"
   ```

4. Poll `GET /api/radar-runs/{run_id}` every 10-15 seconds.
5. Stop polling after 5 minutes by default unless the user explicitly requested
   a longer run. Do not wait 30 minutes silently.
6. If the run is still queued/running after timeout, report current status,
   worker/runtime config if available, and useful log commands instead of
   pretending the run completed.

Never substitute another host or local process when the configured remote API
is unavailable. Repair/deploy the remote contour or stop as blocked.

## After Terminal State

For a behavior-changing Radar slice, preserve the run ID and product-safe report
as acceptance evidence. Compare it requirement-by-requirement with the slice
acceptance manifest. A terminal run is not enough: missing required evidence
keeps the slice In Progress.

For architecture migrations that claim no behavior change, run the full
regression proof named by the slice, not a cheaper smoke substitute. When
`0.7.6.4.19` or an equivalent closure slice is active, this means:

1. a fresh blind candidate-discovery benchmark and post-run evaluation;
2. semantic trace comparison with the accepted candidate baseline;
3. a fresh initial signal quality run;
4. a fresh incremental signal run;
5. comparison with both accepted signal baselines;
6. API/worker restart and persisted-report round trip;
7. machine validation PASS.

Do not mark the slice complete when only tests, recorded fixtures, or one
terminal live run are available.

Run the `radar-run-diagnostics` workflow on the resulting run id:

- completed runs still require critical algorithm review;
- failed runs require error metadata and technical trace review;
- review-needed/stopped runs require checkpoint/adaptive-action analysis.

The final answer must include:

- run id;
- whether the run reached terminal state within the timeout;
- status and duration;
- candidate/source counts only as supporting facts;
- a plain-language explanation of every major count surface that can look
  inconsistent, especially `candidate_universe`, public `candidates`,
  benchmark matches, review matches, and `product_candidate_count`;
- root cause verdict;
- whether the result supports continuing the roadmap or requires a corrective
  implementation slice.

## Guardrails

- Prefer short bounded test settings for self-test unless the user requests a
  full quality benchmark.
- Do not start multiple concurrent runs automatically.
- Do not retry failed POST/run creation automatically if the first request may
  have queued a run; inspect run state first.
- Do not treat a long live run as the first validation step. Use preflight,
  targeted probes, and recorded tests before full runs.
- If OpenRouter returns `401` or `User not found`, first verify the effective
  runtime is using `.env`, not a stale inherited process variable.
- Never leak OpenRouter, DaData, Redis, database, or bearer credentials.
