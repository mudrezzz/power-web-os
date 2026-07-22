---
name: remote-dev-validation
description: Run Power Web OS validation on the configured remote server. Use for tests, frontend builds, Playwright, Docker-backed checks, migrations, seed, validation artifact collection, remote execution diagnostics, or any task that would otherwise run a local project test/runtime command.
---

# Remote Dev Validation

## Mandatory Workflow

1. Read `deploy/remote-dev.env` and choose one safe session ID.
2. Announce the session ID, runner, exact command, and whether provider calls are
   allowed.
3. Probe and sync through `scripts/remote_dev.ps1`.
4. Run commands with `-Action Test` and runner `backend`, `frontend`, or
   `playwright`. The `-Command` value executes inside that remote container.
5. Use `-Action Deploy` only when the persistent UI/API stack is required.
6. Use `-Action Exec -Runner stack` for bounded persistent-stack commands.
7. Collect only allowlisted evidence with `-Action Collect`.
8. Clean only the named validation session with `-Action Cleanup`.

Use `-Action ImportHistory -Runner stack` only for an explicitly requested
migration of the checkpointed local `demo/output/power_web_os.sqlite3` into the
persistent contour. The action must retain a server-side backup, run SQLite
integrity checks, hold the lifecycle lock, and roll back if the API does not
recover. Never replace or upload SQLite with ad hoc `scp` or `Exec` commands.
If integrity fails only in recoverable technical-trace rows, report the exact
unreadable IDs and use `-AllowPartialTraceRecovery` only after making that loss
explicit to the user. Core runs, outputs, foreign keys, and final integrity must
remain complete.

Canonical start:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/remote_dev.ps1 -Action Probe -SessionId <id>
powershell -ExecutionPolicy Bypass -File scripts/remote_dev.ps1 -Action Sync -SessionId <id>
```

## Rules

- Never execute project Docker, pytest, npm build, Playwright, migrations, seed,
  or product runs locally.
- Never silently fall back when SSH or remote Docker fails.
- Offline validation is the default and must use zero provider calls.
- Provider-backed execution requires explicit user-visible notice plus
  `-Runner stack -AllowProviderCalls`.
- Preserve and report `.remote-validation/<id>/manifest.json`.
- Report non-zero remote status and diagnose before retrying.
