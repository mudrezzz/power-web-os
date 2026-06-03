# AGENTS.md

## Project identity

Project name: **Power Web OS**.

Repository name: `power-web-os`.

Product source requirements:

- `power_web_os_concept.md`
- `Power Web OS — концепция продукта.pdf`

Required AI-agent framework:

- `mudrezzz/langgraph-document-ai-platform`
- local research checkout may exist at `.external/langgraph-document-ai-platform`
- `.external/` must not be committed

Current technical direction:

- Python 3.12+.
- Domain package in `src/power_web_os`.
- Deterministic Access Planner first, then LangGraph workflow wrapper.
- Keep Power Web OS as system of strategy above CRM, not CRM replacement.

## Project operating model

This project is developed iteratively.

Work is organized as:

1. Iterations
2. Slices
3. Small, reviewable increments

A slice is the smallest meaningful unit of product progress. Each slice must leave the project in a working, demonstrable, documented, and tested state.

Do not work in a waterfall style where one large module is fully built before the rest of the product becomes usable. Prefer concentric product growth: first create a limited but complete working product perimeter, then expand it in controlled circles.

## Source of truth

The project backlog is maintained in `ROADMAP.md`.

Always keep `ROADMAP.md` current:

- Add new tasks there.
- Take work from there.
- Update task status during and after work.
- Record completed slices.
- Record blocked items and assumptions.
- Keep the next actionable task easy to identify.

Before starting implementation, inspect `ROADMAP.md`.

If the user asks to “take the next task”, “continue the project”, “work on the next slice”, or gives a vague continuation request, use `$project-onboarding` first.

## Product requirements source

The project must be driven by the user's source requirements document.

When starting architecture, bootstrapping, or planning work:

1. Ask the user to identify the source requirements file if it is not known.
2. If the user did not specify a file, search the repository root for likely requirements documents, including:
   - `SPEC.md`
   - `SPECIFICATION.md`
   - `REQUIREMENTS.md`
   - `PRD.md`
   - `TASK.md`
   - `TZ.md`
   - `ТЗ.md`
   - files containing "requirements", "spec", "prd", "task", "тз", or "задание" in the name.
3. If several candidates exist, inspect them and choose the most likely primary requirements source. State the choice and uncertainty.
4. Do not invent requirements when the source document is missing or ambiguous. Record assumptions explicitly in `ROADMAP.md` or the relevant architecture document.

## Documentation standards

Keep documentation current together with code.

The repository should maintain:

- `README.md` as the main entry point.
- `ROADMAP.md` as the backlog and delivery tracker.
- `docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md`.
- ADRs in `docs/adr/`.
- Contributor documentation in `docs/contributor/CONTRIBUTING.md`.
- Developer documentation in `docs/developer/DEVELOPER_GUIDE.md`.
- User documentation in `docs/user/USER_GUIDE.md`.
- Demo documentation in `demo/README.md`.

Documentation must be suitable for publishing on GitHub.

When behavior, architecture, setup, commands, public APIs, or user-facing flows change, update the relevant documentation in the same slice.

Use `$docs-sync` when a task changes architecture, setup, public behavior, demo behavior, or user-facing functionality.

## Architecture principles

Use object-oriented design where appropriate.

Follow these principles:

- Single Responsibility Principle: one component should own one clear role.
- Keep domain logic separated from infrastructure, UI, persistence, transport, and integration code.
- Prefer explicit boundaries between modules.
- Prefer small cohesive classes, services, functions, and modules.
- Avoid god objects, hidden coupling, and cross-layer shortcuts.
- Avoid premature abstractions, but extract abstractions when repetition or role confusion appears.
- Keep public interfaces intentional and documented.

Use `$architecture-design` for new architectural decisions, major feature design, or module boundary changes.

## Testing standards

Maximize useful test coverage.

Expected test layers:

- Unit tests for isolated logic.
- Integration tests for component collaboration.
- Smoke tests for critical startup and happy-path behavior.
- End-to-end tests for important user-facing flows when applicable.

Every slice must include or update tests for the behavior it introduces or changes.

After each slice:

1. Run targeted tests relevant to the changed area.
2. Run smoke tests if the project has them.
3. Run broader regression tests when there is meaningful risk to existing behavior.
4. Report which tests were run and which were not run.

Use `$regression-and-test-strategy` when choosing the right validation scope or when a change may affect existing functionality.

## Demo standards

Maintain a realistic demo example.

The demo must:

- Evolve with the project.
- Show available working functionality clearly.
- Be realistic, live, and market-relevant.
- Allow a user to see, touch, and understand the product value.
- Cover the most important supported flows.
- Avoid toy examples when a realistic example is possible.

Use `$demo-maintenance` when adding or changing user-visible functionality.

## Code and test comments

Comment code and tests where comments increase maintainability.

Comments should explain:

- non-obvious intent
- domain rules
- trade-offs
- assumptions
- edge cases
- test purpose

Do not add comments that merely restate obvious code.

## Git and GitHub

The project should be connected to Git.

When bootstrapping a new project:

- Initialize a Git repository if one does not exist.
- Create a useful initial commit.
- Propose a concise, marketable project name.
- Create a GitHub repository under the account `mudrezzz` when GitHub CLI authentication is available.
- Prefer a repository name that is lowercase, hyphenated, and easy to remember.
- Do not overwrite existing remotes without asking.
- Do not publish secrets, local environment files, or generated private artifacts.

Use `$project-bootstrap` for initial repository creation, structure setup, README creation, Git initialization, and GitHub setup.

## Workflow expectations

Before making changes:

1. Inspect `ROADMAP.md`.
2. Inspect relevant documentation.
3. Inspect the source requirements file if the task depends on product requirements.
4. Identify the current iteration and slice.
5. Propose or infer the smallest useful next increment.

During changes:

- Keep the slice small.
- Keep the product runnable.
- Keep docs and tests synchronized.
- Prefer minimal, localized changes.
- Preserve existing behavior unless the task explicitly changes it.

Before finishing:

1. Update `ROADMAP.md`.
2. Update relevant docs.
3. Add or update tests.
4. Run the relevant validation commands.
5. Summarize:
   - what changed
   - which slice was completed or advanced
   - which tests were run
   - which docs were updated
   - remaining risks or next tasks

## Skills routing

Use these skills when available:

- `$architecture-design` for architecture design based on user input and root project files.
- `$project-bootstrap` for initial project creation, repository structure, Git, GitHub, README, and baseline docs.
- `$project-onboarding` when entering an existing project, starting a new chat, or continuing from `ROADMAP.md`.
- `$roadmap-slice-planning` for turning requirements into iterations, slices, and actionable backlog items.
- `$slice-implementation` for implementing the next small product increment.
- `$docs-sync` for keeping README, architecture docs, ADRs, contributor docs, developer docs, user docs, and demo docs current.
- `$regression-and-test-strategy` for deciding and running the correct test scope.
- `$demo-maintenance` for creating or updating the realistic demo example.

Do not duplicate full skill workflows here. The `SKILL.md` files are the source of truth for task-specific procedures.
