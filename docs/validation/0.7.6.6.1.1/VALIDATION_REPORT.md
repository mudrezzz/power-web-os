# Remote-first development and validation contour

Slice: `0.7.6.6.1.1`

Validation status: **PASS**

## Contours

- Server: `213.148.13.45` via SSH target `flowise`.
- Validation session: `20260722-remote-first-proof`; Compose project `pwos-val-20260722-remote-first-proof`.
- Parallel proof session: `20260722-remote-parallel-b`.
- Persistent project: `power-web-os-dev`.
- Validated source workspace SHA-256: `ee1bad8cab3f7695992ea13857ed9f05d0edd47600d442f6c1c1afa76f158d36`.
- Documentation/tracker closeout workspace SHA-256: `6e33429abdafcccdf4f71c0ace58288942e7d805cf7e9b52cb5739caa5eed555`.
- Roadmap postcheck session: `20260722-roadmap-postcheck`; workspace SHA-256: `8c287832fe478d1b268321ca12d484d20c36a8011e63d0eee7acfefd938b4630`.
- Active release: `/opt/power-web-os/releases/20260722-remote-first-proof`.
- Frontend: `http://213.148.13.45:5173`; API: `http://213.148.13.45:8001`.

## Results

| Gate | Result |
|---|---|
| Probe | PASS: SSH, Docker 29.1.3, Compose 2.40.3, resources, env presence and lock |
| Backend process contracts | PASS: 9 tests |
| Roadmap/process postcheck | PASS: 14 tests; generated roadmap and JSONL are current |
| Backend architecture/handoff regression | PASS: 82 tests; one dependency deprecation warning |
| Frontend production build | PASS |
| Playwright handoff DoD | PASS: RU 1280x720 and EN 1366x768; 14 roles; run count 2 to 2 |
| Control Playwright runner | PASS: Docker socket and Compose 2.40.3 available under lifecycle lock |
| Failure propagation | PASS: intentional exit 23 returned non-zero |
| Parallel isolation | PASS: two concurrent independent Compose projects |
| Lock contention | PASS: second process received `remote_stack_busy`; remote code 75 |
| Restart persistence | PASS: handoff hash unchanged after API/worker restart |
| Artifact collection | PASS: allowlisted Playwright JSON downloaded |
| Cleanup | PASS: validation resources removed; persistent stack and shared state retained |
| Exec after cleanup | PASS: persistent stack inspected without recreating the deleted workspace |

## Security and cost

- Local Docker, pytest, npm and Playwright invocations: `0`.
- Provider calls: `0`.
- New Candidate Discovery, Signal Monitoring and Power Web Discovery runs: `0`.
- The server-owned `.env` was not printed, downloaded or replaced. Only its presence and protected mode were checked.
- Ordinary Playwright had no Docker socket. Only the locked control runner received it.

## RCA and corrections

The first real remote browser gate found that Product API calls were hardcoded to `127.0.0.1`. Radar API requests worked, but product policy hydration failed inside the remote browser, leaving the Power Web action disabled. Product API now uses the same configured API origin as Radar.

The gate also exposed an async preflight race: a response for an obsolete product selection could overwrite the current response. Empty selections no longer trigger preflight, and a generation guard rejects stale responses.

The Playwright scenario was made tolerant of the valid transition where an existing persisted handoff replaces the action button while the test is about to click it. One transient Docker snapshot export error passed on a bounded retry without cache or state deletion.

Validation artifacts must be collected immediately after their producing test and before another `Sync`, because Sync intentionally recreates the isolated workspace.

Post-cleanup `Exec` retains its local session manifest when the remote validation workspace is already absent, so persistent-stack diagnostics remain usable after cleanup.

## Decision

The remote contour is the mandatory execution environment for Codex. Remote failure blocks validation; there is no local fallback. Product/provider execution remains separately gated by an explicit live action and `-AllowProviderCalls`.

## Persisted history follow-up

The local Radar and Signal Monitoring history was migrated after the initial
remote-first closeout. See
[`HISTORY_MIGRATION_REPORT.md`](HISTORY_MIGRATION_REPORT.md) for source
integrity recovery, backup, API counts, restart proof and focused UI evidence.
