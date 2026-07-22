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

The project backlog is maintained through the local roadmap tracker. `ROADMAP.md`
is the generated human-readable report.

Always keep `ROADMAP.md` current:

- Add new tasks through the roadmap tracker when it is available.
- Take work from the tracker or generated `ROADMAP.md` report.
- Update task status through the tracker during and after work.
- Record completed slices.
- Record blocked items and assumptions.
- Keep the next actionable task easy to identify.

Tracker commands:

```bash
python -m power_web_os.roadmap list --status Ready
python -m power_web_os.roadmap show <slice-id>
python -m power_web_os.roadmap update-status <slice-id> Done --note "validated"
python -m power_web_os.roadmap export
python -m power_web_os.roadmap render --output ROADMAP.md
python -m power_web_os.roadmap check
```

Before starting implementation, inspect the tracker when available; otherwise
inspect `ROADMAP.md`.

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

## Frontend design system

All frontend work must use the local Power Web OS design system in `ui-design-system/`.

Before creating, changing, or reviewing frontend UI:

1. Read `ui-design-system/START-HERE.md`.
2. Use `ui-design-system/colors_and_type.css` as the source of truth for CSS tokens.
3. Use `ui-design-system/components-spec.md` for component API, states, sizing, hover, press, and focus behavior.
4. Use `ui-design-system/app-prototype/` as the behavioral, information-architecture, shell, and layout reference.
5. Use `ui-design-system/preview/` as the visual reference.

For app-level frontend work, start from the product shell:

- Read `ui-design-system/app-prototype/README.md`.
- Read `ui-design-system/app-prototype/AppShell.jsx` before creating or changing product screens.
- Read the relevant screen prototype before implementing the screen:
  - `AccountsScreen.jsx` for account portfolio work.
  - `MapScreen.jsx` and `AccountMap.jsx` for account map / Power Web work.
  - `PlansScreen.jsx` for Access Plan work.
  - `ExtraScreens.jsx` for Playbook and Signals work.
- If the production frontend does not yet have a durable app shell, create or extend it before adding a new full-screen product feature.
- Do not create standalone full-screen demo pages for product features when the shell exists or is intended by the prototype. Put the feature inside the Power Web OS workspace shell.
- Menu items for future functionality may be visible as planned/placeholder states, but must not pretend unavailable functionality is implemented.
- Treat the app as a bounded SPA workspace, not a landing page. Keep sidebar profile/navigation visible inside the viewport and put scrolling inside workspace panes.
- Validate visible shell or screen changes at small desktop viewports such as 1280x720 and 1366x768.
- Prevent text from overlapping adjacent UI; use `min-width: 0`, wrapping, ellipsis, or owned scroll containers for dense tables and cards.
- Route new visible UI strings through the frontend i18n resources and keep English/Russian UI resources synchronized.
- Visible deterministic demo data should be localized in the presentation layer when the UI language changes. Raw IDs, source refs, company names, and person names may remain as artifact data unless a slice says otherwise.

Strict rules:

- Do not hardcode hex colors, radii, shadows, spacing, or typography when a design-system token exists.
- Use `var(--*)` tokens from `colors_and_type.css`.
- Cobalt is rationed: active route, one primary button per screen, active nav, links, and focus ring.
- Stance colors are semantic only: ally, blocker, unsurfaced, neutral.
- Use sentence case for UI text. Use uppercase only for mono eyebrow labels.
- Scores, confidence, IDs, domains, and counters use mono typography and must have nearby rationale.
- Do not use emoji or exclamation marks in UI copy.
- Use Lucide icons in production instead of copied inline SVG paths from the prototype.
- Respect `prefers-reduced-motion`.
- Verify frontend changes against the checklist in `ui-design-system/START-HERE.md`.

Use `$frontend-design-system` for any frontend implementation, UI review, component creation, styling, layout, responsive behavior, visual QA, or frontend copy task.

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

For every Radar slice whose tracker metadata contains `Pipeline` and
`Behavior change: true`, completion additionally requires the evidence loop:
current AS IS and persisted-run RCA, reviewed TO BE Markdown/PDF, an adjacent
acceptance manifest with mandatory requirement IDs and test node IDs, persisted
runtime evidence, a machine-generated PASS validation report, and a finalized
AS IS change record. The roadmap CLI must reject `Done` while this evidence is
missing or failed. Autofix may make at most five local corrective passes and
must not weaken the approved TO BE or DoD.

## Execution transparency

The desktop client may collapse tool activity into generic messages such as
"Background terminal completed". Do not rely on those cards as the user's only
record of what happened. Maintain a concise, user-facing execution audit in the
chat through commentary updates and the final response.

