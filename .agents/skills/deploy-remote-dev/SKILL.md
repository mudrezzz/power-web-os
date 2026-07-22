---
name: deploy-remote-dev
description: Deploy or update the persistent Power Web OS remote dev stack. Use when the user asks to upload to the server, update the server, deploy remote dev, rebuild the remote stack, or publish the current workspace to the configured remote Docker contour.
---

# Deploy Remote Dev

Read `deploy/remote-dev.env` and run the canonical wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy_remote_dev.ps1 -SessionId <session-id>
```

The wrapper delegates to `scripts/remote_dev.ps1 -Action Deploy`. Do not
reconstruct SSH or Compose commands manually.

## Safety

- Run `git status --short --branch` and report dirty scope before deployment.
- Never print or upload the local `.env`.
- The server-owned secret file is `/opt/power-web-os/shared/.env`; never read,
  download, replace, or include it in logs.
- Deploy through release/shared/current layout and the remote lifecycle lock.
- Do not start provider-backed product runs during deployment.
- A failed deploy is a blocker; do not fall back to local Docker.

Report session ID, release, workspace SHA, public frontend/API URLs, HTTP checks,
rollback outcome when relevant, and any running background process.
