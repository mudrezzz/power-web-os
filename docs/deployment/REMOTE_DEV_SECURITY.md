# Remote Development Security

## Secrets

- The server owns `/opt/power-web-os/shared/.env` with mode `600`.
- Never print, download, replace, archive, or commit local/remote `.env` files.
- Validation workspaces and images do not receive provider credentials.
- Logs are bounded and redact common authorization/key markers.

## Docker Socket

Ordinary backend, frontend, and Playwright runners do not mount the Docker
socket. Only the lifecycle-control Playwright service mounts it, together with
the active release at the same absolute host path. Its use requires the remote
lifecycle lock.

## Artifact Allowlist

Collection accepts validation JSON/Markdown, generated acceptance PDFs,
frontend test results, screenshots/traces, and session summaries. It rejects
path traversal, `.env`, databases, raw payloads, tokens, and private logs.

## Access

The current contour uses SSH `root` on a dedicated development server. A
non-root deploy identity and tighter Docker authorization remain a hardening
follow-up. This contour is not production deployment infrastructure.