Before substantial work:

- State the exact skills selected for the task and briefly explain why each one
  applies. If no skill is needed, say so.
- Announce any skill selected later in the task before reading or applying its
  workflow.
- State whether the task is expected to invoke external providers, consume paid
  tokens, start product runs, rebuild Docker, or create background processes.

Before each terminal or external-tool batch:

- Show the exact command or commands that will run, together with their purpose.
- For a very long generated command, show the executable, arguments, affected
  paths, and purpose; do not dump a large generated payload into chat.
- Announce file edits with the affected paths and intended change before editing.
- Announce web searches, provider calls, MCP/app actions, image generation,
  Docker operations, Radar/Signal/Power Web runs, and Git writes before calling
  them.
- Never display secrets, credentials, authorization headers, private provider
  payloads, or raw environment-variable values. Replace sensitive values with
  explicit placeholders such as `<redacted>`.

For background or long-running work:

- Identify the command, why it is running in the background, and the process or
  session identifier when available.
- Clearly distinguish polling or waiting on an existing process from starting a
  new process.
- Do not start a duplicate provider, benchmark, Docker, migration, or test run
  merely because the UI rendered another background-terminal card.
- Report completion, failure, cancellation, or timeout. Do not leave a process
  required by the user's request running when sending the final response.

Before finishing, include an execution summary containing:

- Skills actually used, including implicitly selected skills.
- Commands and external tools actually executed. Repeated identical polls may be
  grouped with a count.
- Tests and checks with their outcome; identify required checks that were not run.
- Provider-backed/product runs, their IDs when applicable, and whether paid token
  usage occurred.
- Any background processes still running. State `none` when there are none.

Keep the audit readable: explain intent in normal language, group repetitive
read-only inspection commands, and retain exactness for state-changing,
provider-backed, validation, Docker, and Git commands.

## Mandatory remote execution contour

Codex must execute Power Web OS tests and runtime validation on the configured
remote development server through `scripts/remote_dev.ps1`.

- Local work is limited to editing, Git and roadmap mutations, static source
  inspection, diff inspection, and invoking the remote orchestrator.
- Do not run local Docker Compose, pytest, npm builds, Playwright, migrations,
  demo seed, or Radar/Signal/Power Web product runs.
- Read `deploy/remote-dev.env`; do not infer host, paths, URLs, or ports.
- Use `$remote-dev-validation` for Probe, Sync, remote tests, artifact
  collection, and cleanup. Use `$deploy-remote-dev` for the persistent dev
  release.
- A remote failure blocks validation. Never silently fall back to local
  execution.
- State the remote session ID and contour before each validation batch.
- Provider-backed commands require an explicit user-visible live-action notice,
  `-Runner stack`, and `-AllowProviderCalls`.
- Collect the remote session manifest and required allowlisted validation
  artifacts before roadmap closeout.

Local Docker compatibility remains available to a human developer only; it is
not a Codex execution path.

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
- `$frontend-design-system` for all frontend UI work, including screens, components, CSS, layout, visual QA, frontend copy, responsive behavior, and design reviews. This skill is mandatory whenever frontend app files are created or changed.
- `$deploy-remote-dev` for uploading or rebuilding the configured remote Docker dev stack without exposing `.env` secrets.
- `$remote-dev-validation` for all remote Probe, Sync, test, build, Playwright, execution, evidence collection, and validation-session cleanup work.
- `$radar-run-diagnostics` when the user provides a Radar run id and asks what happened, why results look wrong, whether the behavior matches the roadmap, or what corrective slice should come next.
- `$radar-run-self-test` when the user asks Codex to start a Radar run itself, poll it to completion or timeout, and then diagnose the result without making the user act as the tester.
- `$radar-run-autofix` when the user asks Codex to run Radar, diagnose the result, compare it with `ROADMAP.md`, and automatically patch non-architectural defects in a bounded correction loop before rerunning.
- `$radar-pipeline-to-be-design` before substantial Radar search pipeline changes that affect planner, retrieval, extraction, source routing, registry lookup, candidate universe, checkpoints, budgets, signal search, dossier projection, or evaluation.
- `$radar-pipeline-as-is-sync` after implemented Radar pipeline behavior changes and `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md` plus the generated PDF must be synchronized.
- `$radar-pipeline-to-as-is-finalize` after a TO BE Radar pipeline slice is implemented and the reviewed design must be reconciled with actual AS IS behavior.

Do not duplicate full skill workflows here. The `SKILL.md` files are the source of truth for task-specific procedures.
