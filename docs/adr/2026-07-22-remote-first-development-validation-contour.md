# ADR: Remote-First Development And Validation Contour

Date: 2026-07-22

Status: Accepted

## Context

The local workstation cannot reliably build and run the complete Power Web OS
Docker/test surface. Previous skills mixed local tests, local Docker and a
single mutable remote deployment path. That made evidence environment-dependent
and allowed accidental local fallback.

## Decision

Codex uses the configured remote server for every project test, build,
Playwright check, migration, seed, Docker lifecycle action and product run.
Validation sessions are isolated and credential-free. The persistent dev stack
uses release/shared/current layout, server-owned secrets and a lifecycle lock.
All actions go through `scripts/remote_dev.ps1` and produce a session manifest.

The root Compose file remains human-only local compatibility. It is not an
accepted Codex validation contour.

## Consequences

- Remote unavailability blocks validation instead of triggering fallback.
- Offline tests cannot consume provider tokens.
- Concurrent validation is isolated; persistent lifecycle mutation is serial.
- Validation is reproducible from workspace SHA and command history.
- SSH root and Docker socket control runner require later hardening.
