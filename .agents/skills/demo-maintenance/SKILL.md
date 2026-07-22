---
name: demo-maintenance
description: Use when creating, updating, or validating the project demo. Ensures the demo is realistic, market-relevant, complete enough to show current functionality, and evolves with each user-visible slice.
---

# Demo Maintenance Skill

Execute demo seed, migration, Docker, test, build, and visual validation only
through the announced remote session and `scripts/remote_dev.ps1`. Never use a
local runtime fallback. Demo seed is an explicit remote stack action and must
not invoke providers.

## Goal

Keep a realistic demo that shows the current working product clearly and convincingly.

## Demo principles

The demo must be:

- realistic
- market-relevant
- runnable
- understandable
- broad enough to show current functionality
- updated as the product grows

Avoid toy scenarios when a real-world scenario is possible.

## Process

1. Inspect current product functionality.
2. Inspect `demo/`.
3. Inspect `ROADMAP.md` for the current slice.
4. Identify whether the slice changes user-visible behavior.
5. Update demo data, scripts, documentation, or flows.
6. Ensure demo instructions are clear.
7. Validate the demo if possible.

## Demo README should include

- What the demo shows
- How to run it
- Expected result
- Main user flows
- Demo data explanation
- Known limitations

## Completion checklist

Before finishing:

- Demo reflects current functionality.
- Demo remains realistic.
- Demo can be run using documented commands.
- `demo/README.md` is current.
- Any demo gaps are recorded in `ROADMAP.md`.
