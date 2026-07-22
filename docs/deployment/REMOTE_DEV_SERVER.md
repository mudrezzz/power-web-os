# Remote Development Runbook

Power Web OS uses the server configured in `deploy/remote-dev.env` as the
mandatory Codex execution contour. Local execution is limited to editing, Git,
roadmap mutations, static inspection, and invoking `scripts/remote_dev.ps1`.

## Contours

### Isolated validation

- workspace: `/opt/power-web-os/workspaces/<session_id>`;
- Compose project: `pwos-val-<session_id>`;
- no host ports;
- no `.env` or provider credentials;
- temporary containers and volumes are removed by session cleanup;
- Docker, pip, and npm caches remain available.

### Persistent development

- active symlink: `/opt/power-web-os/current`;
- immutable releases: `/opt/power-web-os/releases/<session_id>`;
- shared state: `/opt/power-web-os/shared`;
- Compose project: `power-web-os-dev`;
- frontend: `http://213.148.13.45:5173`;
- API: `http://213.148.13.45:8001`.

The server owns `/opt/power-web-os/shared/.env`. Deployment never uploads the
local `.env`. Existing `/opt/power-web-os/.env` is copied once during bootstrap
when shared secrets do not yet exist, and the source file is retained.

## Canonical Interface

```powershell
powershell -ExecutionPolicy Bypass -File scripts/remote_dev.ps1 `
  -Action <Probe|Sync|Test|Deploy|Exec|ImportHistory|Collect|Logs|Cleanup> `
  -SessionId <id> `
  -Runner <backend|frontend|playwright|stack> `
  -Command <command>
```

Typical offline validation:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/remote_dev.ps1 -Action Probe -SessionId <id>
powershell -ExecutionPolicy Bypass -File scripts/remote_dev.ps1 -Action Sync -SessionId <id>
powershell -ExecutionPolicy Bypass -File scripts/remote_dev.ps1 -Action Test -SessionId <id> -Runner backend -Command "python -m pytest tests/test_backend_architecture_contract.py -q"
powershell -ExecutionPolicy Bypass -File scripts/remote_dev.ps1 -Action Test -SessionId <id> -Runner frontend -Command "npm run build"
powershell -ExecutionPolicy Bypass -File scripts/remote_dev.ps1 -Action Cleanup -SessionId <id>
```

Deploy the persistent stack:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy_remote_dev.ps1 -SessionId <id>
```

## Action Semantics

- `Probe`: checks SSH, Docker, Compose, resources, paths, secrets presence, lock,
  and current stack without starting containers.
- `Sync`: creates a secret-free archive, verifies SHA-256 remotely, and replaces
  only the named validation workspace.
- `Test`: executes the command inside a purpose-built validation container.
- `Deploy`: builds a release, atomically updates `current`, starts the locked dev
  stack, and checks frontend/API HTTP.
- `Exec`: runs a bounded command against the persistent stack under the lock.
- `ImportHistory`: explicitly imports the checkpointed local
  `demo/output/power_web_os.sqlite3`, verifies its SHA-256 and integrity, backs
  up server state, replaces the database under the lifecycle lock, runs the
  normal migration/seed startup, and rolls back if API health does not recover.
- `Collect`: downloads one allowlisted validation artifact.
- `Logs`: returns bounded, sanitized persistent-service logs.
- `Cleanup`: removes only the named validation project/workspace.

## Import Existing Local History

Normal `Sync` and `Deploy` always exclude `demo/output`, so historical runs are
never copied accidentally. After stopping the human-owned local stack and
confirming that SQLite `-wal` and `-shm` sidecars are absent, import history
explicitly:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/remote_dev.ps1 `
  -Action ImportHistory `
  -SessionId <id> `
  -Runner stack `
  [-AllowPartialTraceRecovery]
```

The previous server database remains under
`/opt/power-web-os/shared/backups/`. Do not upload a database with direct `scp`
and do not overwrite the mounted SQLite file while API or worker is running.
The optional recovery flag is fail-closed and limited to unreadable technical
trace rows. It logically rebuilds every table, requires equal core run counts,
zero foreign-key errors and final `integrity_check=ok`, and reports every trace
ID that could not be recovered.

## Provider Guard

Offline validation is the default. A provider-backed API/CLI command requires
both an explicit user-visible live-action notice and:

```text
-Runner stack -AllowProviderCalls
```

Without both, the orchestrator rejects recognized product/provider commands.

## Locking And Concurrency

Validation sessions use different workspaces and Compose project names and may
run concurrently. Deploy, restart, persistent Exec, and lifecycle-changing
Playwright use `/var/lock/power-web-os-dev.lock`. A competing lifecycle action
returns `remote_stack_busy`; it never stops or replaces the active action.

## Evidence

Every session creates `.remote-validation/<session_id>/manifest.json` locally
and `session-manifest.json` remotely. The manifest records branch, commit, dirty
state, workspace SHA, server, Compose project, commands, timestamps, exit codes,
and provider permission. Collect required allowlisted reports before cleanup.

See [security](REMOTE_DEV_SECURITY.md) and
[troubleshooting](REMOTE_DEV_TROUBLESHOOTING.md).

## Human-Only Local Compatibility

The root Compose file remains usable manually by a human developer. Codex must
not use that local path or treat it as fallback evidence.
