---
name: deploy-remote-dev
description: Deploy or update the Power Web OS remote dev server. Use when the user asks to "залить на сервер", "обновить сервер", "deploy remote dev", "пересобрать remote stack", or otherwise publish the current workspace to the configured remote Docker dev contour.
---

# Remote Dev Deployment Skill

## Goal

Deploy the current Power Web OS workspace to the configured remote dev server
without leaking secrets or reconstructing deployment commands from chat history.

## Required Inputs

Always read `deploy/remote-dev.env` first. Treat it as the source of truth for:

- SSH target;
- remote project path;
- public frontend/API URLs;
- host ports and Redis bind address.

Do not infer the host, path, or ports from memory when the config file exists.

## Safety Rules

- Never print local `.env`, remote `.env`, API keys, tokens, bearer strings, or
  provider credentials.
- Before deploying, run `git status --short --branch`.
- If the worktree is dirty, report the changed-file scope before deployment.
  Do not commit automatically unless the user explicitly asks for a commit.
- Use `scripts/deploy_remote_dev.ps1`; do not hand-roll a new SSH/scp command
  sequence unless the script is broken and you are fixing it.
- Use `-DryRun` when validating the deployment plan or when the user asks what
  would happen.
- Redis must stay bound to the configured private host bind, normally
  `127.0.0.1:6380`.

## Workflow

1. Read `deploy/remote-dev.env`.
2. Check `git status --short --branch`.
3. Confirm local `.env` exists without printing it.
4. Run:

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/deploy_remote_dev.ps1
   ```

5. If the user requested a dry run, add `-DryRun`.
6. After a live deploy, report:
   - branch and commit deployed;
   - frontend URL;
   - API health URL and health status;
   - Radar catalog check status;
   - useful remote log commands.

## Troubleshooting

- If SSH fails, verify the configured `POWER_WEB_OS_REMOTE_SSH_TARGET`.
- If `docker compose config --quiet` fails remotely, inspect the remote project
  path and `.env` overrides, but do not print secrets.
- If the frontend loads but stays in demo fallback, verify
  `VITE_POWER_WEB_OS_API_BASE_URL` and API CORS origin overrides.
- If live runs stay queued, inspect worker and Redis logs.
