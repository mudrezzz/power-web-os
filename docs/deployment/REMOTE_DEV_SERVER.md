# Remote Dev Server

This document records the supported remote development contour for Power Web OS.
It is a dev environment for manual checks and shared demonstrations, not a
production deployment.

## Server

Remote configuration lives in `deploy/remote-dev.env`.

Current defaults:

```text
Host: 213.148.13.45
SSH target: flowise
Remote path: /opt/power-web-os
Frontend: http://213.148.13.45:5173
API: http://213.148.13.45:8001
Redis host bind: 127.0.0.1:6380
```

Use the config file when changing the host, path, ports, or SSH alias. Do not
hardcode those values into ad hoc commands.

## Stack

The remote server runs the same Docker Compose dev stack as local development:

- `redis`;
- `backend-init`;
- `api`;
- `worker`;
- `frontend`.

The stack uses SQLite in `demo/output/power_web_os.sqlite3`. The local `.env`
file is copied to the server separately from the source archive and is kept out
of Git and the Docker build context.

Redis is development infrastructure for Celery only. It should not be exposed
publicly; keep the host bind on `127.0.0.1`.

## Deploy

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy_remote_dev.ps1
```

Dry-run without copying files or mutating the server:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy_remote_dev.ps1 -DryRun
```

The script:

1. reads `deploy/remote-dev.env`;
2. verifies local `.env` exists without printing it;
3. archives the repository while excluding Git metadata, local vendor checkouts,
   virtual environments, `node_modules`, build outputs, caches, and local DB
   artifacts;
4. copies the archive and `.env` through `scp`;
5. extracts to `/opt/power-web-os`;
6. applies server overrides to the remote `.env`;
7. runs `docker compose config --quiet`;
8. runs `docker compose up --build -d`;
9. checks API health, Radar catalog, and frontend HTTP response.

## Manual Checks

```powershell
curl http://213.148.13.45:8001/health
curl http://213.148.13.45:8001/api/radars
```

Open:

```text
http://213.148.13.45:5173
```

Remote service status:

```bash
ssh flowise "cd /opt/power-web-os && docker compose ps"
```

Useful logs:

```bash
ssh flowise "cd /opt/power-web-os && docker compose logs --tail=100 api"
ssh flowise "cd /opt/power-web-os && docker compose logs --tail=100 worker"
ssh flowise "cd /opt/power-web-os && docker compose logs --tail=100 frontend"
```

## Environment Safety

- Never commit `.env`.
- Never paste `.env` or API keys into issue comments, logs, or docs.
- The deploy script copies `.env` separately and sets remote permissions to
  `600`.
- Server-specific non-secret overrides are applied after the copy:
  API host port, frontend API URL, CORS origins, and Redis host bind.

## Manual Recovery

If the scripted deploy fails after files are copied, connect to the configured
SSH target and inspect Compose state:

```bash
ssh flowise
cd /opt/power-web-os
docker compose config --quiet
docker compose ps
docker compose logs --tail=200 api
docker compose logs --tail=200 worker
```

Restart the stack:

```bash
docker compose up --build -d
```
