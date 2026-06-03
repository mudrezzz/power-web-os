---
name: project-bootstrap
description: Use when creating a new project from scratch or initializing an existing folder as a structured repository. Sets up project structure, ROADMAP.md, README, documentation skeleton, demo folder, tests, Git, and optionally GitHub under mudrezzz. Do not use for normal feature implementation after the project is already initialized.
---

# Project Bootstrap Skill

## Goal

Create the initial project structure so development can proceed through documented, tested, iterative slices.

## Process

1. Inspect the current folder.
2. Identify whether this is an empty project, partially initialized project, or existing codebase.
3. Locate the source requirements document:
   - use the user-specified file if available
   - otherwise search the repository root for likely requirements documents
4. Propose a concise project name.
5. Select the smallest appropriate initial technical structure based on requirements.
6. Create baseline project files.
7. Initialize Git if needed.
8. Create a GitHub repository under `mudrezzz` if GitHub CLI is available and authenticated.
9. Create the first commit.

## Required baseline files

Create or update:

- `README.md`
- `ROADMAP.md`
- `AGENTS.md` if missing
- `docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md`
- `docs/adr/README.md`
- `docs/contributor/CONTRIBUTING.md`
- `docs/developer/DEVELOPER_GUIDE.md`
- `docs/user/USER_GUIDE.md`
- `demo/README.md`
- test structure appropriate for the stack

## ROADMAP.md initialization

`ROADMAP.md` must contain:

- Product vision
- Current iteration
- Slice backlog
- Status legend
- Completed slices
- Blocked items
- Open questions
- Next recommended task

Use statuses:

- `Backlog`
- `Ready`
- `In Progress`
- `Blocked`
- `Done`

## GitHub rules

When creating a GitHub repository:

- Use account `mudrezzz`.
- Prefer lowercase hyphenated repository names.
- Do not overwrite an existing remote.
- Do not force-push.
- Do not publish secrets.
- If `gh` is unavailable or unauthenticated, document the exact manual command the user can run.

Example command shape:

```bash
gh repo create mudrezzz/<repo-name> --private --source=. --remote=origin --push
```

Ask before making the repository public.

## Completion checklist

Before finishing:

- Project has a clear entry point in `README.md`.
- `ROADMAP.md` contains the first iteration and first slices.
- Documentation skeleton exists.
- Demo folder exists.
- Test structure exists or is explicitly deferred in `ROADMAP.md`.
- Git is initialized.
- Initial commit is created if possible.
- GitHub setup is completed or manual next steps are documented.
