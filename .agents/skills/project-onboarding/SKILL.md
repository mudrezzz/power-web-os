---
name: project-onboarding
description: Use at the start of a new Codex chat or when asked to continue an existing project, take the next task, inspect project status, or resume from ROADMAP.md. Reconstructs context from repository files without requiring the user to re-explain the project.
---

# Project Onboarding Skill

## Goal

Quickly understand the project state and select the next appropriate action from repository context.

## Process

1. Read `AGENTS.md`.
2. Read `ROADMAP.md`.
3. Read `README.md`.
4. Read the source requirements document if identifiable.
5. Inspect:
   - `docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md`
   - latest ADRs
   - developer docs
   - user docs
   - demo docs
6. Inspect the project structure and test structure.
7. Identify the current iteration, active slice, next ready task, blocked tasks, and open questions.

## When asked to "take the next task"

Do not ask the user to repeat project context.

Instead:

1. Determine the next `Ready` task from `ROADMAP.md`.
2. If there is an `In Progress` task, prefer continuing it unless it is blocked.
3. If no task is ready, propose the smallest next slice based on requirements and current architecture.
4. Update `ROADMAP.md` before starting implementation if the selected task needs clarification.

## Required output before implementation

Provide a short project state summary:

- Current product goal
- Current iteration
- Active or next slice
- Relevant files
- Risks or blockers
- Intended validation commands

Then continue with the task unless the task is genuinely blocked.

## Completion checklist

Before finishing onboarding:

- The next task is identified.
- The reason for selecting it is clear.
- Relevant docs and requirements were inspected.
- Any ambiguity is recorded in `ROADMAP.md`.
