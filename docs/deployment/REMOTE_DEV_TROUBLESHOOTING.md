# Remote Development Troubleshooting

## Probe Fails

Run `remote_dev.ps1 -Action Probe` and use its first failed check. Do not switch
to local execution. Verify the SSH alias, remote Docker service, free disk/RAM,
configured roots, and presence (not contents) of the server-owned `.env`.

## Remote Stack Busy

`remote_stack_busy` means another deploy/restart/control action owns the lock.
Wait for that action to finish. Do not kill it or start an unlocked Compose
command.

## Build Or Test Fails

The local exit code mirrors the remote command. Inspect the bounded output and
session manifest, fix the workspace, sync the same session, and rerun only the
failed layer. Do not recreate successful product runs.

## Deploy Fails

The previous release remains available. Inspect bounded `api`, `worker`, or
`frontend` logs through `-Action Logs`; do not read `.env`. If activation failed,
verify `current`, release directory, shared data, and Compose project separately.

## Cleanup Refused

Cleanup accepts only a safe session ID and a path under the configured
validation root. It deliberately refuses shared/current/releases and another
session. Correct the session ID instead of deleting manually.

## Artifact Collection Refused

Move or generate evidence under an allowlisted validation/test-results path.
Private logs, databases, secret files, and arbitrary absolute paths are never
collectable.
