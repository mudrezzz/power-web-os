---
name: docs-sync
description: Use when code, architecture, setup, public behavior, demo behavior, or user-facing functionality changes and documentation must be synchronized. Updates README, architecture overview, ADRs, contributor docs, developer docs, user docs, demo docs, and ROADMAP.md.
---

# Docs Sync Skill

## Goal

Keep documentation accurate, useful, and GitHub-ready.

## Process

1. Inspect changed files.
2. Identify documentation affected by the change.
3. Update the minimum necessary docs.
4. Add ADRs for meaningful architectural decisions.
5. Ensure `README.md` remains the project entry point.
6. Ensure `ROADMAP.md` reflects completed or new work.

## Documentation responsibilities

- `README.md`: product overview, quick start, links to docs.
- `ROADMAP.md`: backlog, iterations, slices, statuses.
- `docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md`: architecture and component responsibilities.
- `docs/adr/`: architectural decisions.
- `docs/contributor/CONTRIBUTING.md`: contribution workflow.
- `docs/developer/DEVELOPER_GUIDE.md`: local development, commands, internals.
- `docs/user/USER_GUIDE.md`: user-facing usage.
- `demo/README.md`: how to run and understand the demo.

## Completion checklist

Before finishing:

- Docs match current behavior.
- Links from `README.md` work.
- New public behavior is documented.
- Setup commands are current.
- Architecture changes are reflected.
- `ROADMAP.md` is consistent with the work done.
