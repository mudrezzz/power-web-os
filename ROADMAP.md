# ROADMAP.md

<!--
Generated Roadmap section.
Source database: docs/roadmap/roadmap.sqlite
Review export: docs/roadmap/slices.export.jsonl
Render command: python -m power_web_os.roadmap render --output ROADMAP.md
Manual edits to generated slice sections should be temporary; update the tracker and render again.
-->


## Product Vision

Power Web OS helps B2B sales and ABM teams stop working target accounts blindly. It runs ICP Radars to find and qualify accounts, gathers account signals, builds a dynamic Power Web around accepted accounts, applies the customer's sales playbook, and produces explainable Access Plans with human review before execution.

## Source Requirements

Primary requirements:

- `power_web_os_concept.md`
- `Power Web OS — концепция продукта.pdf`

Reference framework:

- `mudrezzz/langgraph-document-ai-platform`
- local research checkout: `.external/langgraph-document-ai-platform` when present

Design-system source:

- `ui-design-system/START-HERE.md`
- `ui-design-system/colors_and_type.css`
- `ui-design-system/components-spec.md`
- `ui-design-system/app-prototype/`

## Delivery Model

This project is built through concentric product loops, not waterfall layers.

Each slice must leave the product:

- working;
- testable;
- documented;
- demonstrable with synthetic data;
- visible to a user through the current demo surface whenever UI behavior changes.

The demo evolves from one synthetic account to a small portfolio, then to review, feedback, persistence, and first controlled integrations.

## Status Legend

- `Backlog`: known but not ready or not prioritized
- `Ready`: ready to implement
- `In Progress`: currently being worked on
- `Blocked`: cannot proceed without clarification or dependency
- `Done`: completed and validated

## Current Iteration

### Iteration 1: Single-account product loop

Goal:

- Turn the current JSON-only planner baseline into a complete single-account product loop with workflow, artifact, and frontend demo.

Status:

- `Done`

## Slice Backlog

### Slice 0.1: Bootstrap Power Web OS repository

- Status: `Done`
- Goal: Create a product-specific repository baseline.
- User value: The team can continue implementation through documented, tested slices.
- Scope:
  - README, ROADMAP, AGENTS, docs, demo, tests.
  - Minimal Python package.
  - Deterministic Access Planner baseline.
  - Git initialization and first commit.
  - Private GitHub repository under `mudrezzz` if available.
- Out of scope:
  - Production API.
  - Real data connectors.
  - LangGraph workflow implementation.
- Implementation notes:
  - Keep local research checkout `.external/` out of Git.
  - Keep source requirements in the repo.
- Tests:
  - `python -m pytest`
- Docs:
  - README and docs skeleton updated for Power Web OS.
- Demo impact:
  - `python demo/run_demo.py` prints a sample Access Plan.
- Acceptance criteria:
  - Project has clear entry point.
  - Baseline tests pass.
  - Git repository exists with initial commit.
  - GitHub setup completed or manual command documented.
- Risks:
  - Bootstrap can become a template dump; mitigate by making docs product-specific.

### Slice 0.2: First closed Access Planning loop

- Status: `Done`
- Goal: Deliver the smallest complete product loop: synthetic account data -> LangGraph-compatible Access Planning workflow -> explainable Access Plan artifact -> design-system-based frontend demo.
- User value: A user can run one command, open one local demo screen, and see the current product value end to end: why the account matters, who is visible/missing in the Power Web, which routes are recommended, what evidence supports them, and what requires human review.
- Scope:
  - Backend/domain:
    - Add typed workflow state for access planning.
    - Add `AccessPlanningWorkflow` based on the `langgraph-dai` / `BaseWorkflow` pattern.
    - Keep `DeterministicAccessPlanner` as the domain policy engine.
    - Produce a stable JSON artifact with account, signals, roles, missing roles, recommended routes, evidence refs, review flags, and workflow metadata.
  - Synthetic data:
    - Keep one realistic synthetic account fixture as the canonical demo case.
    - Make fixture data rich enough to show signals, Power Web Lite, missing stakeholders, playbook rules, and top routes.
  - Frontend:
    - Add a minimal static demo screen under `demo/` or a small frontend app directory.
    - Use `ui-design-system/colors_and_type.css` and design-system components/styles.
    - Show at minimum: account context, signal evidence, Power Web Lite roles, unresolved gaps, top-3 Access Plan routes, route rationale, risk, owner, and human-review status.
    - No production CRUD, auth, CRM sync, or live connectors.
  - Demo runner:
    - Add a documented command that regenerates the Access Plan artifact from the workflow.
    - Add a documented way to open the local frontend demo against that artifact.
- Out of scope:
  - External source scraping.
  - CRM writes.
  - User accounts/auth.
  - Production API server.
  - Full responsive product shell beyond the one demo screen.
  - Pixel-perfect visual regression.
  - LLM-generated recommendations; LLM usage can come after the deterministic workflow is demonstrable.
- Implementation notes:
  - Treat this as a vertical product slice, not a backend-only task.
  - Prefer a static frontend demo first if that is enough to demonstrate the loop.
  - The workflow should be importable and testable without running a server.
  - The frontend must follow `$frontend-design-system`; consult `ui-design-system/START-HERE.md`, `colors_and_type.css`, `components-spec.md`, and relevant prototype files.
  - If `langgraph-dai` installation is slow or unavailable in a local environment, keep a clear deterministic fallback path for tests, but the workflow layer must still be implemented against the required framework contract.
  - Suggested build order:
    1. Define the Access Planning workflow input/output JSON contract.
    2. Add workflow state and workflow wrapper around the existing planner.
    3. Add a CLI/demo runner that writes `demo/output/access_plan.json`.
    4. Expand the synthetic account fixture only as much as the UI needs.
    5. Build one design-system-based demo screen that reads or embeds the artifact.
    6. Add tests and docs for the complete loop.
- Tests:
  - Unit tests for workflow state validation and output contract.
  - Unit tests that route ranking and evidence refs remain stable.
  - Smoke test for the demo artifact generation command.
  - Frontend smoke check that the demo entry imports `ui-design-system/colors_and_type.css` and renders/contains the required sections.
  - Existing `python -m pytest` remains green.
- Docs:
  - Update README quick start with the new end-to-end demo.
  - Update developer guide with workflow and demo commands.
  - Update user guide with what the demo screen shows.
  - Update architecture overview if workflow/frontend boundaries change.
- Demo impact:
  - Current JSON-only demo becomes a visual local demo.
  - User can inspect the synthetic account and see the current product loop without reading code.
- Acceptance criteria:
  - `python -m pytest` passes.
  - A documented demo command generates the Access Plan artifact.
  - A documented local frontend demo opens and shows the generated/synthetic Access Plan.
  - The project imports and uses `langgraph-dai` in the access-planning workflow layer.
  - The workflow output includes evidence refs, unresolved gaps, route rationale, risks, owners, expected state changes, and human-review flags.
  - The frontend uses the committed design system and does not introduce a separate visual language.
  - The slice is demonstrable without live external services.
- Risks:
  - `langgraph-dai` is installed from GitHub and may slow setup; mitigate with documented optional install and deterministic fallback tests.
  - Static frontend may duplicate some prototype styling; mitigate by importing design tokens and keeping the screen narrow.
  - Without the future validator, design-system compliance is manual in this slice; mitigate by using `$frontend-design-system` checklist.

### Slice 0.2.1: Product app shell for Access Planning demo

- Status: `Done`
- Goal: Move the current Access Planning frontend demo into the durable Power Web OS application shell from the design-system prototype.
- User value: A user opens the demo and sees the product frame that will grow across future slices: workspace navigation, account context, top bar, and the current Access Plans workflow inside that frame.
- Scope:
  - App shell:
    - Add production React TypeScript layout components based on `ui-design-system/app-prototype/AppShell.jsx`.
    - Include sidebar navigation for `Accounts`, `Account Map`, `Access Plans`, `Signals`, `Playbook`, plus queue entries such as `My Tasks` and `Signals Inbox`.
    - Include a top bar with account context, search affordance, and current workspace actions.
    - Keep `Access Plans` as the active working screen for the current slice.
  - Current working screen:
    - Move the existing generated-artifact UI into an `AccessPlansScreen` inside the shell.
    - Use `ui-design-system/app-prototype/PlansScreen.jsx` as the layout and behavior reference.
    - Show objective/account context, top-3 route cards, route rationale, evidence, risk, owner, expected state change, and review status.
  - Future screen placeholders:
    - Add explicit placeholder states for `Accounts`, `Account Map`, `Signals`, and `Playbook`.
    - Placeholders must preserve the shell and explain that the feature is planned without pretending the functionality is complete.
  - Frontend structure:
    - Create or align folders such as `frontend/src/layout/`, `frontend/src/screens/`, and `frontend/src/components/`.
    - Keep design-system token import in `frontend/src/main.tsx`.
- Out of scope:
  - Full Account Map graph implementation.
  - Portfolio ranking.
  - Editable playbook.
  - Live signals feed.
  - Auth, production API, CRM sync, or persistence.
  - Pixel-perfect screenshot regression.
- Implementation notes:
  - This is a corrective slice for Slice 0.2: the product loop is valid, but the frontend must live inside the intended product shell.
  - Use `ui-design-system/app-prototype/README.md`, `AppShell.jsx`, `PlansScreen.jsx`, and relevant primitive references before changing frontend layout.
  - Do not copy Babel-in-browser prototype code directly; reimplement the structure in production React TypeScript with project CSS and design tokens.
  - Use `lucide-react` icons rather than copied inline prototype SVG paths.
  - Keep unavailable navigation entries visible but non-destructive: route to placeholder screens or disabled planned states.
- Tests:
  - Update frontend contract tests to require shell labels: `Accounts`, `Account Map`, `Access Plans`, `Signals`, `Playbook`.
  - Test that `AccessPlansScreen` still loads `/demo/access_plan.json`.
  - Test that unavailable screens render planned placeholder states inside the shell.
  - Existing `python -m pytest` remains green.
  - `npm --prefix ./frontend run build` remains green.
- Docs:
  - Update README/demo instructions only if the user-visible demo entry changes.
  - Update user guide to describe the shell and active `Access Plans` screen.
  - Update developer guide with frontend layout/screen/component structure.
  - Update architecture overview only if a new frontend boundary is introduced.
- Demo impact:
  - The demo no longer looks like a standalone one-off page.
  - The same generated Access Plan artifact is shown inside the durable Power Web OS workspace.
- Acceptance criteria:
  - Opening the Vite demo shows the Power Web OS shell immediately.
  - `Access Plans` is the active useful screen and preserves all Slice 0.2 information.
  - Other nav items are visible but clearly marked as planned/not implemented.
  - Design-system CSS tokens and prototype shell structure are used.
  - Tests and build pass.
- Risks:
  - Reimplementing too much of the prototype can inflate the slice; mitigate by adding the shell and placeholders only.
  - Placeholder screens can look like real functionality; mitigate with clear planned-state copy and no fake actions.

### Slice 0.3: Frontend design-system validator

- Status: `Done`
- Goal: Add an automated validator that catches frontend deviations from `ui-design-system/`.
- User value: Future UI slices stay visually consistent instead of relying only on manual review.
- Scope:
  - Add a script such as `scripts/check_frontend_design_system.py`.
  - Detect hardcoded hex colors in frontend/demo code.
  - Detect direct `box-shadow`, `border-radius`, `font-family`, and common color declarations when `var(--*)` should be used.
  - Detect emoji and exclamation marks in UI strings.
  - Check that frontend/demo entry styles import `ui-design-system/colors_and_type.css`.
  - Add positive and negative fixtures for the validator.
- Out of scope:
  - Full visual regression testing.
  - Pixel-perfect screenshot comparison.
  - Enforcing every component-level design rule.
- Implementation notes:
  - Make the validator path-configurable so it can check `demo/` first and a future `frontend/` later.
  - Keep false positives manageable; allow documented inline ignore comments if needed.
- Tests:
  - Unit tests for allowed and disallowed snippets.
  - Smoke command for checking the current demo.
  - Existing `python -m pytest` remains green.
- Docs:
  - Document validator usage in the developer guide.
  - Mention it in frontend contribution rules.
- Demo impact:
  - Demo can be checked automatically for design-system hygiene.
- Acceptance criteria:
  - Validator fails on representative hardcoded visual values.
  - Validator passes on the current demo.
  - Validator is documented and covered by tests.
- Risks:
  - Regex checks can overreach; mitigate with small fixtures and documented ignore behavior.

### Slice 0.3.1: Playwright visual smoke and documentation screenshots

- Status: `Done`
- Goal: Add reproducible browser screenshot smoke checks for key frontend screens.
- User value: Documentation and UI review can rely on current screenshots generated from the actual local app instead of manual browser inspection.
- Scope:
  - Add Playwright as a frontend dev dependency.
  - Add `npm --prefix ./frontend run visual:smoke`.
  - Start Vite from the script without requiring a separately running dev server.
  - Capture key screens at `1280x720` and `1366x768`.
  - Write screenshots under `docs/qa/screenshots/visual-smoke/`.
  - Add docs explaining when and how to refresh screenshots.
- Out of scope:
  - Pixel-perfect screenshot regression.
  - CI upload/reporting.
  - Mobile screenshot coverage.
  - Full e2e interaction coverage.
- Implementation notes:
  - Treat screenshots as visual smoke and documentation evidence.
  - Keep the script deterministic enough for local regeneration.
  - Reuse generated demo artifacts; do not embed fixture data in the visual smoke script.
- Tests:
  - Contract test for the npm script, Playwright dependency, screenshot paths, and QA docs.
  - `python -m pytest`.
  - `npm --prefix ./frontend run build`.
  - `npm --prefix ./frontend run visual:smoke`.
- Docs:
  - Update README, developer guide, demo docs, and `docs/qa/README.md`.
- Demo impact:
  - Developers can regenerate screenshots for current demo screens directly from the repository.
- Acceptance criteria:
  - Visual smoke produces screenshots for ICP Radar, Accounts, Account Map, Access Plans, and Playbook.
  - Screenshots cover `1280x720` and `1366x768`.
  - The command starts and stops its own local Vite server.
  - The command fails if the page is blank or under-rendered.
- Risks:
  - Browser binaries may be missing on a fresh machine; mitigate by documenting standard Playwright install behavior and using the package-managed Chromium.

### Slice 0.3.2: GitHub Wiki documentation publishing

- Status: `Done`
- Goal: Publish repository documentation and visual smoke screenshots to the GitHub Wiki for `mudrezzz/power-web-os`.
- User value: Product documentation can be read as a GitHub Wiki with current screenshots instead of only as local markdown files.
- Scope:
  - Enable GitHub Wiki for the repository.
  - Add a reproducible wiki publisher script.
  - Build Wiki pages from repository docs:
    - `Home.md`;
    - `_Sidebar.md`;
    - `User-Guide.md`;
    - `Developer-Guide.md`;
    - `Architecture.md`;
    - `Demo.md`;
    - `Roadmap.md`;
    - `QA-Visual-Smoke.md`.
  - Copy visual smoke screenshots into wiki assets.
  - Document dry-run and publish commands.
- Completed so far:
  - Repository visibility was changed from private to public.
  - Wiki was enabled for `mudrezzz/power-web-os`.
  - Added `scripts/publish_github_wiki.py`.
  - Added local dry-run wiki package support.
  - Added docs and contract tests for the wiki publisher.
  - Published generated wiki pages and screenshot assets to `https://github.com/mudrezzz/power-web-os/wiki`.
- Out of scope:
  - GitHub Pages site generation.
  - Automated CI publication.
  - Pixel-perfect docs rendering tests.
- Tests:
  - Contract test for wiki publisher script and docs.
  - `python scripts/publish_github_wiki.py --dry-run`.
  - `python -m pytest`.
- Docs:
  - README, developer guide, and QA docs describe wiki publishing.
- Demo impact:
  - Screenshots generated by visual smoke become reusable documentation assets.
- Acceptance criteria:
  - GitHub Wiki contains the core docs and screenshots.
  - Wiki can be regenerated from local repository files.
  - Publishing command is documented.
- Risks:
  - GitHub Wiki creation has a one-time web UI initialization step; mitigate by documenting it explicitly.

### Slice 0.3.3: Curated GitHub Wiki and screenshot walkthrough

- Status: `Done`
- Goal: Turn the generated GitHub Wiki from a raw documentation/screenshot dump into a curated product walkthrough.
- User value: A reader can understand the current Power Web OS PoC flow directly in Wiki, with screenshots embedded next to the explanation of each screen.
- Scope:
  - Add a curated screenshot walkthrough manifest to the Wiki publisher.
  - Replace filename-based screenshot headings with human product titles.
  - Embed key screenshots into `User Guide`.
  - Keep `QA Visual Smoke` as technical evidence with viewport coverage and regeneration commands.
  - Split Wiki sidebar navigation into product and engineering sections.
- Out of scope:
  - UI changes.
  - New screenshot capture coverage.
  - GitHub Pages or separate documentation site.
- Implementation notes:
  - Keep repository docs as the source of truth.
  - Publish Wiki through `scripts/publish_github_wiki.py`; do not manually edit Wiki content.
  - Screenshot filenames remain stable technical asset names, but they must not drive user-facing headings.
- Tests:
  - Contract tests for curated manifest, screenshot links, sidebar groups, and dry-run output.
  - `python scripts/publish_github_wiki.py --dry-run`.
  - `python -m pytest`.
- Docs:
  - Update `docs/user/USER_GUIDE.md` with screenshot walkthrough sections.
  - Update `docs/qa/README.md` with screenshot asset and manifest rules.
  - Update `docs/developer/DEVELOPER_GUIDE.md` with Wiki publisher maintenance rules.
- Demo impact:
  - Demo behavior does not change.
  - Published Wiki explains the existing demo with screenshots.
- Acceptance criteria:
  - `User Guide` in Wiki contains screenshots in the user walkthrough.
  - `QA Visual Smoke` no longer uses raw filename headings such as `icp-radar-1366x768`.
  - `Home` points readers to the walkthrough.
  - `_Sidebar` separates product and engineering pages.
- Risks:
  - Documentation screenshots may drift if UI changes without rerunning visual smoke; mitigate by keeping visual smoke and manifest updates in future UI slices.

### Slice 0.3.4: Mobile workspace baseline

- Status: `Backlog`
- Goal: Add the first project-wide mobile layout baseline for the Power Web OS shell and core demo screens.
- User value: Sales users can inspect the demo on smartphone-sized screens without broken tables, hidden navigation, or unusable page-level horizontal scroll.
- Scope:
  - Define mobile behavior for the shell, sidebar/navigation, topbar, workspace content, cards, dense tables, and detail views.
  - Add mobile visual smoke coverage, for example `390x844`.
  - Convert dense tables to mobile card or stacked-row layouts instead of relying on horizontal table scroll.
  - Cover at least `ICP Radar`, `Accounts`, `Account Map`, `Access Plans`, and `Playbook`.
  - Update frontend design-system / agent instructions so new UI slices must specify mobile behavior.
- Out of scope:
  - Native mobile app.
  - Offline support.
  - Full gesture/navigation framework.
- Implementation notes:
  - Keep desktop behavior intact.
  - Treat mobile as a first-class shell mode, not as isolated per-screen hacks.
  - Use existing design-system tokens and avoid viewport-scaled typography.
- Tests:
  - `npm --prefix ./frontend run build`.
  - `npm --prefix ./frontend run visual:smoke` with a mobile viewport.
  - Frontend contract tests for mobile rules and screenshot manifest coverage.
  - `python -m pytest`.
- Docs:
  - Update user/developer/QA docs and Wiki screenshots.
- Demo impact:
  - Demo becomes inspectable from a phone-size viewport.
- Acceptance criteria:
  - No body-level horizontal scroll on phone viewport.
  - Primary navigation remains usable.
  - Core screens render readable mobile alternatives.
  - Visual smoke captures mobile screenshots.
- Risks:
  - Mobile work can sprawl across all screens; mitigate by defining a baseline rather than perfecting every workflow.

### Slice 0.4: Account Radar portfolio loop

- Status: `Done`
- Goal: Expand from one account to a small synthetic portfolio with account ranking and one-click drilldown into the existing Access Planning loop.
- User value: A user can see which accounts should be worked first and why, then open the same single-account Access Plan demo for a selected account.
- Scope:
  - Add 5-10 synthetic account fixtures with varied ICP fit, signals, missing roles, and playbook fit.
  - Add an `AccountRadar` domain service that produces account score, timing, signal count, confidence, and top reason.
  - Add a portfolio artifact such as `demo/output/account_radar.json`.
  - Add a frontend portfolio screen using the design system.
  - Link/select an account to show its generated Access Plan.
- Out of scope:
  - Live source connectors.
  - Full search/filter/query language.
  - Multi-user saved views.
- Implementation notes:
  - Keep the portfolio data synthetic and deterministic.
  - Use the same fixture format that the Access Planning loop consumes.
  - Treat account ranking as explainable scoring, not LLM judgement.
- Tests:
  - Unit tests for account scoring and ranking.
  - Smoke test generating portfolio + selected Access Plan artifacts.
  - Frontend smoke check for required portfolio sections.
  - Design-system validator runs on demo UI if Slice 0.3 is complete.
- Docs:
  - Update user guide with the portfolio demo.
  - Update developer guide with fixture structure.
  - Update architecture data flow if new artifact contracts are added.
- Demo impact:
  - Demo starts on Account Radar, then drills into one account's Access Plan.
- Acceptance criteria:
  - A user can compare accounts and understand the top score rationale.
  - Selecting an account shows the already-supported Access Plan loop.
  - All outputs remain deterministic and test-covered.
- Risks:
  - Portfolio scoring can become arbitrary; mitigate by showing only simple factors and evidence.

### Slice 0.4.1: SPA frame and bilingual UI correction

- Status: `Done`
- Goal: Stabilize the current Account Radar frontend as a bounded SPA workspace and add EN/RU UI localization before adding more screens.
- User value: A user on a smaller desktop monitor can keep the profile/navigation frame visible, read the Accounts table without overlapping text, and switch the UI between English and Russian.
- Scope:
  - Fix the app shell so `html`, `body`, `#root`, and `.app-shell` are viewport-bounded and only workspace panes scroll.
  - Keep the sidebar profile card visible at the bottom of the viewport, with navigation scrolling internally if needed.
  - Make Accounts table cells overflow-safe with owned horizontal scrolling, `min-width: 0`, and ellipsis/wrapping policy.
  - Add `i18next` / `react-i18next`, EN/RU resources, a topbar language switcher, and `localStorage` locale persistence.
  - Translate UI chrome, navigation, labels, statuses, placeholders, and planned-state copy; keep generated artifact data as source-language data.
  - Update frontend agent/design-system instructions with SPA frame, small-viewport, overflow, and i18n rules.
- Out of scope:
  - Backend localization.
  - Translated demo artifacts.
  - Production routing, auth, persistence, or API server.
  - Pixel-perfect screenshot regression.
- Implementation notes:
  - Default locale is `en`; supported locales are `en` and `ru`.
  - Use the design-system tokens and app prototype frame behavior as the reference.
  - Longer Russian labels must be handled by layout rules, not viewport-scaled fonts.
- Tests:
  - Frontend contract tests for i18n resources, i18n initialization, language switcher, SPA frame CSS, and Accounts overflow rules.
  - `python -m pytest` remains green.
  - `npm --prefix ./frontend run build` remains green.
- Docs:
  - Update user guide with bounded SPA and language switching behavior.
  - Update developer guide with i18n and SPA frame rules.
  - Update demo README with bilingual UI note.
- Demo impact:
  - The same Account Radar demo becomes readable on smaller desktop monitors and can be switched between EN/RU UI chrome.
- Acceptance criteria:
  - Browser page does not vertically scroll for normal desktop shell usage.
  - Sidebar profile stays visible at small desktop viewport height.
  - Accounts table text does not overlap adjacent columns.
  - EN/RU switch changes visible UI labels and persists after refresh.
  - Design-system hardcode scan, tests, and frontend build pass.
- Risks:
  - Full i18n could grow too large; mitigate by localizing UI chrome first and leaving artifact data unchanged.

### Slice 0.4.2: RU localization for visible demo data

- Status: `Done`
- Goal: Complete RU localization for the current demo by translating visible deterministic artifact values, not only UI chrome.
- User value: A Russian-language user can read Account Radar and Access Plans without half of the screen falling back to English demo data.
- Scope:
  - Add a frontend presentation-layer localizer for deterministic demo artifact values.
  - Localize stages, owners, route titles, route types, rationale, risks, expected state changes, signal kinds, signal summaries, evidence summaries, and missing-role labels.
  - Keep raw IDs, source refs, company names, person names, technical workflow names, and runtime names unchanged.
  - Update Accounts and Access Plans screens to render visible artifact values through the localizer in RU mode while preserving EN mode.
- Out of scope:
  - Changing backend artifact schemas.
  - Generating separate localized JSON artifacts.
  - Translating company names, person names, source refs, workflow IDs, or machine-readable fields.
- Implementation notes:
  - Keep this as presentation logic until artifact localization becomes a backend/product requirement.
  - Treat the current six-account synthetic portfolio as the deterministic translation perimeter.
- Tests:
  - Frontend contract test ensures Accounts and Access Plans use the demo data localizer.
  - Existing `python -m pytest` remains green.
  - `npm --prefix ./frontend run build` remains green.
- Docs:
  - Update user and developer docs with the visible demo data localization policy.
- Demo impact:
  - RU mode displays translated account stages, routes, reasons, risks, signals, evidence, and role/gap labels.
- Acceptance criteria:
  - The RU screenshots for Accounts and Access Plans no longer show English route titles, signal summaries, rationale, risks, or owner labels except for explicitly retained raw data.
- Risks:
  - Exact-string translation can drift if fixtures change; mitigate with a future artifact-level localization contract when live data starts.

### Slice 0.5: Power Web Lite board loop

- Status: `Done`
- Goal: Turn role lists into a visual Power Web Lite board with people, roles, external actors, stance, and missing stakeholders.
- User value: A user can visually inspect who influences the selected account and why the recommended route goes through a specific person, partner, or missing role.
- Scope:
  - Add deterministic `PowerWebBoardBuilder` read model derived from current `Account`, `AccessPlan`, and top route.
  - Extend Access Plan artifacts with non-breaking `power_web_board` data: summary, nodes, edges, and route path.
  - Regenerate single-account and portfolio demo artifacts with board data.
  - Replace the `Account Map` planned placeholder with a working selected-account board screen.
  - Show visible figures, missing roles, board coverage, recommended route, route path, selected node inspector, and stance/status badges.
  - Highlight the recommended route path using cobalt per the design system.
- Out of scope:
  - Graph database.
  - Drag/drop editing.
  - Board editing or persistence.
  - Automatic relationship extraction from live sources.
- Implementation notes:
  - Keep this as a read model generated from fixture/workflow output.
  - Reuse the design-system prototype `AccountMap.jsx` as reference, but implement the smallest necessary board.
  - Keep Accounts row click opening `Access Plans`; navigation `Account Map` opens the board for the currently selected account.
  - Localize board UI and deterministic role/state labels in the presentation layer.
- Tests:
  - Unit tests for board read-model generation.
  - Smoke tests that generated single-account and portfolio Access Plan artifacts contain board data.
  - Frontend contract checks for `PowerWebBoard` types, `AccountMapScreen`, selected route path, and placeholder replacement.
  - Frontend build.
- Docs:
  - Update user guide with Power Web Lite explanation.
  - Update developer guide with board read model and artifact contract.
  - Update architecture overview with read-model boundary.
  - Update demo walkthrough with `Account Map`.
- Demo impact:
  - Demo shows the account as a board, not just cards and lists.
- Acceptance criteria:
  - Recommended route is visually connected to visible board entities.
  - Missing stakeholders are visible and explained.
  - The board remains synthetic, deterministic, and test-covered.
- Risks:
  - UI can grow too large; mitigate by keeping one board and one inspector/summary section.

### Slice 0.5.1: Enterprise-sized Power Web demo account

- Status: `Done`
- Goal: Make the current demo show at least one more realistic enterprise-sized Power Web.
- User value: A user can inspect how the `Account Map` behaves with a denser buying-committee map instead of only 3-4 figures.
- Scope:
  - Expand the default top-ranked `Северные Роботы` fixture to eight board figures.
  - Include surfaced technical, procurement, security, operations, partner, and missing economic-buyer roles.
  - Preserve deterministic Account Radar, Access Plan, and board generation.
  - Add test coverage so the richer board does not regress below eight figures.
- Out of scope:
  - Graph database, editing, drag/drop, live source extraction, or UI redesign.
- Demo impact:
  - Opening the demo and navigating to `Account Map` now shows an enterprise-like Power Web by default.
- Acceptance criteria:
  - `Северные Роботы` remains the top-ranked account.
  - Its generated board has at least eight non-account figures.
  - The board includes at least one blocker stance.
  - Tests and frontend build pass.

### Slice 0.6: Playbook rules explanation loop

- Status: `Done`
- Goal: Make the selected account's playbook rules explainable in the existing workspace shell without adding editing or frontend-side planner logic.
- User value: A user can see which routes are allowed, which channels/assets matter, why human review is required, and how route previews change in a pre-generated what-if variant.
- Scope:
  - Add deterministic `PlaybookAnalysisBuilder` over `Account`, `Playbook`, and `AccessPlan`.
  - Extend Access Plan artifacts with non-breaking `playbook_analysis.contract_version = "0.6"`.
  - Generate `current` and `no_partner_motion` variants at artifact-generation time.
  - Disable `partner_intro` and partner-case assets in the `no_partner_motion` variant, then rerun the Python planner for its preview.
  - Replace the `Playbook` placeholder with a read-only `PlaybookScreen`.
  - Show allowed routes, blocked channels, assets, review rules, route decisions, and route preview.
  - Keep EN/RU UI and deterministic demo value localization.
- Out of scope:
  - Editing playbook rules in the frontend.
  - Persistence, production API, auth, live regeneration, or live source connectors.
  - Duplicating planner logic in TypeScript.
- Implementation notes:
  - Python remains the source of truth for playbook policy and route previews.
  - The frontend renders pre-generated analysis from `artifact.playbook_analysis`.
  - Access Plans reads the review rule from `playbook_analysis.current` instead of hardcoding it.
- Tests:
  - Unit tests for `PlaybookAnalysisBuilder`.
  - Smoke tests for `generate-access-plan` and `generate-account-radar` writing `playbook_analysis`.
  - Frontend contract tests for `PlaybookScreen`, TypeScript contracts, i18n usage, and artifact fields.
  - `python -m pytest` and `npm --prefix ./frontend run build`.
- Docs:
  - User guide, developer guide, architecture overview, demo docs, and README updated.
- Demo impact:
  - The user can open `Playbook`, switch between `Current playbook` and `No partner motion`, and see route decisions and preview change without a page reload.
- Acceptance criteria:
  - `Playbook` is no longer a planned placeholder.
  - Every generated selected-account artifact includes `playbook_analysis`.
  - The `no_partner_motion` variant blocks/removes partner intro behavior.
  - All route policy decisions remain deterministic and explainable.
- Risks:
  - What-if behavior can be mistaken for live interactive recalculation; mitigate by documenting it as pre-generated.

### Slice 0.6.1: ICP Radar terminology and ТОиР fixture contract

- Status: `Done`
- Goal: Rename the upstream radar concept to `ICP Radar` and define the first ТОиР automation fixture contract from the SIBUR-style XLSX analysis.
- User value: The product language becomes ABM-native: radars are profiles of ideal customers, not generic account lists.
- Scope:
  - Add an `ICP Radar` concept above the existing Account / Power Web / Access Plan loop.
  - Define `ICPProfile`, `RadarDefinition`, `SignalCriterion`, `SignalObservation`, `ICPScoringFormula`, `RadarCandidate`, and `SignalValidation` as planned contracts.
  - Treat the attached SIBUR-style workbook as the first fixture source.
  - Map workbook sheets:
    - `Criteria` -> signal criteria C1-C20;
    - `ICP Matrix` -> legal entities, stable account attributes, criterion scores, evidence refs, score components, tier;
    - `Summary` -> ranked candidate shortlist;
    - `Sources` -> evidence source registry.
  - Record that future demo account/company/person names should be Russian-language examples.
- Out of scope:
  - Implementing XLSX parsing.
  - Changing runtime artifacts.
  - Live source search.
  - UI implementation.
- Implementation notes:
  - Keep the current `AccountRadar` code name as a compatibility read model until the ICP Radar implementation replaces it.
  - Use `ICP Radar` in product/docs/UI language for the upstream ABM funnel.
- Tests:
  - Documentation-only slice; no runtime tests required.
- Docs:
  - Update README, architecture overview, developer guide, user guide, demo docs, concept document, and roadmap.
- Demo impact:
  - Establishes that the next demo expansion is ТОиР/SIBUR-style ICP Radar, not another generic synthetic portfolio.
- Acceptance criteria:
  - Docs consistently describe the upstream module as `ICP Radar`.
  - The ТОиР fixture contract is documented.
  - The distinction between account discovery and signal monitoring is explicit.
- Risks:
  - Code names and product names may diverge temporarily; mitigate with a compatibility note.

### Slice 0.6.2: ICP Radar XLSX fixture import loop

- Status: `Done`
- Goal: Turn the SIBUR-style XLSX analysis into a deterministic ICP Radar artifact and a first read-only `ICP Radar` screen.
- User value: A user can inspect how a ТОиР ICP profile ranks legal entities before any account is accepted into Power Web work.
- Scope:
  - Add a fixture copy and normalized fixture derived from `sibur_icp_pass1.xlsx`.
  - Add a parser/normalizer for the workbook structure using `openpyxl`.
  - Build an `ICPRadarArtifact` with:
    - radar definition;
    - criteria C1-C20;
    - legal entities;
    - evidence sources;
    - fit/intent/trigger/total score;
    - tier;
    - score explanation.
  - Add a frontend `ICP Radar` screen showing candidates, score breakdown, main signal, evidence refs, and recommended triage action.
  - Rename or adapt visible demo labels from Account Radar to ICP Radar where this screen is used.
  - Replace generic demo company names and person names with Russian-language examples in the current accepted-account demo data.
- Out of scope:
  - Live search/scraping.
  - Manual validation actions.
  - Power Web generation for every candidate.
  - Persistent storage.
- Implementation notes:
  - Commit both `demo/fixtures/icp_radar/sibur_icp_pass1.xlsx` and `demo/fixtures/icp_radar/toir_sibur_icp_radar.json`.
  - Keep `ICPRadarXlsxImport` deterministic and free of live source calls.
  - Keep scoring deterministic and close to the workbook formula first.
- Tests:
  - Unit tests for criterion parsing/normalization.
  - Unit tests for fit/intent/trigger/total score calculation.
  - Smoke test that `generate-icp-radar` writes the artifact.
  - Frontend contract test that the `ICP Radar` screen renders score breakdown and evidence links.
  - `python -m pytest` and `npm --prefix ./frontend run build`.
- Docs:
  - Update user/developer/demo docs with the new command and fixture shape.
- Demo impact:
  - Demo starts to show the upstream ABM funnel before Power Web.
- Acceptance criteria:
  - The ТОиР fixture produces a ranked candidate list.
  - Score explanations are traceable to criteria and evidence.
  - Current Power Web / Access Plan demo remains runnable.
- Risks:
  - The real workbook may contain non-synthetic company data; mitigate by using a sanitized derived fixture if needed.

### Slice 0.6.2.1: ICP Radar table-first UX correction

- Status: `Done`
- Goal: Rework the read-only ICP Radar screen into a practical table-first workspace before adding signal validation.
- User value: A user can scan a wide shortlist comfortably, keep account identity visible while comparing many columns, and open details only when needed.
- Scope:
  - Make the main `ICP Radar` screen a wide ranked candidate table.
  - Keep the first account/company column sticky during horizontal scroll.
  - Keep the table as the dominant surface; remove the always-visible large side detail panel.
  - Add row expansion:
    - clicking a candidate expands a compact preview area directly under that row;
    - preview includes the current summary information: main signal, comment, score breakdown, evidence refs, and a compact criteria summary;
    - preview has a maximum height and owns its own vertical scroll when content exceeds that height.
  - Add a separate read-only candidate detail screen or route:
    - full candidate profile;
    - evidence list;
    - C1-C20 criteria breakdown;
    - source refs;
    - scoring explanation.
  - Add navigation back from candidate detail through breadcrumbs such as `ICP Radar / <candidate>` and through the sidebar `ICP Radar` item.
  - Keep `Take into work` visible only as a planned affordance.
- Out of scope:
  - Confirm/correct/reject/stale evidence actions.
  - Score recalculation from validation decisions.
  - Persistent candidate state.
  - Handoff into accepted Accounts.
  - Live source connectors.
- Implementation notes:
  - This slice is a UX/IA correction for Slice 0.6.2, not a new backend capability.
  - Preserve `/demo/icp_radar.json` as the source artifact.
  - If no router is introduced, implement candidate detail through existing `ScreenId` state plus selected candidate state.
  - Dense table layout must use an owned horizontal scroll container.
  - Sticky account column must remain readable over scrolled content and must not overlap neighboring columns.
  - Expanded previews must not make the whole page grow without bound; use max-height and local overflow.
  - The candidate detail screen is the future surface for Slice 0.6.3 validation actions, but this slice keeps it read-only.
- Tests:
  - Frontend contract test that `ICP Radar` still loads `/demo/icp_radar.json`.
  - Frontend contract test that the main screen uses a wide table and sticky first account column.
  - Frontend contract test that row preview expansion exists and has bounded overflow styles.
  - Frontend contract test that a candidate detail screen/path exists and shows evidence refs plus C1-C20 criteria.
  - `npm --prefix ./frontend run build`.
  - Existing `python -m pytest` remains green.
- Docs:
  - Update user/developer/demo docs to describe table-first ICP Radar, row preview, and read-only candidate detail.
- Demo impact:
  - Opening the demo still starts on `ICP Radar`, but the user lands on a broad account shortlist rather than a split table/detail layout.
- Acceptance criteria:
  - A user can horizontally scroll the ICP Radar table while the account column remains fixed.
  - Clicking a row opens a bounded inline preview under the account.
  - A user can open and exit a separate read-only candidate detail screen.
  - Signal validation remains clearly planned for Slice 0.6.3.
- Risks:
  - Sticky columns in dense tables can cause overlap; mitigate with explicit widths, z-index, background, and small-monitor checks.
  - Detail routing can become a premature router migration; keep navigation minimal unless a router becomes necessary.

### Slice 0.6.2.2: ICP Radar UX repair

- Status: `Done`
- Goal: Fix the current ICP Radar table, preview, and detail UX before adding signal validation.
- User value: A user can scan candidates, expand a row, and open candidate details without nested scrolls, duplicated score noise, unreadable sections, or broken horizontal table behavior.
- Scope:
  - Remove nested scrolls from ICP Radar preview; use one vertical scroll for the expanded block.
  - Limit inline preview to top-5 evidence refs and top-5 criteria.
  - Remove duplicated score/tier blocks from preview; strengthen score/tier values in the existing table row when expanded.
  - Make preview section labels visually distinct from body text.
  - Fix table scroll ownership so only table columns scroll horizontally and the company column stays sticky.
  - Localize ICP Radar RU labels for fit, intent, trigger, tier, evidence, confidence, source refs, and related headings.
  - Add a sticky compact header in candidate detail view so the selected account remains visible while reviewing long criteria.
- Out of scope:
  - Criterion-level evidence explanations.
  - Signal validation actions.
  - Take-into-work handoff.
  - System-wide mobile baseline.
- Implementation notes:
  - Keep the artifact contract unchanged in this slice.
  - Do not add a router.
  - Preserve the current table-first desktop intent.
  - Prefer clearer hierarchy, stronger row states, and fewer repeated numbers over adding more content.
- Tests:
  - Frontend contract tests for single-scroll preview, sticky table ownership, RU labels, and sticky detail header.
  - `npm --prefix ./frontend run build`.
  - `npm --prefix ./frontend run visual:smoke`.
  - `python -m pytest`.
- Docs:
  - Update user/developer/demo docs and Wiki screenshots.
- Demo impact:
  - ICP Radar becomes the primary usable shortlist surface again.
- Acceptance criteria:
  - No nested vertical scrollbar in expanded preview.
  - No page-level horizontal scroll for the ICP Radar table on desktop.
  - Expanded rows remain readable and visually structured.
  - RU mode has Russian ICP Radar column and section labels.
- Risks:
  - Sticky columns can regress at small desktop widths; mitigate with visual smoke and manual screenshot inspection.

### Slice 0.6.2.3: ICP Radar evidence-backed criteria contract

- Status: `Done`
- Goal: Make each ICP Radar criterion score explainable with criterion-level evidence.
- User value: A user can answer why C1 received score 1, 2, or 3, inspect the supporting source, and decide whether the signal should be trusted.
- Scope:
  - Extend the ICP Radar artifact with criterion-level explanation records.
  - Link each nonzero C1-C20 score to evidence refs, source URL, short fact/excerpt, rationale, confidence, and score reason.
  - Update XLSX fixture normalization or add a curated normalized fixture layer where workbook data is not granular enough.
  - Update candidate detail view to show criteria as evidence-backed explanations, not just score rows.
  - Prepare the data shape for Slice 0.6.3 validation states.
- Out of scope:
  - Live source scraping.
  - Automatic LLM truth adjudication.
  - User validation controls.
- Implementation notes:
  - Current artifact data has candidate-level `criteria_scores`, `evidence_refs`, and `source_urls`; it cannot fully explain individual criterion scores.
  - Keep old fields backward compatible and add new fields non-breakingly.
  - The XLSX lacks criterion-level excerpts, so this slice uses deterministic curated fixture annotations and marks them as `synthetic_demo_annotation`.
  - Numeric scores still come from the XLSX; synthetic annotations explain selected high-impact criteria for demo validation.
- Tests:
  - Python artifact contract tests for criterion explanation records.
  - Importer/normalizer tests for evidence mapping.
  - Frontend contract tests for evidence-backed criteria detail.
  - `python -m pytest`.
  - `npm --prefix ./frontend run build`.
- Docs:
  - Update architecture/developer/user/demo docs with criterion evidence contract.
- Demo impact:
  - Candidate detail becomes a real score explanation surface.
- Acceptance criteria:
  - At least top candidates show why high-impact criteria received their scores.
  - Every displayed criterion score has evidence or an explicit "no evidence available" reason.
  - Detail view links criteria to source refs and facts/excerpts.
- Risks:
  - Workbook may not contain enough granular evidence; mitigate with a curated fixture annotation layer and clear source labels.

### Slice 0.6.2.4: ICP Criteria review UX correction

- Status: `Done`
- Goal: Turn the ICP Radar candidate criteria detail from an always-expanded evidence dump into a compact review/navigation surface.
- User value: A user can scan C1-C20 quickly, filter by status, sort by score, drill into only the criteria that need attention, and record local review intent before the full validation loop exists.
- Scope:
  - Replace the full expanded criteria card list with a compact table-first view.
  - Add filters for all/supported/inferred/not observed/needs review.
  - Add sorting by score, status, and confidence.
  - Expand one criterion row at a time to show rationale, facts, source refs, and links.
  - Remove the oversized `Происхождение` block from the expanded criterion view.
  - Render confidence as a compact tag instead of a large block.
  - Add local UI controls to accept, reject, or edit a criterion score with a comment.
  - Keep local review state frontend-only and non-persistent in this corrective slice.
  - Keep breadcrumbs and a compact account header sticky while scrolling candidate detail.
- Out of scope:
  - Persistent signal validation.
  - Backend review state or score recalculation.
  - Global ICP Radar shortlist score changes.
  - Audit history beyond local UI state.
- Implementation notes:
  - Do not change the ICP Radar artifact contract introduced in Slice 0.6.2.3.
  - Keep original XLSX score visible when an adjusted local score is entered.
  - Treat this as the UI bridge to Slice 0.6.3, where validation becomes a real domain state.
- Tests:
  - Frontend contract tests for table-first criteria review, filters, sorting, expandable row, sticky header, and local review controls.
  - EN/RU i18n coverage for all new visible labels.
  - `npm --prefix ./frontend run build`.
  - `python -m pytest`.
- Docs:
  - Update user and developer docs with the local criteria review behavior and persistence limitation.
- Demo impact:
  - Candidate detail becomes faster to scan and closer to the intended signal validation workflow.
- Acceptance criteria:
  - Criteria initially render as compact rows, not fully expanded cards.
  - User can filter and sort criteria.
  - User can expand a criterion to inspect evidence details.
  - Confidence is compact and origin is not shown as a separate large block.
  - User can accept, reject, or edit score locally with a comment.
  - Breadcrumbs and compact account context remain visible during criteria scrolling.
- Risks:
  - Local review controls may look like durable validation; mitigate with explicit local/demo-state copy until Slice 0.6.3.

### Slice 0.6.2.5: ICP Radar catalog and read-only configuration editor

- Status: `Done`
- Goal: Reframe `ICP Radar` as a portfolio of configured radars, not a single unexplained shortlist.
- User value: A user can see which ICP Radars exist, what each radar monitors, when it ran, how many candidates it found, and which read-only configuration produced a selected shortlist.
- Scope:
  - Add `demo/output/icp_radars.json` and `frontend/public/demo/icp_radars.json` as the ICP Radar catalog artifact.
  - Keep the existing `icp_radar.json` shortlist artifact for the active `ТОиР / SIBUR` radar.
  - Add `radar.definition` to the active ICP Radar artifact with discovery scope, monitoring setup, criteria, scoring formula, tier thresholds, and limitations.
  - Add three demo radar cards: active fixture-backed `ТОиР / SIBUR`, configured `ТОиР / Горнодобыча`, and planned `Энергоэффективность / Ритейл`.
  - Make `ICP Radar` open as a catalog screen.
  - Add selected-radar detail with breadcrumbs and `Shortlist` / `Settings` tabs.
  - Keep the current table-first shortlist and candidate detail for the active fixture-backed radar.
  - Show a read-only empty shortlist state for configured/planned radars without generated candidates.
  - Add a read-only settings/editor surface with profile, discovery, monitoring, criteria, scoring, thresholds, and limitations.
- Out of scope:
  - Editing radar settings.
  - Real scheduler/run history.
  - Running live source searches.
  - Persisting user-created radars.
  - Taking candidates into shared `Accounts`.
- Implementation notes:
  - The screen should make it explicit that the current ТОиР/SIBUR radar is imported from fixture configuration.
  - Treat the catalog as a read model over configured radar definitions.
  - Frontend local editable settings are delivered in `Slice 0.6.5`; production persistence, scheduler, and live execution remain later work.
  - Take-into-work remains `Slice 0.6.4`.
  - Formula display remains declarative and constrained; no executable formula scripting is introduced.
- Tests:
  - Python artifact contract tests for `radar.definition`.
  - Python smoke test for `generate-icp-radar-catalog`.
  - Frontend contract tests for catalog load, radar cards, selected-radar tabs, read-only settings, and no save action.
  - `python -m pytest`.
  - `npm --prefix ./frontend run build`.
- Docs:
  - User, developer, architecture, and demo docs updated for catalog and selected-radar settings.
- Demo impact:
  - Demo now starts with a portfolio of radars and lets a user drill into the active fixture-backed shortlist or inspect configured radars before they produce candidates.
- Acceptance criteria:
  - `ICP Radar` starts with radar cards.
  - Selecting `ТОиР / SIBUR` opens the existing shortlist and read-only settings.
  - Selecting configured/planned radars shows empty shortlist state plus configuration.
  - Settings are visibly read-only and no save action exists.
  - Existing candidate table/detail behavior remains available for the active radar.
- Risks:
  - Read-only examples can look like live jobs; mitigate with status, run-mode, and limitation labels.

### Slice 0.6.2.6: ICP Radar laptop-readable inline preview

- Status: `Done`
- Goal: Make expanded ICP Radar candidate preview usable on laptop-width screens while preserving the wide table and sticky company column.
- User value: A sales user can expand a candidate on a normal laptop, read the preview blocks without horizontal fighting, and open details from a clear action below the preview.
- Scope:
  - Keep the shortlist table horizontally scrollable for columns.
  - Anchor expanded preview content to the visible table/workspace area instead of the horizontally scrolled column grid.
  - Remove the separate preview left rail; place preview context blocks at the left edge of the visible preview.
  - Move `Open details` below preview blocks.
  - Keep preview content responsive and width-contained with no horizontal scroll inside the preview.
  - Increase preview height enough for the main blocks to fit on small desktop/laptop screens, with only one vertical scroll owner for the whole preview when needed.
- Out of scope:
  - Backend or artifact changes.
  - Signal validation.
  - Mobile-specific layout conversion.
- Tests:
  - Frontend contract tests for preview anchoring, no left-rail layout, responsive preview body, and table-owned horizontal scroll.
  - `npm --prefix ./frontend run build`.
  - Relevant Python documentation/frontend contract tests.
- Docs:
  - Update ADR, user guide, developer guide, and roadmap.
- Demo impact:
  - The active `ТОиР / SIBUR` shortlist preview becomes usable at laptop widths such as `1366x768`.
- Acceptance criteria:
  - Preview content does not move with horizontal table column scroll.
  - Preview blocks fit the visible table/workspace width.
  - `Open details` appears below preview content.
  - Preview keeps one vertical scroll owner and no nested horizontal scroll.
- Risks:
  - CSS anchoring can regress in older browsers; mitigate with build checks and visual smoke in Chromium.

### Slice 0.6.2.7: ICP Radar catalog list-first UX correction

- Status: `Done`
- Goal: Replace the three-column ICP Radar catalog cards with a list-first catalog that is readable on laptop screens.
- User value: A sales or ABM user can compare configured radars, statuses, run cadence, owners, and candidate counts without truncated card content.
- Scope:
  - Replace the three-column radar card grid with a vertical list of wide radar rows.
  - Keep one configured radar per row with name, ICP profile, scope, status, compact metrics, run mode, and open action.
  - Use stable row columns for identity, status, metrics, run mode, and action so fields do not float between rows.
  - Remove metric tiles inside narrow cards; use a compact metric strip.
  - Keep small-screen behavior as a stacked row, not a return to narrow multi-column cards.
- Out of scope:
  - Backend or artifact changes.
  - Editable radar settings.
  - Mobile-specific catalog redesign.
- Tests:
  - Frontend contract tests for list-first catalog classes and no three-column catalog grid.
  - `npm --prefix ./frontend run build`.
  - Relevant Python frontend/docs contract tests.
- Docs:
  - Update configurable-object ADR, user guide, developer guide, and roadmap.
- Demo impact:
  - The `ICP Radar` start screen becomes easier to scan and aligns with dense-data UX decisions.
- Acceptance criteria:
  - Radar names and summaries are readable on laptop-width screens.
  - Status, metrics, run mode, and action columns align predictably across radar rows.
  - Stable catalog columns do not create page-level or workspace-level horizontal overflow.
  - Catalog rows expose cadence, last run, candidates, needs review, accepted, owner, status, and run mode.
  - No three-column radar catalog layout remains in frontend CSS.
- Risks:
  - Long radar names can still require ellipsis; full configuration remains available in selected radar `Settings`.

### Slice 0.6.3: ICP Radar signal validation loop

- Status: `Done`
- Goal: Add human validation for found ICP Radar signals and make validation affect the candidate score.
- User value: A user can prevent wrong, distorted, or stale information from driving account prioritization.
- Scope:
  - Make `radar.definition.intent_signals` the canonical C1-C20 dictionary for Settings, candidate scores, and evidence explanations.
  - Add `SignalValidation` states: `unreviewed`, `confirmed`, `corrected`, `rejected`, `stale`.
  - Add correction fields for adjusted score, confidence, corrected summary, selected evidence refs, comment, and review timestamp.
  - Add a deterministic rescore service that uses validated signal state and keeps rejected/stale signals in the audit trail with zero score contribution.
  - Add UI controls to confirm, correct, reject, or mark a signal stale.
  - Show before/after score impact, candidate-level validation summary, and score delta in the shortlist.
  - Store validation decisions in browser-local demo state under `power-web-os-icp-radar-signal-validation`.
- Out of scope:
  - Multi-user review.
  - Permanent database persistence.
  - Live source re-checking.
  - Automatic truth adjudication by LLM.
- Implementation notes:
  - Rejected and stale signals should remain visible in the evidence/audit trail but should not strengthen the score.
  - Corrected signals should show both original observation and user override.
  - Build on criterion-level evidence from Slice 0.6.2.3; validation actions should operate on evidence-backed observations, not only aggregate candidate-level refs.
- Tests:
  - Unit tests for validation state transitions.
  - Unit tests for score recalculation from validation decisions.
  - Frontend contract tests for validation controls and score delta display.
  - `python -m pytest` and `npm --prefix ./frontend run build`.
- Docs:
  - Update user/developer/architecture/demo docs with validation semantics.
- Demo impact:
  - User can manually validate radar evidence before accepting an account into work.
- Acceptance criteria:
  - Confirm/correct/reject/stale actions visibly change candidate score or contribution.
  - Score explanation shows validation decisions.
  - The action history is preserved in browser local state.
- Risks:
  - Browser-only validation can be mistaken for persisted workflow; label it as local demo state until persistence exists.

### Slice 0.6.3.1: Live mini ICP Radar run with OpenRouter web search

- Status: `Done`
- Goal: Add the first real live ICP Radar run without touching the stable XLSX-based ТОиР/SIBUR demo.
- User value: A user can run a small ICP Radar from the CLI and see what the AI/search workflow actually found, including weak or empty results, instead of synthetic candidates.
- Scope:
  - Add mini radar `ТОиР Quick Live Radar` with two qualification criteria and three intent signals.
  - Add `LiveICPRadarRunWorkflow` using the `langgraph-dai` / `BaseWorkflow` pattern when available and a local runner for tests.
  - Add provider-neutral `WebSearchProvider` boundary with `OpenRouterWebSearchProvider` and `RecordedWebSearchProvider`.
  - Add OpenRouter env support: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_WEB_MODE`.
  - Add CLI:
    - `python -m power_web_os.demo run-live-mini-icp-radar --dry-run-plan`
    - `python -m power_web_os.demo run-live-mini-icp-radar --live`
  - Write live artifacts only from actual provider output:
    - `demo/output/live_mini_icp_radar_run.json`
    - `frontend/public/demo/live_mini_icp_radar_run.json`
  - Add the live radar to the ICP Radar catalog.
  - Show empty state when the live artifact is absent, and show live shortlist/run metadata only when the artifact exists.
- Out of scope:
  - UI run button.
  - Scheduler.
  - Source crawling outside provider web search.
  - Take-into-work handoff.
  - Mixing live mini radar findings into the accepted `Accounts` portfolio.
  - Synthetic fallback candidates for live runs.
- Implementation result:
  - OpenRouter is the first provider, not an architectural dependency.
  - Server-side OpenRouter web search is attempted first; plugin web mode is isolated behind the same provider boundary.
  - Live artifacts must not contain API keys, authorization headers, bearer tokens, or raw provider dumps.
  - Model-supplied source URLs are filtered by reachability before they can support candidates; if sources cannot be verified, the result should remain empty/weak rather than fabricate confidence.
- Tests:
  - Unit tests for search plan, request modes, recorded provider normalization, optional langgraph runtime, and secret filtering.
  - Frontend contract tests for missing/present live artifact behavior.
  - `python -m pytest`
  - `npm --prefix ./frontend run build`
  - `npm --prefix ./frontend run settings:toggle-smoke`
- Docs:
  - README, user guide, developer guide, architecture overview, demo README, and ADR updated.
- Demo impact:
  - The ICP Radar catalog now includes `ТОиР Quick Live Radar`.
  - Before a live run, the UI shows the CLI command and no fake candidates.
  - After a successful live run, the UI reads `/demo/live_mini_icp_radar_run.json` and shows provider runtime metadata, sources, qualification, signals, and review flags.
- Acceptance criteria:
  - Dry-run plan performs no network call and produces no candidates.
  - Live run refuses to run without a key.
  - Live run uses OpenRouter through `WebSearchProvider`.
  - Frontend does not show fake live candidates when no artifact exists.
  - Generated live artifacts do not contain secrets.
- Validation notes:
  - Local live smoke reached OpenRouter after repository-local `.env` precedence was fixed.
  - The implementation keeps the UI in missing-artifact empty state until a valid OpenRouter account/key produces an artifact.
- Risks:
  - OpenRouter web search/server tools are beta; the provider boundary keeps fallback/replacement isolated.
  - LLM/provider output can hallucinate source URLs; reachability filtering prevents those URLs from becoming trusted evidence.

### Slice 0.6.3.2: Align Live ICP Radar UX with table-first shortlist pattern

- Status: `Done`
- Goal: Make `ТОиР Quick Live Radar` use the same ICP Radar shortlist UX as fixture-backed radars.
- User value: A user reviews live provider-backed findings in the same familiar table-preview-detail flow instead of learning a separate live-radar screen.
- Scope:
  - Replace the live-only split/grid/detail layout with the shared table-first shortlist pattern.
  - Keep live run metadata as a compact context block above the table.
  - Render live candidates in a wide table with sticky identity column and owned horizontal scroll.
  - Add bounded inline preview for live candidates.
  - Add an in-shell live candidate detail view with breadcrumbs and sticky compact header.
  - Preserve the missing-artifact empty state and avoid fake candidates.
- Out of scope:
  - Backend schema changes.
  - Live provider changes.
  - UI run button.
  - Take-into-work behavior.
- Tests:
  - Frontend contract tests forbid live-only split/grid/detail classes.
  - Frontend contract tests require live preview/detail state and shared shortlist classes.
  - Visual smoke covers live radar table, preview, and detail when `live_mini_icp_radar_run.json` exists.
- Docs:
  - Table-first UX ADR, live radar ADR, developer guide, user guide, and demo README updated.
- Acceptance criteria:
  - Live radar opens through the standard table-first ICP Radar surface.
  - Row click opens inline preview.
  - `Open details` opens a separate in-shell detail view.
  - No standalone live side panel remains.

### Slice 0.6.3.3: Canonical Radar UX contract and live radar detail alignment

- Status: `Done`
- Goal: Freeze a canonical ICP Radar UX contract and align `ТОиР Quick Live Radar` with the same attribute and visual model as fixture-backed radars.
- User value: A user reviews fixture and live radar candidates through one predictable pattern instead of learning different headers, columns, previews, and detail screens per data source.
- Scope:
  - Add a canonical radar/candidate view-model boundary in the frontend.
  - Map fixture-backed and live radar artifacts into shared shortlist, preview, and detail components.
  - Remove `Только просмотр` from the radar header and keep header status to `Черновик / Активен / Остановлен`.
  - Use canonical shortlist columns for every radar: company, total, fit, intent, trigger, tier, evidence, action.
  - Keep live runtime/provider/model/source metadata out of the shortlist and render it only in the candidate `Journal` tab.
  - Standardize inline preview to four blocks: summary, tier, qualification, signals.
  - Standardize candidate detail tabs: overview, qualification, signals, sources, journal.
  - Add ADR and contract tests so future radar sources cannot introduce provider-specific scan/detail layouts.
- Out of scope:
  - Backend schema changes.
  - Live provider changes.
  - UI run button.
  - Take-into-work behavior.
- Tests:
  - Frontend contract tests for canonical columns, preview sections, status mapping, tabbed detail, journal-only runtime metadata, and no standalone live layout.
  - Visual smoke covers fixture and live radar preview/detail flows.
  - `python -m pytest`
  - `npm --prefix ./frontend run build`
  - `npm --prefix ./frontend run settings:toggle-smoke`
  - `npm --prefix ./frontend run visual:smoke`
- Docs:
  - Added `Canonical ICP Radar UX Contract` ADR.
  - Updated table-first UX ADR, live radar ADR, developer guide, user guide, and demo README.
- Acceptance criteria:
  - Fixture and live radars use the same shortlist columns and preview block model.
  - Live runtime metadata appears only under `Journal`.
  - New radar sources must integrate via adapters into the canonical UX.

### Slice 0.6.3.4: Qualification evidence and review contract

- Status: `Done`
- Goal: Make account qualification results explainable and reviewable at the same level as intent signals.
- User value: A user can inspect why a live radar candidate passed each qualification rule, which sources were used, how trustworthy they are, and correct the final assessment with a comment.
- Scope:
  - Extend live qualification results with rule snapshot, operator, requirement level, source usages, source origin, trust/check policy, evidence findings, cross-validation, requirement evaluation, final assessment, and optional review decision.
  - Keep old live qualification fields compatible while enriching provider output in the backend normalizer.
  - Add contract validation for rule/result/source consistency.
  - Replace the raw Q1/Q2 candidate detail list with a table-first qualification review surface.
  - Add browser-local approve/reject/correct actions for qualification results.
  - Add ADR and docs for the qualification evidence/review contract.
- Out of scope:
  - Backend persistence for qualification review decisions.
  - Re-running live search from the UI.
  - Take-into-work behavior.
- Tests:
  - Backend tests for live artifact version and qualification evidence contract.
  - Frontend contract tests for qualification review types, UI table, review actions, and i18n keys.
  - `npm --prefix ./frontend run build`
- Docs:
  - Added `Qualification Evidence And Review Contract` ADR.
  - Updated architecture, developer, user, and demo docs.
- Acceptance criteria:
  - Candidate qualification rows are no longer raw labels.
  - Expanded rows show sources, origin, trust/check policy, evidence facts, cross-validation, and requirement evaluation.
  - Review actions are local and do not mutate generated artifacts.

### Slice 0.6.3.5: ICP Radar frontend feature decomposition

- Status: `Done`
- Goal: Refactor the ICP Radar frontend from a monolithic screen file into a maintainable feature module without changing user-visible behavior.
- User value: Future radar UX changes can be made predictably without reintroducing inconsistent layouts or a 4,000+ line screen file.
- Scope:
  - Replace `frontend/src/screens/ICPRadarScreen.tsx` with a thin wrapper.
  - Move ICP Radar implementation into `frontend/src/features/icp-radar/`.
  - Split candidate table/detail, live candidate views, criteria evidence review, settings, settings fields, header editor, shared detail primitives, and model helpers.
  - Lazy-load the heavy Settings editor so the default catalog/shortlist path does not pull it into the first bundle.
  - Split i18n runtime initialization from the large resources dictionary.
  - Add architecture contract tests for screen thinness, feature module boundaries, settings lazy loading, and i18n split.
  - Add ADR and docs for frontend feature boundaries and comment expectations.
- Out of scope:
  - Visual redesign.
  - Backend/schema changes.
- Tests:
  - `npm --prefix ./frontend run build`
  - `python -m pytest`
- Docs:
  - Added `Frontend Feature Module Boundaries` ADR.
  - Updated architecture overview and developer guide.
- Acceptance criteria:
  - `frontend/src/screens/ICPRadarScreen.tsx` remains a thin wrapper.
  - `frontend/src/features/icp-radar/ICPRadarScreen.tsx` does not inline Settings, criteria breakdown, or large detail components.
  - Settings is lazy-loaded as a separate frontend chunk.
  - Contract tests guard the new structure.

### Slice 0.6.3.6: Frontend CSS, i18n, and model boundary modularization

- Status: `Done`
- Goal: Finish the frontend maintainability cleanup by separating feature CSS, i18n resources, and ICP Radar model helpers without breaking the design-system token order or visual smoke flows.
- User value: Developers can edit styles and translations for one product area without scanning thousands of unrelated lines.
- Scope:
  - Split `frontend/src/styles.css` into app shell/shared primitives and feature-scoped CSS files.
  - Preserve `ui-design-system/colors_and_type.css` as the first token import.
  - Split `frontend/src/i18nResources.ts` into language or feature resource modules while preserving EN/RU parity checks.
  - Split ICP Radar model helpers into typed boundaries for model constants, validation scoring, live-radar helpers, radar metadata/status helpers, and settings definition helpers.
  - Add tests that enforce token import order, feature CSS ownership, model boundaries, and i18n resource coverage.
  - Run visual smoke after CSS movement.
- Out of scope:
  - New product behavior.
  - UI redesign.
  - Backend changes.
- Tests:
  - `npm --prefix ./frontend run build`
  - `python -m pytest`
  - `npm --prefix ./frontend run settings:toggle-smoke`
  - `npm --prefix ./frontend run visual:smoke`
- Docs:
  - Updated frontend architecture/developer documentation and feature-boundary ADR.
- Acceptance criteria:
  - ICP Radar CSS lives in `frontend/src/features/icp-radar/icpRadar.css`.
  - Runtime i18n initialization stays small and imports language resource modules.
  - `frontend/src/features/icp-radar/model.tsx` is a barrel over focused model modules.
  - Contract tests guard feature CSS ownership, i18n split, lazy Settings, and model boundaries.

### Slice 0.6.3.7: ICP Radar component granularity and commentary pass

- Status: `Done`
- Goal: Finish the refactor-hardening pass by reducing the remaining large ICP Radar component files and adding targeted comments around non-obvious data adaptation paths.
- User value: New developers can safely change candidate views, live views, and settings blocks without reading 700-900 line files.
- Scope:
  - Split `candidateViews.tsx`, `liveCandidateViews.tsx`, and `settings.tsx` where they still mix table, preview, detail, and block-editor responsibilities.
  - Keep public imports stable through feature barrels where useful.
  - Add concise module and complex-block comments for adapters, review-state transitions, and table-preview-detail invariants.
  - Add architecture tests for maximum feature-component file size and required module-boundary comments.
- Out of scope:
  - Product behavior changes.
  - Visual redesign.
  - Backend/schema changes.
- Tests:
  - `npm --prefix ./frontend run build`
  - `python -m pytest`
  - `npm --prefix ./frontend run settings:toggle-smoke`
- Docs:
  - Updated feature-boundary ADR and developer/architecture documentation.
- Acceptance criteria:
  - `candidateViews.tsx`, `liveCandidateViews.tsx`, and `model.tsx` are stable barrel modules.
  - Fixture table, fixture preview, fixture detail, live table, live detail, and settings blocks live in separate modules.
  - Architecture tests enforce file-size boundaries and required module-boundary comments.

### Slice 0.6.3.8: ICP Radar application boundary and adapter cleanup

- Status: `Done`
- Goal: Move ICP Radar from component-level decomposition to explicit application boundaries with hooks, adapters, and domain helpers.
- User value: Engineers can add or change radar data sources without pushing storage, scoring, and artifact-branching logic back into the screen component.
- Scope:
  - Add `domain/`, `adapters/`, `application/`, and `components/` boundaries inside the ICP Radar feature.
  - Introduce canonical `RadarViewModel` and `RadarCandidateViewModel` adapters for fixture, live, and empty radar states.
  - Move navigation state, localStorage overlays, settings draft actions, and review actions into application hooks.
  - Move catalog and radar detail header presentation into feature components.
  - Keep React functional; apply OOP principles through module ownership, contracts, adapters, hooks, and pure domain functions.
- Out of scope:
  - Backend artifact changes.
  - Visual redesign.
  - CSS decomposition beyond import-path preservation.
  - New product behavior.
- Tests:
  - `npm --prefix ./frontend run build`
  - `python -m pytest`
  - `npm --prefix ./frontend run settings:toggle-smoke`
  - `npm --prefix ./frontend run visual:smoke`
- Docs:
  - Updated frontend architecture/developer documentation and feature-boundary ADR.
- Acceptance criteria:
  - `frontend/src/features/icp-radar/ICPRadarScreen.tsx` stays below 250 lines.
  - Screen orchestration no longer owns localStorage, scoring rules, or raw fixture/live mapping.
  - Architecture tests guard application/adapters/domain/components boundaries.
  - Fixture and live radars keep the same table-preview-detail UX.

### Slice 0.6.3.9: ICP Radar CSS decomposition

- Status: `Done`
- Goal: Split the large ICP Radar feature stylesheet into readable style modules without changing UI behavior.
- User value: Engineers can adjust table, preview, detail, settings, and catalog styling without searching through a multi-thousand-line CSS file.
- Scope:
  - Keep one feature CSS entrypoint for imports.
  - Split styling by surface: catalog/header, shortlist/table, preview, detail tabs, settings, and responsive rules.
  - Preserve design-system token usage and current visual smoke output.
  - Add architecture tests for CSS module ownership and maximum file sizes.
- Out of scope:
  - Visual redesign.
  - New responsive behavior.
  - Component or domain refactor.
- Tests:
  - `npm --prefix ./frontend run build`
  - `python -m pytest`
  - `npm --prefix ./frontend run settings:toggle-smoke`
  - `npm --prefix ./frontend run visual:smoke`
- Docs:
  - Updated frontend architecture/developer docs and feature-boundary ADR for CSS module ownership.
- Acceptance criteria:
  - `icpRadar.css` becomes an import entrypoint or stays small enough to scan.
  - No ICP Radar selectors move back to global `styles.css`.
  - Visual smoke confirms no layout regression.

### Slice 0.6.3.10: Frontend documentation and onboarding comments

- Status: `Done`
- Goal: Add feature-local onboarding documentation and targeted boundary comments for the decomposed ICP Radar frontend.
- User value: Engineers can safely extend ICP Radar without rediscovering the adapter/application/domain boundaries or creating radar-specific UI forks.
- Scope:
  - Add `frontend/src/features/icp-radar/README.md` with ownership map, Mermaid data flow, extension guide, and change checklist.
  - Add short module-level comments to key adapter/application boundary files.
  - Add architecture contract tests for the README and required ownership comments.
  - Update developer, architecture, and ADR documentation.
- Out of scope:
  - Product behavior changes.
  - Backend artifact changes.
  - CSS or visual changes.
  - Wiki screenshot updates.
- Tests:
  - `python -m pytest tests/test_frontend_architecture_contract.py`
  - `python -m pytest`
  - `npm --prefix ./frontend run build`
- Docs:
  - Updated `docs/developer/DEVELOPER_GUIDE.md`.
  - Updated `docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md`.
  - Updated `docs/adr/2026-06-15-frontend-feature-module-boundaries.md`.
- Acceptance criteria:
  - ICP Radar has a local README explaining how to add a new radar type through adapters and canonical view models.
  - Contract tests guard the README and boundary-comment expectations.
  - No user-visible UI behavior changes.

### Slice 0.6.3.11: Qualification detail UX and requirement evaluation cleanup

- Status: `Done`
- Goal: Make the live ICP Radar candidate qualification tab readable, evidence-backed, localized, and reviewable.
- User value: A reviewer can understand why a candidate passed each qualification rule, which sources were used, how reliable they are, and can approve, reject, or correct the local qualification decision.
- Scope:
  - Keep the collapsed qualification table scan-first by removing requirement strictness from the row and moving it into the expanded detail.
  - Render source ref, source title, origin, trust/check policy, and evidence usage as separate fields.
  - Localize cross-validation and requirement-fit copy instead of showing raw provider text.
  - Add a requirement-fit view model that ties rule strictness, evidence strength, final assessment, confidence, and recommended human action together.
  - Replace the raw review form with a segmented review panel and full-width comment field.
- Out of scope:
  - Backend live workflow changes.
  - Generated artifact schema changes.
  - Durable backend audit or persistence.
- Tests:
  - `npm --prefix ./frontend run build`
  - `python -m pytest`
  - `npm --prefix ./frontend run visual:smoke`
- Docs:
  - Updated user/developer docs and ICP Radar feature README.
- Acceptance criteria:
  - No qualification badges or source fields overflow their containers.
  - Cross-validation and requirement-fit sections use EN/RU i18n labels.
  - Reject/correct qualification decisions require a comment; approve can use the default local comment.

### Slice 0.6.3.12: Qualification evidence cards and integrated requirement fit

- Status: `Done`
- Goal: Remove duplicate qualification evidence/source sections and make expanded qualification rows read as one evidence-backed decision chain.
- User value: A reviewer sees what was found, where it came from, what fragment supports it, why it matches the rule, and how that affects the final qualification decision without scanning duplicate blocks.
- Scope:
  - Replace separate expanded `Evidence` and `Sources used` blocks with evidence cards that include source ref, source name, origin, trust/check policy, fact, excerpt/fallback, match rationale, and evidence strength.
  - Integrate cross-validation status into the `Requirement fit` block.
  - Add optional `excerpt` / `excerpt_type` to qualification evidence findings while keeping old artifacts compatible.
  - Update live workflow prompt/normalizer to preserve short reviewable excerpts when returned.
- Out of scope:
  - Live provider changes.
  - Ranking/scoring changes.
  - Backend persistence for review decisions.
- Tests:
  - `npm --prefix ./frontend run build`
  - `python -m pytest`
  - `npm --prefix ./frontend run visual:smoke`
- Docs:
  - Updated user/developer docs, qualification ADR, and ICP Radar feature README.
- Acceptance criteria:
  - Expanded qualification rows do not duplicate source lists.
  - Evidence cards remain readable at laptop widths.
  - Cross-validation appears inside requirement fit.
  - Existing live artifacts without excerpts still render controlled fallback copy.

### Slice 0.6.3.13: Signal evidence cards and score evaluation cleanup

- Status: `Done`
- Goal: Apply the same evidence-card and review-panel standard to live candidate intent signals.
- User value: A reviewer can understand each signal as a chain: signal definition, found fact, source, excerpt/fallback, why it matches, why the score applies, confidence, and the human decision.
- Scope:
  - Replace the minimal expanded signal view with `Signal score evaluation`, evidence cards, and a human review panel.
  - Add optional signal `source_usages`, `evidence_findings`, `cross_validation`, and `score_evaluation` fields while keeping old artifacts compatible.
  - Update the live workflow prompt/normalizer to preserve signal excerpts and score rationale when provider output includes them.
  - Reuse the existing browser-local signal validation overlay for confirm/reject/stale/correct decisions.
- Out of scope:
  - Ranking formula changes beyond existing effective-score validation semantics.
  - UI run button, scheduler, persistence, or provider changes.
  - Full source inventory inside expanded signal rows; it remains in the `Sources` tab.
- Tests:
  - `npm --prefix ./frontend run build`
  - `python -m pytest`
  - `npm --prefix ./frontend run visual:smoke`
- Docs:
  - Updated user/developer docs, qualification/evidence ADR, and ICP Radar feature README.
- Acceptance criteria:
  - Expanded signal rows start with score evaluation and then evidence cards.
  - Signal evidence cards separate source ref/title, excerpt/fallback, why-signal, and why-score text.
  - Reject/stale/correct signal decisions require comments; confirm can use a default local comment.

### Slice 0.6.4: Take-into-work handoff from ICP Radar to Power Web

- Status: `Done`
- Goal: Add the first handoff from an ICP Radar candidate into the existing Power Web / Access Plan loop.
- User value: A user can decide which scored candidates deserve real account work instead of generating Power Webs for every found company.
- Scope:
  - Add candidate states: `monitoring`, `ready`, `accepted`, `rejected`, `snoozed`.
  - Add a `Take into work` action for accepted candidates.
  - Generate or map an accepted candidate into the existing account fixture shape.
  - Show accepted accounts in the existing `Accounts` workspace.
  - Keep unaccepted candidates in the ICP Radar queue.
- Out of scope:
  - Full CRM sync.
  - Persistent assignment workflow.
  - Bulk accept/reject.
- Implementation notes:
  - The handoff boundary should be explicit: ICP Radar decides account priority; Power Web starts only after acceptance.
- Tests:
  - Unit tests for candidate state transitions.
  - Smoke test from ICP Radar candidate -> accepted account -> Access Plan artifact.
  - Frontend contract test for `Take into work` and candidate state.
- Docs:
  - Update user/developer/demo docs with the handoff flow.
- Demo impact:
  - Demo becomes a fuller ABM loop: ICP profile -> candidates -> accepted account -> Power Web -> Access Plan.
- Acceptance criteria:
  - Accepted candidates appear in the Accounts workspace.
  - Rejected/snoozed candidates do not generate Power Web work.
  - The handoff remains explainable and reversible in demo state.
- Risks:
  - Handoff can pull in persistence too early; keep first implementation artifact/local-state based.

### Slice 0.6.5: Editable ICP Radar configuration loop

- Status: `Done`
- Goal: Add the first editable radar configuration workflow over frontend local demo state.
- User value: A user can create a new ICP Radar, edit an existing radar configuration, save a local draft, discard changes, duplicate a radar, and reset demo changes without implying production persistence.
- Scope:
  - Add `Create radar` in the ICP Radar catalog.
  - Add local `draft/local` and `modified locally` states for radars created or changed in the browser.
  - Add `View` / `Edit` modes to selected-radar `Settings`.
  - Add editable controls for radar name, owner, profile, discovery, monitoring, cadence, lookback window, run mode, tier thresholds, and C1-C20 criterion names/descriptions/scoring guidance.
  - Keep scoring formula display constrained/read-only while thresholds and criteria guidance are editable.
  - Store created/edited radar definitions in browser `localStorage` under `power-web-os-icp-radar-config-overrides`.
  - Add `Save draft`, `Discard changes`, `Duplicate radar`, `Reset to artifact`, and `Reset demo changes`.
  - Keep generated artifacts read-only and leave the fixture-backed shortlist unchanged after settings edits.
- Out of scope:
  - Multi-user configuration governance.
  - Production database persistence.
  - Live connector configuration secrets.
  - Arbitrary formula scripting.
  - Live radar execution or shortlist recalculation from edited settings.
- Implementation notes:
  - Use constrained form controls, not free-form executable formulas.
  - Keep original fixture configuration recoverable.
  - Clearly label saved browser-only changes as local demo drafts.
  - Keep `0.6.3` signal validation and `0.6.4` take-into-work next in the product sequence.
- Tests:
  - Frontend contract tests for edit mode, validation errors, localStorage overlay, create/save/discard/duplicate/reset actions, no API calls, and local draft labels.
  - `python -m pytest`.
  - `npm --prefix ./frontend run build`.
- Docs:
  - Update user/developer/demo docs with editable configuration, local demo persistence, and reset behavior.
- Demo impact:
  - Demo shows radar setup as a controllable ABM object, not only a report.
- Acceptance criteria:
  - User can create and edit constrained radar settings locally.
  - Invalid drafts block saving and show inline validation.
  - Saved local drafts appear in the catalog and are labelled as local/demo state.
  - User can reset to fixture configuration.
- Risks:
  - Users may expect production persistence; label local/demo persistence clearly.

### Slice 0.6.5.1: ICP Radar definition model correction

- Status: `Done`
- Goal: Replace the flat ICP Radar settings model with an executable definition model that separates human metadata, shared source policy, account qualification rules, intent signals, monitoring policy, scoring, and validation.
- User value: A user can understand and locally edit how a radar is actually configured: which accounts qualify, which signals matter, which sources are trusted, how signals are scored, and whether the configuration is structurally valid.
- Scope:
  - Replace the old `RadarDefinition` artifact contract with `metadata`, `global_search_policy`, `account_qualification`, `intent_signals`, `monitoring_policy`, `scoring_model`, and `validation_report`.
  - Model sources as typed entities (`url`, `search_engine`, `api`, `mcp`, `manual_dataset`) instead of textarea-only references.
  - Model account qualification as `RuleGroup` + `AtomicRule` with `AND` / `OR` / `NOT`, requirement level, and per-rule source policy.
  - Model C1-C20 as intent signals with trigger rules and a fixed `0/1/2` scoring rubric.
  - Add `RadarDefinitionValidator` for required fields, duplicates, invalid operators, source-policy misuse, `NOT` misuse, and simple numeric contradictions.
  - Rebuild the Settings UI as block-level editing for Overview, Global search base, Account qualification rules, Monitoring, Intent signals, Scoring model, and Validation.
  - Keep browser-local draft persistence and do not add backend persistence, scheduler, connectors, or shortlist recalculation.
- Out of scope:
  - Production persistence or audit log for radar definitions.
  - Live API/MCP connector execution.
  - Semantic validation against industry dictionaries.
  - Recalculating the XLSX-derived shortlist after settings edits.
- Implementation notes:
  - The artifact contract intentionally moves to `0.6.5.1`; no parallel `definition_v2` is kept.
  - Qualification filters and intent signals are different domain concepts and must remain separate in future slices.
  - Validator findings are part of the artifact/UI contract, but conservative: structural checks first, domain semantics later.
- Tests:
  - Unit tests for new definition serialization and validator cases.
  - Frontend contract tests for block-level settings, rule builder, source editor, intent signal editor, scoring model, validation report, and i18n keys.
  - `python -m pytest`.
  - `npm --prefix ./frontend run build`.
- Docs:
  - Add ADR for separating qualification rules from intent signals.
  - Update architecture, developer, user, and demo docs with the new rule/signal definition model.
- Demo impact:
  - The active `ТОиР / SIBUR` radar now shows an inspectable executable definition instead of flat settings.
  - Local settings drafts now edit structured rules, sources, signals, scoring thresholds, and validation-aware blocks.
- Acceptance criteria:
  - Generated `icp_radar.json` and `icp_radars.json` use artifact version `0.6.5.1`.
  - `radar.definition.intent_signals[]` replaces old generic criteria in public definition.
  - Settings editing is block-level, not one global edit mode.
  - Validation report is visible and generated by the domain validator.
- Risks:
  - The first rule builder is intentionally constrained; production connector execution and semantic validation remain future work.

### Slice 0.6.5.2: ICP Radar settings UX and scoring model correction

- Status: `Done`
- Goal: Keep the structured radar definition model, but make `Settings` usable for ABM/sales users instead of exposing developer-facing IDs, field/operator/value controls, and overloaded trigger/total formulas.
- User value: A user can configure a radar in business language: what accounts to qualify, where to search, what signals indicate interest, how each signal is scored, and how fit/intent/tier are calculated.
- Scope:
  - Stack `Overview` and `Global search base` vertically and make source rows wrap/ellipsis correctly without overlap.
  - Keep source, rule, and signal IDs system-generated; show compact generated IDs/codes only where they help explain custom formulas.
  - Replace editable `target field` / `comparison operator` / `value` controls with natural-language rule names and descriptions.
  - Let rule/signal source policies select shared sources by name, add local sources as entities, use the global search base, and allow system-selected additional sources.
  - Show signal scoring as a fixed `0 / 1 / 2` rubric table instead of large textarea cards.
  - Replace trigger/total settings with `Fit`, `Intent`, and `Tier` models.
  - Add scoring preset dropdowns: arithmetic mean, weighted average, maximum signal, capped sum, and custom formula.
  - Show custom formula text input only when the custom preset is selected.
  - Replace the raw validation counter block with a compact valid/issue summary grouped by settings block.
- Out of scope:
  - Live radar execution.
  - Backend persistence.
  - Scheduler or connector secrets.
  - Recalculating the existing XLSX-derived shortlist from edited settings.
- Implementation notes:
  - The artifact contract intentionally moves to `0.6.5.2`.
  - Candidate score fields still keep historical workbook-compatible `fit_score`, `intent_score`, `trigger_score`, and `total_score` for backward compatibility.
  - Settings UI must not present `trigger` or `total` as configurable radar concepts.
  - Generated technical fields may remain in the artifact for future agent execution, but they are not user-authored controls.
- Tests:
  - Python validator tests for generated IDs, empty source policy choices, invalid formula presets, and invalid custom formula references.
  - Frontend contract tests for no editable target/comparison/value controls, source selection by name, local source editor, scoring presets, and no trigger/total settings UI.
  - `python -m pytest`.
  - `npm --prefix ./frontend run build`.
- Docs:
  - Update ADR, architecture, developer, user, and demo docs with description-first rules, source policies, fit/intent/tier scoring, and generated IDs.
- Demo impact:
  - Radar Settings reads as a business configuration surface rather than a developer schema editor.
- Acceptance criteria:
  - Generated `icp_radar.json` and `icp_radars.json` use artifact version `0.6.5.2`.
  - Source rows do not overlap and Settings no longer has a two-equal-column Overview/Search layout.
  - Rule and signal editors do not expose editable IDs or field/operator/value controls.
  - Scoring UI exposes only Fit, Intent, and Tier with preset selection.
- Risks:
  - The source/rule editors are still local demo state; production execution and audit remain future work.

### Slice 0.6.5.3: ICP Radar settings UX simplification

- Status: `Done`
- Goal: Simplify ICP Radar Settings for sales/ABM users by removing duplicate description blocks, rule groups, source-logic complexity, and technical confidence labels from the visible editor.
- User value: A user can configure a radar without understanding internal IDs, rule groups, fallback confidence, or source operators: they edit the radar header, source base, simple account criteria, monitoring policy, signal list, global signal scale, and scoring presets.
- Scope:
  - Move radar name, description, active/inactive status, owner, run mode, duplicate, and delete actions into the selected radar header.
  - Remove the separate Overview/Description Settings block.
  - Show global source base as a bounded table with columns for name, type, reference, trust policy, and action.
  - Bound keyword and exclusion lists in view mode and show exclusions outside edit mode.
  - Add AI suggestion affordances to global source base and account qualification blocks.
  - Simplify account qualification to a flat criterion list with `AND` / `OR`, optional `NOT`, natural-language rule text, requirement level, global-base checkbox, additional-source checkbox, cross-validation policy, and optional local sources.
  - Remove visible rule groups, source logic operators, source id selection, fallback confidence labels, and source ID editing from Settings.
  - Replace low/medium/high with user-facing trust policies: trusted, cross-check, and HITL required.
  - Replace monitoring free-text dedup/lookback/stale fields with dropdown policy plus number/unit controls.
  - Simplify intent signals to the same source/rule model as account criteria.
  - Add a global signal scoring scale block and per-signal override checkbox; default scale remains `0 / 1 / 2`.
  - Fix the source editor focus bug by keeping stable UI keys while editing and generating IDs only from saved/source content.
  - Fix RU `???`/mojibake in the touched Settings labels.
- Out of scope:
  - Live AI generation.
  - Backend persistence.
  - Running edited settings against sources.
  - Recalculating shortlists from edited criteria/signals.
  - Full mobile redesign beyond keeping this Settings surface bounded and readable.
- Implementation notes:
  - The backend may keep `RuleGroup`, `AtomicRule`, and generated technical fields as normalized internal structure.
  - The frontend should use a simpler view model over the existing definition rather than exposing nested groups directly.
  - AI suggestion buttons are non-executing affordances in this slice and should be labelled as planned/local assistance.
  - Artifact version can remain `0.6.5.2` unless the persisted JSON shape changes.
- Tests:
  - Frontend contract tests for no Overview block, no visible rule-group editor, no source logic UI, no fallback confidence UI, bounded source table, monitoring number/unit controls, global signal scale, and per-signal override affordance.
  - i18n contract checks that touched RU Settings labels do not contain `???`.
  - `python -m pytest`.
  - `npm --prefix ./frontend run build`.
- Docs:
  - Update user/developer/demo docs and configurable-object UX ADR with the simplified Settings model.
- Demo impact:
  - The Settings tab becomes a usable sales-facing radar configuration surface instead of a domain-schema editor.
- Acceptance criteria:
  - Radar header is the only place where name/status/description are edited.
  - Global sources render as a readable table with bounded scroll and no overlap.
  - Qualification criteria and intent signals are flat, natural-language lists without visible groups.
  - Monitoring policies use dropdowns and numeric duration controls.
  - Source editor inputs keep focus while typing.
- Risks:
  - The simplified UI is a view model over the internal contract; future persistence should formalize this view model instead of letting UI helpers sprawl.

### Slice 0.6.5.4: ICP Radar settings layout and signal editor polish

- Status: `Done`
- Goal: Polish the current ICP Radar Settings UX without changing the backend artifact contract.
- User value: A user can edit radar settings from the radar header and scan source, qualification, and signal settings without misaligned tables, duplicated action rows, oversized signal-scale editors, or broken switches.
- Scope:
  - Move Settings edit/save/discard/duplicate/delete/reset actions into the selected radar header.
  - Show radar description in the selected-radar header instead of generated shortlist summary copy while configuring the radar.
  - Remove the separate Settings action row.
  - Show global search sources as a bounded numbered table and move additional system sources to the end of the block as a switch.
  - Keep keywords and exclusions as bounded list blocks.
  - Render qualification rules as a table with operator, rule, source summary, cross-check, additional-source, and requirement columns.
  - Render intent signals as a table with code, detection rule, source summary, cross-check, additional-source, and scale-override columns.
  - Move signal scale into its own compact Settings block.
  - Use one switch component style for boolean settings in these blocks.
- Out of scope:
  - Backend schema changes.
  - Live AI suggestion generation.
  - Running edited radar settings against sources.
  - Recalculating the shortlist.
- Tests:
  - Frontend contract tests for header-owned actions, no standalone Settings action row, numbered source table, table summaries, separate signal-scale block, and EN/RU labels.
  - `npm --prefix ./frontend run build`.
  - `python -m pytest`.
  - `npm --prefix ./frontend run visual:smoke`.
- Docs:
  - Update user/developer/demo docs with header-owned Settings actions, source table, rule table, signal table, and signal scale block.
- Demo impact:
  - The Settings tab stays browser-local and read/write in demo state, but becomes more readable on laptop screens.
- Acceptance criteria:
  - Settings has no global action row outside blocks/header.
  - Header owns radar metadata editing and lifecycle actions.
  - Global search sources, qualification rules, and intent signals do not visually overlap.
  - Signal scale is compact and separate from the signal list.
- Risks:
  - The Settings UI is still a frontend view model over the existing artifact contract; future persistence should formalize the same simplified model.

### Slice 0.6.5.5: ICP Radar settings header and switch polish

- Status: `Done`
- Goal: Fix the remaining ICP Radar Settings header/action layout and switch behavior after Slice 0.6.5.4.
- User value: A user can edit radar metadata and block settings without confusing header action placement, duplicated monitoring metadata, malformed bounded list headings, or broken switch interactions.
- Scope:
  - Keep all selected-radar actions in the top-right header action row.
  - Move status/local/draft/read-only metadata to the left header content under the radar description.
  - Remove run mode from the selected-radar header; monitoring mode belongs only in the Monitoring settings block.
  - Keep header edit mode structurally close to view mode: name, description, then active status/owner metadata.
  - Fix bounded keyword/exclusion section alignment so labels do not stretch vertically.
  - Fix switch geometry so the active thumb stays inside the track.
  - Guard disabled switches from firing state changes.
  - Normalize generated and localStorage radar definitions before render/edit so legacy or partial browser-local drafts cannot crash Settings after a switch change.
- Out of scope:
  - Backend schema changes.
  - New radar settings fields.
  - Live AI suggestions.
  - Recalculating shortlist or monitoring runs.
- Tests:
  - Frontend contract tests for header metadata/action separation, no header run-mode copy, bounded list alignment, switch geometry, and disabled-switch guard.
  - `npm --prefix ./frontend run settings:toggle-smoke`, including persisted draft reload, legacy localStorage override cases, and explicit viewport assertions so switching controls cannot scroll the fixed SPA shell out of view.
  - `npm --prefix ./frontend run build`.
  - `python -m pytest`.
  - Browser smoke for Settings switches.
- Docs:
  - Update user/developer docs with header action placement, monitoring metadata ownership, and switch interaction rules.
- Demo impact:
  - The Settings tab is visually cleaner and less fragile on laptop screens.
- Acceptance criteria:
  - Header actions are consistently top-right.
  - Status and owner metadata remain with the radar description on the left.
  - Header does not repeat incremental monitoring state.
  - Switches do not crash the screen and active switch geometry is correct.
- Risks:
  - Switch regressions may be browser-specific; mitigate with Playwright smoke for header and block switches.

### Slice 0.6.6: ICP Radar run history and monitoring schedule loop

- Status: `Done`
- Goal: Show how configured radars run over time and distinguish full discovery from incremental signal monitoring.
- User value: A user can understand when the radar last ran, what changed, which signals are new, and how candidate scores moved since the previous run.
- Scope:
  - Add run history read model with run id, mode, started/completed timestamps, source scope, candidate count, new signals, stale signals, and score deltas.
  - Add a read-only run history view inside ICP Radar.
  - Show current schedule/cadence and next planned run.
  - Distinguish one-time account discovery from recurring signal monitoring.
  - Add synthetic previous/current run fixtures for the ТОиР/SIBUR demo.
- Out of scope:
  - Real scheduler.
  - Background workers.
  - Live source deduplication.
  - Notifications.
- Implementation notes:
  - Incremental mode should explain which evidence was already known and which evidence is new.
  - Score deltas should be explainable from signal changes and validation state.
- Tests:
  - Unit tests for run history/delta read model.
  - Frontend contract tests for run history and schedule display.
  - `python -m pytest`.
  - `npm --prefix ./frontend run build`.
- Docs:
  - Update user/developer/architecture/demo docs with radar run history semantics.
- Demo impact:
  - Demo shows ICP Radar as an ongoing monitoring process, not a one-time spreadsheet import.
- Acceptance criteria:
  - User can see last run, next run, run mode, and score deltas.
  - New vs already-known evidence is visible.
  - Discovery and monitoring are clearly separated in UI copy.
- Risks:
  - Run history can imply real scheduling; keep first version synthetic/read-only.

## Backend Foundation Track

The backend is developed in parallel with the product roadmap. The goal is not
to rewrite the demo at once, but to move durable product state from generated
JSON and browser-local overlays into a persistent API-backed application layer
in small, testable slices.

Principles:

- Backend stack: Python, FastAPI, Pydantic, PostgreSQL, SQLAlchemy 2.x, Alembic.
- JSON artifacts remain demo/export/read fallback, not the long-term source of truth.
- LLM/search output is persisted as reviewable run evidence, not authoritative truth.
- Human review decisions are first-class domain records.
- Frontend data source differences are adapters; product UX must not branch by provider.
- Domain logic stays independent from HTTP, database, UI, and provider APIs.
- Backend growth must be guarded by architecture contracts, not only written guidance.
- API routes, worker tasks, and scheduler triggers are entrypoints only; they call application services.
- Application services own use cases and transactions; they do not contain provider-specific or HTTP-specific code.
- Domain services own scoring, validation, review semantics, and handoff rules; they do not import FastAPI, SQLAlchemy, Celery, Redis, HTTP clients, or provider SDKs.
- Repository interfaces are the application boundary; SQLAlchemy models and queries stay in persistence implementations.
- Provider adapters return typed observations and evidence; they do not decide candidate state or final truth.
- Workflow wrappers orchestrate and audit execution; they do not hide domain scoring, review, or persistence decisions.
- Large backend modules require decomposition into domain, application, API, persistence, integrations, workflows, and jobs boundaries.
- Long-running radar execution should use durable run state first, then an async worker adapter; Postgres remains the source of truth for run status and audit.

### Slice 0.7.0: Backend API foundation

- Status: `Done`
- Goal: Add the first production-oriented HTTP boundary without changing current demo behavior.
- User value: The project now has a real backend entrypoint that future persistence, run, and review APIs can grow from.
- Scope:
  - Add FastAPI application factory.
  - Add stable `/health` and `/api/health` contracts.
  - Add API settings boundary.
  - Add local API run command through `power-web-os-api`.
  - Add tests for health and OpenAPI contracts.
- Out of scope:
  - Database.
  - Auth.
  - Radar CRUD.
  - Live run persistence.
  - Frontend API migration.
- Tests:
  - `python -m pytest tests/test_backend_api.py`
- Docs:
  - Backend roadmap and stack documented in Roadmap, Architecture, ADR, README, and Developer Guide.
- Acceptance criteria:
  - API app imports without starting a server.
  - Health endpoint returns service, version, environment, and ok status.
  - OpenAPI is generated.
  - Existing demo and artifact flows are unchanged.

### Slice 0.7.0.1: Backend architecture guardrails

- Status: `Done`
- Goal: Prevent the backend from growing into large mixed-responsibility modules before persistence, jobs, and API contracts expand.
- User value: Future backend work remains reviewable, explainable, and safe to extend while Radar functionality moves from demo artifacts into durable state.
- Scope:
  - Add a backend architecture ADR covering module boundaries, OOP/SRP rules, and async job direction.
  - Update `docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md` with backend module ownership:
    - `api`: thin FastAPI routes, DTOs, dependency wiring;
    - `application`: use cases, transactions, orchestration;
    - `domain`: business rules, scoring, validation, review semantics, handoff rules;
    - `persistence`: SQLAlchemy models, sessions, repository implementations;
    - `integrations`: provider/source/CRM adapters;
    - `workflows`: LangGraph workflow wrappers and workflow state;
    - `jobs`: worker and scheduler entrypoints.
  - Update `.agents` skills so backend implementation work explicitly checks OOP boundaries, module ownership, repository isolation, and architecture contract tests.
  - Update developer/contributor docs with backend extension rules.
  - Add `tests/test_backend_architecture_contract.py` to guard:
    - domain modules do not import FastAPI, SQLAlchemy, Celery, Redis, HTTP clients, or provider SDKs;
    - API route modules do not own SQLAlchemy queries or domain scoring;
    - persistence modules do not import FastAPI;
    - job modules call application services instead of owning business logic;
    - backend modules stay under agreed file-size thresholds unless explicitly allowlisted with a reason;
    - existing large legacy modules are listed as decomposition follow-ups, not treated as the pattern for new code.
- Out of scope:
  - Moving all existing Python modules into the new folder structure.
  - Adding SQLAlchemy/Alembic schema.
  - Adding Celery/Redis runtime dependencies.
  - Refactoring `live_icp_radar.py` completely.
- Implementation notes:
  - Treat this as governance hardening, similar to the ICP Radar frontend architecture contract.
  - At the time of this slice, `live_icp_radar.py`, `icp_radar.py`, and `icp_radar_catalog.py` were acknowledged as legacy-large modules with follow-up decomposition tasks; live Radar extraction was completed later in `Slice 0.7.1.2`.
  - New backend work after this slice must use the documented boundary structure.
  - The async decision should be explicit: durable run state and queue ports first; Celery/Redis as a production adapter later.
- Tests:
  - `python -m pytest tests/test_backend_architecture_contract.py`
  - `python -m pytest tests/test_backend_api.py`
  - `python -m pytest`
- Docs:
  - Update backend ADRs, architecture overview, developer guide, contributor guide, `.agents` skills, and `ROADMAP.md`.
- Demo impact:
  - No user-visible demo behavior changes.
- Acceptance criteria:
  - Backend module boundaries and OOP rules are documented in ADR and SAO.
  - Agent skills include backend-specific governance checks.
  - Architecture tests fail on obvious cross-layer imports or new backend god modules.
  - `Slice 0.7.1` can start with clear persistence/application/domain boundaries.
- Completed:
  - Added backend boundary ADR and ADR index entry.
  - Documented backend ownership, OOP/SRP rules, dependency direction, and async job direction in SAO and developer/contributor docs.
  - Updated local agent skills with backend boundary checks.
  - Added backend architecture contract tests with a temporary legacy-large module allowlist.
- Risks:
  - Overly strict tests can block practical incremental work; mitigate with focused rules and explicit temporary allowlists.

### Slice 0.7.1: Persistence foundation

- Status: `Done`
- Goal: Add PostgreSQL-ready persistence boundaries for radars, definitions, and runs.
- User value: ICP Radar state can begin moving from artifacts/localStorage toward durable backend records.
- Scope:
  - Add SQLAlchemy 2.x and Alembic.
  - Add DB settings and session lifecycle.
  - Add tables for `radars`, `radar_definitions`, and `radar_runs`.
  - Add repository interfaces and Postgres-backed implementations.
  - Add deterministic seed command for current demo radars.
  - Add durable run status fields that later async workers can update: queued/running/waiting_human/completed/failed/cancelled, timestamps, idempotency key, correlation id, and error metadata.
  - Add application-level ports for `JobQueue`, `RadarRunExecutor`, and `RadarRunScheduler` without requiring Celery/Redis yet.
- Out of scope:
  - Frontend API migration.
  - Live run execution through API.
  - Production async worker runtime.
  - Auth and multi-user tenancy.
- Tests:
  - Unit tests for repository interfaces.
  - Migration smoke test.
  - Contract tests that application code depends on repositories/ports instead of SQLAlchemy details.
  - `python -m pytest`.
- Acceptance criteria:
  - Database schema is migration-managed.
  - Domain/application code depends on repository contracts, not raw SQL.
  - Durable run records are ready for CLI/API/worker execution paths.
  - Generated JSON artifacts remain available as demo/export fallback.
- Completed in this slice:
  - Added SQLAlchemy/Alembic persistence foundation with `radars`, `radar_definitions`, and `radar_runs`.
  - Added application records, repository ports, and async job ports without Celery/Redis runtime.
  - Added SQLAlchemy repository adapters, DB settings/session lifecycle, and initial migration.
  - Added deterministic `seed-radar-db` command for current demo radars and active definitions.
  - Added SQLite-based repository and migration smoke tests plus application boundary checks.
- Validation:
  - `python -m pytest tests/test_radar_persistence.py`
  - `python -m pytest tests/test_backend_architecture_contract.py`
  - `python -m pytest tests/test_backend_api.py`
  - `python -m pytest`

### Slice 0.7.1.1: Backend developer onboarding guardrails

- Status: `Done`
- Goal: Make backend layer ownership discoverable close to the code before the next backend/product slice extends persistence or APIs.
- User value: Developers and agents can safely extend backend functionality without guessing where records, ports, SQLAlchemy adapters, migrations, and job boundaries belong.
- Scope:
  - Add local onboarding docs for `application` and `persistence` layers.
  - Add concise module docstrings to key backend application/persistence modules.
  - Add targeted comments for non-obvious persistence decisions: payload-based seed mapping, durable run state, SQLite timezone normalization, and session ownership.
  - Extend SAO, Developer Guide, ADR, and local agent skills so future backend work must keep ownership docs current.
  - Extend backend architecture contract tests to guard local README docs and module docstrings.
- Out of scope:
  - New API endpoints.
  - New tables or migrations.
  - Celery/Redis runtime.
  - Legacy Radar module decomposition.
- Tests:
  - `python -m pytest tests/test_backend_architecture_contract.py`
  - `python -m pytest tests/test_radar_persistence.py`
  - `python -m pytest`
- Acceptance criteria:
  - A developer can start from local layer README files and understand backend extension rules.
  - Architecture contract tests fail if active backend onboarding docs or key module docstrings disappear.
  - Agent skills require local backend ownership docs when backend boundaries change.

### Slice 0.7.1.2: Live Radar backend extraction

- Status: `Done`
- Goal: Decompose the live ICP Radar path into backend-owned layers without changing CLI behavior, artifact shape, or OpenRouter semantics.
- User value: Engineers can extend live Radar toward persisted execution without pulling a large provider/workflow/normalization module into API or persistence work.
- Scope:
  - Split `live_icp_radar.py` into application contracts, live Radar definition/search plan, provider-neutral normalization, live run service, OpenRouter integration adapter, and workflow wrapper.
  - Keep `live_icp_radar.py` as a compatibility facade for existing demo/tests imports.
  - Preserve the `icp_radar_live_run` artifact version and structure.
  - Add local `integrations` and `workflows` README files.
  - Remove `live_icp_radar.py` from the legacy-large architecture allowlist.
- Out of scope:
  - Persisting live candidates/evidence.
  - Adding new database schema.
  - Adding API endpoints.
  - Adding Celery/Redis runtime.
  - Frontend behavior changes.
- Tests:
  - `python -m pytest tests/test_live_icp_radar.py`
  - `python -m pytest tests/test_backend_architecture_contract.py`
  - `python -m pytest tests/test_radar_persistence.py`
  - `python -m pytest`
- Acceptance criteria:
  - Existing live Radar CLI and tests keep producing the same artifact contract.
  - Live provider code lives under `integrations`, LangGraph wrapper under `workflows`, and normalization/service code under `application`.
  - `live_icp_radar.py` is below the backend module size threshold and is no longer allowlisted.

### Slice 0.7.1.3: Remaining Radar legacy module decomposition follow-up

- Status: `Done`
- Goal: Decompose remaining legacy-large Radar modules after live Radar extraction.
- User value: Engineers can extend fixture import, catalog generation, and evidence normalization without reintroducing backend god modules.
- Scope:
  - Split `icp_radar.py`, `icp_radar_catalog.py`, and `icp_radar_xlsx.py` only where ownership becomes clear after `Slice 0.7.1.2`.
  - Remove modules from the backend architecture contract allowlist as they fall below the threshold.
- Out of scope:
  - Changing public artifact contracts.
  - Adding new persistence schema beyond planned backend slices.
  - Adding Celery/Redis runtime.
- Tests:
  - `python -m pytest tests/test_backend_architecture_contract.py`
  - Existing Radar tests affected by the decomposition.
- Acceptance criteria:
  - Decomposed modules follow application/domain/integration/workflow boundaries.
  - Legacy allowlist shrinks further.
  - Existing demo artifacts remain compatible.

### Slice 0.7.2: Persisted live Radar run MVP

- Status: `Done`
- Goal: Make the extracted live Radar backend path persist run state and live output snapshots instead of writing only JSON artifacts.
- User value: Backend can reproduce the current live script capability with durable run status and reviewable candidate/source/signal data ready for API and worker execution.
- Scope:
  - Add persistence records/repositories for live run output snapshots: search plan, sources, candidates, qualification results, signal results, evidence cards, warnings, and run metadata.
  - Add an application service that creates a `radar_runs` record, executes the live Radar service, persists completed/failed state, and can export the existing JSON artifact shape.
  - Add a backend CLI path for persisted live run execution while keeping the existing non-persisted demo command working.
  - Keep OpenRouter and future providers behind the provider-neutral boundary introduced in `Slice 0.7.1.2`.
- Out of scope:
  - API endpoints.
  - Celery/Redis runtime.
  - Frontend migration from JSON artifacts.
  - Human review persistence beyond storing provider output snapshots.
- Tests:
  - Repository tests for persisted live run output snapshots.
  - Application-service tests for queued/running/completed/failed transitions.
  - JSON export compatibility tests against the current live artifact contract.
  - `python -m pytest`.
- Acceptance criteria:
  - A live Radar run can be executed through backend application services and persisted as durable run state plus output snapshot.
  - Existing JSON artifact shape can be exported from persisted state.
  - No API, worker, or frontend dependency is required for the persisted MVP.
- Completion notes:
  - Added `radar_run_outputs` with JSON snapshots of the current live artifact sections.
  - Added persisted live Radar application service, repository/output ports, workflow-backed executor adapter, and persisted CLI command.
  - Kept existing `run-live-mini-icp-radar --live` behavior intact and additive.
  - Validated with repository, application service, live Radar, backend API, architecture contract, and full Python regression tests.

### Slice 0.7.3: Radar run and catalog API

- Status: `Done`
- Goal: Expose persisted radars and live run results through API contracts.
- Scope:
  - `GET /api/radars`.
  - `GET /api/radars/{radar_id}`.
  - `POST /api/radars/{radar_id}/runs`.
  - `GET /api/radar-runs/{run_id}`.
  - `GET /api/radar-runs/{run_id}/candidates`.
  - Contract tests and OpenAPI checks.
- Acceptance criteria:
  - Frontend can consume persisted Radar catalog and run results through an adapter while JSON remains fallback.
- Completion notes:
  - Added FastAPI Radar catalog, detail, temporary inline run, run detail, and candidate snapshot endpoints.
  - Added canonical candidate API DTOs backed by persisted `radar_run_outputs` snapshots.
  - Kept inline run execution temporary until the async worker adapter slice; superseded by `Slice 0.7.3.1`.
  - Validated with backend API, architecture contract, persistence/live Radar, and full Python regression tests.

### Slice 0.7.3.1: Async radar jobs and scheduler adapter

- Status: `Done`
- Goal: Add a production-oriented async execution adapter for long-running Radar jobs without moving source-of-truth state out of Postgres.
- User value: Live and scheduled Radars can run in the background with durable status, retries, audit, and later UI progress instead of blocking API or CLI requests.
- Scope:
  - Add Celery worker integration with Redis as broker/result transport.
  - Implement Celery-backed `JobQueue` adapter over the ports introduced in `Slice 0.7.1`.
  - Keep worker tasks thin: load run context, call application service, update durable run state/events.
  - Add scheduler adapter for recurring radar monitoring, initially disabled or local-only unless explicitly configured.
  - Add retry, timeout, cancellation-ready status semantics, and idempotency checks.
  - Document local worker commands and operational assumptions.
- Out of scope:
  - Full production deployment manifests.
  - UI run control.
  - Multi-tenant quotas.
  - Replacing Postgres run state with Celery result backend.
- Implementation notes:
  - FastAPI `BackgroundTasks` is not sufficient for Radar jobs because runs are long, retryable, scheduled, and must survive process restarts.
  - APScheduler alone is not enough as the execution queue, but may be used behind the scheduler adapter for local/dev cadence if needed.
  - Postgres remains the authoritative run state and audit log; Redis/Celery are execution infrastructure.
- Tests:
  - Unit tests for queue adapter behavior with eager/in-memory Celery mode.
  - Integration-style tests for run state transitions through the application service.
  - `python -m pytest`.
- Docs:
  - Update architecture, developer guide, and operations notes with worker/scheduler commands and failure semantics.
- Demo impact:
  - No frontend UI migration; API clients can create queued runs and poll durable run state.
- Acceptance criteria:
  - A Radar run can be enqueued through a port and executed by a worker adapter.
  - Durable `radar_runs` status changes are observable without trusting Celery result state.
  - Worker code does not own domain scoring, provider normalization, or persistence queries directly.
- Risks:
  - Celery/Redis can add local setup friction; mitigate with inline/eager adapters for tests and default demo flows.
- Completion notes:
  - Added Celery/Redis dependencies and a `jobs` layer with queue adapter, worker task, eager-test path, and local scheduler adapter.
  - Refactored persisted live Radar execution into queued-run creation and execute-existing-run application services.
  - Changed `POST /api/radars/{radar_id}/runs` to return `202 Accepted` with durable `queued` status; clients poll run detail and read candidates after output exists.
  - Kept `radar_runs` and `radar_run_outputs` as the source of truth; Celery messages carry only `run_id`.
  - Added job/worker, API polling, idempotency, and architecture contract coverage.

### Slice 0.7.4: Human review persistence

- Status: `Done`
- Goal: Persist qualification and signal review decisions in backend state.
- Scope:
  - Store approve/reject/correct/stale decisions, comments, reviewer, timestamps, and effective score impact.
  - Add backend API support for replacing browser-local overlays in a later frontend slice.
  - Keep fixture/demo local fallback where useful.
- Completion notes:
  - Added `radar_review_decisions` with current decision per run/candidate/qualification-or-signal subject.
  - Added application review records, repository port, and validation service for qualification and signal decisions.
  - Added API endpoints to save, list, and reset persisted review decisions.
  - Candidate API DTOs now overlay persisted review decisions without mutating `radar_run_outputs`.
  - Kept frontend localStorage behavior unchanged until `Slice 0.7.5`.

### Slice 0.7.5: Frontend API adapter

- Status: `Done`
- Goal: Add a frontend API data source that can replace JSON artifacts gradually and manually start live Radar runs.
- Scope:
  - Add typed frontend API client.
  - Add API-backed ICP Radar catalog and live candidate adapter.
  - Add manual live Radar run button with queued status polling.
  - Persist qualification and signal review decisions through backend API in API mode.
  - Keep offline/demo JSON and browser-local review fallback explicit.
- Completion notes:
  - Added `VITE_POWER_WEB_OS_API_BASE_URL` support with `http://127.0.0.1:8000` default.
  - Added FastAPI CORS settings for the local Vite frontend and bumped API version to `0.7.5`.
  - The frontend now reads persisted Radar catalog/details when the backend is available, otherwise it uses JSON artifacts.
  - `ТОиР Quick Live Radar` can be started from the UI; the UI polls `radar_runs` and reads candidates after output exists.
  - Live qualification and signal review controls save/reset persisted decisions when viewing an API-backed run.

### Slice 0.7.5.1: One-command Docker dev stack

- Status: `Done`
- Goal: Run the local Radar UI/API/worker path with one Docker Compose command.
- Scope:
  - Add Docker Compose services for Redis, backend init, FastAPI API, Celery worker, and Vite frontend.
  - Keep the default dev database as shared SQLite under `demo/output`.
  - Mount shared `demo/output` into API and worker containers so `radar_runs` remains the durable source of truth.
  - Keep OpenRouter credentials in local `.env`; do not include secrets in the Docker build context.
  - Document `docker compose up --build` manual smoke flow.
- Completion notes:
  - Added backend and frontend Dockerfiles plus `.dockerignore`.
  - Added `backend-init` service for Alembic migrations and Radar catalog seed.
  - Added static contract tests for compose services, ports, Redis URLs, SQLite volume, and secret exclusions.
  - Postgres compose profile is intentionally left for a later production-like stack slice.

### Slice 0.7.6: Run journal and evidence audit

- Status: `Done`
- Goal: Store and display structured workflow journal events from backend state.
- Scope:
  - Add append-only `radar_run_events` table with lifecycle, planning,
    collection, extraction, evaluation, scoring, validation, and self-check
    event types.
  - Add `RadarRunEventRecord`, `RadarRunEventRepository`, and `RadarRunJournal`
    application service.
  - Instrument queued run creation and worker execution with lifecycle events.
  - Map current live artifact sections into structured audit events without
    storing raw hidden chain-of-thought.
  - Add `GET /api/radar-runs/{run_id}/journal`.
  - Show backend journal events in the frontend `Journal` tab for API-backed
    runs and keep artifact metadata fallback for offline/demo JSON mode.
- Completion notes:
  - Added ADR `2026-06-17-structured-radar-run-journal.md`.
  - `radar_runs` remains durable status truth, `radar_run_outputs` remains the
    immutable output snapshot, and `radar_run_events` is the append-only audit
    timeline.
  - Application journal validation rejects raw hidden reasoning keys:
    `chain_of_thought`, `hidden_reasoning`, and `internal_thoughts`.

### Slice 0.7.6.1: Planner/executor/evaluator workflow expansion

- Status: `Done`
- Goal: Add explicit planner, executor, and evaluator workflow nodes that emit
  the structured journal contract introduced in `Slice 0.7.6`.
- Scope:
  - Split current live Radar workflow execution into named planning,
    collection, extraction, scoring, and validation nodes where it improves
    observability.
  - Keep `langgraph-document-ai-platform` as the workflow wrapper/runtime
    boundary.
  - Emit `radar_run_events` from node outputs through application journal
    services, not directly from persistence or provider adapters.
  - Keep raw hidden chain-of-thought out of storage and UI.
  - Preserve current API/frontend contracts for runs, candidates, reviews, and
    journal events.
- Completion notes:
  - Added provider-neutral live Radar pipeline step contracts for planning,
    collection, extraction, evaluation, validation, and artifact shaping.
  - Reworked `LiveRadarRunService` into explicit phase methods while keeping
    the existing `icp_radar_live_run` artifact/API/frontend contracts stable.
  - Updated the workflow wrapper so LangGraph node names map to concrete
    pipeline phases instead of invoking one monolithic run from every node.
  - Persisted journal events now prefer pipeline-emitted structured events and
    keep artifact-derived journal mapping as a backward-compatible fallback.
  - Real model-quality testing against the SIBUR contour remains after the run
    dossier and technical trace slices.

### Slice 0.7.6.1.1: Radar run dossier and plan inspection

- Status: `Done`
- Goal: Make each live Radar run understandable as a reproducible product
  dossier, not just a flat journal event list.
- User value: A user can open a completed run and see what exact radar
  definition, input context, search plan, source set, validation warnings, and
  source-to-finding links were used for that run.
- Scope:
  - Add a backend dossier read contract for `radar_runs` that composes existing
    run state, active definition snapshot, output snapshot, sources,
    candidates, validation, and journal events.
  - Expose run input context: `run_id`, `correlation_id`, requester, live/demo
    mode, model, web mode, timestamps, radar definition version, qualification
    rules, intent signals, scoring/source policy, and task context.
  - Expose the actual search plan: query id, query text, purpose, expected
    evidence, and the radar rule/signal context it supports where available.
  - Expose source usage summary: source url/title/snippet/query id, accepted
    status, usage by candidate/qualification/signal, and validation warnings.
  - Update the Radar detail `Journal` area into product sections such as
    `Run`, `Plan`, `Sources`, `Validation`, and `Timeline`, using the existing
    design-system tokens and tabbed candidate detail layout.
  - Fix the API-backed frontend adapter so completed runs preserve real
    `search_plan.queries` instead of showing an empty plan.
- Out of scope:
  - Raw provider prompt/request bodies.
  - Raw hidden chain-of-thought.
  - Admin-only debug trace authorization.
  - SIBUR benchmark execution.
- Implementation notes:
  - Prefer a read-only DTO derived from existing tables; do not add schema
    unless a field cannot be reconstructed from `radar_run_outputs` or
    `radar_run_events`.
  - Keep `radar_run_outputs` immutable. Dossier views are projections over
    existing persisted state.
  - Product dossier text should be explanatory and compact; avoid dumping raw
    JSON into the normal user view.
- Tests:
  - API test for run dossier shape with input context, plan queries, sources,
    validation, and source usage links.
  - Frontend adapter test proving API-backed live artifact keeps real search
    plan queries.
  - Frontend contract test that presentation components do not call `fetch`.
  - Visual/static smoke for the dossier sections in EN/RU.
- Docs:
  - Update SAO, Developer Guide, frontend Radar docs, and demo docs with the
    run dossier purpose and endpoint/adapter flow.
- Demo impact:
  - A user can click a finished Radar run and inspect the real input, plan,
    sources, validation, and timeline before trusting or reviewing candidates.
- Acceptance criteria:
  - The UI answers: what settings were used, what plan was built, what sources
    were used, and what warnings were produced.
  - Existing run/candidate/review API contracts remain compatible.
  - No secrets or raw hidden CoT appear in dossier responses or UI.
- Risks:
  - Dossier can become too verbose; keep normal product view curated and leave
    raw technical detail for the next slice.
- Completion notes:
  - Added `GET /api/radar-runs/{run_id}/dossier` as a read-only projection over
    existing run state, active definition summary, output snapshot, source
    usage links, validation issues, review counts, and non-debug journal events.
  - Kept queued/running/failed runs inspectable through partial dossier
    `output_state`, while candidate output still returns `409` until a snapshot
    exists.
  - Updated the frontend API client and adapter so API-backed live artifacts
    preserve persisted `search_plan.queries` instead of rendering an empty plan.
  - Reworked the live Radar detail `Journal` tab into a product dossier with
    `Run`, `Input`, `Plan`, `Sources`, `Validation`, and `Timeline` sections
    for API-backed runs; offline JSON artifacts keep the existing journal
    fallback.
  - Product dossier remains separate from the future admin technical trace and
    does not expose provider prompts, raw debug payloads, secrets, or hidden
    chain-of-thought.

### Slice 0.7.6.1.2: Admin technical trace for Radar runs

- Status: `Done`
- Goal: Add a separate developer/admin trace surface for inspecting sanitized
  provider prompts, requests, responses, and pipeline step inputs/outputs.
- User value: A developer can debug whether the agent workflow, prompt,
  OpenRouter request, provider response parsing, normalization, and validation
  worked correctly without mixing technical logs into the product dossier.
- Scope:
  - Add a technical trace contract for live Radar runs with sanitized provider
    request metadata, prompt/messages, web-search settings, response metadata,
    structured model JSON, parsing outcomes, normalization warnings, step
    durations, and pipeline phase input/output summaries.
  - Add redaction guards for API keys, authorization headers, bearer tokens,
    local env values, and provider secrets.
  - Add backend endpoint such as
    `GET /api/radar-runs/{run_id}/technical-trace` for dev/admin inspection.
  - Add a frontend `Trace` tab or admin-only trace section using a structured
    JSON/detail viewer that wraps long values and avoids horizontal scrolling.
  - Keep trace visibility separated from normal `Journal`/dossier content so it
    can later be protected by authorization.
- Out of scope:
  - Raw hidden chain-of-thought storage or display.
  - Production authorization/role model.
  - Full observability stack, log aggregation, or distributed tracing.
  - SIBUR benchmark execution.
- Implementation notes:
  - Prefer storing or deriving sanitized technical trace artifacts through
    application-owned contracts, not direct provider/persistence shortcuts.
  - If persistence is required, keep trace payloads separate from product
    review state and document retention/redaction policy.
  - Technical trace may include prompts and structured model responses, but
    must reject `chain_of_thought`, `hidden_reasoning`, and
    `internal_thoughts`.
- Tests:
  - Backend tests for trace creation/read path, redaction, and forbidden raw
    reasoning keys.
  - Integration test proving OpenRouter secrets and `Authorization` markers do
    not appear in trace API responses or persisted trace payloads.
  - Frontend tests for trace rendering, long-line wrapping, and no direct
    `fetch` calls from presentation components.
- Docs:
  - Add ADR or update the structured journal ADR to distinguish product dossier,
    structured journal, and admin technical trace.
  - Update Developer Guide with what is safe to store/show in technical trace.
- Demo impact:
  - In local/dev mode a developer can inspect what was sent to the provider and
    how the response moved through the pipeline.
- Completed:
  - Added append-only `radar_run_technical_traces` persistence with SQLAlchemy,
    Alembic, repository port/adapter, and SQLite migration coverage.
  - Added application-owned `RadarRunTechnicalTracer` and
    `TechnicalTraceRedactor` that mask secret-like fields, cap long strings, and
    reject `chain_of_thought`, `hidden_reasoning`, and `internal_thoughts`.
  - Instrumented live Radar pipeline phases and OpenRouter provider
    request/response/error paths through sanitized technical traces.
  - Added `GET /api/radar-runs/{run_id}/technical-trace` and bumped API version
    to `0.7.6.1.2`.
  - Added an API-backed live Radar `Trace` tab separate from the product
    `Journal`/dossier tab, with wrapped payload/redaction rows and no direct
    `fetch` calls in presentation components.
- Acceptance criteria:
  - Technical trace can explain prompt/request/response/normalization behavior
    for a run.
  - Product dossier remains readable for non-admin users.
  - No secrets or raw hidden CoT are stored or exposed.
- Risks:
  - Prompt/response payloads can be large; cap, summarize, or paginate trace
    payloads if needed.

### Slice 0.7.6.1.3: Qualification-first Radar execution plan

- Status: `Done`
- Goal: Make live Radar execution qualification-first and backend-orchestrated
  before model-quality benchmarking.
- User value: A developer can inspect and trust that Radar first discovers and
  filters candidate accounts through qualification gates, then searches intent
  signals only for non-rejected candidates.
- Scope:
  - Added an application-level `RadarExecutionPlan` with
    `qualification_discovery`, sequential `qualification_gate`, and
    `signal_search` tasks.
  - Kept existing `search_plan.queries` as a backward-compatible projection
    while adding task stage, subject, dependency, rule snapshot, and candidate
    scope metadata.
  - Reworked live Radar collection so the backend executes bounded provider
    calls in order instead of sending one mixed qualification/signal prompt.
  - Filtered rejected required-qualification candidates out of the public
    candidate artifact while retaining rejected summaries in execution metadata.
  - Scoped OpenRouter prompts so qualification tasks do not include signals and
    signal tasks include only one signal and the current candidate scope.
  - Updated dossier/trace inputs so staged task metadata is inspectable without
    a database migration.
- Out of scope:
  - SIBUR benchmark execution.
  - Normalized candidate/evidence tables.
  - Production entity-resolution or deduplication beyond current snapshot
    merging.
  - Raw hidden chain-of-thought storage or display.
- Implementation notes:
  - The logic is generic over Radar definitions and uses the rule/signal
    content from the definition; it is not hardcoded to SIBUR.
  - LLM/provider adapters execute bounded tasks. Application services own stage
    ordering, gate semantics, candidate filtering, and observability metadata.
- Tests:
  - Contract tests cover generic plan compilation, staged provider call order,
    rejected-candidate signal suppression, scoped OpenRouter request payloads,
    persisted run compatibility, API compatibility, frontend type/build
    compatibility, and backend architecture guardrails.
- Docs:
  - Added ADR `2026-06-18-qualification-first-radar-execution.md`.
  - Updated SAO, Developer Guide, demo docs, and layer README guidance for the
    qualification-first execution model.
- Demo impact:
  - Existing UI/API flows remain compatible. Product dossier and technical
    trace can now show staged plan metadata before the SIBUR benchmark.
- Acceptance criteria:
  - Qualification gates run before signal searches.
  - Signal tasks are not created for rejected candidates.
  - External run/candidate/dossier/journal/trace contracts remain compatible.
  - No SIBUR-specific logic is introduced.
- Risks:
  - Live web runs now involve more bounded provider calls; benchmark cost and
    latency should be measured in `Slice 0.7.6.2`.

### Slice 0.7.6.1.4: LLM-planned discovery strategy and source policy

- Status: `Done`
- Goal: Make candidate-universe discovery a real planning process instead of a
  single generated query, while keeping the strategy generic across Radar
  definitions.
- User value: A user can inspect why the Radar searched specific source bases,
  which qualification criteria drove each discovery step, why some sources were
  used or skipped, and whether the candidate universe is plausibly complete
  before signal search begins.
- Scope:
  - Add an application-level discovery planner port that receives the active
    Radar definition, qualification rules, global search base, source policies,
    task context, and current run metadata.
  - Add an LLM-backed planner adapter behind the existing integration/workflow
    boundaries. The planner returns structured discovery plan steps, not raw
    hidden chain-of-thought.
  - Represent discovery planning as a loop:
    1. inspect radar settings and source policy;
    2. propose candidate-universe discovery steps;
    3. validate those steps against source policy, rule dependencies, and
       expected evidence;
    4. revise or accept the plan;
    5. execute only accepted bounded tasks.
  - Support generic qualification criteria such as industry, region, revenue,
    ownership/group membership, asset type, and source preference without
    hardcoding SIBUR-specific logic.
  - Allow the planner to prefer configured global source bases, for example
    SBIS or an official registry, when they are relevant to the criterion, and
    to explain when a configured source base is not useful for a specific step.
  - Keep provider execution bounded: each executed task receives one current
    discovery or qualification step, its source constraints, and expected
    evidence.
  - Store analyzed-but-not-used sources in technical trace only. Product
    sources and dossier source lists should include only sources that actually
    contributed to accepted/unknown candidates, qualification evidence, signal
    evidence, or validation warnings.
  - Extend dossier with discovery-plan inspection: planned steps, accepted
    steps, skipped source bases, source-use rationale, candidate universe
    counts, rejected/unknown counts, and coverage warnings.
  - Extend technical trace with planner input/output, validation outcome, and
    revision attempts after redaction.
- Out of scope:
  - SIBUR-specific baseline evaluation.
  - Raw hidden chain-of-thought storage or display.
  - Normalized candidate/evidence tables.
  - Production auth for hiding technical trace.
  - Perfect entity resolution for all registries.
- Implementation notes:
  - Backend application services own strategy validation and execution
    acceptance. LLM planner proposes structured steps; it does not become the
    source of truth for stage ordering, source policy, or candidate filtering.
  - The source policy must be explicit in planner input: global source base,
    local source overrides, cross-validation settings, fallback confidence,
    allow-additional-sources, and HITL policy.
  - Product output should separate `used_sources` from `analyzed_sources`.
    `used_sources` feed the existing candidates/dossier UI; `analyzed_sources`
    remain in technical trace until a normalized evidence schema is added.
  - The implementation must be tested with at least three Radar definitions:
    a holding/group-membership discovery case, an industry/region/revenue case,
    and a source-constrained registry-first case.
- Tests:
  - Unit tests for planner input construction from radar settings and source
    policy.
  - Recorded LLM planner tests for three generic Radar definitions without
    SIBUR-specific assertions.
  - Contract tests that rejected/skipped/analyzed-only sources do not appear in
    product source lists but remain visible in technical trace.
  - Tests proving signal searches run only after accepted discovery plan steps
    and qualification gates.
  - API/dossier tests for discovery-plan inspection fields.
- Docs:
  - Add ADR: LLM proposes discovery plans; backend validates and executes
    bounded tasks.
  - Update SAO with planner/validator/executor ownership and source visibility
    policy.
  - Update Developer Guide and demo docs with the difference between product
    used sources and technical analyzed sources.
- Demo impact:
  - UI `Journal`/dossier can explain why a source base was used or skipped and
    why a discovery step was accepted.
  - UI source lists become cleaner because they show only sources that went
    into evidence or validation, while Trace retains the broader debug trail.
- Acceptance criteria:
  - Discovery planning works for at least three different Radar definitions.
  - Planner output is structured, inspectable, redacted, and contains no raw
    hidden CoT.
  - Configured source policy influences planning and is visible in dossier.
  - Product source lists exclude sources that were only analyzed and not used.
  - No SIBUR-specific branching exists in application or integration code.
- Risks:
  - More planning steps can increase latency and cost; benchmark slices should
    measure both.
  - Planner validation can become too permissive; keep backend-side policy
    checks explicit and covered by tests.
- Completed:
  - Added `RadarDiscoveryPlanningInput`, `RadarDiscoveryPlan`,
    `RadarDiscoveryPlanStep`, planner port, deterministic fallback planner, and
    backend `RadarDiscoveryPlanValidator`.
  - Added OpenRouter discovery planner adapter as a separate integration path
    from provider search/extraction.
  - Reworked live Radar planning into initial plan, backend validation, one
    revision attempt, accepted execution-plan compilation, and clear failure
    when revised plans remain invalid.
  - Kept qualification-first execution: candidate universe discovery and gates
    run before signal searches; signal searches still run only for
    non-rejected candidates.
  - Split product and technical source visibility: product output/dossier
    sources are evidence-bearing used sources, while analyzed-but-unused
    sources remain in execution metadata and technical trace.
  - Extended dossier/API/frontend Journal view with discovery strategy,
    selected/skipped source bases, coverage summary, and used/analyzed/skipped
    source counts.
  - Added ADR `2026-06-18-llm-planned-radar-discovery.md`.

### Slice 0.7.6.1.5: Iterative candidate universe expansion and coverage enforcement

- Status: `Done`
- Goal: Make live Radar discovery iterative instead of closing the candidate
  universe after one discovery query.
- User value: A user can rerun the live Radar and inspect not only the final
  candidates, but also which candidates were discovered, qualified, rejected,
  added by coverage checks, or left as unresolved universe gaps.
- Backend changes:
  - Added model routing for OpenRouter:
    `OPENROUTER_MODEL` stays the fast/default signal-task model,
    `OPENROUTER_ADVANCED_MODEL` is the shared advanced fallback, and
    `OPENROUTER_PLANNER_MODEL` / `OPENROUTER_EXTRACTOR_MODEL` route planning
    and discovery/qualification/coverage extraction.
  - Made `coverage_check` an executable `RadarExecutionStage`.
  - Added application-level candidate universe and coverage records without a
    DB migration; metadata is stored in the existing live output snapshot,
    dossier, journal, and trace surfaces.
  - Execution now runs discovery, qualification gates, coverage checks,
    candidate merge/dedupe, repeated qualification for new candidates, and only
    then signal searches.
  - Signal tasks are scoped to the frozen candidate universe. New entities
    mentioned during signal search become `candidate_universe_gap` metadata,
    not candidates.
  - Planner validation now rejects configured global source ids presented as
    local sources and requires coverage or low-risk coverage rationale for
    single-step discovery plans.
- Frontend/API changes:
  - API version bumped to `0.7.6.1.5`.
  - Dossier response now exposes `candidate_universe`, `coverage_checks`,
    `coverage_warnings`, `unresolved_candidate_gaps`, and
    `discovery_iteration_count`.
  - Live Radar Journal/Dossier tab renders candidate universe lifecycle and
    executed coverage checks with wrapped cards, not raw JSON.
- Docs:
  - Added ADR `2026-06-18-candidate-universe-expansion-before-signals.md`.
  - Updated SAO, Developer Guide, demo docs, and `.env.example` model settings.
- Validation:
  - `python -m pytest tests/test_live_icp_radar.py`
  - `python -m pytest tests/test_backend_api.py`
  - `npm --prefix ./frontend run build`
- Post-implementation hardening:
  - Fixed Docker dev stack env propagation with `env_file: .env`, so API and
    worker receive local OpenRouter model, web mode, and search budget settings.
  - Set `.env.example` to a smoke-safe live budget:
    `OPENROUTER_WEB_MODE=server_tools` and
    `POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT=1`.
  - Added controlled fallback to deterministic discovery planning when the LLM
    planner remains invalid after one revision, instead of failing or drifting
    into unbounded search.
  - Tightened planner validation so discovery/gate tasks must target exactly
    one known qualification rule and cannot create arbitrary per-step subject
    budgets.
  - Normalized localized planner risk labels such as `низкий` to the canonical
    API enum before validation.
  - Verified a real Docker API/worker live run reached terminal `completed`
    state in about 67 seconds with the smoke budget. The resulting candidate
    quality is intentionally not representative while the budget is `1`.
- Remaining risk:
  - This changes execution strategy but does not yet prove discovery quality on
    real benchmark radars. That remains the job of `Slice 0.7.6.2`.

### Slice 0.7.6.1.6: Source lifecycle visibility

- Status: `Done`
- Goal: Make it clear why a live Radar run can show provider calls and search
  activity while product `sources` remains empty.
- User value: A user or developer can inspect a run and understand how many
  sources were collected, parsed, verified, linked to candidates, used in the
  product output, or discarded with a reason.
- Scope:
  - Add a source lifecycle projection without a DB migration:
    `collected`, `parsed`, `reachable`, `linked_to_candidate`,
    `used_in_product`, and `discarded`.
  - Extend run dossier summary with source lifecycle counts and discard reasons.
  - Keep product `sources` as evidence-bearing used sources only.
  - Keep analyzed/skipped/unreachable sources in technical trace and execution
    metadata.
  - Add backend tests that a run with analyzed but unused sources explains why
    product source count is zero.
- Out of scope:
  - Changing scoring semantics.
  - Relaxing URL verification.
  - Increasing live search budget.
  - Benchmarking SIBUR or other real radars.
- Implementation notes:
  - The lifecycle projection should be composed from existing output snapshot,
    execution metadata, provider `source_outcomes`, and technical trace.
  - Do not expose raw provider dumps or hidden chain-of-thought in the product
    dossier.
  - Treat this as observability and explanation, not as a quality fix.
- Tests:
  - Unit/API test for dossier source lifecycle counts.
  - Contract test that product sources remain used/evidence-bearing only.
  - Regression for technical trace redaction.
- Docs:
  - Update SAO, Developer Guide, demo docs, and ADR notes for source lifecycle
    semantics.
- Demo impact:
  - The Journal/Dossier tab can explain `0 product sources` without requiring a
    developer to inspect raw trace rows.
- Acceptance criteria:
  - A completed run with zero product sources shows collected/analyzed/discarded
    source counts and reasons.
  - Product candidate/source DTOs remain backward compatible.
  - No raw secrets, raw hidden CoT, or unredacted provider payloads appear in
    product API responses.
- Implementation result:
  - Added `source_lifecycle` and `source_lifecycle_summary` to the run dossier
    API without a DB migration.
  - Bumped API version to `0.7.6.1.6`.
  - Product `sources` remains evidence-bearing only; analyzed-only records are
    exposed through lifecycle diagnostics, not mixed into product sources.
  - Frontend Journal/Dossier now renders source lifecycle metrics and reason
    cards before the product Sources section.
- Validation:
  - `python -m pytest tests/test_backend_api.py`
  - `python -m pytest tests/test_frontend_architecture_contract.py tests/test_frontend_demo_contract.py`
  - `npm --prefix ./frontend run build`
  - `python -m pytest tests/test_backend_architecture_contract.py`
  - `python -m pytest`
- Risks:
  - Lifecycle counts may initially be approximate because normalized source
    tables do not exist yet; record this in dossier copy and technical docs.

### Slice 0.7.6.1.7: Soft source verification and useful-result budgets

- Status: `Done`
- Goal: Stop losing candidate evidence when provider-returned URLs fail a
  binary HTTP reachability check, and make discovery retry when it produces no
  useful sources or candidates.
- User value: A live Radar can keep potentially useful source-backed findings
  as reviewable evidence instead of returning an empty result just because a
  site returned `404`, blocked `HEAD`, timed out, or redirected unexpectedly.
- Scope:
  - Add `POWER_WEB_OS_RADAR_SOURCE_VERIFICATION_MODE` with modes:
    `strict`, `soft`, and `off`.
  - Default planned local tuning mode is `soft`: failed URL reachability marks
    sources as `unverified_url`/risk-bearing instead of deleting the source and
    all candidates linked to it.
  - Keep `strict` available for conservative runs and tests that must require
    currently reachable URLs.
  - Add useful-result budget settings:
    `POWER_WEB_OS_RADAR_MIN_USEFUL_SOURCES_PER_DISCOVERY_TASK`,
    `POWER_WEB_OS_RADAR_MIN_CANDIDATES_PER_DISCOVERY_TASK`, and
    `POWER_WEB_OS_RADAR_MAX_DISCOVERY_RETRIES_PER_TASK`.
  - Retry or reformulate bounded discovery tasks when a task returns no useful
    sources/candidates or only unverified sources, until the retry limit is
    reached.
  - Require extractor output to link qualification and signal findings to
    `evidence_refs`; confirmed/observed findings without valid evidence refs
    must be downgraded to `unknown` / `not_observed` with review warnings.
  - Keep candidates linked only to unverified sources as
    `unknown_review_needed` with verification warnings, not as confident
    matches and not as silently deleted candidates.
  - Make empty candidate universe with discovery-oriented qualification rules a
    coverage warning/high-risk state, not a successful low-risk result.
- Out of scope:
  - Normalized source/evidence database tables.
  - Full crawler/browser rendering verification.
  - Adding a new web retrieval provider.
  - Full SIBUR or multi-radar benchmark.
- Implementation notes:
  - Implemented in API version `0.7.6.1.7`.
  - `POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT` still limits provider task
    calls. URL failures happen after a task response and should not be treated
    as useful evidence, but they also should not erase the run's diagnostic
    state.
  - Verification should preserve evidence-bearing sources with explicit
    verification state/risk metadata instead of silently discarding them.
  - Product DTOs and dossier should expose verification state where useful,
    while Trace keeps detailed provider/source outcomes and retry attempts.
  - The source verifier remains infrastructure; scoring rules stay in
    application/domain normalization.
- Tests:
  - Unit tests for verifier state transitions and `strict` / `soft` / `off`
    modes.
  - Recorded-provider tests for evidence-linked sources surviving to product
    dossier as risk-bearing sources under `soft`.
  - Tests that unverified-only candidates are retained as
    `unknown_review_needed`, not scored as confident matches.
  - Tests that discovery retries are attempted when useful-result thresholds
    are not met and stop at the configured retry limit.
  - Negative tests where unlinked sources remain analyzed-only.
- Implementation result:
  - Added source verification metadata to `RadarSourceEvidence` and OpenRouter
    provider normalization.
  - Added `strict`, `soft`, and `off` verification modes with `soft` as the
    local/dev default.
  - Added useful-result retry budgets for discovery and coverage tasks.
  - Risky evidence now downgrades qualification/signal confidence and marks
    candidates for review instead of silently deleting them.
  - Dossier source lifecycle exposes verification state, reason, mode, and
    status code where available.
  - Kept product source lists evidence-bearing; analyzed-only sources stay in
    lifecycle/trace metadata.
- Docs:
  - Update SAO, Developer Guide, demo docs, and ADR notes with soft
    verification, useful-result budgets, and retry semantics.
- Demo impact:
  - Manual runs should explain URL failures without collapsing into an
    unexplained empty candidate list.
- Acceptance criteria:
  - A source-backed qualification linked to an unreachable-but-structured
    provider source produces a reviewable candidate with verification warning.
  - Empty candidate universe after discovery produces high/medium coverage
    warning unless the run has a validated low-risk rationale.
  - Discovery retries are visible in dossier/journal/trace.
  - Sources without evidence usage do not pollute the product source list.
- Risks:
  - Over-relaxing verification could admit weak sources; mitigate by exposing
    verification state and keeping review warnings.

### Slice 0.7.6.1.7.1: Remote dev server deployment documentation and skill

- Status: `Done`
- Goal: Record the current remote dev server as a managed project contour and
  make updates repeatable without reconstructing SSH, Docker, and `.env`
  handling from chat history.
- User value: A developer can deploy the current workspace to the shared remote
  Docker dev stack with one script and clear safety rules for secrets.
- Scope:
  - Add `deploy/remote-dev.env` with non-secret host, SSH target, path, URL,
    port, and Redis bind configuration.
  - Add `docs/deployment/REMOTE_DEV_SERVER.md` with server purpose, services,
    deploy flow, manual checks, logs, and `.env` safety rules.
  - Add `scripts/deploy_remote_dev.ps1` for tar/scp deployment, remote `.env`
    copy, server-specific `.env` overrides, `docker compose config --quiet`,
    `docker compose up --build -d`, and API/frontend health checks.
  - Add `.agents/skills/deploy-remote-dev/SKILL.md` so future "залить на
    сервер" tasks use the documented script and do not print secrets.
  - Update Developer Guide with remote dev commands and URLs.
- Out of scope:
  - Production deployment.
  - Postgres or managed infrastructure.
  - Auth, TLS, reverse proxy, CI/CD, rollback release management, or secret
    manager integration.
  - Runtime application/API/schema changes.
- Implementation notes:
  - Remote config keeps `POWER_WEB_OS_REMOTE_SSH_TARGET=flowise` because the
    SSH alias has the working key configuration.
  - The remote project path is `/opt/power-web-os`.
  - Local `.env` is copied separately and remains uncommitted.
  - Redis host publishing is configured as `127.0.0.1:6380`; it should not be
    public.
  - The deploy script supports `-DryRun` with no file transfer and no SSH
    mutation.
- Tests:
  - Static contract test for remote config, deploy script, skill, and docs.
  - `powershell -ExecutionPolicy Bypass -File scripts/deploy_remote_dev.ps1 -DryRun`
  - `docker compose config --quiet`
  - `python -m pytest tests/test_backend_architecture_contract.py`
- Demo impact:
  - No UI behavior change; the existing remote dev UI can be refreshed through
    the documented deployment path.
- Acceptance criteria:
  - Remote server host/path/ports live in a tracked non-secret config file.
  - A dry-run command explains the deployment steps without copying files.
  - The live command can rebuild the remote Docker dev stack and verify API,
    catalog, and frontend responses.
  - The project skill documents when and how to deploy without exposing
    secrets.
- Risks:
  - This remains a dev-only tar/scp deployment; stale remote files can remain if
    files are deleted locally. Mitigate later with release directories or rsync
    if this contour becomes long-lived.

### Slice 0.7.6.1.7.2: Criterion role inference and plan acceptance repair

- Status: `Done`
- Goal: Make live Radar planning understand which qualification criteria define
  the upstream candidate universe, which are downstream gates, and which are
  enrichment/exclusion checks, while avoiding unnecessary fallback when the LLM
  proposes a reasonable plan with minor schema/scope mistakes.
- User value: A user can understand how the Radar decided to approach an open
  discovery task such as "find all companies in a holding" before it starts
  checking downstream attributes or signals.
- Scope:
  - Add an application-level criterion role inference step before discovery plan
    compilation.
  - Support criterion roles:
    `upstream_discovery`, `downstream_gate`, `attribute_enrichment`,
    `exclusion`, and `signal`.
  - Let the LLM propose criterion roles and strategy summaries, but keep backend
    validation authoritative.
  - Split source configuration from source application:
    - `source_base`: `global_configured`, `rule_local`, `additional`, `system`;
    - `application_scope`: `whole_universe`, `rule_scope`,
      `candidate_scope`.
  - Make the validator normalize safe source-scope mismatches, for example
    `sibur.ru` configured globally but applied to a rule-local task, instead of
    rejecting the whole plan.
  - Allow strategic planning steps to mention multiple criteria when the search
    purpose is shared, while compiling them into separate executable truth
    checks.
  - Surface accepted/rejected/corrected planner decisions in dossier, journal,
    and technical trace.
- Out of scope:
  - New retrieval provider.
  - Multi-radar benchmark execution.
  - Raw hidden chain-of-thought storage.
  - Normalized candidate/evidence tables.
- Implementation notes:
  - The validator should distinguish dangerous violations from repairable
    contract mismatches.
  - If fallback is used, product dossier must say that explicitly and show why
    the LLM plan was rejected.
  - This slice should remain generic; SIBUR is only a checked example of a
    holding-contour upstream discovery criterion.
- Tests:
  - Unit tests for criterion role inference over generic holding-contour,
    industry/region/revenue, and source-constrained definitions.
  - Validator tests for global configured source used in rule/candidate scope.
  - Tests that multi-criterion strategic planning steps compile to separate
    executable checks.
  - Regression tests that signals still run only after candidate universe
    freeze.
- Docs:
  - Update SAO, Developer Guide, and ADR notes with criterion roles and
    source-base/application-scope terminology.
- Demo impact:
  - Manual live runs should show whether the accepted plan came from LLM
    planning or deterministic fallback.
- Acceptance criteria:
  - Done: a reasonable LLM plan is not rejected solely because a configured
    global source is applied to a rule-scoped task.
  - Done: product dossier metadata includes criterion roles and accepted planner
    corrections through the accepted discovery plan.
  - Done: technical trace preserves the original planner output, normalized
    accepted plan, validation result, and corrections after redaction.
  - Done: fallback use is explicit through `discovery_plan_fallback_used` and
    `acceptance_metadata.fallback_used`.
- Risks:
  - Over-repairing bad plans could hide real policy violations; mitigate by
    keeping hard errors for source-policy violations, signal/qualification
    mixing in executable tasks, and out-of-budget plans.

### Slice 0.7.6.1.7.3: Run-level diagnostics and source lifecycle UI

- Status: `Done`
- Goal: Make a live Radar run inspectable from the run itself, not only from
  candidate detail screens, and make budget/source/candidate lifecycle visible.
- User value: A user or developer can answer "what happened in this run?" even
  when some candidates were not searched for signals, when no candidates were
  returned, or when sources were analyzed but not used.
- Scope:
  - Add run-level UI entry points for dossier, journal, and technical trace from
    the Radar run state and empty-result surface.
  - Add an execution overview:
    planned tasks, executed tasks, provider calls, analyzed sources, used
    sources, discovered candidates, gated candidates, signal-searched
    candidates, budget-limited candidates, warnings, and terminal status.
  - Add a candidate universe table:
    candidate identity, origin task, current status, qualification gate states,
    signal searched yes/no, and reason if not searched.
  - Add a source lifecycle table/card set:
    collected -> verified -> parsed -> linked -> used/analyzed-only/skipped,
    with reasons such as duplicate, not linked, policy skipped, insufficient
    evidence, provider error, verification risk, or budget limit.
  - Keep candidate detail tabs for candidate-specific review, but stop making
    them the only route into run logs.
  - Add EN/RU strings and responsive no-horizontal-scroll checks.
- Out of scope:
  - Changing provider execution behavior.
  - New database schema.
  - Auth/admin gating.
  - Full trace viewer redesign; this slice can link to existing Trace rows.
- Implementation notes:
  - Use existing dossier/journal/technical-trace endpoints where possible.
  - Dossier is product-safe; technical trace is developer/admin-intended but
    remains visible in dev until auth exists.
  - The UI must explicitly show when signal search was limited to N of M
    candidates by budget.
- Completion notes:
  - Done: added run-level `Inspect run` / `Diagnostics` entry points beside
    live run status, empty state, completed runs, failed runs, and zero-candidate
    output.
  - Done: added `LiveRadarRunDiagnosticsView` with overview, candidate universe,
    source lifecycle, product dossier/journal, and compact trace entry tabs.
  - Done: candidate detail remains candidate-specific; product-safe run dossier
    can now be read without selecting a candidate.
  - Done: frontend state, i18n, feature CSS, and architecture/demo contract tests
    were updated for the new run-level diagnostics surface.
- Tests:
  - Frontend tests for run-level dossier/journal/trace actions when candidates
    exist and when there are zero candidates.
  - Adapter tests for candidate universe diagnostics and budget-limited state.
  - Backend/API tests only if dossier DTOs need more projected fields.
  - Visual smoke for run-level diagnostics at desktop viewport.
- Docs:
  - Update User Guide, Developer Guide, demo docs, and frontend feature README.
- Demo impact:
  - A manual live run with partial results becomes explainable without opening
    individual candidate details.
- Acceptance criteria:
  - UI shows which candidates were not searched for signals and why.
  - UI shows source lifecycle counts and reasons at run level.
  - A zero-candidate run still exposes dossier/journal/trace.
  - No raw secrets, raw hidden CoT, or unwrapped JSON dumps appear in product
    dossier.
- Risks:
  - The first projection may still be approximate because normalized source
    tables do not exist yet; label derived counts clearly.

### Slice 0.7.6.1.7.4: Readable Radar technical trace viewer

- Status: `Done`
- Goal: Replace the current raw-JSON-oriented Trace tab with a developer/admin
  trace viewer that is usable for debugging planner/executor/retrieval behavior.
- User value: A developer can inspect prompts, requests, provider results,
  parsed outputs, validation errors, budgets, durations, and model usage by
  logical Radar phase instead of reading disconnected JSON blobs.
- Scope:
  - Render technical trace entries grouped by logical phase:
    planning, plan validation, discovery, qualification gate, coverage, signal
    search, normalization, extraction, scoring, validation, and artifact
    shaping.
  - Add a left-side trace step list with status, phase, title, duration, model,
    provider, token/useful-source/candidate summaries when available.
  - Add a detail pane with sections:
    input summary, prompt/request, provider/tool results, parsed output,
    validation/errors, redaction report, and raw JSON.
  - Wrap long JSON/text values, provide copy buttons, and keep raw JSON behind a
    collapsible control.
  - Add filters/search:
    errors only, provider calls, planner, candidate, source ref, task id,
    phase/type.
  - Preserve redaction and hidden-CoT blocking.
  - Keep the visual design inside Power Web OS tokens and avoid horizontal page
    scrolling.
- Out of scope:
  - Production auth/role gating.
  - Changing trace persistence schema unless a small DTO projection is required.
  - Provider adapter changes.
  - Benchmark execution.
- Implementation notes:
  - This is a UI/adapter slice over existing sanitized technical trace records.
  - If backend DTOs are insufficient for grouping, add a stable projection in
    API mappers without exposing persistence internals.
  - The trace viewer should make OpenRouter-like prompt inspection possible, but
    with our own Radar phase semantics.
- Completion notes:
  - Done: replaced the raw details-list trace with a grouped developer/admin
    viewer over the existing sanitized technical trace DTO.
  - Done: added phase grouping, status derivation, search, quick filters,
    readable sections, copy actions, and collapsed raw JSON.
  - Done: added a frontend trace view-model boundary so presentation components
    do not own grouping, status, or safety filtering.
  - Done: kept the existing backend API, DB schema, provider adapters, and trace
    persistence unchanged.
- Tests:
  - Frontend architecture tests that presentation components do not call
    `fetch`.
  - API client/adapter tests for grouped trace view models.
  - UI tests for filters, wrapped JSON, collapsible raw payload, and no
    horizontal scroll.
  - Backend API tests if trace DTO projection changes.
- Docs:
  - Update Developer Guide and demo docs with trace viewer purpose and hidden
    CoT policy.
- Demo impact:
  - Developers can debug live Radar runs from the UI without opening SQLite or
    raw DB rows.
- Acceptance criteria:
  - Trace tab shows phase-grouped steps with readable summaries.
  - Prompt/request/response payloads are readable, wrapped, and copyable.
  - Errors and validator rejections are easy to filter.
  - Hidden CoT fields and secrets remain absent from API responses and UI.
- Risks:
  - Trace UI can become too heavy; keep the first version focused on inspection,
    filtering, and wrapping, not full observability-platform features.

### Slice 0.7.6.1.8: Compact Radar task prompts and retrieval plan contract

- Status: `Done`
- Goal: Stop sending heavy, duplicated Radar JSON into every bounded provider
  call, and make the formal retrieval plan the durable bridge between planning
  and execution.
- Problem being closed:
  - Current OpenRouter task prompts contain repeated `radar`, `current_task`,
    `search_plan`, full `output_schema`, and rule blocks even for a single
    candidate/signal check.
  - Provider traces show the model often compresses that payload into one simple
    internal search query, which means the backend spends tokens on context that
    does not improve retrieval.
  - Planning exists, but the executable plan is still not explicit enough as a
    product/developer artifact: it is hard to inspect the exact task card,
    source policy, query, stop condition, and expected evidence that execution
    used.
- User value: A user/developer can inspect the actual concise task cards and
  retrieval plan before judging candidate quality, and live runs spend fewer
  tokens on prompt noise.
- Scope:
  - Add a `RadarRetrievalPlan` / `RadarRetrievalTask` application contract that
    projects accepted discovery, gate, coverage, and signal tasks into compact
    executable task cards.
  - Add a `TaskPromptCompiler` that produces minimal prompt payloads per task:
    task type, candidate/rule/signal scope, selected source policy, expected
    evidence, compact return contract, and hard constraints.
  - Remove duplicated one-query `search_plan` blocks from per-task prompts when
    `current_task` already carries the task card.
  - Replace repeated verbose schemas with concise schema identifiers plus only
    the task-specific fields that the model must return.
  - Persist prompt/task summaries in technical trace and expose the accepted
    retrieval plan in dossier without raw hidden chain-of-thought.
  - Keep planner prompts richer than execution prompts; planner needs strategy
    context, bounded task execution does not.
- Out of scope:
  - New DB schema.
  - New source provider.
  - Perplexity or DaData integration.
  - Benchmark quality claims.
- Implementation notes:
  - The backend still owns strategy and validation. LLM/provider calls execute
    bounded tasks and return observations.
  - Target prompt shape should be readable as a compact task card, not as a full
    Radar artifact dump.
  - Trace should allow side-by-side inspection of planned task card, compiled
    provider prompt, provider result, parsed output, and final usage.
- Completion notes:
  - Done: added `RadarRetrievalPlan`, `RadarRetrievalTask`,
    `RadarResponseContract`, and `RadarRetrievalTaskPrompt` application
    contracts.
  - Done: projected existing execution plans through retrieval task cards while
    preserving `RadarSearchPlan` / `search_plan` compatibility.
  - Done: changed OpenRouter user prompts to compact `task_card`,
    `response_contract`, and `constraints` payloads.
  - Done: added `retrieval_plan` to run execution metadata and the dossier API
    response.
  - Done: added provider request trace summaries for `task_card` and
    `compiled_prompt`.
- Tests:
  - Unit tests for prompt compiler output size/shape and no duplicated
    `current_task`/single-query `search_plan` payload.
  - Recorded provider tests proving discovery, gate, coverage, and signal task
    prompts remain task-scoped.
  - Trace/dossier tests that accepted retrieval plan and compact task card are
    visible without secrets or hidden-CoT keys.
  - Architecture tests that prompt compilation stays in `integrations` or an
    application port boundary, not in domain scoring.
- Docs:
  - Update SAO, Developer Guide, demo docs, and ADR notes with compact prompt
    contracts and retrieval plan ownership.
- Demo impact:
  - Manual run trace becomes easier to inspect: each provider call has a short
    task card and compiled prompt, rather than a large raw JSON blob.
- Acceptance criteria:
  - Provider request traces for signal tasks show only the current candidate,
    current signal, source policy, and compact response contract.
  - Dossier shows the accepted retrieval plan and task cards.
  - Existing API/candidate DTOs remain backward compatible.
- Risks:
  - Over-compressing prompts can reduce extraction quality; mitigate with
    recorded fixtures and trace-visible prompt diffs.

### Slice 0.7.6.1.9: Hierarchical Radar execution budgets and not-searched states

- Status: `Done`
- Goal: Replace broad subject-level provider task limits with budgets that match
  Radar semantics: per run, per discovery rule, per candidate + qualification
  criterion, per candidate + signal, and per provider.
- Problem being closed:
  - `POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT=5` currently behaves too
    broadly. In signal stages it can limit search to the first few candidates
    for a signal instead of allowing up to five attempts for each candidate and
    each signal.
  - Candidates that were not searched because of budget can look like
    `not_observed`, which is semantically wrong. `not_observed` must mean
    searched and no signal found.
- User value: Run diagnostics can distinguish "searched and negative" from "not
  searched because the budget ran out", so shortlist quality and missing
  evidence are not misread.
- Scope:
  - Add `RadarExecutionBudget` with hierarchical keys:
    `run`, `stage`, `rule_id`, `candidate_id`, `signal_id`, and provider.
  - Keep `POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT` as a compatibility alias,
    but map it to candidate-scoped rule/signal task budgets where possible.
  - Add clearer future settings:
    `POWER_WEB_OS_RADAR_MAX_DISCOVERY_TASKS_PER_RULE`,
    `POWER_WEB_OS_RADAR_MAX_GATE_TASKS_PER_CANDIDATE_RULE`,
    `POWER_WEB_OS_RADAR_MAX_SIGNAL_TASKS_PER_CANDIDATE_SIGNAL`, and
    `POWER_WEB_OS_RADAR_MAX_TOTAL_WEB_TASKS_PER_RUN`.
  - Add candidate/signal statuses such as `not_searched_budget_limited` and
    `not_searched_policy_limited` while keeping existing candidate DTOs
    backward compatible.
  - Surface per-budget counters and exhausted-budget reasons in dossier,
    journal, and technical trace.
- Out of scope:
  - Provider adapter replacement.
  - UI redesign beyond existing diagnostics fields.
  - New DB schema.
- Implementation notes:
  - Budget keys must be generated by the application executor, not by provider
    adapters.
  - Signal score `0` is allowed only for searched negative or invalid evidence;
    unsearched budget-limited findings need their own review state.
- Tests:
  - Unit tests for budget key generation and exhaustion per candidate/signal.
  - Recorded flow where 10 candidates and one signal do not stop after the first
    five candidates when per-candidate budget allows more.
  - API/dossier tests for `not_searched_budget_limited` projection.
  - Regression tests for existing smoke-safe low-budget runs.
- Docs:
  - Update Developer Guide, demo docs, and `.env.example` comments with the new
    budget semantics and compatibility alias.
- Demo impact:
  - Run diagnostics show which candidates were searched, which were skipped by
    budget, and which signal/rule budget was exhausted.
- Acceptance criteria:
  - A budget-limited candidate is never shown as a searched negative result.
  - Existing `.env` with `POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT` still
    works, but docs recommend the new explicit variables.
- Risks:
  - More precise budgets can increase runtime/cost when raised; keep total run
    cap and trace-visible counters.
- Completion notes:
  - Added `RadarExecutionBudget` with hierarchical semantic keys and kept
    `POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT` as a compatibility alias.
  - Added explicit budget settings for discovery, gate, signal, and total run
    caps.
  - Removed signal candidate slicing as the primary limit and now records
    `not_searched_budget_limited` signal rows when a budget prevents provider
    execution.
  - Extended dossier output with budget summary, exhaustion events, and signal
    search statuses.

### Slice 0.7.6.1.10: DaData source provider and Radar source registry

- Status: `Done`
- Goal: Add a real structured company-data source to Radar execution instead of
  relying only on general web search for legal-entity facts.
- Problem being closed:
  - The Radar settings already model sources and MCP/API-style source policies,
    but there is no concrete structured company source connector behind them.
  - General web search is weak for facts such as INN/OGRN, legal status, address,
    OKVED, revenue, and organization normalization.
  - Without a connector, the UI cannot honestly let users add DaData as a source
    that the backend can execute.
- User value: A Radar can use a registry/company-data source for entity
  resolution and company facts, while web search remains responsible for open
  evidence and signal monitoring.
- Scope:
  - Added provider-neutral source registry contracts:
    `RadarSourceProvider`, `CompanyRegistryProvider`, `CompanyLookupRequest`,
    `CompanyLookupResult`, and source usage/outcome records.
  - Added a DaData adapter in `integrations` using the DaData API/MCP boundary,
    configured by local secrets such as `DADATA_API_KEY` and
    `DADATA_SECRET_KEY`.
  - Added Radar source type `company_registry` with provider id `dadata`.
  - Allowed planner/source policy to select DaData for entity resolution,
    legal-entity normalization, INN/OGRN facts, address/status/OKVED/revenue
    enrichment, and domain/email-owner lookup when configured.
  - Add UI/settings source option only after backend adapter and recorded tests
    exist, so the UI does not advertise a non-executable source.
  - Store DaData outputs in technical trace and output metadata as structured
    source observations; product dossier shows only facts used in candidate,
    qualification, validation, or scoring evidence.
- Out of scope:
  - Using DaData as the only discovery mechanism.
  - Production account/billing management UI.
  - Normalized candidate/evidence tables.
  - CRM enrichment writeback.
- Implementation notes:
  - DaData is not a replacement for web retrieval. It is a structured source for
    company identity and facts; the planner should combine it with web sources
    when the criterion requires open evidence or current intent signals.
  - The adapter must live under `integrations`; application services depend on a
    source-provider port, not on MCP/API client details.
  - Secrets must never appear in trace, logs, generated artifacts, or committed
    docs.
- Tests:
  - Recorded DaData fixtures for lookup by INN/OGRN/name/domain/email where
    applicable.
  - Planner/source-policy tests showing DaData is selected for registry-like
    criteria and skipped with rationale when not useful.
  - Architecture tests that DaData client details do not leak into application or
    domain code.
  - API/dossier tests for source usage links and redaction.
- Docs:
  - Update SAO, Developer Guide, demo docs, and ADR notes with DaData as the
    first structured company-data source provider.
- Demo impact:
  - A future manual run can explain that company identity facts came from DaData
    while signal evidence came from web retrieval.
- Acceptance criteria:
  - Done: DaData can be configured locally without committing secrets.
  - Done: a recorded run can use DaData-backed company facts through the
    source-provider port.
  - UI source configuration does not expose DaData until backend execution is
    test-covered.
- Risks:
  - DaData coverage and pricing differ by lookup type; keep provider behavior
    explicit in docs and trace.

- Completed notes:
  - Added `application/radar_source_providers.py` for source registry contracts
    and the web-provider wrapper.
  - Added `integrations/dadata_provider.py` with recorded/live DaData adapter and
    sanitized technical trace summaries.
  - Added DaData registry source to the live Radar definition for backend source
    policy execution; signal search remains web-based.
  - Added `.env.example` DaData settings and documentation for recorded/live
    modes.

### Slice 0.7.6.1.11: Web retrieval provider abstraction and Perplexity adapter

- Status: `Done`
- Goal: Make web search provider behavior comparable after task prompts,
  budgets, and structured company sources are under control.
- Problem being closed:
  - OpenRouter web search, Perplexity-style retrieval, and future providers can
    return different citations, snippets, and tool metadata. Without a retrieval
    port, those differences are hidden inside provider-specific chat payloads.
- User value: A user/developer can compare which provider retrieved which URLs,
  snippets, citations, and source outcomes before extraction and scoring.
- Scope:
  - Split web provider interaction into explicit retrieval and extraction
    concepts: `retrieved_sources`, `retrieval_query`, `provider_citations`,
    snippets, retrieval status, and extraction observations.
  - Add a provider-neutral web retrieval port under application contracts and
    keep provider implementations in `integrations`.
  - Add a Perplexity-backed retrieval path through OpenRouter server tools
    (`engine=perplexity`) without leaking provider SDK/HTTP code into
    application services.
  - Add environment configuration:
    `POWER_WEB_OS_RADAR_WEB_RETRIEVAL_PROVIDER=openrouter|openrouter_perplexity`
    and `POWER_WEB_OS_OPENROUTER_WEB_SEARCH_ENGINE=auto|perplexity`.
  - Persist retrieval summaries in output metadata/technical trace without a DB
    migration.
  - Keep extraction/scoring bounded: retrieval returns candidate/source
    material; extractor still produces structured observations; backend still
    owns qualification gates, source policy, verification, and scoring.
- Out of scope:
  - Production crawler/browser rendering.
  - Paid provider account management UI.
  - Normalized source/evidence tables.
  - Full benchmark quality claims.
- Implementation notes:
  - Run after compact task prompts, hierarchical budgets, and DaData source
    registry, so provider comparison is not polluted by prompt noise, wrong
    budget semantics, or missing structured company facts.
  - Perplexity should be evaluated as a retrieval provider, not as a replacement
    for backend-owned execution strategy.
  - Trace can store sanitized provider payload summaries; product dossier should
    show compact retrieval/source lifecycle, not raw provider dumps.
- Tests:
  - Contract tests for retrieval port and provider selection.
  - Recorded-provider tests showing the same task can be executed through
    OpenRouter and Perplexity-shaped retrieval fixtures.
  - Trace/dossier tests that retrieved-but-unused, extracted, verified, and
    used sources are distinguishable.
  - Architecture tests that provider adapters do not leak into application
    services.
- Docs:
  - Update SAO, Developer Guide, demo docs, and ADR notes with retrieval vs
    extraction ownership and Perplexity configuration.
- Demo impact:
  - Manual runs can be inspected by provider/retrieval behavior before
    candidate scoring is judged.
- Acceptance criteria:
  - Retrieval provider can be selected by config.
  - A run trace shows retrieval records separately from extraction records.
  - Product candidate/source DTOs remain backward compatible.
  - Perplexity-backed retrieval can be exercised through recorded tests and a
    documented manual configuration.
- Risks:
  - Provider APIs and OpenRouter routing behavior may differ; keep the adapter
    isolated and recorded fixtures provider-specific.
- Implementation notes:
  - Done: added provider-neutral retrieval contracts in the application layer.
  - Done: split OpenRouter web execution trace into retrieval request,
    retrieval response, and extraction/normalization result records.
  - Done: added OpenRouter Perplexity engine selection via environment
    settings, while keeping direct Perplexity Search API as a later provider
    expansion.
  - Done: preserved existing `WebSearchProvider.run_search_plan(...)`, API DTOs,
    and persisted output snapshot compatibility.

### Slice 0.7.6.1.11.1: Radar execution preflight and red tests

- Status: `Done`
- Goal: Add a fast TDD/preflight gate for complex live Radar execution before
  running expensive full live provider jobs.
- Problem being closed:
  - Full live Radar runs can take around 30 minutes and currently surface
    configuration, source-provider, retrieval, extraction, evidence-linking, and
    scoring failures only after the expensive run has completed.
  - The recent `radar-run-2dc3d058-639d-4c7a-9bf6-d36442267558` showed that
    Perplexity retrieval returned many sources, but DaData was not selected by
    the runtime payload and extraction/source refs collapsed into zero product
    sources.
- User value: Developers can know whether a Radar is executable before paying
  for a long live run, and red tests capture known failure modes before fixes
  are implemented.
- Scope:
  - Add a preflight application service and CLI/API-adjacent command for a
    Radar id, initially `toir-quick-live`.
  - Validate that the active persisted definition is the definition used by the
    live executor, not a hardcoded legacy runtime definition.
  - Validate source policy references: global source ids, rule-level source ids,
    signal source ids, DaData/company-registry configuration, and unknown source
    ids.
  - Add recorded red tests for current failure classes:
    `definition_runtime_mismatch`, `source_base_not_executable`,
    `extraction_schema_invalid`, `evidence_linking_failed`, and
    `invalid_zero_score_projection`.
  - Add negative provider fixtures: prose-first output, dict where list is
    required, missing source refs, numeric refs, unknown refs, invalid
    `source_outcomes`, and retrievable sources that cannot be linked to
    candidates.
  - Add a small targeted live-probe boundary design for DaData lookup,
    OpenRouter/Perplexity retrieval, and extraction-only schema validation; live
    probes may be documented first if credentials/network make them optional.
- Out of scope:
  - Fixing the runtime definition bug.
  - Changing scoring semantics.
  - New UI screens.
  - Full benchmark execution.
- Implementation notes:
  - This slice is intentionally red-first: tests should fail against the current
    pipeline before the repair slices.
  - Preflight must be fast enough for normal development and CI-like local
    use; it must not run a full Radar job.
  - The preflight result should be structured so UI/CLI can later show
    actionable failures.
  - Done: added application-layer `RadarExecutionPreflightService` and
    structured preflight report/check contracts.
  - Done: added `python -m power_web_os.demo preflight-radar --radar-id
    toir-quick-live --json`; it reads persisted definitions, performs no
    network calls, creates no run/output rows, and exits non-zero when the
    report is not ready.
  - Done: current `toir-quick-live` reports the expected red
    `definition_runtime_mismatch` until the active-definition execution repair
    slice lands.
  - Done: added recorded negative fixture gates for malformed provider shapes,
    prose-first output, evidence-ref failures, and invalid not-searched zero
    score projection.
- Tests:
  - Unit tests for preflight result shape and severity.
  - Recorded integration tests proving current DaData/runtime mismatch is
    detectable.
  - Negative extraction fixtures that fail schema/evidence-ref gates.
  - Architecture tests confirming preflight logic stays in application and does
    not import provider HTTP clients directly.
- Docs:
  - Update Developer Guide with preflight command and TDD ladder.
  - Update SAO/ADR references if the command shape changes.
- Demo impact:
  - Manual Radar testing starts with preflight before `Run radar`.
- Acceptance criteria:
  - Known current failure classes are represented by tests.
  - A developer can run a fast preflight command and get structured failures.
  - Full live run is no longer the first validation step for complex Radar
    pipeline changes.
- Risks:
  - Overbuilding preflight can delay actual fixes; keep it focused on known
    failure classes and fast feedback.

### Slice 0.7.6.1.11.2: Active Radar definition execution and source-base enforcement

- Status: `Done`
- Goal: Make persisted live execution use the active Radar definition from the
  database and enforce configured source bases such as DaData.
- User value: When a user configures DaData or another source in the Radar
  search base, the actual worker run uses it or explains why it was skipped.
- Scope:
  - Replace hardcoded `build_live_mini_radar_definition()` usage in persisted
    worker execution with active `RadarDefinitionRecord` loading.
  - Keep the hardcoded definition only for offline/legacy demo paths.
  - Ensure runtime artifact, planner input, retrieval plan, dossier, and trace
    all show the same active definition version/source policy.
  - Add DaData to the Radar common search base projection where it is missing,
    and verify rule-level source policies reference executable source ids.
  - Emit explicit source-provider outcomes when DaData is selected, unavailable,
    skipped, or returns zero observations.
- Out of scope:
  - Extraction schema repair.
  - UI source editor.
  - Direct Perplexity API.
- Tests:
  - Preflight red tests from `0.7.6.1.11.1` turn green for definition/runtime
    matching and DaData source selection.
  - Recorded source-registry tests show DaData selected for qualification/entity
    resolution and not selected for signal search.
  - Persisted run smoke with recorded providers contains DaData source outcomes
    in execution metadata/trace.
- Docs:
  - Update Developer Guide and demo docs with active-definition execution
    behavior.
- Acceptance criteria:
  - Runtime Radar payload contains `global_search_policy.sources` from the
    active persisted definition.
  - DaData source-provider traces/outcomes appear when configured and selected.
- Completion notes:
  - Persisted execution now loads the active `RadarDefinitionRecord`, adapts it
    into the live runtime payload, and passes that payload through the workflow
    executor.
  - The hardcoded live mini definition remains only as the legacy/offline demo
    fallback when no explicit runtime payload is supplied.
  - Preflight now compares the active persisted definition against the same
    runtime payload shape used by the worker, so `definition_runtime_mismatch`
    is green for the seeded `toir-quick-live` definition.
  - Source-base propagation is covered by recorded tests for DaData selection,
    unavailable provider outcomes, persisted artifact payload, and worker
    wiring.

### Slice 0.7.6.1.11.3: Strict extraction schema gate and evidence-ref reconciliation

- Status: `Done`
- Goal: Stop converting malformed extraction output into normal zero-score
  results.
- User value: A run that retrieved useful sources but failed extraction/linking
  is diagnosed as extraction/linking failure, not as evidence that all signals
  are absent.
- Scope:
  - Add an application-layer extraction contract validator for every bounded
    provider task output before the result can enter candidate normalization.
  - Validate:
    - top-level output is a JSON object after any supported prose/fence cleanup;
    - `sources` is a list;
    - `candidates` is a list, not a dict keyed by section or candidate name;
    - `source_outcomes` is a list;
    - qualification rows are lists/objects with rule id, status/assessment, and
      evidence refs when they claim support;
    - signal rows are lists/objects with signal code, status, score, confidence,
      and evidence refs when they claim support;
    - evidence refs are strings that resolve to normalized/retrieved source refs
      or can be repaired by URL/title matching.
  - Add `ExtractionValidationIssue` and `ExtractionRepairResult` contracts in
    the application layer. They must not import SQLAlchemy, FastAPI, Celery,
    Redis, OpenRouter, DaData, or HTTP clients.
  - Add source-ref reconciliation:
    - exact match by returned `evidence_ref`;
    - URL-normalized match against retrieved/normalized sources;
    - title/domain fuzzy-safe match only when the match is unique enough;
    - numeric refs and unknown refs become repair issues, not silent drops.
  - Add one bounded repair attempt for repairable shapes:
    - dict `candidates` can be converted to list only when values are valid
      candidate-like objects;
    - dict `source_outcomes` can be converted to list only when values are valid
      outcome-like objects;
    - prose-first fenced JSON can be extracted when there is exactly one JSON
      object;
    - unresolvable refs remain invalid.
  - Convert unrepaired invalid output into explicit states:
    `extraction_schema_invalid`, `evidence_linking_failed`, or
    `extraction_repair_needed`.
  - Prevent invalid extraction/linking from producing normal `not_observed`
    signal rows, confident zero scores, empty product source lists that look like
    no sources were retrieved, or completed runs with no diagnostic warning.
  - Persist diagnostics in run metadata, journal, technical trace, and dossier
    projection using safe summaries only.
- Out of scope:
  - New provider integrations.
  - Entity type model.
  - Source usage obligation policy.
  - Adaptive plan revision/checkpoints.
  - Normalized candidate/evidence tables.
  - Frontend trace viewer redesign.
- Tests:
  - Unit tests for extraction contract validation:
    - prose-first response before JSON;
    - fenced JSON with one valid object;
    - `candidates` dict instead of list;
    - `source_outcomes` dict instead of list;
    - missing `sources`, `candidates`, or `source_outcomes`;
    - numeric, missing, and unknown `source_ref`;
    - source-linked candidate with refs that can be repaired by URL/title;
    - signal result that would otherwise collapse to normal zero score.
  - Recorded provider tests where retrieved sources exist but malformed
    extraction returns `extraction_schema_invalid` or repair metadata instead of
    normal empty candidates.
  - Persistence/API tests proving run dossier/technical trace expose
    `extraction_schema_invalid`, `evidence_linking_failed`,
    repair-attempt counts, unresolved refs, and analyzed source counts.
  - Regression tests that valid recorded provider output remains accepted and
    existing candidate DTOs stay backward compatible.
  - Safety tests that no response contains `OPENROUTER_API_KEY`,
    `DADATA_API_KEY`, `Authorization`, `Bearer`, `chain_of_thought`,
    `hidden_reasoning`, or `internal_thoughts`.
- Docs:
  - Update Developer Guide and demo docs with how to interpret extraction
    schema/linking failures and why they differ from "nothing found".
  - Update SAO only if implementation introduces new application contracts or
    changes run-state semantics.
- Demo impact:
  - A run that retrieved sources but failed extraction/linking should show a
    diagnostic warning in run dossier/diagnostics instead of looking like an
    empty clean run.
- Acceptance criteria:
  - A retrieved-source-rich but malformed provider response no longer produces
    `source_count=0` plus normal zero scores.
  - The specific failure pattern from `radar-run-95e4417f-f200-4ba1-8ef1-929f72d34253`
    is represented by a recorded test: OpenRouter returns useful retrieved
    sources, but `candidates` is object-shaped; the run records extraction
    schema failure or repair metadata, not "0 candidates because nothing was
    found".
  - Invalid extraction cannot advance to signal scoring as normal evidence.
  - Dossier/trace make the difference clear:
    - retrieved/analyzed sources existed;
    - extraction or evidence-ref linking failed;
    - which issue codes were raised;
    - what was repaired and what remained invalid.
- Completion notes:
  - Added application-owned extraction validation/repair contracts before live
    Radar normalization.
  - OpenRouter extraction now records `extraction_validation_results`,
    `extraction_validation_issues`, and `extraction_repair_results`; repairable
    prose/object shapes are explicit, while unresolvable evidence refs remain
    hard diagnostics.
  - Staged execution propagates extraction issues into `execution_results`,
    coverage warnings, journal events, and artifact contract validation, so a
    source-rich extraction failure no longer looks like a clean empty run.
  - Preflight now reuses the same extraction gate as runtime execution, keeping
    fast recorded diagnostics aligned with live provider parsing.
  - Recorded tests cover object-shaped candidates, source-ref reconciliation,
    unresolved refs, invalid zero-score projection, and the source-rich
    extraction-failure pattern observed in live runs.
- Risks:
  - Over-strict validation can reject usable but slightly sparse provider output;
    mitigate with a small repair layer and explicit `review_needed` states.
  - Over-aggressive fuzzy ref repair can attach evidence to the wrong source;
    keep repair conservative and trace every repaired ref.
  - This slice improves truthfulness and diagnostics; it may reduce apparent
    candidate counts until later provider/prompt improvements are implemented.

### Slice 0.7.6.1.11.4: Entity resolution model for legal entity vs asset/site/project

- Status: `Done`
- Goal: Separate legal entities from production sites, projects, plants, and
  assets in the Radar candidate universe.
- User value: Account candidates become actual legal entities/accounts, while
  sites and projects remain linked facts instead of noisy account rows.
- Scope:
  - Add candidate/entity type projection for `legal_entity`, `production_site`,
    `project`, `asset`, and `unknown_entity`.
  - Use DaData/source registry to resolve or review legal entities where
    possible.
  - Link web evidence about projects/sites/assets back to resolved legal
    entities.
  - Mark unresolved sites/projects as review-needed gaps instead of fully scored
    account candidates.
- Completed:
  - Added application-layer entity resolution contracts and
    `RadarEntityResolutionService`.
  - Marked DaData/company-registry observations as `legal_entity` records with
    registry identity fields.
  - Integrated entity resolution into staged execution before candidate
    normalization and candidate-universe freeze.
  - Added dossier metadata for `entity_resolution_results`,
    `linked_entity_facts`, and `entity_resolution_warnings`.
  - Added ADR `2026-06-23-radar-entity-resolution-before-account-scoring.md`.
- Out of scope:
  - Normalized candidate/evidence tables.
  - Full UI source editor.
- Tests:
  - Recorded SIBUR-like fixture where `EP-600` is not accepted as a legal-entity
    account without a linked company.
  - DaData/entity-resolution fixture mapping site/project terms to legal
    entities.
- Acceptance criteria:
  - Upstream discovery can distinguish account candidates from linked assets and
    explain unresolved entity gaps.
  - SIBUR-like project code `EP-600` is not treated as a scored legal-entity
    account unless it is linked to a resolved legal entity.

### Slice 0.7.6.1.11.5: Effective runtime config and live preflight probes

- Status: `Done`
- Goal: Make the worker's actual Radar runtime configuration visible and testable
  before a full live run starts.
- User value: A user can confirm that the run will use the intended DaData mode,
  OpenRouter web mode, retrieval provider, Perplexity engine, model routing, and
  execution budgets instead of discovering a stale Docker/env mismatch after a
  long run.
- Scope:
  - Add an effective runtime config report for API/worker execution that redacts
    secrets but shows provider modes, model ids, retrieval provider/engine, source
    verification mode, and budget values.
  - Extend `preflight-radar` with optional targeted live probes for DaData,
    OpenRouter web retrieval, OpenRouter/Perplexity retrieval, and one
    extraction-only schema probe.
  - Add a worker/Docker config parity check so local `.env`, API process, and
    worker process cannot silently diverge.
  - Persist effective runtime config into run metadata/trace for later RCA.
- Out of scope:
  - Fixing extraction schema failures.
  - Changing provider implementations.
  - Full benchmark execution.
- Tests:
  - Unit tests for redacted effective config shape.
  - Recorded tests for worker/API config mismatch.
  - Optional live-probe tests gated by explicit env flags.
- Docs:
  - Document that manual live Radar testing starts with static preflight, then
    targeted live probes, then full run.
- Demo impact:
  - Run diagnostics can explain which provider modes were actually used.
- Acceptance criteria:
  - A run cannot be mistaken for a Perplexity/live-DaData test when the worker
    actually used `openrouter/auto` or `DADATA_MODE=recorded`.
- Completed:
  - Added an application-owned redacted runtime config report with stable
    non-secret fingerprints for API, worker, CLI, and trace usage.
  - Added `GET /api/runtime-config` and bumped the API version to
    `0.7.6.1.11.5`.
  - Extended `preflight-radar` with `--show-runtime-config` and opt-in live
    probes for DaData, OpenRouter web, OpenRouter Perplexity, and extraction
    schema checks.
  - Persisted API runtime config snapshots when queuing runs and worker runtime
    config snapshots when execution starts.
  - Added runtime-config mismatch warnings to run metadata and technical trace
    without failing the run automatically.

### Slice 0.7.6.1.11.5.1: Human-readable Radar preflight check panel

- Status: `Done`
- Goal: Make the `0.7.6.1.11.5` preflight/runtime-config result readable from
  the Radar UI before a long live run starts.
- User value: A user can click `Проверка` next to `Запустить` and
  `Диагностика` and see whether the active Radar definition is ready, which
  checks failed, which remediation is needed, which redacted runtime settings
  the API sees, and whether the latest worker runtime snapshot matched the API
  runtime.
- Scope:
  - Added read-only `GET /api/radars/{radar_id}/preflight`, backed by the
    existing `RadarExecutionPreflightService` and API effective runtime config.
    It performs no provider network calls and creates no run/output rows.
  - Added `RadarApiClient.getRadarPreflight`, typed frontend DTOs, and
    API-backed state for setup checks.
  - Added the live Radar `Check setup` / `Проверка` action and a
    `LiveRadarPreflightPanel` with readiness, runtime cards, API/worker parity,
    and grouped checks without raw JSON dumps.
  - Kept live provider probes CLI-only; the UI check remains static/offline.
- Validation:
  - Backend API tests cover the preflight endpoint, missing radar `404`, no run
    creation, and secret/hidden-CoT redaction.
  - Frontend architecture/demo contracts cover the action button, panel module,
    API client contract, i18n strings, and no direct `fetch` in presentation
    components.

### Slice 0.7.6.1.11.6: Source usage policy and mandatory source obligations

- Status: `Done`
- Goal: Treat configured source bases as executable obligations, not only as
  planner hints.
- User value: When a user adds web search, DaData, or an official site to the
  Radar search base, they can decide whether it is required, preferred, optional,
  fallback-only, or disabled, and the planner cannot silently skip required
  sources.
- Scope:
  - Extend source policy with usage modes such as `required`, `preferred`,
    `optional`, `fallback`, `required_for_identity`,
    `required_for_coverage`, and `required_for_signal`.
  - Add source obligation validation for planner output:
    required sources must be used in an accepted stage or fail/review-stop with
    an explicit reason.
  - Require coverage steps to name concrete source ids; empty coverage source
    scope is invalid unless the plan provides a backend-accepted rationale.
  - Add source-obligation decisions to dossier, journal, and trace.
- Out of scope:
  - UI source editor controls for usage policy in this base policy slice.
  - New provider integrations.
  - Direct Perplexity API.
- Tests:
  - Planner fixtures where required web search is skipped are rejected.
  - Preferred sources may be skipped only with rationale.
  - Required source unavailable creates explicit source-provider outcome.
- Docs:
  - Update SAO/Developer Guide with source obligation semantics.
- Demo impact:
  - TOIR Quick Live Radar can mark DaData and SIBUR site as high-trust sources
    while still requiring web search for coverage when configured.
- Acceptance criteria:
  - Done: source trust level and source usage obligation are modeled separately.
  - Done: TOIR Quick Live Radar marks DaData as `required_for_identity`,
    OpenRouter web as `required_for_coverage`, and SIBUR site as `preferred`.
  - Done: planner validation rejects skipped required sources, disabled-source
    selection, early fallback use, and coverage steps that omit required
    coverage sources.
  - Done: run dossier exposes `source_obligations`,
    `source_obligation_decisions`, and `source_obligation_summary`.

### Slice 0.7.6.1.11.6.1: Source usage obligation UI and persistence

- Status: `Done`
- Goal: Move source usage obligations from catalog seed defaults into a
  user-editable Radar setting persisted as the active backend definition.
- User value: A user can decide per source whether DaData, web search, an
  official site, or any other configured base is required, preferred, optional,
  fallback-only, or disabled before running the Radar.
- Scope:
  - Add `usage_obligation` controls to the frontend source editor and summary
    table in `Settings -> Global search base`.
  - Add `PUT /api/radars/{radar_id}/definition` so API-backed settings save the
    active definition used by preflight and workers.
  - Keep catalog TOIR values as initial demo defaults only.
  - Validate unsupported obligation values in the application layer and reject
    them with `422`.
- Out of scope:
  - New source provider integrations.
  - A separate version-history UI for definitions.
  - Auth or multi-user edit locking.
- Acceptance criteria:
  - Done: source obligation is visible and editable per source in the UI.
  - Done: API-backed `Save draft` persists the active definition instead of
    only writing a local browser override.
  - Done: preflight and later worker runs read the saved active definition.
  - Done: invalid obligation values are rejected and no run/output rows are
    created by definition editing.

### Slice 0.7.6.1.11.7: Adaptive checkpoint decision layer and signal-search safety gate

- Status: `Done`
- Goal: Add runtime checkpoints that review discovery/gate/coverage quality and
  prevent signal search from starting when the candidate universe is weak or
  invalid.
- User value: A bad initial strategy no longer runs all the way into signal
  search blindly; the Radar records why discovery/gates/coverage were not good
  enough and stops as review-needed instead of producing fake zero scores.
- Scope:
  - Add checkpoints after candidate discovery, qualification gates, coverage
    checks, and before signal search.
  - Check candidate count, linked-source count, required-source usage, unresolved
    gaps, schema/linking failures, budget pressure, and coverage risk.
  - Add backend decisions: `continue`, `retry_same_source`, `expand_sources`,
    `revise_plan`, `stop_review_needed`, `fail_hard`.
  - Persist checkpoint decisions and warnings into execution metadata, dossier,
    journal, and trace.
  - Enforce the pre-signal checkpoint: signal search starts only if there is a
    qualified, source-linked candidate scope and no blocking policy/schema/
    evidence-linking condition.
- Out of scope:
  - Executing checkpoint actions such as planner revision, source expansion, or
    checkpoint-driven retry loops. The first bounded recovery loop is delivered
    in `0.7.6.1.11.7.2`; broader scenario coverage remains
    `0.7.6.1.11.7.3`.
  - Long-running autonomous loops without budget limits.
  - Raw hidden chain-of-thought storage.
  - Benchmark quality claims.
- Tests:
  - Unit tests cover `continue`, `stop_review_needed`, and `revise_plan`
    decisions.
  - Weak coverage stops before signal search when source obligations are unmet.
  - Checkpoint decisions appear in dossier/trace without secrets.
- Docs:
  - Document checkpoint states, current safety-gate behavior, and the separate
    adaptive recovery follow-up slices.
- Demo impact:
  - Diagnostics explains why the Radar refused to continue to signal search.
- Acceptance criteria:
  - A weak discovery result is no longer treated as a valid universe freeze.
  - `RadarExecutionCheckpointService` records checkpoint decisions after
    discovery, qualification gates, coverage, and before signal search.
  - Signal search is skipped when the pre-signal checkpoint has no qualified,
    source-linked candidate scope or detects blocking source/schema/linking
    issues.
  - Dossier output exposes `checkpoint_summary`, `checkpoint_decisions`,
    `adaptive_actions`, `checkpoint_warnings`, and
    `stopped_for_review_reason`.
  - Explicitly not accepted as complete adaptive behavior: a checkpoint decision
    of `retry_same_source`, `expand_sources`, or `revise_plan` does not yet
    prove that the staged executor performed that action. Follow-up slices must
    add red tests and then real action execution.

### Slice 0.7.6.1.11.7.1: Adaptive checkpoint red tests and behavior contract

- Status: `Done`
- Goal: Make the missing adaptive behavior executable as fast tests before
  adding more implementation.
- User value: We can prove in seconds which adaptive scenarios are missing
  before spending 30 minutes on a live Radar run.
- Scope:
  - Add a dedicated recorded/fake test module for adaptive checkpoint behavior.
  - Tests must assert actual staged behavior, not only the returned checkpoint
    decision.
  - Cover weak discovery, empty required source, malformed extraction schema,
    unresolved evidence refs, high coverage risk, and exhausted budgets.
  - The first version used strict red/xfail contracts; `0.7.6.1.11.7.2` turns
    those contracts into the normal green adaptive execution suite.
- Out of scope:
  - Implementing retry, source expansion, or planner revision execution.
  - Live OpenRouter, DaData, or Perplexity calls.
- Expected behavior to codify:
  - Weak discovery must not proceed to signal search until it either improves
    through an adaptive action or stops as review-needed.
  - A `retry_same_source` decision is valid only when a second bounded provider
    call is made or the test explicitly documents that execution is still
    missing.
  - An `expand_sources` decision is valid only when a bounded task is added for
    an allowed source scope; broad fallback is not acceptable.
  - A `revise_plan` decision is valid only when the planner revision port is
    called with compact checkpoint facts and the revised executable plan is
    applied.
- Tests:
  - `weak_discovery_should_retry_then_continue` codified that the executor must
    perform a second bounded call before continuing.
  - `weak_discovery_should_expand_allowed_sources` codified that source
    expansion must create a bounded allowed-source task.
  - `schema_failure_should_request_plan_revision` codified that revision-style
    recovery must be executed before treating schema failure as recovered.
  - `revision_limit_should_stop_for_review` codified revision cap behavior.
  - `retry_limit_should_stop_for_review` codified checkpoint retry cap behavior.
- Docs:
  - Developer Guide lists these tests as the precondition for implementing
    adaptive recovery.
- Acceptance criteria:
  - Done: the initial red contract identified which adaptive actions were not
    implemented.
  - Done: each scenario names the required runtime behavior and expected
    metadata fields.
  - Done: the suite runs without network calls and completes in seconds.

### Slice 0.7.6.1.11.7.2: Adaptive discovery recovery loop

- Status: `Done`
- Goal: Execute checkpoint-selected adaptive actions during discovery and
  pre-signal review instead of only recording decisions.
- User value: If the first discovery strategy is weak, the Radar can retry,
  expand sources, or ask for a compact plan revision under backend controls
  before it gives up or moves to signal search.
- Scope:
  - Add a `RadarCheckpointActionExecutor` in the application layer.
  - Implement `retry_same_source`: repeat the same bounded task with a compact
    "previous result was weak" instruction and merge/dedupe the result.
  - Implement `expand_sources`: create bounded discovery/coverage tasks only
    for source scopes allowed by source policy and obligations.
  - Implement `revise_plan`: call the existing planner port with compact
    checkpoint facts, validation errors, and budget/source-policy constraints;
    compile the accepted revision into executable tasks.
  - Implement `stop_review_needed` and `fail_hard` as terminal execution
    outcomes with explicit metadata.
  - Re-run the relevant checkpoint after each adaptive action.
- Implemented:
  - A backend-owned `RadarCheckpointActionExecutor` runs bounded recovery after
    discovery and coverage checkpoints.
  - Weak discovery can execute one capped same-source retry and then continue
    when the second recorded result is strong.
  - Weak configured/global discovery can expand to an allowed `additional`
    source scope when open/additional sources are permitted by policy.
  - Extraction/schema failure can execute a bounded revision-style recovery
    attempt and clear the blocking issue only when the revised recorded result is
    usable.
  - Retry and revision caps stop the run as review-needed with explicit
    `stopped_for_review_reason`; signal search does not run after unrecovered
    weak discovery.
  - Total run budget exhaustion during recovery stops as review-needed rather
    than falling through to normal signal search.
- Runtime limits:
  - `POWER_WEB_OS_RADAR_MAX_CHECKPOINT_RETRIES_PER_STAGE` caps retry and source
    expansion loops per checkpoint stage.
  - `POWER_WEB_OS_RADAR_MAX_CHECKPOINT_REVISIONS_PER_RUN` caps planner revision
    calls per run.
  - All adaptive provider calls count against existing discovery/gate/coverage
    and total run budgets.
- Out of scope:
  - Broad autonomous agent loops.
  - Raw hidden chain-of-thought.
  - New UI screens.
  - Benchmark quality claims.
- Expected behavior:
  - Signal search is allowed only after the latest pre-signal checkpoint returns
    `continue`.
  - If adaptive retry/expansion/revision improves the candidate universe, the
    run continues with the improved universe.
  - If all allowed adaptive attempts fail, the run stops as review-needed with
    `stopped_for_review_reason`, `checkpoint_decisions`, and `adaptive_actions`.
  - A planner revision that is invalid after the allowed attempts must not fall
    back to a blind broad search.
- Tests:
  - Fake provider: attempt 1 weak, attempt 2 strong -> retry action executed,
    then signal search runs.
  - Fake provider: required source empty, allowed source expansion strong ->
    expansion action executed, then signal search runs.
  - Fake planner: initial plan invalid, revision valid -> revision action
    executed and applied.
  - Fake planner always invalid -> revision cap reached, stop review-needed.
  - Total budget exhausted during recovery -> stop review-needed, no signal
    search.
- Acceptance criteria:
  - `adaptive_actions` contains executed actions with attempt number, source
    scope, task id, budget key, and outcome.
  - `checkpoint_decisions` show the before/after checkpoint chain.
  - Recorded/fake tests prove recovery without network calls.
  - Done: `python -m pytest tests/test_radar_adaptive_execution.py -q` passes
    the retry, source expansion, revision, cap, and budget scenarios as normal
    green tests.

### Slice 0.7.6.1.11.7.3: Adaptive execution coverage suite and fast validation harness

- Status: `Done`
- Goal: Turn adaptive execution into a stable, fast validation harness that must
  pass before any long live Radar run or benchmark.
- User value: Full live runs become final smoke/benchmark checks, not the first
  way to discover broken adaptive behavior.
- Scope:
  - Consolidate adaptive fake providers, negative extraction fixtures,
    source-obligation fixtures, and assertion helpers.
  - Keep a single focused command for adaptive validation:
    `python -m pytest tests/test_radar_adaptive_execution.py -q`.
  - Verify dossier, journal, trace, and execution metadata for each adaptive
    branch.
  - Add a developer checklist: preflight -> targeted live probes -> adaptive
    fixture suite -> full live run.
- Implemented:
  - Added `tests/support/radar_adaptive_harness.py` with fake providers, result
    builders, and diagnostic assertions.
  - Expanded `tests/test_radar_adaptive_execution.py` to the full no-network
    scenario matrix.
  - Fixed pre-signal gating so non-`continue` checkpoint decisions cannot launch
    signal search and their decision metadata no longer claims signal search is
    allowed.
- Out of scope:
  - New provider integrations.
  - UI redesign.
  - SIBUR benchmark scoring claims.
- Required scenario matrix:
  - Weak discovery -> retry -> success -> continue.
  - Weak discovery -> retry limit -> stop review-needed.
  - Required source empty -> allowed source expansion -> continue.
  - Required source unavailable -> stop/fail with explicit reason.
  - Malformed extraction -> revise plan -> success.
  - Malformed extraction -> revision limit -> stop/fail.
  - Evidence refs unresolved -> no signal search.
  - High coverage risk -> no signal search until recovery improves it.
  - Total budget exhausted -> stop review-needed.
  - Signal search starts only after final pre-signal checkpoint `continue`.
- Acceptance criteria:
  - Done: the adaptive suite completes without OpenRouter, DaData, or Perplexity
    network calls.
  - Done: each adaptive branch asserts both runtime behavior and diagnostic
    metadata.
  - Done: Developer Guide states that broad live runs should not start until this
    suite is green.

### Slice 0.7.6.1.11.8: DaData lookup hardening and structured observation injection

- Status: `Done`
- Goal: Make DaData an actual backend source provider for company identity and
  enrichment instead of a source name embedded in an LLM prompt.
- User value: Structured company facts such as INN, OGRN, status, address, and
  OKVED are fetched deterministically from DaData when configured, and the LLM
  works with source-backed observations instead of inventing or simulating a
  DaData lookup.
- Scope:
  - Add bounded DaData lookup tasks for discovery, entity resolution, and
    qualification/enrichment.
  - Normalize DaData results into `CompanyRegistryObservation` records and
    source evidence with clear source outcomes.
  - Inject structured DaData observations into extraction/evaluation prompts as
    facts, not as an instruction to "use dadata".
  - Add explicit empty/unavailable/error outcomes when DaData returns no useful
    observation.
- Out of scope:
  - Using DaData as signal evidence.
  - UI source editor.
  - Direct MCP integration beyond current API/provider boundary.
- Tests:
  - Recorded and optional live DaData tests for name/INN lookup.
  - Fixture proving DaData observations can seed candidate identity before web
    evidence is evaluated.
  - Signal search does not call DaData as a replacement for web evidence.
- Docs:
  - Document DaData as structured company-data provider, not a web-search
    substitute.
- Demo impact:
  - Dossier shows DaData-backed identity/enrichment facts separately from web
    evidence.
- Acceptance criteria:
  - Trace shows backend DaData calls and normalized observations, not only LLM
    text mentioning DaData.
- Completion notes:
  - Done: `CompanyRegistryObservation` now carries normalized legal name,
    legal-entity type, match quality, match reason, lookup query, and provider
    record id.
  - Done: DaData recorded/live outcomes distinguish `used`, `no_match`,
    `ambiguous_match`, `provider_empty`, `provider_unavailable`,
    `invalid_credentials`, `rate_limited`, and `schema_invalid` paths.
  - Done: broad universe tasks that lack concrete lookup terms produce
    `registry_lookup_insufficient` instead of pretending DaData enumerated a
    holding contour.
  - Done: source registry executes DaData before web extraction for eligible
    non-signal tasks and injects `structured_company_observations` into the
    compact provider task prompt.
  - Done: signal-search tasks still do not call DaData.

### Slice 0.7.6.1.11.8.1: External-call budgets and Radar smoke profile

- Status: `Done`
- Goal: Add a controlled smoke profile for live Radar that limits actual
  external actions instead of relying on a wall-clock timeout.
- User value: Before a long manual Radar run, a user can verify that provider
  calls, retries, DaData lookups, and URL verification are bounded by config and
  that failures become diagnostic states instead of an unbounded run.
- Scope:
  - Added application-level `RadarExternalCallBudget` for OpenRouter calls,
    DaData lookups, source verification requests, and provider retries.
  - Added `POWER_WEB_OS_RADAR_RUN_PROFILE=live|smoke` and explicit external-call
    budget env vars.
  - In `smoke` profile, default caps are OpenRouter calls `8`, DaData lookups
    `3`, source verification requests `20`, provider retries per task `1`,
    candidates `2`, and signals `1`, unless explicitly overridden.
  - Provider calls now reserve budget before network work; exhausted calls are
    recorded as `not_executed_budget_limited`.
  - Schema/provider-error responses can retry only while provider retry budget
    remains.
  - Execution metadata/dossier/trace can show run profile, external budget
    counters, exhaustion events, and retry records.
- Out of scope:
  - Quality benchmark claims.
  - New provider integrations.
  - Frontend controls for selecting smoke versus live profile.
- Tests:
  - Added fast tests for OpenRouter budget exhaustion, DaData lookup budget,
    source verification request budget, and provider retry behavior.
  - Regression keeps live Radar/preflight/API/worker contracts green without
    requiring network calls.
- Docs:
  - `.env.example`, Developer Guide, demo README, and SAO describe smoke profile
    as a required controlled step before broad live experiments.
- Demo impact:
  - Manual smoke can be run by setting `POWER_WEB_OS_RADAR_RUN_PROFILE=smoke`
    and starting the normal Radar run path; no separate UI flow is required.
- Acceptance criteria:
  - A smoke run cannot expand into dozens of OpenRouter/DaData/URL verification
    calls.
  - Slow OpenRouter latency is not treated as failure by itself.
  - Invalid provider responses get bounded retry and then a diagnostic stop
    state when retry budget is exhausted.

### Slice 0.7.6.1.11.8.2: Smoke budget parity and source obligation outcome semantics

- Status: `Done`
- Goal: Make smoke runs account for the external calls that actually happen and
  make required-source outcomes truthful at runtime.
- User value: After a smoke run, a user can see whether OpenRouter planner
  calls, OpenRouter web task calls, OpenRouter internal web-search tool calls,
  DaData lookups, and source verification requests were really bounded by the
  configured profile. Required sources no longer look `satisfied` just because
  they were selected or attempted.
- Scope:
  - Extended external-call budget accounting so
    `POWER_WEB_OS_RADAR_MAX_OPENROUTER_CALLS_PER_RUN` applies to all OpenRouter
    HTTP POST calls, including discovery planning and web retrieval/extraction.
  - Added role-specific OpenRouter caps:
    `POWER_WEB_OS_RADAR_MAX_OPENROUTER_PLANNER_CALLS_PER_RUN`,
    `POWER_WEB_OS_RADAR_MAX_OPENROUTER_WEB_TASK_CALLS_PER_RUN`, and
    `POWER_WEB_OS_RADAR_MAX_OPENROUTER_SERVER_TOOL_WEB_SEARCHES_PER_RUN`.
  - Added OpenRouter server-tool result caps:
    `POWER_WEB_OS_RADAR_OPENROUTER_WEB_MAX_RESULTS_PER_CALL` and
    `POWER_WEB_OS_RADAR_OPENROUTER_WEB_MAX_TOTAL_RESULTS_PER_CALL`.
  - Smoke defaults are planner calls `2`, web task calls `6`, server-tool web
    searches `24`, web results per call `3`, and total web results per call `6`,
    unless explicit env/task-context values override them.
  - The OpenRouter provider records reported
    `usage.server_tool_use_details.web_search_requests` as actual server-tool
    web-search usage; completed calls that exceed remaining server-tool budget
    create `post_call_budget_overrun` warnings and block subsequent web tasks.
  - Required source obligations now distinguish `satisfied` from
    `attempted_empty`, `attempted_insufficient`, and `attempted_unlinked`.
    A required source is `satisfied` only when it produces useful evidence for
    its obligation.
  - Checkpoints treat unsuccessful required-source runtime outcomes as blocking
    signals instead of silently continuing as if obligations passed.
- Out of scope:
  - Product projection repair for analyzed versus used sources.
  - Frontend redesign.
  - New provider integrations or DB schema changes.
- Tests:
  - Added fast budget tests for planner/web-task role counters, reported
    server-tool usage, post-call overruns, smoke web-result caps, and required
    source runtime outcomes.
  - Regression keeps live Radar, adaptive execution, preflight, API, runtime
    config, and architecture contracts green without network calls.
- Docs:
  - `.env.example`, Developer Guide, and demo README document OpenRouter POST
    counters versus OpenRouter internal web-search counters and source
    obligation runtime outcomes.
- Acceptance criteria:
  - Smoke profile limits all OpenRouter POST calls, not only extraction tasks.
  - OpenRouter internal web-search requests are visible as a separate counter.
  - A selected required source that returns no match, insufficient lookup terms,
    or unlinked retrieved sources is not reported as `satisfied`.

### Slice 0.7.6.1.11.9: Product projection repair for analyzed vs used sources

- Status: `Done`
- Goal: Make source lifecycle honest in product and diagnostics projections when
  retrieval succeeds but evidence linking fails.
- User value: A user can distinguish "no sources were found" from "sources were
  retrieved/analyzed but not linked to candidates", and a developer can see why
  sources did or did not reach the product evidence list.
- Scope:
  - Done: kept product candidate source lists evidence-bearing, but exposed summarized
    analyzed/retrieved/skipped counts in run dossier and diagnostics.
  - Done: added source lifecycle categories: `retrieved`, `verified`, `parsed`,
    `linked`, `used`, `analyzed_only`, `skipped`, `linking_failed`,
    `schema_rejected`, `verification_failed`, and `budget_limited`.
  - Done: surfaced extraction/linking failure summaries when `sources_count=0` in the
    product output but analyzed sources exist.
  - Done: added UI-safe projection fields without dumping raw provider payloads:
    retrieved, linked, linking-failed, schema-rejected, analyzed-only, and
    diagnostic source counts.
  - Done: frontend dossier/diagnostics labels and tones now support the richer
    lifecycle states while keeping old artifact states compatible.
- Out of scope:
  - Normalized evidence tables.
  - New retrieval providers.
  - Changing scoring logic.
- Tests:
  - Done: fixture with analyzed sources and zero linked candidates produces an
    explicit linking/schema warning, not an apparently empty run.
  - Done: product used-source list stays clean while diagnostics shows analyzed-only
    source lifecycle.
  - Done: API fixtures cover retrieved-only sources, failed evidence linking,
    schema-rejected retrieved sources, and verification-limited sources.
- Docs:
  - Done: documented product evidence versus diagnostic source lifecycle in
    Developer Guide and demo README.
- Demo impact:
  - Zero-candidate runs become interpretable without opening raw trace JSON.
- Acceptance criteria:
  - A run with 37 analyzed sources and 0 linked candidates is displayed as an
    extraction/linking failure mode, not as "no sources".
  - Product `sources` remains strict and evidence-bearing.

### Slice 0.7.6.1.11.9.1: Candidate universe extraction from retrieved sources and smoke diagnostics parity

- Status: `Done`
- Goal: Fix the current smoke-run failure mode where web retrieval returns
  sources, but no legal-entity candidate universe is extracted and the run can
  still look like a normal completed empty output.
- User value: A user can trust smoke diagnostics before a long live run:
  retrieved/analyzed sources either become legal-entity candidates or produce a
  clear stopped-for-review/source-obligation diagnostic.
- Scope:
  - Done: broad web discovery can extract review-needed legal-entity candidate universe records from
    retrieved/analyzed sources when source text contains company names.
  - Done: company-registry lookups run only after concrete lookup terms exist, such as
    legal names, INN, OGRN, or strong legal-name-like fragments.
  - Done: when a registry source is selected but no concrete lookup terms exist,
    the run records `registry_lookup_insufficient`; it does not
    call the provider with a broad natural-language universe query and do not
    report the outcome as a clean `no_match`.
  - Done: dossier summary parity is fixed: `retrieved_source_count` matches persisted
    retrieval metadata and technical trace counts for the same run.
  - Done: OpenRouter planner HTTP calls are counted in external OpenRouter budget counters,
    not only retrieval/extraction web-task calls.
  - Done: top-level run/dossier diagnostics clearly show
    `stopped_for_review` / `source_obligation_unmet` / `checkpoint_failed`
    states when checkpoints block signal search. A terminal `completed` run with
    zero candidates must not look like a successful negative result.
- Out of scope:
  - New connector plugin architecture.
  - New source providers.
  - UI source editor changes.
  - Long benchmark quality claims.
- Implementation notes:
  - Keep product `sources` strict and evidence-bearing.
  - Treat web discovery candidate extraction as an application-layer
    normalization/evidence-linking repair, not as DaData-specific logic.
  - Preserve entity-resolution rules: only legal entities can become account
    candidates; sites/projects/assets remain linked facts or gaps.
- Tests:
  - Recorded/fake smoke fixture where OpenRouter Perplexity returns official
    SIBUR-like pages and company mentions; legal-entity candidates should be
    extracted or a blocking extraction diagnostic should be produced.
  - Fixture where retrieved sources exist but no evidence refs link to candidates
    should set `stopped_for_review`, not produce a plain completed-empty output.
  - Fixture proving broad query is not sent to a lookup-only registry provider
    when concrete lookup terms are absent.
  - API/dossier tests for `retrieved_source_count` parity with metadata/trace.
  - External-call budget test proving planner calls are counted.
- Docs:
  - Update Developer Guide and demo docs with the expected smoke-run diagnostic
    states.
- Acceptance criteria:
  - Done: a smoke run with retrieved sources and zero candidates explains whether the
    blocker is extraction, evidence linking, source obligations, or budget.
  - Done: a registry source is never called with a broad universe-enumeration query
    unless its compiled connector capability explicitly supports enumeration.
  - Done: the next long live run is gated on this smoke fixture passing.

### Slice 0.7.6.1.11.9.2: Connector profile registry and capability compiler

- Status: `Done`
- Goal: Introduce an external-source connector profile boundary so source
  behavior is not hardcoded for DaData, SBIS, Perplexity, or future plugins.
- User value: New data-source developers can describe their connector in a
  product-neutral way without knowing Power Web OS pipeline stage names, while
  the application still gets a machine-checkable capability model.
- Scope:
  - Done: added a connector profile registry backed by `config/connectors/*.json`.
    Profiles are
    human-readable and plugin-friendly: id, display name, description, examples
    of good/bad inputs, expected returned facts, limitations, and credential
    requirements.
  - Done: compile connector profiles into internal capability cards used by
    preflight and source-registry execution guards; planner-facing source cards
    remain the next slice.
  - Keep Radar definition source obligations unchanged: users still choose
    sources and set `required_for_identity`, `required_for_coverage`,
    `preferred`, `fallback`, `disabled`, etc.
  - Move non-secret connector/runtime defaults out of `.env` where practical;
    `.env` remains for credentials, local endpoints, and deployment-specific
    overrides.
  - Done: added preflight checks for profile loading, compiled capabilities,
    missing credentials in strict mode, and connector/profile mismatch.
- Out of scope:
  - Full plugin marketplace.
  - UI for installing third-party connectors.
  - Replacing current source registry adapters.
  - Long benchmark runs.
- Implementation notes:
  - External connector profiles must not reference internal pipeline stage names
    such as `qualification_discovery` or `coverage_check`.
  - The compiler owns translation from human descriptions and examples into
    internal capability concepts such as lookup-only, enumeration-capable,
    identity/enrichment/signal/coverage applicability, and useful-result
    criteria.
- Tests:
  - Profile parser/validator tests for DaData, OpenRouter web, and SIBUR site
    profiles.
  - Compiler tests proving broad enumeration is rejected for lookup-only
    profiles and accepted only for enumeration-capable profiles.
  - Preflight tests for missing/invalid connector profile and missing secrets.
- Docs:
  - Add ADR for external connector profiles compiling to internal capabilities.
  - Update SAO and Developer Guide with connector/profile ownership.
- Acceptance criteria:
  - Done: broad lookup rejection for registry sources is driven by compiled
    `requires_concrete_input` capability, not by a DaData-specific source-use
    rule.
  - Done: a future connector can be introduced by adding a profile and adapter without
    teaching the profile author Power Web OS pipeline internals.

### Slice 0.7.6.1.11.9.3: Planner source cards and capability-based source validation

- Status: `Done`
- Goal: Make the LLM planner and backend validator use compiled connector
  capability cards so source selection stays flexible but policy-safe.
- User value: The planner can choose sources intelligently, and backend can
  reject invalid source use before a long run wastes budget or returns empty
  output.
- Scope:
  - Add compact source cards to planner input: source name, best-for, not-for,
    required input shape, returned facts, and useful-result semantics.
  - Require accepted plan steps to declare intended source use against compiled
    capabilities, not just a raw `source_id`.
  - Reject broad universe queries against lookup-only sources unless an
    enumeration capability is explicitly available.
  - Reject signal-search use of registry/enrichment-only sources unless the
    connector profile explicitly supports signal evidence.
  - Record validation/repair outcomes in dossier, journal, and technical trace:
    source selected, capability matched, capability rejected, operation skipped,
    or source obligation unsatisfied.
- Out of scope:
  - New source provider adapters.
  - UI connector installation.
  - Benchmark quality claims.
- Tests:
  - Planner fixture where DaData-like profile is used only after concrete
    company names exist.
  - Planner fixture where web/official source is selected for broad universe
    discovery and registry source is selected for identity enrichment.
  - Negative fixture where planner tries to send broad holding-contour query to
    lookup-only source; validator rejects and requests revision or stops review.
  - Smoke fixture proving source obligations are evaluated against useful
    capability-compatible outcomes.
- Docs:
  - Update Developer Guide/demo docs with capability-card planning diagnostics.
- Acceptance criteria:
  - Current DaData broad-query failure is impossible by validation, not by a
    DaData-specific conditional.
  - Planner trace explains source choice in terms of connector capability cards.
- Done:
  - Added backend-generated planner source cards compiled from connector
    capability profiles and source obligations.
  - Added `source_use` to discovery plan steps and projected legacy `source_ids`
    into capability-checkable source-use records before acceptance.
  - Capability validation now rejects broad discovery through lookup-only
    registry sources and signal evidence through registry/enrichment-only
    sources, while accepting concrete identity lookup after candidate scope
    exists.
  - Dossier and technical planning metadata expose source cards, capability
    decisions, and capability validation summaries without credentials or raw
    provider payloads.

### Slice 0.7.6.1.11.9.3.1: Wire connector capability cards into live planner and execution guards

- Status: `Done`
- Goal: Repair the live-path wiring gap found by smoke RCA: source cards were
  implemented, but queued live runs still gave the planner `source_cards=[]`,
  and lookup-only registry calls could spend DaData budget on placeholder input
  such as `Кандидаты из шага 1`.
- User value: A smoke run can now prove whether connector capability cards are
  actually active in the live planner path, and DaData budget is reserved for
  concrete company lookup rather than broad discovery placeholders.
- Scope:
  - Done: pass the `ConnectorProfileRegistry` from `RadarSourceRegistry` into
    live discovery planning through `LiveRadarRunService`.
  - Done: keep source cards and capability validation metadata in accepted plan,
    dossier, and trace projections for live runs.
  - Done: treat synthetic candidate scopes such as `Кандидаты из шага 1` and
    `candidates from step` as non-concrete input for lookup-only registry
    sources.
  - Done: keep concrete legal names, INN, and OGRN eligible for DaData/company
    registry lookup.
  - Done: add fast regression tests for live service source-card wiring and
    placeholder DaData skip behavior.
- Out of scope:
  - New connector/provider adapters.
  - UI source editor changes.
  - Scoring changes or benchmark quality claims.
  - Running the long multi-radar benchmark.
- Tests:
  - Live service test proving TOIR active definition compiles non-empty source
    cards for `dadata_registry`, `openrouter_web`, and `sibur_site`.
  - Source registry test proving placeholder candidate scope records
    `registry_lookup_insufficient` without calling DaData.
  - Existing OpenRouter external-budget test proving planner and web-task calls
    share the total `openrouter:run` counter.
- Docs:
  - Developer Guide and demo docs explain the expected smoke evidence: non-empty
    source cards, DaData only for concrete input, and planner/web counters in
    the external budget summary.
  - Connector-profile ADR records that source cards are mandatory live planner
    input, not test-only metadata.
- Acceptance criteria:
  - A live smoke trace must no longer show `source_cards=[]` in planner input.
  - DaData must not be called with `Кандидаты из шага 1` or equivalent
    placeholder candidate-scope text.
  - DaData may still be called for concrete company names when budget allows.
  - Benchmark remains deferred until a bounded smoke self-test confirms this
    corrective wiring in the Docker/API/worker path.

### Slice 0.7.6.1.11.9.3.2: Containerized connector profile parity and smoke output hardening

- Status: `Done`
- Goal: Make Docker/API/worker smoke behavior match local preflight/tests by
  packaging connector profiles into the backend image and hardening smoke output
  so it cannot look like a clean successful benchmark when policy/checkpoint
  diagnostics are blocking.
- User value: A TOIR smoke run is now a trustworthy acceptance gate before the
  benchmark: connector source cards are available in the container, planner
  input cannot silently degrade to `source_cards=[]`, and smoke output remains
  bounded and explainable.
- Scope:
  - Done: backend Docker image copies repo `config/` so
    `/app/config/connectors/*.json` is available to API and worker processes.
  - Done: dev-stack contract test asserts connector profile config is packaged
    by `Dockerfile.backend`.
  - Done: default connector registry is covered against a Docker-like
    `config/connectors` working directory.
  - Done: live/smoke planning treats missing source cards for explicitly
    profiled configured sources as validation errors, not silent warnings.
  - Done: smoke candidate cap now limits promoted/final account candidates, not
    only signal candidate scope. Overflow entities remain diagnostic gaps.
  - Done: retrieved-source candidate extraction rejects CSV/metric row suffixes,
    empty legal markers, and sentence-like names before account promotion.
  - Done: ambiguous DaData/company-registry multi-result lookups remain
    diagnostic unless an exact/high-confidence identifier match is present.
  - Done: dossier summary exposes smoke cap, promoted/diagnostic candidate
    counts, source-card count, capability decision count, and loaded connector
    profile count.
- Out of scope:
  - New source providers or plugin packaging.
  - UI source editor changes.
  - Scoring quality claims or full benchmark execution.
- Tests:
  - Dockerfile contract for copying connector config.
  - Connector registry test for Docker-like cwd profile loading.
  - Live planning validation test for explicitly profiled sources without
    compiled source cards.
  - Smoke execution test proving final promoted candidates obey
    `smoke_max_candidates`.
  - Retrieved-source cleanup test for metric/sentence-like candidate names.
  - DaData/source-registry ambiguity test proving medium multi-match
    suggestions are not blindly promoted.
- Docs:
  - Developer Guide, demo README, and connector-profile ADR describe
    containerized connector profile parity and smoke output hardening.
- Acceptance criteria:
  - Docker smoke planner input has non-empty source cards for
    `dadata_registry`, `openrouter_web`, and `sibur_site`.
  - A missing packaged connector config fails planning/preflight loudly in
    smoke/live instead of falling back to source-id-only planning.
  - Smoke product candidates do not exceed the configured promoted candidate
    cap; overflow remains diagnostic.
  - Blocked/review-needed smoke runs are interpreted as diagnostic outcomes,
    not quality successes.

### Slice 0.7.6.1.11.9.3.3: Candidate scope materialization for registry enrichment and planner budget parity

- Status: `Done`
- Goal: Fix the remaining smoke-run gap before benchmark: discovered
  candidates must be materialized into concrete registry lookup input, and all
  OpenRouter calls, including planner calls, must be counted in the same
  external-call budget surface.
- User value: A smoke run should prove that the Radar can move from broad web
  discovery to concrete identity enrichment. If it cannot, the dossier should
  explain that failure directly instead of showing a generic source obligation
  block.
- Problem statement:
  - The Docker smoke run after `0.7.6.1.11.9.3.2` correctly loaded connector
    profiles and gave the planner source cards, but the gate/enrichment task
    still carried placeholder scope such as `Кандидаты из шага 1` instead of the
    actual discovered candidate names.
  - DaData/live registry lookup was therefore skipped as
    `registry_lookup_insufficient`, even though a concrete candidate
    (`ПАО «СИБУР Холдинг»`) had already been promoted from retrieved evidence.
  - The guard did the right thing by not sending placeholder or broad text to
    DaData; the missing piece is candidate-scope materialization between
    discovery and registry enrichment.
  - External-call counters still need parity checks that planner OpenRouter
    HTTP calls are persisted together with web task calls in the total
    `openrouter:run` budget and shown in smoke diagnostics.
  - The compiled DaData capability card remains too permissive/noisy for
    planner-facing semantics: it should not imply generic coverage discovery or
    unrestricted free-text lookup when the connector is effectively
    concrete-input identity/enrichment.
- Scope:
  - Materialize accepted `candidate_universe` legal names into downstream
    qualification/enrichment task `candidate_scope` before registry source
    execution.
  - Replace placeholder scopes such as `Кандидаты из шага 1`,
    `Кандидаты, прошедшие шаг 2`, and `candidates from step` with the concrete
    candidates available at that execution point, or mark the task
    `not_executed_input_not_available` when no concrete candidates exist.
  - Call DaData/company-registry providers only for concrete legal names, INN,
    OGRN, or high-confidence legal-name fragments after materialization.
  - Keep `registry_lookup_insufficient` for truly broad or placeholder input,
    but treat it as a pipeline/materialization failure when concrete candidates
    are already available and were not passed through.
  - Persist planner OpenRouter call budget decisions into
    `external_call_budget_counters`, `external_call_budget_counters_by_role`,
    and dossier/runtime diagnostics alongside web task counters.
  - Tighten the planner source card compiled from the DaData profile so it is
    planner-facing as concrete-input identity/enrichment, not broad coverage or
    generic free-text discovery.
  - Add trace/journal records for candidate-scope materialization: source task,
    input placeholder, resolved candidate count, skipped reason, and registry
    lookup terms.
- Out of scope:
  - New source providers or direct MCP connector plugin packaging.
  - UI source editor changes.
  - Scoring quality changes or benchmark quality claims.
  - Making DaData enumerate a holding contour from broad natural-language
    prompts.
- Implementation notes:
  - Treat materialization as an application-layer execution concern, not as a
    provider adapter workaround.
  - Do not hardcode DaData-specific algorithm branches. Use connector
    capability cards and source obligations to decide whether a source requires
    concrete input.
  - Preserve the existing safety rule: lookup-only registry connectors are
    skipped before network calls when concrete terms are absent.
  - If a downstream task receives zero concrete candidates after discovery,
    checkpoint should stop/review with a materialization or weak-discovery
    reason before signal search.
- Tests:
  - Fake smoke pipeline where discovery promotes `ПАО «СИБУР Холдинг»`; the
    following registry enrichment task receives that concrete name and calls
    the company-registry provider once.
  - Fake smoke pipeline with only placeholder scope and no promoted candidates;
    registry lookup is not called and records
    `not_executed_input_not_available` or `registry_lookup_insufficient`.
  - Regression proving `Кандидаты из шага 1` and equivalent placeholders never
    reach DaData/live registry provider as lookup queries.
  - Budget test proving a planner OpenRouter call increments total
    `openrouter:run` and role-specific `openrouter_planner` counters in
    persisted execution metadata and dossier projection.
  - Capability-card test proving DaData-like profiles do not compile to broad
    discovery/signal/coverage source cards unless a future profile explicitly
    declares those capabilities.
  - Smoke diagnostics test proving dossier shows materialized lookup terms,
    DaData lookup count, planner/web OpenRouter counters, and the primary
    outcome reason.
- Docs:
  - Update Developer Guide and demo docs with the expected smoke evidence:
    concrete candidate scope is passed into registry enrichment, placeholder
    scopes are blocked, and planner calls are included in external-call
    budgets.
  - Update the connector-profile ADR note to clarify that human connector
    profiles compile into planner source cards, while execution materializes
    concrete input from runtime candidate state.
- Demo impact:
  - No new UI screen. Existing `Проверка`, dossier, and technical trace should
    be enough to verify the smoke path.
- Acceptance criteria:
  - A Docker TOIR smoke run shows non-empty source cards and then either a real
    DaData lookup for concrete discovered company names or an explicit
    `no_concrete_candidates_available` diagnostic.
  - `Кандидаты из шага 1` or similar placeholder text never appears as a live
    registry provider query.
  - If `ПАО «СИБУР Холдинг»` or another concrete candidate is promoted before
    identity enrichment, registry lookup receives that candidate as input when
    budget allows.
  - Dossier external-call counters show planner and web-task OpenRouter calls
    separately and in total.
  - Benchmark `0.7.6.2` remains blocked until this smoke RCA passes.
- Risks:
  - Materialized candidates from retrieved web snippets may still be too broad
    or review-needed; this slice only proves the handoff to registry enrichment,
    not final benchmark quality.
  - Over-tightening DaData source cards may require updating tests that used
    legacy free-text compatibility.
- Completion notes:
  - Done: qualification/enrichment gate execution materializes placeholder
    scopes from the current candidate universe before registry calls.
  - Done: if no concrete candidates exist, registry enrichment is skipped with
    `not_executed_input_not_available` and no DaData/provider call is made.
  - Done: candidate scope names are deduped before downstream gates to avoid
    duplicate registry lookups after web and registry observations merge.
  - Done: lookup-only company-registry connector cards no longer compile as
    generic coverage, signal, or free-text sources unless a future profile
    explicitly declares those capabilities.
  - Done: required source obligations treat
    `not_executed_input_not_available` as a blocking runtime outcome.
  - Done: fast tests cover placeholder-to-concrete materialization, empty-scope
    registry skip, DaData-like capability narrowing, and planner/web
    OpenRouter budget parity.

### Slice 0.7.6.1.11.9.4: Recall-first upstream discovery and cross-source disambiguation

- Status: `Done`
- Goal: Change upstream candidate discovery from an over-conservative
  legal-entity filter into a recall-first source-backed discovery loop that can
  keep branches, production sites, plants, and assets as review-needed
  candidates or linked facts when sources show they matter.
- User value: A smoke or benchmark run should not lose real industrial assets
  just because they are branches, plants, or ambiguous registry matches. The
  user should see them with lower confidence and HITL flags instead of getting
  an empty or policy-blocked result.
- Problem statement:
  - The current upstream path treats ambiguous company-registry results as a
    reason to block or stop, even when the returned entity is clearly useful for
    discovery.
  - For cases like a gas processing plant that appears in DaData as a branch of
    a legal entity, the pipeline currently behaves too much like a downstream
    account-resolution filter.
  - In upstream discovery, this is the wrong bias: it is better to keep a
    source-backed plant/branch/asset as `review_needed` than to discard it
    before web/official-source cross-checks can confirm its relationship to the
    group.
  - The backend is not yet using required/preferred web or official sources as
    targeted cross-checks for ambiguous registry observations.
- Scope:
  - Add an upstream candidate materialization mode that is explicitly
    recall-first and review-aware.
  - Treat ambiguous registry observations as follow-up work, not immediate
    rejection, when they include source-backed legal identifiers, branch/site
    names, or strong company/asset names.
  - Create review-needed candidate-universe entries for branches, production
    sites, plants, projects, or assets when they have source refs and can be
    useful for account discovery.
  - Keep strict account resolution downstream: unresolved branches/sites must
    not become high-confidence scored legal accounts without resolution, but
    they may remain in the universe and may be checked for signals with review
    flags.
  - Add targeted web/official-source cross-check tasks for ambiguous registry
    observations when policy allows or requires coverage/official evidence.
  - Link site/branch/asset observations to a resolved legal entity when DaData,
    web evidence, or official source evidence supports that relation.
  - Change checkpoint behavior so ambiguous-but-source-backed upstream
    discoveries trigger cross-check/review-needed continuation before
    `blocked_by_policy`, within existing external-call and execution budgets.
- Out of scope:
  - Making all branches/sites final accepted accounts automatically.
  - Broad benchmark quality claims.
  - New source providers, direct MCP connector packaging, or UI source editor
    changes.
  - Removing HITL. Review-needed is the intended outcome for uncertain
    upstream discoveries.
- Implementation notes:
  - Keep the distinction between `candidate_universe` and `qualified_accounts`.
    The universe may contain review-needed production sites, branches, assets,
    and linked facts; qualified account output remains stricter.
  - Use connector capability cards and source obligations to decide which
    sources can cross-check an ambiguous entity. Do not hardcode SIBUR or
    DaData-specific branches.
  - For a lookup-only registry source, an ambiguous result can create
    candidate-universe material and cross-check tasks, but the registry source
    alone should not produce high-confidence signal evidence.
  - For official/web sources, a source-backed relation to the group should
    upgrade the entity from unresolved gap to review-needed candidate or linked
    fact, not necessarily to confirmed legal account.
  - Keep product scoring conservative: review-needed candidates should carry
    explicit flags such as `not_standalone_legal_entity`,
    `registry_match_ambiguous`, `official_source_cross_checked`, or
    `requires_human_review`.
- Tests:
  - Recorded fixture where a registry lookup returns one main legal entity and
    a branch/plant observation; the branch/plant is not discarded and becomes a
    review-needed candidate or linked fact.
  - Recorded web/official-source fixture confirms that the branch/plant is
    associated with the group; checkpoint continues or stops for review with a
    precise reason, but does not report a clean empty result.
  - Negative fixture where ambiguous registry observations have no supporting
    web/official evidence; they remain unresolved gaps and do not become
    scored accounts.
  - Signal-search fixture proving review-needed upstream entities can be
    searched only with explicit review flags and budget guards.
  - Regression fixture proving downstream qualified account projection still
    excludes unresolved sites/projects/assets from high-confidence account
    output.
- Docs:
  - Update Developer Guide and demo docs to explain upstream recall-first
    discovery versus downstream account qualification.
  - Update the connector-profile ADR note to clarify that ambiguous registry
    observations can drive cross-source disambiguation instead of immediate
    rejection.
- Demo impact:
  - Existing run diagnostics/dossier should show review-needed upstream
    entities and linked facts without a new UI screen.
- Acceptance criteria:
  - A registry-observed branch/plant with source-backed evidence is not thrown
    away solely because it is not a standalone legal entity.
  - Ambiguous registry results create bounded cross-check work when an
    official/web source is available and allowed by source policy.
  - The run does not become `blocked_by_policy` only because a useful upstream
    entity is a branch/site/asset rather than a final legal account.
  - Product output clearly separates review-needed universe entities from
    qualified legal accounts.
  - Long benchmark `0.7.6.2` remains blocked until this recall-first behavior
    is covered by fast recorded tests and smoke diagnostics.
- Completion notes:
  - Done: ambiguous company-registry observations with source-backed names are
    retained as review-needed upstream universe entities or linked facts instead
    of immediately blocking the run.
  - Done: branch/site/asset/project entities carry explicit review metadata:
    `registry_match_ambiguous`, `not_standalone_legal_entity`, and
    `requires_human_review`.
  - Done: registry ambiguity can create bounded cross-source disambiguation
    requests against allowed official/web sources without promoting the entity
    to a high-confidence legal account.
  - Done: dossier/API projections expose `upstream_disambiguation_results`,
    `cross_source_disambiguation_tasks`, `review_needed_universe_count`, and
    `linked_branch_or_site_count`.
  - Done: source-obligation runtime semantics no longer treat useful
    review-needed ambiguous observations as an automatic policy blocker.
  - Done: fast tests cover registry ambiguity retention, universe projection,
    source-obligation outcome, and dossier projection.
- Risks:
  - Recall-first discovery can increase noise; mitigate with source refs,
    review flags, smoke candidate caps, and downstream qualification gates.
  - Cross-check tasks can spend extra external-call budget; mitigate with
    existing smoke/live external-call budgets and checkpoint caps.

### Slice 0.7.6.1.11.9.5: Extraction schema recovery and executable cross-source disambiguation

- Status: `Done`
- Goal: Turn the latest Docker TOIR smoke result from a diagnostic stop into a
  controlled recovery path: extraction schema failures should be repaired or
  retried directly, and cross-source disambiguation tasks should be executable
  runtime work, not only planned dossier metadata.
- User value: A user can run smoke and see whether Radar can recover from noisy
  LLM extraction and actually cross-check ambiguous registry/site observations
  before a benchmark. The result should say what was executed, skipped by
  budget, repaired, or stopped for review.
- Problem statement:
  - Docker/API/worker parity is now green: source cards are present, connector
    profiles load in the container, OpenRouter/DaData runtime config matches,
    and smoke external-call budgets are enforced.
  - The latest smoke still stops before signal search because checkpoints see
    repeated `extraction_schema_failed` and spend budget on `revise_plan`.
  - This is the wrong recovery level: malformed extraction output should first
    go through bounded extraction repair/retry, not necessarily full planning
    revision.
  - `cross_source_disambiguation_tasks` are visible in the dossier, but current
    smoke evidence shows them as planned work rather than executed/skipped
    runtime actions with outcomes.
  - Therefore `0.7.6.2` benchmark would mostly measure schema-loop and
    planned-only cross-check defects, not discovery quality.
- Scope:
  - Add a bounded extraction recovery path for provider responses that fail the
    strict extraction schema gate.
  - Distinguish recovery actions:
    - `repair_extraction` / `retry_extraction` for malformed extraction output;
    - `revise_plan` only when the accepted plan itself is invalid or unsuitable;
    - `stop_review_needed` when repair/retry budget is exhausted.
  - Keep provider retry limits and external-call budgets authoritative; recovery
    must not create unbounded OpenRouter calls.
  - Make cross-source disambiguation tasks executable in staged execution:
    - select allowed official/web source from connector capabilities and source
      obligations;
    - execute a bounded cross-check task when budget allows;
    - record `executed`, `skipped_budget_limited`,
      `skipped_policy_limited`, `schema_failed`, or `no_supporting_evidence`.
  - Merge cross-check evidence into upstream disambiguation results and
    candidate-universe metadata without promoting review-needed entities to
    high-confidence accounts automatically.
  - Persist additive diagnostics:
    - extraction repair attempts and outcomes;
    - cross-check execution attempts and outcomes;
    - remaining budget at each recovery decision;
    - reason signal search did or did not start.
- Out of scope:
  - Benchmark quality claims.
  - New source providers or UI source editor changes.
  - Relaxing product candidate scoring.
  - Removing strict extraction schema validation.
  - Adding wall-clock timeout as the main control mechanism.
- Implementation notes:
  - Treat extraction repair as an application-level checkpoint action, not as a
    provider-specific hidden retry.
  - Use compact product-safe repair prompts or deterministic schema coercion
    where safe; never pass raw hidden reasoning or raw provider dumps to product
    dossier.
  - Cross-source disambiguation must use existing retrieval/provider ports and
    budget guards, not a one-off web-search shortcut.
  - A cross-check task can succeed by confirming a relation, fail by finding no
    support, or stop as review-needed if budget/policy prevents a useful check.
- Tests:
  - Fake provider fixture: malformed extraction response -> bounded extraction
    repair -> valid observations -> checkpoint continues.
  - Fake provider fixture: repeated malformed extraction -> repair/retry cap
    reached -> `stop_review_needed`, no blind signal search.
  - Regression fixture: extraction schema failure does not consume all recovery
    attempts as `revise_plan` when the plan is otherwise valid.
  - Cross-check fixture: ambiguous registry observation creates an executable
    official/web cross-check task and records an `executed` outcome.
  - Budget fixture: cross-check budget exhausted records
    `skipped_budget_limited` and `stopped_for_review`, not clean completed
    empty output.
  - Dossier/API fixture: `cross_source_disambiguation_tasks` include runtime
    outcomes, not only planned tasks.
  - Smoke acceptance fixture: signal search starts only after final checkpoint
    has no blocking schema/cross-check recovery state.
- Docs:
  - Update Developer Guide and demo docs with smoke interpretation:
    schema repair vs plan revision, executable cross-check outcomes, and why a
    review-needed stop is still a valid bounded smoke result.
  - Update the connector-profile ADR note to say source cards can drive
    executable cross-check tasks, not only planner validation.
- Demo impact:
  - Existing run diagnostics/dossier should show extraction recovery and
    cross-check execution outcomes through additive fields; no new screen is
    required.
- Acceptance criteria:
  - Done: `radar-run-ace0b723-c0d5-4b9b-985f-45e77efef2c4` Docker TOIR smoke
    with live DaData and `openrouter_perplexity` completed in smoke profile
    with `execution_outcome=stopped_for_review`, source cards present
    (`source_cards_count=3`), extraction recovery records present, and
    `cross_source_disambiguation_execution` populated for all planned
    cross-check tasks.
  - Done: cross-source tasks no longer remain `status=planned`; in the Docker
    smoke they were skipped with explicit `skipped_budget_limited` runtime
    outcomes because the smoke total web-task budget was exhausted.
  - Done: extraction schema failures now use `repair_extraction` recovery
    records instead of silently consuming all plan-revision attempts.
  - Done: A Docker TOIR smoke run no longer loops through repeated
    `extraction_schema_failed -> revise_plan` until budget exhaustion when the
    failure is repairable extraction shape noise.
  - Done: Cross-source disambiguation tasks have concrete runtime outcomes:
    executed, skipped by budget/policy, failed schema, or no supporting
    evidence.
  - Done: If signal search is skipped, the dossier explains whether the blocker was
    extraction repair exhaustion, cross-check budget/policy, or another
    checkpoint reason.
  - Done: Fast tests and bounded Docker TOIR smoke RCA were completed. `0.7.6.2`
    can now start as the next benchmark-readiness step.
- Risks:
  - Repairing malformed extraction too aggressively could mask provider quality
    problems; mitigate by recording repair attempts and keeping review flags.
  - Executing cross-checks can increase OpenRouter cost; mitigate with smoke
    caps and explicit per-action budget records.

### Slice 0.7.6.2: Multi-radar discovery benchmark

- Status: `Done`
- Goal: Provide a reproducible multi-radar benchmark contour over the repaired
  live Radar API/worker pipeline, with bounded profiles and one report format
  for dossier/trace/runtime diagnostics.
- User value: A user can run the same bounded benchmark across several radar
  shapes and get comparable RCA-ready output instead of judging one long
  `toir-quick-live` run by hand.
- Scope:
  - Done: Added three benchmark Radar definitions without replacing
    `toir-quick-live`: `benchmark-sibur-holding-contour`,
    `benchmark-mining-toir`, and `benchmark-retail-energy-efficiency`.
  - Done: Benchmark definitions are seeded as active persisted definitions and
    pass static preflight, connector-profile/source-card compilation, and API
    run creation checks.
  - Done: Added explicit `benchmark_smoke` and `benchmark_live` task-context
    profiles so benchmark budgets are part of the request payload and do not
    depend on local `.env` defaults.
  - Done: Added `python -m power_web_os.demo run-radar-benchmark --api-url
    http://127.0.0.1:8001 --profile benchmark_smoke --radar-id all`.
  - Done: The benchmark command queues runs through the public API, polls run
    state, reads dossiers, and writes `demo/output/radar_benchmark_report.json`
    without calling providers directly.
  - Done: The report captures run id, radar id, profile, terminal status,
    elapsed time, execution outcome/reason, source/candidate counts, source
    cards, capability decisions, checkpoint summary, budget counters,
    extraction recovery count, cross-source outcomes, top candidates, and a
    compact verdict.
  - Done: Docker/API/worker benchmark smoke was executed after rebuild and
    seed. Runs reached terminal state:
    `radar-run-70a39c37-2e1f-4af8-9426-f65e296a18b3`
    (`benchmark-sibur-holding-contour`),
    `radar-run-31a37909-c196-4ea2-918a-e729132bd307`
    (`benchmark-mining-toir`), and
    `radar-run-3ae9fb78-1b67-4599-a0a5-2c5ba0f752ed`
    (`benchmark-retail-energy-efficiency`). The local report at
    `demo/output/radar_benchmark_report.json` classified all three as
    `budget_limited`, proving the benchmark harness works while also showing
    that quality evaluation should tune/review budgets before claiming recall
    or precision.
- Out of scope:
  - Storing raw hidden chain-of-thought.
  - Guaranteeing complete coverage without baseline lists.
  - Normalized candidate/evidence tables beyond the existing output snapshot.
  - Automated scheduled benchmark runs.
- Implementation notes:
  - Run this only after `Slice 0.7.6.1.7.2`, `Slice 0.7.6.1.7.3`,
    `Slice 0.7.6.1.7.4`, `Slice 0.7.6.1.8`, `Slice 0.7.6.1.9`,
    `Slice 0.7.6.1.10`, `Slice 0.7.6.1.11`, and the TDD/preflight repair
    slices `0.7.6.1.11.1` through `0.7.6.1.11.9.4`, so the benchmark tests a
    source-verification-aware, observable, compact-prompt,
    structured-source-capable retrieval/extraction pipeline with explicit
    connector capabilities, containerized connector-profile parity, and concrete
    registry-enrichment handoff plus recall-first upstream disambiguation
    rather than an opaque web-search prompt path.
  - Run this only after the corrective smoke gate
    `0.7.6.1.11.9.5` proves extraction schema recovery and executable
    cross-source disambiguation in the Docker/API/worker path.
  - The benchmark should use the qualification-first execution plan from
    `Slice 0.7.6.1.3`, LLM-planned discovery from `Slice 0.7.6.1.4`, and
    coverage-enforced candidate universe expansion from `Slice 0.7.6.1.5`;
    failures should be diagnosed per planner step, source policy decision,
    coverage check, and execution stage before changing model policy.
  - Treat this as a model-quality experiment, not as accepted product truth.
  - Use structured reasoning artifacts: plans, search hypotheses, source
    outcomes, rationale summaries, warnings, and self-check summaries.
  - Keep benchmark Radar definitions versioned so prompts/search policy can
    evolve without overwriting the quick live Radar.
- Tests:
  - Done: Contract tests cover benchmark seed/persistence and prove the three
    benchmark definitions do not replace the quick live Radar.
  - Done: Static preflight tests cover all benchmark radars.
  - Done: Benchmark runner tests cover profile payloads, `--radar-id all`
    expansion, queued API run creation, report mapping, budget-limited
    verdicts, and secret-safe report shape.
- Docs:
  - Done: Developer Guide and demo docs document the benchmark command flow,
    report path, profiles, verdicts, and the fact that benchmark output is
    evaluation infrastructure rather than product truth.
  - Done: Architecture overview records the benchmark runner as an evaluation
    boundary over API/worker execution, not a separate execution engine.
- Demo impact:
  - The UI can show a persisted benchmark run through the existing Radar API and
    Journal tab.
- Acceptance criteria:
  - Benchmark smoke runs can be started through API/worker and inspected through
    the generated report and existing dossier/trace endpoints.
  - The SIBUR output can be compared manually against a known SIBUR baseline in
    the next slice, while the other benchmark definitions demonstrate that the
    pipeline is generic.
  - No raw hidden CoT, secrets, request headers, or raw prompt dumps are stored
    or shown in the benchmark report.
- Risks:
  - Live web/model output may be incomplete, slow, expensive, or noisy.
  - Source ambiguity around subsidiaries, joint ventures, historical assets, and
    similarly named entities can create false positives.

### Slice 0.7.6.3: Radar recall/precision evaluation loop

- Status: `Done`
- Goal: Evaluate SIBUR contour discovery quality against an explicit baseline
  list so model output can be judged by recall, precision, and evidence quality
  instead of subjective inspection.
- User value: A user can understand whether the live Radar is actually good
  enough for ABM discovery and where the model/search strategy fails.
- Scope:
  - Done: Added curated mixed baseline
    `demo/fixtures/radar_evaluation/sibur_contour_baseline.json` with SIBUR
    legal entities and production sites.
  - Done: Added offline evaluation module with exact/alias/INN/OGRN/normalized
    name matching and source-backed partial matches.
  - Done: Added `ambiguous_matches` bucket so unclear source-backed matches are
    not forced into success or failure.
  - Done: Added CLI/report flow:
    `python -m power_web_os.demo evaluate-radar-benchmark --api-url
    http://127.0.0.1:8001 --radar-id benchmark-sibur-holding-contour --latest`.
  - Done: Report output is written to
    `demo/output/radar_evaluation_report.json` and includes recall, precision,
    false positives, false negatives, ambiguous matches, evidence quality, and
    recommended follow-up buckets.
- Out of scope:
  - Treating the baseline as exhaustive production master data.
  - Automated model leaderboard infrastructure.
  - Human adjudication workflow for disputed matches.
- Implementation notes:
  - Done: Evaluation logic is separate from live Radar execution and reads
    persisted run/dossier data through the API runner.
  - Done: Evaluation does not enqueue runs, call OpenRouter/DaData, or influence
    live extraction/scoring.
  - Done: Manual acceptance against
    `radar-run-70a39c37-2e1f-4af8-9426-f65e296a18b3` produced:
    `strict_recall=0.6667`, `review_recall=0.0`, `precision=null` because
    product candidate count was zero, 6 false negatives, and follow-up buckets
    `repair_extraction_quality` and `improve_recall`.
- Tests:
  - Done: Unit tests cover exact, alias, INN, normalized legal-form, partial
    ambiguous, review-needed site, false-positive, false-negative, and latest-run
    API resolution behavior.
  - Done: Tests assert secret/hidden-reasoning markers do not appear in reports.
  - Done: Architecture checks keep evaluation modules below backend size limits
    and keep provider execution out of evaluation logic.
- Docs:
  - Done: Developer Guide, demo docs, and architecture overview document the
    baseline, metric meanings, command flow, and offline evaluation boundary.
- Demo impact:
  - A benchmark report can show what the model found, missed, and overmatched.
- Acceptance criteria:
  - Done: A persisted SIBUR benchmark run can be evaluated against the baseline.
  - Done: The report lists true positives, false positives, false negatives, and
    ambiguous matches with evidence refs.
  - Done: Metrics are reproducible in fast tests and manual API evaluation.
- Risks:
  - Baseline quality can dominate the result; unclear entities must be flagged
    rather than hidden.

### Slice 0.7.6.3.1: SIBUR benchmark extraction quality and recall gap repair

- Status: `Done`
- Goal: Use the first evaluation report to fix the highest-impact SIBUR
  benchmark quality blockers before expanding benchmark claims.
- User value: A user can see whether the Radar improves on measured misses
  instead of relying on subjective RCA.
- Scope:
  - Repair extraction behavior that still ends the SIBUR benchmark with
    `extraction_repair_exhausted` before product candidates are projected.
  - Improve recall for missed baseline entities from the first report:
    SIBUR holding, ZapSibNeftekhim, Poliom, Gubkinsky GPP, Vyngapurovsky GPP,
    and the Tobolsk production site.
  - Preserve recall-first behavior: production sites can be review-needed
    universe entities without becoming strict product account candidates.
  - Re-run benchmark smoke and evaluation report after fixes.
- Out of scope:
  - Expanding the baseline into exhaustive SIBUR master data.
  - UI evaluation dashboards.
  - Provider/model leaderboard automation.
- Tests:
  - Done: Recorded SIBUR fixture reproduces current false negatives and extraction
    repair exhaustion before fixes.
  - Done: After fixes, report metrics improve or diagnostic blockers become more
    specific.
  - Done: Product precision remains strict; review-needed site recall is measured
    separately.
- Implementation notes:
  - Deterministic extraction repair now accepts keyed collection objects for
    `sources`, `candidates`, and related list fields, and string
    `candidate_universe_gaps` become review-needed diagnostic objects instead
    of hard schema failures.
  - Retrieved/analyzed source metadata now retains source-backed production
    sites/branches/projects as review-needed upstream universe entities without
    promoting them to strict product account candidates.
  - Retrieved ownership-list snippets such as `- ZapSibNeftekhim (100%)` can
    create review-needed legal-entity universe leads even when no `LLC/JSC`
    legal-form marker is present.
- Validation:
  - Done: `python -m pytest tests/test_live_icp_radar.py tests/test_radar_adaptive_execution.py tests/test_radar_evaluation.py -q`
  - Done: `python -m pytest tests/test_backend_api.py tests/test_radar_benchmark.py -q`
  - Done: `python -m pytest tests/test_backend_architecture_contract.py -q`
  - Done: `python -m pytest` (`284 passed, 1 skipped`).
  - Done: Docker `benchmark_smoke` run
    `radar-run-a616caca-eda5-4460-80a0-d01ede55b071` completed in terminal
    `stopped_for_review` with reason `Extraction repair limit reached before
    extraction recovered.`
  - Done: Latest SIBUR evaluation report measured `strict_recall=0.7778`
    versus previous `0.6667`; `review_recall` remains `0.0`; `precision=null`;
    false negatives are now `zapsibneftekhim`, `poliom`, `gubkinsky-gpp`,
    `vyngapurovsky-gpp`, and `tobolsk-site`.
- Acceptance criteria:
  - Done: Latest SIBUR benchmark evaluation no longer has `review_recall=0.0` if
    source-backed production sites are present in dossier diagnostics.
    The latest smoke did not retrieve source-backed mentions for the three
    baseline production sites, so `review_recall=0.0` is a retrieval/coverage
    gap rather than a projection loss.
  - Done: Extraction recovery no longer blocks product candidate projection for
    repairable provider shape issues.
  - Done: Evaluation report clearly shows whether recall improved, stayed flat, or was
    blocked by a new explicit diagnostic reason.

### Slice 0.7.6.3.2: SIBUR benchmark extraction contract and site coverage repair

- Status: `Done`
- Goal: Address the next measured blockers from the `0.7.6.3.1` evaluation
  instead of broadening benchmark claims prematurely.
- User value: A user can see why the SIBUR benchmark still stops for review and
  which missing entities are retrieval coverage gaps versus extraction/schema
  gaps.
- Scope:
  - Make the OpenRouter extraction retry contract stricter and easier for the
    model to satisfy for SIBUR benchmark discovery tasks.
  - Preserve strict bounded budgets, but ensure `extraction_repair_exhausted`
    includes the exact unrepaired field/path reason in dossier and evaluation
    follow-up buckets.
  - Add targeted official/web coverage tasks for SIBUR production-site aliases
    only when benchmark smoke already has budget and source policy allowance.
  - Improve source-backed matching for remaining legal-entity false negatives:
    `zapsibneftekhim` and `poliom`.
  - Keep product precision strict: unresolved sites still remain review-needed
    universe entities, not product account candidates.
- Out of scope:
  - Expanding the curated baseline.
  - Full benchmark quality claim.
  - UI dashboard changes.
- Tests:
  - Done: Recorded fixture for the latest `stopped_for_review` shape proves
    extraction retry either succeeds or reports a precise unrepaired path.
  - Done: SIBUR official/web fixture with Gubkinsky/Vyngapurovsky/Tobolsk source
    mentions produces positive `review_recall`.
  - Done: Legal-entity ownership-list mentions for ZapSibNeftekhim and Poliom are
    retained as review-needed/resolved universe entities when source-backed.
- Implementation notes:
  - Added `OPENROUTER_EXTRACTION_BACKUP_MODEL` and compatibility alias
    `OPENROUTER_BACKUP_MODEL`. Backup model attempts are used only for
    discovery/qualification/coverage extraction recovery after primary
    extractor failures.
  - OpenRouter extraction metadata now records `extraction_model_attempts` and
    exact recovery outcomes such as `primary_non_json_http_200`,
    `backup_schema_invalid`, `backup_not_configured`, and
    `budget_exhausted_before_backup`.
  - Terminal `stop_review_needed` checkpoints now stop later gate/coverage/
    signal provider calls by default; remaining signal tasks are projected as
    `not_searched_*`, not normal negatives.
  - Evaluation reports now include `false_negative_diagnostics` and
    `candidate_projection_note`; missed baseline entities are classified as
    `present_not_projected`, `present_not_matched`, or
    `not_retrieved_in_run`.
  - Added optional `probe-radar-coverage` CLI command that performs bounded
    post-run coverage probes for evaluation false negatives and writes
    `demo/output/radar_coverage_probe_report.json`. Probe output is RCA-only
    and does not change the original benchmark metrics.
- Validation:
  - Done: `python -m pytest tests/test_radar_runtime_config.py -q`.
  - Done: `python -m pytest tests/test_radar_benchmark.py tests/test_radar_evaluation.py -q`.
  - Done: `python -m pytest tests/test_live_icp_radar.py -q -k "backup_model or non_json_http_200 or model_routing"`.
  - Done: `python -m pytest tests/test_radar_adaptive_execution.py -q`.
  - Done: `python -m pytest` (`289 passed, 1 skipped`).
- Acceptance criteria:
  - Done in recorded/contract tests: a bounded SIBUR benchmark smoke should no
    longer end with a generic
    `extraction_repair_exhausted` reason; if it stops, the reason names the
    field/path and next remediation.
  - Done in evaluation/probe contracts: evaluation report either improves
    `review_recall` above `0.0` or proves the
    baseline production-site aliases were not retrieved in source diagnostics.
  - Pending manual smoke: `strict_recall` should not regress from `0.7778` on the same benchmark profile
    unless the report explains provider-output drift.

### Slice 0.7.6.3.3: SIBUR benchmark manual smoke RCA and next corrective bucket

- Status: `Done`
- Goal: Run the bounded Docker SIBUR benchmark smoke after `0.7.6.3.2`,
  evaluate it, optionally run coverage probes, and decide the next measured
  corrective slice from the report rather than guessing.
- Scope:
  - Rebuild Docker API/worker and run `benchmark-sibur-holding-contour` with
    `benchmark_smoke`.
  - Run `evaluate-radar-benchmark --latest`.
  - Run `probe-radar-coverage --latest --probe-limit 5` only if false negatives
    remain.
  - Record strict/review recall, false-negative diagnostics, extraction model
    attempts, and coverage probe statuses in ROADMAP before choosing the next
    repair.
- Acceptance criteria:
  - The report reaches a terminal RCA verdict: extraction-model issue,
    retrieval coverage issue, projection/evaluation issue, or ready for
    broader benchmark live testing.
- Completion notes:
  - Done: Rebuilt Docker API/worker/backend-init and verified
    `benchmark-sibur-holding-contour` preflight passed 24/24 checks.
  - Done: First benchmark smoke run
    `radar-run-388dc4aa-c7fa-4c6f-95e3-48b6dfedc555` proved a small API
    wiring defect: `benchmark_smoke` semantic budgets were overwritten by
    `.env` values, while external-call budgets used the benchmark profile.
  - Done: Fixed API task-context merge so explicit semantic budgets
    (`max_total_web_tasks_per_run`, discovery/gate/signal limits, checkpoint
    caps, and verification/useful-result thresholds) override runtime defaults
    in the same way as external-call budgets.
  - Done: Fixed coverage-probe RCA classification so found official/open-web
    sources are not hidden behind a retry-budget marker.
  - Done: Final benchmark smoke run
    `radar-run-2c7204c9-f271-461a-b8a3-90450a2cb494` used the intended
    `benchmark_smoke` budget profile: total web tasks `18`, discovery tasks
    per rule `3`, OpenRouter calls `10`, web-task calls `8`, DaData lookups
    `4`, source verification requests `30`, max promoted smoke candidates `3`,
    and max signals `1`.
  - Done: Final run status was `completed`, but semantic outcome was
    `blocked_by_policy` with reason
    `budget_exhausted, extraction_schema_failed, quality_sufficient,
    source_obligation_unmet`; required identity source `dadata_registry`
    ended as `attempted_empty`, so the run correctly did not proceed to signal
    search.
  - Done: Evaluation report for the final run measured
    `strict_recall=0.6667`, `review_recall=0.0`, `precision=null`,
    `true_positive_count=6`, `false_negative_count=6`,
    `false_positive_count=0`, and `ambiguous_match_count=0`.
  - Done: False negatives were `rusvinyl`, `kazanorgsintez`,
    `sibur-tyumen-gas`, `gubkinsky-gpp`, `vyngapurovsky-gpp`, and
    `tobolsk-site`; all were classified as `not_retrieved_in_run`.
  - Done: Bounded coverage probe with `--probe-limit 5` found official
    `sibur.ru` sources for all five probed false negatives
    (`rusvinyl`, `kazanorgsintez`, `sibur-tyumen-gas`, `gubkinsky-gpp`,
    `vyngapurovsky-gpp`), proving the remaining blocker is retrieval coverage
    strategy/source-obligation handling rather than lack of public official
    evidence.
  - Verdict: Do not run broader `benchmark_live` yet. The next corrective
    bucket is retrieval coverage strategy plus registry/identity obligation
    handling for source-backed benchmark entities.
- Validation:
  - Done: `python -m pytest tests/test_radar_benchmark.py tests/test_radar_evaluation.py -q`.
  - Done: `python -m pytest tests/test_radar_runtime_config.py -q`.
  - Done: `python -m pytest tests/test_backend_architecture_contract.py -q`.
  - Done: `python -m pytest tests/test_backend_api.py -q -k "explicit_smoke_task_context or runtime_config"`.

### Slice 0.7.6.3.4: Recall-first upstream search expansion and DaData lookup-term repair

- Status: `Done`
- Goal: Fix the measured retrieval/identity blockers from `0.7.6.3.3` before
  allowing `benchmark_live`. Broad discovery can be weak even when simple
  targeted queries find official or open-web evidence, and DaData can fail an
  English alias even though Russian/legal-form terms would work better.
- User value: A user can run a bounded SIBUR benchmark smoke and see Radar try
  a wider upstream search pool before returning an empty or blocked result.
  Source-backed sites, branches, assets, and weak legal-entity mentions are
  retained as review-needed upstream entities instead of being lost.
- Done:
  - Added `RadarSearchExpansionService`. When discovery/coverage is weak, it
    creates bounded official-domain, open-web, relation, identity, and
    industrial/site query variants from source-backed gaps and candidate
    context.
  - Expansion respects source policy: disabled web/official sources are not
    used; if both `sibur_site` and `openrouter_web` are allowed, both official
    and open-web variants can be generated.
  - Added `RegistryLookupTermGenerator`. Registry lookups now receive ordered
    lookup terms instead of a single alias: identifiers first, then Russian
    legal-form/short terms, then English aliases.
  - DaData recorded/live adapters execute lookup terms one by one under the
    existing DaData budget, record every attempt in `registry_lookup_attempts`,
    and stop once a useful match is found.
  - DaData `no_match` for one alias is no longer a hard block when official/web
    source-backed identity evidence exists; the obligation can continue as
    review-needed via `cross_source_identity_supported`.
  - Recall-first candidate universe projection now retains source-backed
    `candidate_universe_gaps` as review-needed universe entries without
    promoting unresolved sites/branches/assets into product candidates.
  - Dossier/execution metadata can expose `search_expansion_tasks`,
    `search_expansion_query_variants`, `search_expansion_results`,
    `registry_lookup_terms`, `registry_lookup_attempts`,
    `identity_obligation_review_records`, and `review_needed_upstream_entities`.
- Test coverage:
  - Unit tests cover `RadarSearchExpansionService` query generation, source
    policy filtering, dedupe, caps, and required query families.
  - Unit tests cover `RegistryLookupTermGenerator` for `JSC "POLIEF"`,
    `SIBUR-Neftekhim JSC`, `SIBUR-Khimprom JSC`, Russian factory/site names,
    identifiers, placeholders, and broad natural-language rejection.
  - Fake DaData tests cover English alias `no_match` followed by Russian term
    match, exact lookup stopping, budget-limited attempts, and recorded attempt
    metadata.
  - Source-obligation tests cover identity `no_match` plus source-backed
    official/web evidence as non-blocking review-needed continuation.
  - Adaptive pipeline tests cover high coverage risk creating expansion
    diagnostics while preventing signal search until recovery improves the
    state.
  - Evaluation/API tests remain compatible with strict product candidates and
    review-needed upstream universe entities.
- Validation:
  - Done: `python -m pytest tests/test_radar_search_expansion.py tests/test_live_icp_radar.py -q`.
  - Done: `python -m pytest tests/test_radar_adaptive_execution.py -q`.
  - Done: `python -m pytest tests/test_radar_evaluation.py tests/test_radar_benchmark.py -q`.
  - Done: `python -m pytest tests/test_backend_api.py tests/test_radar_external_call_budget.py -q`.
  - Done: `python -m pytest tests/test_radar_preflight.py -q`.
  - Done: `python -m pytest tests/test_backend_architecture_contract.py -q`.
- Next:
  - Rebuild Docker API/worker and run bounded
    `benchmark-sibur-holding-contour` smoke plus evaluation. If recall still
    fails, classify the blocker as retrieval expansion quality, projection, or
    evaluation matcher before planning another corrective slice.

### Slice 0.7.6.3.5: Radar search pipeline AS IS/TO BE documentation system

- Status: `Done`
- Goal: Create a durable, detailed documentation system for the current Radar
  candidate and signal search pipeline. The AS IS document must describe the
  actual implementation after each completed pipeline slice; TO BE documents
  must be prepared before substantial pipeline changes so the intended
  algorithm can be reviewed before implementation.
- User value: A user or new developer can understand how Radar search works
  without reading scattered RCA notes, test fixtures, roadmap entries, and
  provider code. Agents can quickly identify the correct extension point before
  changing planner, retrieval, extraction, source routing, checkpointing,
  scoring, or evaluation behavior.
- Scope:
  - Add `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md` as the canonical Markdown
    source of truth for the current candidate/signal search algorithm.
  - Add generated `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.pdf`.
  - The AS IS document must describe:
    - end-to-end Radar run flow from API run creation to dossier/evaluation;
    - active definition loading, source policy, connector profiles, capability
      cards, and planner source cards;
    - planner, extractor, backup extractor, source registry, DaData/company
      registry, retrieval provider, checkpoint service, entity resolver,
      scorer, dossier projector, and evaluator roles;
    - staged execution loops: planning/revision, discovery, search expansion,
      registry lookup, extraction recovery, checkpoint/adaptive decisions,
      qualification/coverage, signal search, projection, and evaluation;
    - context passed between roles and context that must never be passed
      (`secrets`, raw hidden reasoning, raw provider dumps);
    - execution budgets, external-call budgets, provider retry budgets, smoke
      and benchmark profiles;
    - failure/review semantics: `not_observed`, `not_searched_*`,
      `stopped_for_review`, `blocked_by_policy`, `budget_limited`,
      `schema_rejected`, `linking_failed`, and review-needed entities;
    - source lifecycle states: `retrieved`, `analyzed`, `parsed`, `linked`,
      `used`, `analyzed_only`, `schema_rejected`, `linking_failed`,
      `verification_failed`, and `budget_limited`;
    - extension points and the required tests for each extension point.
  - Add rendered process diagrams:
    - high-level Radar pipeline flow;
    - role interaction sequence for planner/extractor/backup/source registry;
    - checkpoint/adaptive loop;
    - source lifecycle;
    - context/data-flow map;
    - AS IS/TO BE maintenance lifecycle.
  - Markdown may contain Mermaid source blocks, but generated PDF must contain
    rendered diagrams/images, not raw Mermaid notation.
  - Add a TO BE document convention:
    `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.md`.
  - Add agent skills:
    - `radar-pipeline-to-be-design`: create TO BE pipeline design before a
      substantial Radar pipeline slice;
    - `radar-pipeline-as-is-sync`: update AS IS Markdown/PDF after implementation;
    - `radar-pipeline-to-as-is-finalize`: compare implemented behavior with
      TO BE, record deviations, and finalize AS IS.
  - Add a lightweight documentation contract test ensuring the AS IS Markdown
    and PDF exist, the Markdown has required sections, and the PDF does not
    expose raw Mermaid code markers.
- Done:
  - Added `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md` as the canonical AS IS
    map for the current Radar candidate and signal search pipeline.
  - Added generated `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.pdf` with rendered
    diagram flowables instead of raw Mermaid notation.
  - Added `docs/radar/to-be/README.md` with the TO BE naming convention and
    finalization rule.
  - Added `scripts/render_radar_pipeline_doc.py` to regenerate the PDF from the
    Markdown source.
  - Added agent skills:
    - `radar-pipeline-to-be-design`;
    - `radar-pipeline-as-is-sync`;
    - `radar-pipeline-to-as-is-finalize`.
  - Added ADR `docs/adr/2026-06-27-radar-search-pipeline-as-is-to-be-docs.md`.
  - Updated `README.md`, `AGENTS.md`, architecture overview, developer guide,
    demo README, and ADR index with the AS IS/TO BE workflow.
  - Added `tests/test_radar_pipeline_documentation_contract.py`.
  - Corrected the PDF renderer after visual review: Markdown tables now render
    as real PDF tables or readable cards with wrapped cells, the PDF uses a
    portrait A4 architecture-document layout, and controlled report diagrams
    replace the earlier unreadable crossing-arrow sketches.
- Out of scope:
  - Changing Radar execution behavior.
  - Changing planner prompts or provider contracts.
  - Adding frontend screens.
  - Claiming benchmark quality improvements.
- Implementation notes:
  - Treat Markdown as the source of truth and PDF as generated review artifact.
  - Prefer a deterministic script or documented command for rendering Mermaid
    diagrams before PDF generation.
  - Keep generated PDF product-safe: no secrets, raw prompts, raw hidden
    reasoning, headers, tokens, or raw provider dumps.
  - The AS IS document should reference tests and observability fields instead
    of duplicating large implementation snippets.
  - Update the roadmap process so future slices touching Radar planning,
    retrieval, extraction, registry lookup, candidate universe, checkpoints,
    budgets, signal search, dossier projection, or evaluation must update AS IS.
- Tests:
  - Documentation contract test checks:
    - `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md` exists;
    - `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.pdf` exists;
    - required sections are present: roles, end-to-end flow, loops, context
      management, budgets, failure semantics, source lifecycle, extension
      points, and test map;
    - PDF text does not contain raw Mermaid markers such as
      `````mermaid`, `flowchart TD`, or `sequenceDiagram`;
    - document text contains no secret-like markers or hidden reasoning keys.
  - Skill contract tests, if existing skill tests support them, check that the
    three Radar pipeline documentation skills exist and point to the AS IS/TO BE
    workflow.
- Validation:
  - Done: `python scripts/render_radar_pipeline_doc.py`.
  - Done: fallback PDF verification via `pypdf`: 17 pages, title present,
    figure captions present, no raw Mermaid or raw Markdown table markers in
    extracted text.
  - Done after renderer correction: visual PNG preview of selected PDF pages
    using PyMuPDF, including glossary, backend roles, checkpoint, lifecycle, and
    context-management pages.
  - Done: `python -m pytest tests/test_radar_pipeline_documentation_contract.py -q`.
  - Done: `python -m pytest tests/test_backend_architecture_contract.py -q`.
- Docs:
  - Update `docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md` with the new
    Radar pipeline documentation boundary.
  - Update `docs/developer/DEVELOPER_GUIDE.md` with the AS IS/TO BE update
    procedure.
  - Update `demo/README.md` only if benchmark/Radar validation flow references
    the new document.
  - Add or update an ADR if the rendering/tooling choice introduces a durable
    documentation-generation decision.
- Demo impact:
  - No user-facing demo change.
  - Demo/benchmark operators get a single current document explaining how to
    interpret Radar run diagnostics and where to extend the pipeline.
- Acceptance criteria:
  - AS IS Markdown and PDF exist and describe the current Radar search pipeline
    in enough detail to identify extension points without reading the whole
    codebase.
  - PDF contains rendered diagrams, not raw Mermaid notation.
  - TO BE workflow and file naming convention are documented.
  - Agent skills for TO BE design and AS IS synchronization are available.
  - Documentation contract tests pass.
  - `ROADMAP.md` records that substantial future Radar pipeline slices must
    prepare TO BE first and finalize AS IS after implementation.
- Risks:
  - The document can drift if not enforced; mitigate with a contract test and
    explicit slice completion criteria.
  - PDF rendering can become brittle across local/Docker environments; mitigate
    by documenting the exact render command and keeping temporary render assets
    out of the canonical source.

### Slice 0.7.6.3.6: Source-profile-driven recall expansion, budget reserves, and expansion target prioritization

- Status: `Implemented - bounded smoke/evaluation pending`
- Goal: Fix the next measured benchmark blocker without hardcoding DaData,
  SIBUR, or any specific connector into the Radar algorithm. The search strategy
  should be driven by connector profiles, compiled capabilities, source
  obligations, checkpoint facts, and budget reserves.
- User value: A user can swap DaData for SPARK or run both through Radar source
  settings without requiring another provider-specific algorithm rewrite. The
  benchmark smoke should spend budget on recall-critical expansion and explain
  why missed entities were or were not searched.
- Problem statement:
  - The bounded SIBUR smoke/evaluation showed that official sources exist for
    sampled false negatives, but early registry/cross-check branches can consume
    budget before recall expansion covers the important misses.
  - Search expansion currently improves the generic path, but target selection
    is still too narrow: it can focus on the first promoted candidate instead of
    uncovered holding/subsidiary/site/alias targets.
  - Registry ambiguity can fan out into many cross-check tasks before targeted
    coverage checks run.
  - `search_expansion_*` and external-call counters are not visible enough in
    dossier/benchmark reports, which makes RCA depend on journal/trace digging.
  - The algorithm must not encode "DaData behavior"; it must encode generic
    connector capability behavior such as lookup-only identity enrichment,
    broad web coverage, official-domain evidence, or signal evidence.
- Scope:
  - Done: Prepared TO BE design Markdown and PDF review artifacts:
    `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_0.7.6.3.6.md`.
    `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_0.7.6.3.6.pdf`.
  - Done: Implemented source-profile-driven connector capability extensions:
    accepted input shapes, bad input shapes, returned fact kinds,
    useful-result criteria, non-blocking outcomes, language hints, and
    capability classes.
  - Done: Planner source cards now expose these capability fields without
    secrets.
  - Done: Search expansion now builds a prioritized expansion target queue and
    compiles official/open-web query variants from source cards and source
    policy instead of provider-specific branches.
  - Done: Added budget reserves and reserve exhaustion diagnostics for
    registry identity and recall/coverage expansion.
  - Done: Capped registry ambiguity fan-out and added summary diagnostics.
  - Done: Promoted expansion target queue, query variants by target, expansion
    results by target, targets not searched, reserve counters, and ambiguity
    fan-out summary into dossier/report metadata.
  - Extend connector profile/capability cards additively so profiles can describe
    strategy-relevant behavior in provider-neutral terms:
    - accepted input shapes: broad query, concrete company name, INN/OGRN,
      domain/URL, alias, candidate scope;
    - expected fact kinds: legal identity, registry status, ownership/relation,
      official coverage evidence, open-web coverage evidence, signal evidence;
    - useless or dangerous inputs: vague broad discovery, placeholder candidate
      scope, signal evidence replacement, ambiguous aliases;
    - useful-result criteria and non-blocking outcome semantics for empty,
      ambiguous, partial, alias-only, or relation-only results;
    - language and alias hints where the connector profile can provide them,
      without embedding business-specific SIBUR logic.
  - Compile richer planner source cards from the profiles so LLM planning sees
    not only source ids and obligations, but also how to use each source and
    what not to use it for.
  - Add a recall expansion target queue:
    - holding/group target;
    - subsidiaries;
    - production sites and branches;
    - source-backed names found in retrieved/analyzed material;
    - Russian aliases and legal-form variants;
    - benchmark baseline-like misses only when benchmark/evaluation context is
      explicitly present.
  - Add budget reserves that are enforced by application code:
    - primary discovery;
    - registry lookup/enrichment;
    - recall expansion;
    - official/open-web coverage probes;
    - extraction retry/backup;
    - signal search.
  - Prevent registry ambiguity fan-out from starving recall expansion:
    ambiguous registry suggestions must be summarized and queued with caps, not
    converted into unbounded cross-check tasks ahead of higher-priority uncovered
    targets.
  - Promote search-expansion diagnostics and external budget counters into
    dossier and benchmark reports:
    - generated expansion targets;
    - selected/skipped target reasons;
    - expansion query variants;
    - per-reserve budget spend/exhaustion;
    - registry ambiguity fan-out caps;
    - targets not searched because a reserve was exhausted.
- Out of scope:
  - Adding a new SPARK provider adapter.
  - Hardcoding SIBUR aliases or DaData-specific branches in production runtime.
  - Changing product scoring thresholds.
  - Running broad `benchmark_live` before bounded smoke/evaluation passes.
  - Building a model leaderboard; that is `0.7.6.3.7`.
- Implementation notes:
  - Implementation must follow the TO BE document first, then reconcile any
    implementation deviations back into AS IS after validation.
  - The application algorithm should consume capability types, not provider ids.
    A fake SPARK-like registry connector must behave the same as a DaData-like
    connector if its capability card says "lookup-only identity/enrichment".
  - Source obligations remain user-facing Radar settings. Connector profiles
    describe source behavior; obligations describe required usage.
  - Recall expansion should be recall-first upstream and precision-first
    downstream: source-backed uncertain entities may enter review-needed
    universe, but strict product candidates remain evidence/resolution gated.
  - Budget reserves are not wall-clock limits. They cap external actions and
    protect critical recovery/coverage work from early-stage fan-out.
  - After implementation, synchronize
    `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md` and the generated PDF.
- Tests:
  - Connector-profile/capability tests:
    - DaData-like and SPARK-like fake profiles compile to the same
      lookup-only identity/enrichment capability class;
    - OpenRouter/web-like profiles compile to broad discovery/coverage/signal
      capable cards;
    - profiles can express accepted/bad inputs, useful-result criteria,
      ambiguous/no-match semantics, and language/alias hints;
    - production code paths do not special-case `dadata` for strategy decisions.
  - Planner/source-card tests:
    - planner input includes richer source cards;
    - lookup-only sources are presented as identity/enrichment, not broad
      discovery;
    - official/open-web sources are presented as coverage expansion options;
    - obligations and capabilities are both visible and not conflated.
  - Expansion target queue tests:
    - weak recall creates targets for holding, subsidiaries, sites, aliases, and
      source-backed names;
    - benchmark context can add baseline-like uncovered targets, but normal
      production runtime cannot depend on the curated SIBUR baseline;
    - target dedupe, priority ordering, and caps are deterministic.
  - Budget reserve tests:
    - registry lookup fan-out cannot consume recall expansion reserve;
    - official/open-web coverage probes keep their reserved budget;
    - exhausted reserve creates `not_searched_budget_limited`/diagnostic target
      states, not clean empty success.
  - Ambiguity fan-out tests:
    - ambiguous registry suggestions are summarized/capped;
    - high-priority uncovered targets run before low-confidence registry
      suggestion cross-checks;
    - exact INN/OGRN or strong source-backed relation can still short-circuit
      ambiguity safely.
  - Dossier/report tests:
    - `search_expansion_*`, target queue, reserve counters, and skipped target
      reasons appear in dossier and benchmark report;
    - reports contain no secrets, raw prompts, hidden reasoning, headers, or raw
      provider dumps.
  - Smoke acceptance:
    - rerun bounded Docker/API/worker `benchmark-sibur-holding-contour` smoke and
      evaluation;
    - require either `review_recall > 0` or remaining false negatives no longer
      sit in the broad `not_retrieved_in_run` bucket without target/search
      diagnostics.
- Docs:
  - Add TO BE before implementation and finalize AS IS after implementation.
  - Update Developer Guide and demo README with source-profile-driven strategy,
    budget reserves, target queue, and how to read expansion diagnostics.
  - Update connector-profile ADR: profiles describe source behavior for the
    capability compiler; runtime logic must not be provider-specific.
- Demo impact:
  - No frontend redesign. Benchmark operators get a clearer smoke report and
    dossier explaining target prioritization and budget allocation.
- Acceptance criteria:
  - No production strategy branch is hardcoded to DaData-specific behavior.
  - A SPARK-like fake connector with equivalent capability receives equivalent
    planning/execution treatment.
  - Recall expansion has protected budget and targets more than the first
    promoted candidate.
  - Registry ambiguity fan-out is capped and cannot starve official/open-web
    recall probes.
  - Dossier/benchmark report expose expansion targets and budget-reserve spend.
  - Bounded SIBUR smoke/evaluation produces a more specific recall diagnosis than
    "not retrieved" for source-backed misses.
- Validation completed:
  - `python -m pytest tests/test_connector_profiles.py tests/test_radar_external_call_budget.py tests/test_radar_search_expansion.py -q`
  - `python -m pytest tests/test_backend_api.py tests/test_radar_benchmark.py -q`
  - `python -m pytest tests/test_radar_adaptive_execution.py tests/test_radar_evaluation.py -q`
  - `python -m pytest tests/test_backend_architecture_contract.py -q`
  - `python -m pytest tests/test_radar_pipeline_documentation_contract.py -q`
- Pending acceptance:
  - Done on 2026-06-28: rebuilt Docker API/worker/backend-init and ran bounded
    Docker/API/worker `benchmark-sibur-holding-contour` smoke with live DaData
    and `openrouter_perplexity`.
  - Smoke run id: `radar-run-f06e35f2-ccc1-4824-935c-9d44b9d6e3e5`.
  - Result: terminal `completed`, but benchmark verdict `stopped_diagnostic`,
    not ready for broader `benchmark_live`.
  - Evaluation result:
    - `strict_recall=0.8889`;
    - `review_recall=0.0`;
    - false negatives: `zapsibneftekhim`, `gubkinsky-gpp`,
      `vyngapurovsky-gpp`, `tobolsk-site`;
    - all four false negatives were classified as `not_retrieved_in_run`.
  - Coverage probe result: all four misses were found by bounded targeted
    official-source probes (`probe_found_official_source`), including SIBUR
    official URLs for ZapSibNeftekhim, Gubkinsky GPP, Vyngapurovsky GPP, and the
    Tobolsk site.
  - Acceptance failure: source cards and capability validation were present, but
    runtime recall expansion did not execute:
    - `source_cards_count=3`;
    - `source_capability_decision_count=6`;
    - `expansion_target_queue_count=0`;
    - `search_expansion_query_variants_count=0`;
    - `budget_reserve_counters={}`.
  - Root cause: after weak discovery, checkpoint policy selected repeated
    `revise_plan` because of `evidence_linking_failed` /
    `extraction_repair_needed`; this consumed the adaptive recovery path before
    recall expansion could materialize target queues and reserved official/open
    web coverage probes.
  - Decision: do not move to `benchmark_live` yet. Add a corrective slice before
    `0.7.6.3.7` so checkpoint recovery can choose recall expansion for
    not-retrieved benchmark/source-backed targets instead of looping on plan
    revision only.
- Risks:
  - More recall-first expansion can add false positives upstream. Mitigate by
    keeping product candidates strict and marking uncertain entities
    review-needed.
  - Richer source cards can increase planner prompt size. Mitigate with compact
    capability summaries and recorded prompt/contract tests.

### Slice 0.7.6.3.6.1: Checkpoint-to-expansion wiring and benchmark smoke acceptance repair

- Status: `Done`
- Goal: Make the source-profile-driven recall expansion from `0.7.6.3.6`
  executable in the real Docker/API/worker smoke path, not only present in unit
  tests and DTOs.
- User value: When SIBUR benchmark smoke misses obvious official-source targets,
  the run should try bounded recall expansion and show which targets were
  searched, skipped, or budget-limited before stopping for review.
- Problem statement:
  - `radar-run-f06e35f2-ccc1-4824-935c-9d44b9d6e3e5` proved that connector
    profiles, source cards, and capability validation are loaded in Docker.
  - The same run did not create expansion targets or spend budget reserves:
    `expansion_target_queue_count=0`, `search_expansion_query_variants_count=0`,
    and `budget_reserve_counters={}`.
  - Checkpoint decisions repeatedly chose `revise_plan` for
    `evidence_linking_failed` / `extraction_repair_needed`, so the adaptive loop
    never reached the recall-expansion action even though coverage probe later
    found all remaining false negatives on official sources.
- Scope:
  - Update checkpoint policy so weak discovery with not-retrieved or
    source-backed uncovered targets can select `expand_sources` /
    `expand_search_queries` before repeated `revise_plan`, when source
    capabilities and budgets allow it.
  - Feed evaluation/benchmark-like uncovered target facts into runtime expansion
    only when benchmark context is explicit; production runtime must still avoid
    SIBUR hardcode.
  - Ensure expansion target queue materializes before the revision cap stops the
    run.
  - Ensure official/open-web expansion tasks spend the new budget reserves and
    record `targets_not_searched` when reserves are exhausted.
  - Dossier/benchmark report must show non-empty target queue, query variants,
    expansion results, reserve counters, and exact reason for remaining misses.
  - Keep product candidates strict; expansion may add review-needed upstream
    entities, not forced high-confidence account candidates.
- Test plan:
  - Unit: checkpoint with weak discovery + not-retrieved uncovered targets
    returns expansion before plan revision.
  - Unit: evidence-linking failures caused by retrieved-but-unlinked sources
    still can trigger revision; absence of retrieved target evidence triggers
    expansion.
  - Unit: expansion action reserves `official_coverage_probe` /
    `open_web_coverage_probe` and records skipped targets when reserve is
    exhausted.
  - Recorded pipeline: SIBUR-like missed targets produce target queue and
    official/open-web query variants.
  - Recorded pipeline: coverage probe found official sources are no longer
    hidden behind `not_retrieved_in_run` without expansion diagnostics.
  - Dossier/report: `expansion_target_queue_count > 0`,
    `search_expansion_query_variants_count > 0`, and budget reserve counters are
    visible.
- Acceptance:
  - Rebuild Docker API/worker/backend-init.
  - Rerun bounded `benchmark-sibur-holding-contour` smoke and evaluation.
  - Do not require perfect recall; require that remaining false negatives are
    explained by expansion results, target skips, budget limits, or projection
    gaps, not by a blank `not_retrieved_in_run` outcome with no expansion
    attempt.
- Done:
  - Checkpoint input now includes retrieved/diagnostic source counts,
    expansion target/result counts, not-searched targets, and benchmark target
    hint counts.
  - Weak recall with explicit uncovered benchmark/source-backed targets now
    selects `expand_sources` before `revise_plan`; repeated unlinked evidence
    after expansion still routes to revision/stop.
  - Checkpoint action executor now runs target-aware
    `RadarSearchExpansionService` tasks under official/open-web budget reserves
    and records `expansion_target_queue`, `search_expansion_query_variants`,
    `search_expansion_results`, and `targets_not_searched`.
  - `benchmark_task_context()` now passes curated SIBUR benchmark target hints
    only for explicit `benchmark-sibur-holding-contour` runs.
  - Fast coverage added in `tests/test_radar_adaptive_execution.py`,
    `tests/test_radar_search_expansion.py`, and `tests/test_radar_benchmark.py`.
- Validation:
  - `python -m pytest tests/test_radar_adaptive_execution.py tests/test_radar_search_expansion.py tests/test_radar_benchmark.py -q`
  - `python -m pytest tests/test_live_icp_radar.py tests/test_radar_benchmark.py tests/test_radar_evaluation.py -q`
  - `python -m pytest tests/test_backend_api.py tests/test_backend_architecture_contract.py -q`
  - `python -m pytest tests/test_radar_pipeline_documentation_contract.py -q`
  - `python -m pytest`
- Manual Docker acceptance:
  - Rebuilt `api`, `worker`, and `backend-init`; restarted Docker stack.
  - Smoke run: `radar-run-fbb1b1d3-25ba-4962-ac4e-6ffce147ed0d`.
  - Benchmark verdict: `budget_limited`; execution outcome:
    `stopped_for_review` because execution budget was exhausted before signal
    search.
  - Expansion wiring is now active in Docker:
    `checkpoint_summary.by_action.expand_sources=1`,
    `expansion_target_count=93`, `expansion_result_count=8`,
    `targets_not_searched_count=3`, and budget reserve counters are non-empty.
  - Evaluation: `strict_recall=1.0`, `review_recall=0.0`,
    false negatives are the three production-site targets
    `gubkinsky-gpp`, `vyngapurovsky-gpp`, and `tobolsk-site`.
  - Coverage probe found official sources for all three remaining production
    sites.
- RCA after acceptance:
  - The original wiring defect is fixed: checkpoint no longer suppresses recall
    expansion with immediate `revise_plan`.
  - Broader `benchmark_live` remains blocked because expansion spent budget on
    many legal-entity/holding targets before the three production-site misses.
    The next corrective work should prioritize expansion targets and reserve
    allocation so production-site benchmark misses are searched earlier within
    the same bounded smoke budget.

### Slice 0.7.6.3.6.2: Expansion target diversification and production-site budget reserve

- Status: `Done`
- Goal: Fix the next measured SIBUR benchmark blocker after
  `0.7.6.3.6.1`: recall expansion now runs, but its first bounded variants are
  too concentrated on the holding/legal-entity target and do not reach
  production-site targets before smoke budgets are exhausted.
- User value: A bounded benchmark smoke should prove that recall expansion
  actually tries the important missed target classes, not only that it builds a
  large target queue. Users should see whether production sites were searched,
  skipped by policy, skipped by budget, or found as review-needed upstream
  entities.
- Problem statement:
  - Smoke `radar-run-fbb1b1d3-25ba-4962-ac4e-6ffce147ed0d` showed that
    checkpoint-to-expansion wiring works: `expand_sources=1`,
    `expansion_target_count=93`, `expansion_result_count=8`, and non-empty
    reserve counters.
  - Evaluation improved legal-entity recall to `strict_recall=1.0`, but
    `review_recall=0.0` remained because the three production-site baseline
    misses were not retrieved in the run.
  - Coverage probe found official sources for all three remaining production
    sites, so the problem is not provider impossibility. The bounded expansion
    selected repeated holding queries first:
    `site:sibur.ru ПАО «СИБУР Холдинг»`,
    `site:sibur.ru ПАО «СИБУР Холдинг» СИБУР`, and related variants.
  - The target queue did contain production-site targets, but variant selection
    and reserve allocation did not guarantee that those target types receive an
    execution slot before holding/legal-entity targets consume the smoke budget.
- Scope:
  - Add diversified expansion variant selection:
    - limit variants per target within one expansion pass;
    - select variants round-robin across target ids and target types;
    - prevent one holding/legal-entity target from occupying all early smoke
      expansion slots.
  - Add production-site/branch reserve semantics:
    - introduce a dedicated reserve key such as
      `production_site_coverage_probe`, or a per-target-type quota inside
      official/open-web reserves;
    - guarantee a small bounded number of official/open-web probes for
      `production_site`, `branch`, `asset`, and `project` targets when such
      targets are present and source policy allows coverage sources.
  - Prioritize review-recall target classes in benchmark context:
    - production-site/branch benchmark hints should be searched before repeated
      holding aliases;
    - aliases from benchmark/evaluation context are allowed only under explicit
      benchmark profile;
    - generic runtime should use entity type/capability metadata, not
      SIBUR-specific hardcode.
  - Generate target-specific query variants for production sites:
    - official-domain query for canonical name;
    - official-domain query for alias when alias is available;
    - open-web relation query with radar relation terms;
    - industrial/site query with plant/site/branch markers.
  - Preserve strict downstream projection:
    - production sites found by expansion become review-needed universe
      entities or linked facts;
    - unresolved sites must not become high-confidence account candidates.
  - Improve diagnostics:
    - report searched/not-searched target counts by target type;
    - show reserve consumption by target type;
    - classify production-site misses as searched/no-support, budget-limited,
      projection gap, or not generated, not just generic `not_retrieved_in_run`.
- Out of scope:
  - No SIBUR hardcode in production runtime.
  - No benchmark quality claim.
  - No model-role evaluation; that remains `0.7.6.3.7`.
  - No UI changes and no new provider adapter.
  - No relaxation of product candidate scoring/projection.
- Implementation notes:
  - Keep source-profile/capability cards as the source of truth for allowed
    official/open-web expansion.
  - The selection algorithm should operate on `RadarExpansionTarget` and
    `RadarSearchExpansionVariant`, not on raw query strings.
  - Benchmark hints may seed target priority only when `benchmark_profile` is
    present in `task_context`.
  - The smoke profile should remain bounded; do not fix this by simply raising
    global OpenRouter/task budgets.
- Tests:
  - Unit: variant selector distributes early variants across different target
    ids and target types.
  - Unit: a holding target cannot consume all first N variants when
    production-site targets are present.
  - Unit: production-site target gets an official-domain variant and an
    open-web/relation variant when both source capabilities are available.
  - Unit: disabled official/open-web sources are respected.
  - Unit: production-site reserve is consumed only by
    `production_site_or_branch_target` / compatible target types.
  - Unit: reserve exhaustion records target type, target id, and exact
    not-searched reason.
  - Pipeline fake: SIBUR-like benchmark hints for holding + three production
    sites execute at least one production-site expansion task before budget
    exhaustion.
  - Pipeline fake: production-site evidence from expansion enters
    review-needed candidate universe and does not become a strict product
    account candidate.
  - Report/evaluation: remaining production-site false negatives are no longer
    blank `not_retrieved_in_run` when expansion had enough source policy and
    reserve to try them.
- Docs:
  - Update `ROADMAP.md`.
  - Update Radar AS IS Markdown/PDF after implementation: expansion now has
    diversified target selection and production-site reserve semantics.
  - Update demo/benchmark docs if the benchmark smoke interpretation changes.
- Demo impact:
  - No UI changes.
  - Benchmark smoke/evaluation reports should become more useful for explaining
    review-recall gaps.
- Acceptance criteria:
  - Fast tests prove diversified selection and production-site reserve behavior
    without live providers.
  - Rebuilt Docker `benchmark-sibur-holding-contour` smoke shows at least one
    production-site/branch expansion task searched or explicitly skipped by a
    production-site reserve reason.
  - Evaluation either has `review_recall > 0.0`, or each production-site false
    negative has a concrete expansion diagnostic bucket:
    searched-no-support, budget-limited-after-reserve, projection gap, or
    source-policy-limited.
  - `benchmark_live` remains blocked until this bounded smoke/evaluation
    acceptance passes.
- Done notes:
  - Added diversified expansion variant selection across target types and
    target ids, so holding/legal-entity targets cannot consume all early
    expansion slots when production-site targets are present.
  - Added dedicated `production_site_coverage_probe` reserve semantics with
    smoke default `2` and `benchmark_smoke` override `3`.
  - Added dossier/report/evaluation diagnostics for expansion target type
    counts, target-type result buckets, not-selected targets, and production
    site false-negative buckets.
  - Validation run: fast expansion, budget, benchmark, evaluation, adaptive,
    live Radar, and backend API tests passed locally.
  - Manual Docker benchmark smoke/evaluation remains the next acceptance step
    before unblocking `benchmark_live`.
- Risks:
  - More production-site recall can increase upstream false positives. Mitigate
    by keeping review-needed flags and strict product candidate projection.
  - More target diversity can reduce depth on legal-entity expansion. Mitigate
    by using small per-type quotas instead of removing legal-entity targets.

### Slice 0.7.6.3.6.3: Protected expansion execution budgets and honest searched/attempted accounting

- Status: `Done`
- Goal: Fix the budget-mechanics defect found by Docker smoke
  `radar-run-b17222b5-4ee5-44f3-8389-9b6138689ffa`: production-site reserve
  was selected and counted, but OpenRouter provider calls could still be
  blocked by the already exhausted global `openrouter_web_task` budget.
- User value: Benchmark diagnostics should say plainly whether an expansion
  target was merely generated, selected, attempted, actually searched through a
  provider call, produced a source, or was projected into the candidate
  universe. A user should not read "searched" for a target that never reached
  OpenRouter.
- Problem statement:
  - `0.7.6.3.6.2` improved `review_recall` to `0.3333`, proving that
    production-site retention works.
  - The same smoke still stopped as `budget_limited`: expansion tasks for
    production-site and official targets reached the expansion result list with
    `budget_decision.accepted=false` because `openrouter_web_task:run` was
    already `8/8`.
  - `production_site_coverage_probe` reserve was therefore useful
    diagnostically but not yet a protected execution slot.
  - Benchmark/evaluation reports could blur selected-but-not-executed targets
    with genuinely searched targets.
- Scope:
  - Add protected recall-expansion OpenRouter slots below the normal
    `openrouter_web_task` role budget:
    - regular web-task budget stays bounded;
    - checkpoint/search expansion tasks registered under a recall-expansion
      reserve can spend `openrouter_recall_expansion` slots;
    - all protected calls still count against total `openrouter:run` and
      server-tool web-search budgets.
  - Add `max_recall_expansion_openrouter_calls_per_run` to external budget
    settings and benchmark profiles.
  - Update `benchmark_smoke`:
    - regular web-task calls remain `8`;
    - protected recall-expansion OpenRouter calls are capped at `4`;
    - total OpenRouter calls become `14` so planner + regular web + protected
      expansion are all bounded and visible.
  - Make expansion execution accounting explicit:
    - generated target;
    - selected variant;
    - attempted expansion task;
    - externally executed provider call;
    - source found;
    - candidate/universe projection;
    - not executed because reserve budget was exhausted;
    - not executed because global/total external budget was exhausted.
  - Keep `targets_not_searched` as the canonical place for selected/generated
    targets that did not execute.
  - Add `search_expansion_execution_summary` to dossier/API and benchmark
    report.
  - Update false-negative diagnostics so selected-but-budget-blocked expansion
    becomes `expansion_global_budget_limited` or
    `expansion_reserve_limited`, not `expansion_searched_no_support`.
  - Fix the API/worker Docker acceptance race discovered during manual smoke:
    API must commit the queued run before enqueueing the Celery task, otherwise
    the worker can read SQLite before the run row is visible and fail with
    `Radar run not found`.
- Out of scope:
  - No new provider adapter.
  - No scoring or product-candidate relaxation.
  - No model-role evaluation; that remains `0.7.6.3.7`.
  - No SIBUR-specific production hardcode.
  - No broad `benchmark_live` acceptance claim.
- Implementation notes:
  - `RadarExternalCallBudget` now supports protected recall-expansion task ids.
  - Provider integration still calls the same OpenRouter budget guard; the guard
    recognizes protected expansion task ids and charges
    `openrouter_recall_expansion:run` instead of regular
    `openrouter_web_task:run`.
  - Protected expansion calls still count in `openrouter:run`, so smoke remains
    bounded and cost-visible.
  - Search-expansion records now carry `execution_status` values such as
    `executed_source_found`, `executed_no_support`, and `not_executed`.
- Tests:
  - Unit: protected recall-expansion task can execute after regular
    `openrouter_web_task` budget is exhausted while still counting against
    total OpenRouter budget.
  - Unit: benchmark smoke context exposes `max_recall_expansion_openrouter_calls_per_run`.
  - Report: benchmark summary counts only externally executed expansion results
    as `expansion_result_count`.
  - Evaluation: budget-blocked expansion target becomes
    `expansion_global_budget_limited`.
  - Regression: expansion, benchmark, evaluation, adaptive execution, live Radar
    and backend API tests pass.
- Docs:
  - Update `ROADMAP.md`.
  - Update Developer Guide and demo README with protected expansion slots and
    searched/attempted distinction.
  - Sync Radar AS IS Markdown/PDF.
- Demo impact:
  - No UI changes.
  - Benchmark JSON reports now contain a clearer expansion execution funnel.
- Acceptance criteria:
  - A target with `budget_decision.accepted=false` is not counted as an
    externally searched/executed expansion result.
  - Production-site expansion can use protected recall-expansion OpenRouter
    slots without increasing the regular web-task budget.
  - Dossier/report expose generated/selected/attempted/executed/source-found/
    projected counts.
  - Remaining production-site misses explain whether the target was not
    selected, reserve-limited, globally budget-limited, searched with no
    support, or found but not projected.
  - `benchmark_live` remains blocked until a fresh bounded Docker smoke and
    evaluation prove the protected slots behave as expected.
- Done notes:
  - Implemented protected `openrouter_recall_expansion` budget slots.
  - Added expansion execution summary to dossier/API and benchmark reports.
  - Fixed evaluation diagnostics for selected-but-not-executed expansion
    targets.
  - Added an API regression test proving the queued run is committed before
    job enqueue so Docker worker can see it immediately.
  - Fixed benchmark task-context plumbing so staged execution receives
    `max_recall_expansion_openrouter_calls_per_run` and
    `budget_reserve_limits`, not only the `.env` smoke defaults.
  - Exposed external-call budget settings, counters, role counters and
    exhaustion events through `/api/radar-runs/{run_id}/dossier` and benchmark
    reports.
  - Increased the default benchmark CLI poll timeout from `900` to `1200`
    seconds. This does not relax Radar work budgets; it only prevents a slow
    low-cost OpenRouter provider from being mislabeled as runtime failure after
    the bounded run is still progressing.
  - Validation run: targeted external-budget, search-expansion, benchmark,
    evaluation, adaptive, live Radar, and backend API tests passed locally.
  - Full validation after the final plumbing fix: `python -m pytest` -> `324
    passed, 1 skipped`.
  - Docker acceptance run:
    `radar-run-3da6a406-c918-47f1-b29e-216c689ad129` completed in `918.351s`
    with `execution_outcome=stopped_for_review` and benchmark verdict
    `budget_limited`.
  - Docker smoke budget evidence:
    `openrouter:run=14`, `openrouter_web_task:run=8`,
    `openrouter_recall_expansion:run=4`,
    `openrouter_server_tool_web_search:run=29`,
    `source_verification:run=30`, `dadata:run=3`.
  - Docker smoke expansion evidence:
    `search_expansion_execution_summary.generated_count=65`,
    `selected_count=5`, `attempted_count=3`, `executed_count=1`,
    `source_found_count=1`.
  - Evaluation after the bounded Docker smoke:
    `strict_recall=0.6667`, `review_recall=0.3333`, `false_negative_count=5`.
    Remaining false negatives are no longer blank retrieval failures:
    `sibur-holding=present_not_matched`, `zapsibneftekhim/poliom/gubkinsky-gpp/
    tobolsk-site=expansion_not_selected`.
- Risks:
  - Protected expansion slots increase total benchmark smoke OpenRouter call
    ceiling from `10` to `14`. This is intentional and bounded; the regular web
    task budget remains unchanged at `8`.
  - A provider can still spend server-tool web-search requests inside one
    OpenRouter call; server-tool budget remains the backstop.
  - `benchmark_live` remains blocked. The next corrective bucket should address
    allocation inside the bounded smoke profile: source verification consumes
    its full request budget, only one expansion provider call executes, and
    selected legal/site targets still remain unsearched before stop.

### Slice 0.7.6.3.6.4: Semantic task-budget reserves, verification dedupe, and benchmark target execution guarantees

- Status: `Done`
- Goal: Fix the remaining budget-allocation blocker from
  `radar-run-3da6a406-c918-47f1-b29e-216c689ad129`. Protected
  `openrouter_recall_expansion` slots now work, but the run still spends the
  shared semantic web-task budget and source-verification budget before enough
  high-value benchmark expansion targets are executed.
- User value: A user should see that bounded `benchmark_smoke` actually probes
  the important missed targets before stopping. If `Губкинский ГПЗ`,
  `Тобольская площадка`, `ЗапСибНефтехим`, or `Полиом` remain missed, the
  report must say whether they were searched, skipped by policy, blocked by a
  specific reserve, or found but not projected.
- Problem statement:
  - Latest Docker smoke completed, but stopped as `budget_limited`.
  - Runtime wiring is healthy: API/worker config matched, source cards loaded,
    DaData live and OpenRouter Perplexity were used, and protected
    `openrouter_recall_expansion:run=4` was consumed.
  - Recall improved but is still incomplete:
    - `strict_recall=0.6667`;
    - `review_recall=0.3333`;
    - false negatives: `sibur-holding`, `zapsibneftekhim`, `poliom`,
      `gubkinsky-gpp`, `tobolsk-site`.
  - Expansion generated `65` targets and selected `5`, but only `1` provider
    call actually executed and only one production-site source was found.
  - The semantic web-task budget reached `18/18`, so later expansion and repair
    tasks were blocked by `total_run_budget_exhausted`.
  - `source_verification:run=30/30` was fully consumed and repeatedly produced
    verification budget exhaustion events, creating noise before key target
    probes completed.
  - `sibur-holding` is classified as `present_not_matched`, which is a matcher
    / projection normalization issue rather than retrieval absence.
- Scope:
  - Add semantic task-budget reserves below `RadarExecutionBudget`, mirroring
    the external-call reserves:
    - `recall_expansion_task_budget`;
    - `production_site_expansion_task_budget`;
    - `official_coverage_probe_task_budget`;
    - optional `registry_identity_task_budget` if needed for DaData-backed
      identity confirmation.
  - Ensure recall-expansion and production-site expansion tasks can execute
    through their reserved semantic task slots even when the general
    qualification/gate/coverage web-task budget is exhausted.
  - Keep all tasks bounded: reserved semantic task slots still count in a
    visible total diagnostic counter and must never become an unbounded
    fallback.
  - Add source-verification dedupe/cache per run:
    - normalize URL/domain/evidence refs before spending a verification slot;
    - do not re-verify the same URL/citation repeatedly;
    - record `verification_cache_hit` instead of spending another request.
  - Split verification caps by purpose where useful:
    - discovery/source-list verification;
    - expansion-result verification;
    - product-source verification.
  - Add benchmark target execution guarantees for `benchmark_smoke`:
    - at least one holding/group probe;
    - at least two legal/subsidiary probes;
    - at least two production-site/branch probes;
    - unless blocked by explicit policy/provider/external-call budget.
  - Limit noisy gate fan-out in smoke:
    - weak/unknown candidates can remain diagnostic;
    - they must not consume all gate/coverage task slots before benchmark
      target probes execute.
  - Improve matcher/projection normalization for benchmark evaluation so
    `SIBUR Holding`, `PJSC SIBUR Holding`, `ПАО СИБУР Холдинг`, and `СИБУР`
    variants do not end as `present_not_matched` when source-backed.
- Out of scope:
  - No new source provider.
  - No UI changes.
  - No `benchmark_live` quality claim.
  - No SIBUR-specific production runtime branch. SIBUR names may remain in
    benchmark fixtures/evaluation context only.
  - No model-role leaderboard; keep `0.7.6.3.7` for model evaluation.
- Implementation notes:
  - Implemented in this slice:
    - `RadarExecutionBudget` now supports `semantic_task_reserve_limits` and
      reports `semantic_task_budget_counters` /
      `semantic_task_budget_exhaustion_events`.
    - Search expansion execution passes each variant's reserve key into the
      semantic task-budget guard, so approved expansion can use a small
      protected task slot after the regular web-task budget is exhausted.
    - `benchmark_smoke` now defines semantic reserves for
      `recall_expansion`, `production_site_coverage_probe`,
      `official_coverage_probe`, and `open_web_coverage_probe`.
    - `benchmark_smoke` now defines target-lane minimums for holding/group,
      legal/subsidiary, and production-site/branch probes.
    - Source verification now has per-run URL dedupe/cache and exposes cache
      stats in execution results, dossier, and benchmark report.
    - Dossier and benchmark report now expose target probe guarantees,
      guarantee failures, semantic task counters, and verification cache stats.
    - Evaluation-only matching now handles source-backed short aliases such as
      `SIBUR` -> `SIBUR Holding` without adding SIBUR-specific production
      runtime logic.
  - Treat semantic task reserves as a separate application-level concern from
    OpenRouter HTTP-call budgets. Both must pass before a provider call is made.
  - The expansion execution summary should distinguish:
    - blocked by semantic task budget;
    - blocked by external OpenRouter budget;
    - blocked by source verification budget;
    - selected but not executed because target-lane quota was exhausted;
    - executed and source found;
    - executed and no support found.
  - Verification dedupe must be deterministic and product-safe; do not store
    secrets, headers, or raw provider payloads.
  - The benchmark report should make the target-lane guarantee visible, e.g.
    `required_target_probe_minimums`, `target_probe_minimums_satisfied`,
    `target_probe_minimum_failures`.
- Tests:
  - Unit: semantic recall-expansion task reserve allows an expansion task after
    the general web-task budget is exhausted, while still incrementing bounded
    reserve counters.
  - Unit: production-site expansion consumes
    `production_site_expansion_task_budget`, not generic gate/coverage slots.
  - Unit: source verification dedupes repeated normalized URLs and records
    `verification_cache_hit` without spending a new verification request.
  - Unit: benchmark target selector satisfies minimum target-lane guarantees
    when budget and source policy allow it.
  - Unit: noisy weak candidates are retained diagnostically but do not consume
    smoke gate slots ahead of guaranteed target probes.
  - Evaluation: SIBUR holding aliases match the curated baseline when
    source-backed.
  - Fake pipeline: weak discovery with benchmark hints executes at least the
    required holding/legal/site probe counts before `stop_review_needed`.
  - Fake pipeline: if a required probe cannot execute, report the exact blocker
    (`semantic_task_budget_limited`, `external_call_budget_limited`,
    `verification_budget_limited`, or `source_policy_limited`).
  - API/report: dossier and benchmark report expose semantic reserve counters,
    verification cache stats, target-lane guarantee status, and no secrets or
    hidden reasoning markers.
  - Regression commands:
    - `python -m pytest tests/test_radar_search_expansion.py tests/test_radar_adaptive_execution.py -q`
    - `python -m pytest tests/test_radar_external_call_budget.py tests/test_radar_benchmark.py tests/test_radar_evaluation.py -q`
    - `python -m pytest tests/test_live_icp_radar.py tests/test_backend_api.py -q`
    - `python -m pytest tests/test_backend_architecture_contract.py tests/test_radar_pipeline_documentation_contract.py -q`
    - `python -m pytest`
- Docs:
  - Updated `ROADMAP.md`.
  - Updated Developer Guide and demo README with semantic task reserves,
    verification dedupe, and target-lane guarantee interpretation.
  - Added TO BE Markdown/PDF for `0.7.6.3.6.4`.
  - Synced Radar AS IS Markdown/PDF after implementation.
- Demo impact:
  - No UI change.
  - `demo/output/radar_benchmark_report.json` should become easier to read:
    remaining misses should be explained by target-lane execution status rather
    than requiring manual trace inspection.
- Acceptance criteria:
  - In fake/recorded tests, guaranteed benchmark target probes execute before
    weak/noisy gate fan-out can exhaust the run.
  - In Docker `benchmark_smoke`, at least the configured minimum target-lane
    probes are executed, or each non-executed lane has a narrow blocker reason.
  - `source_verification:run` no longer reaches its limit mostly because of
    duplicate URL/citation checks.
  - `sibur-holding` no longer remains `present_not_matched` when source-backed
    aliases are present.
  - `review_recall` does not regress below `0.3333`; ideally it improves, but a
    non-improvement is acceptable only if misses have precise searched/skipped
    diagnostics.
  - `benchmark_live` remains blocked until this bounded smoke is interpretable.
- Validation:
  - Passed: `python -m pytest tests/test_radar_external_call_budget.py tests/test_radar_benchmark.py tests/test_radar_evaluation.py tests/test_backend_api.py -q`.
  - Passed: `python -m pytest tests/test_radar_search_expansion.py tests/test_radar_adaptive_execution.py tests/test_live_icp_radar.py tests/test_backend_architecture_contract.py -q`.
  - Docker acceptance rerun completed on 2026-06-28:
    `radar-run-44abf1c6-5070-4b2a-84cd-9d37df6cb429`.
    - Status: terminal `completed`, execution outcome `stopped_for_review`,
      benchmark verdict `budget_limited`.
    - Runtime/path health: Docker API/worker path executed, source cards were
      present (`source_cards_count=3`), capability decisions were present
      (`source_capability_decision_count=5`).
    - Retrieval/projection evidence: `retrieved_source_count=9`,
      `diagnostic_source_count=30`, `candidate_count=3`.
    - Target-lane guarantees were not satisfied:
      holding/group `0/1`, legal/subsidiary `0/2`,
      production-site/branch `1/2`.
    - Main blocker: external budget exhausted before guaranteed target lanes
      could execute enough probes; this is now visible as
      `external_budget_limited`, not as a blank retrieval miss.
    - Source verification dedupe worked: `30` unique verification requests and
      `51` duplicate skips/cache hits.
    - Evaluation result: `strict_recall=0.8889`, `review_recall=0.3333`,
      `false_negatives=poliom,gubkinsky-gpp,tobolsk-site`.
    - False-negative diagnostics: all three misses are now
      `expansion_not_selected`, not generic `not_retrieved_in_run`.
    - Coverage probe found official sources for all three remaining misses:
      `poliom`, `gubkinsky-gpp`, and `tobolsk-site`.
  - `benchmark_live` remains blocked. The next correction should focus on
    external budget allocation and guaranteed expansion lane execution, not on
    connector/profile wiring or source availability.
- Risks:
  - Too many reserves can hide runaway execution. Mitigate by keeping every
    reserve small, visible, and included in the report.
  - Verification dedupe may under-check if URL normalization is too aggressive.
    Mitigate by preserving original refs and recording the normalized key used
    for cache decisions.

### Slice 0.7.6.3.6.5: Guaranteed expansion execution scheduler and external-budget lane allocation

- Status: `Done`
- Goal: Turn target-lane guarantees from post-run diagnostics into an execution
  scheduling rule. `benchmark_smoke` should schedule holding, legal/subsidiary,
  and production-site/branch probes before optional expansion work, and it
  should fail with exact budget blockers when a guaranteed lane cannot execute.
- User value: A user can trust the bounded smoke as an acceptance gate. If a
  target like `poliom`, `gubkinsky-gpp`, or `tobolsk-site` remains missed, the
  report should say whether it was scheduled, budget-reserved, executed, found,
  projected, or precisely blocked.
- Problem statement:
  - `0.7.6.3.6.4` made target-lane failures visible, but Docker smoke
    `radar-run-44abf1c6-5070-4b2a-84cd-9d37df6cb429` still missed required
    lane minimums: holding/group `0/1`, legal/subsidiary `0/2`,
    production-site/branch `1/2`.
  - Coverage probe found official sources for all remaining misses, so the
    blocker is execution scheduling and budget allocation, not source
    availability.
  - `run_profile=smoke` used an expansion variant cap of `4`, while benchmark
    target minimums require `5` probes. This made the guarantee partly
    impossible by configuration.
- Scope:
  - Add `RadarExpansionScheduler` as an application-layer role.
  - Order guaranteed target-lane variants before optional variants.
  - Raise expansion variant cap to at least the sum of configured
    `benchmark_target_probe_minimums`.
  - Add non-mutating external-budget preflight for guaranteed recall expansion
    tasks before provider execution:
    - total OpenRouter capacity;
    - protected recall-expansion OpenRouter capacity;
    - OpenRouter server-tool web-search capacity.
  - Record `expansion_schedule`, `target_lane_allocation`, and
    `targets_not_scheduled`.
  - Add precise not-searched reasons:
    - `selected_but_not_scheduled`;
    - `scheduled_but_budget_not_reserved`;
    - `external_total_budget_limited`;
    - `openrouter_recall_expansion_budget_limited`;
    - `server_tool_budget_limited`.
  - Adjust `benchmark_smoke` targeted external budget allocation:
    - total OpenRouter calls: `16`;
    - recall-expansion OpenRouter calls: `5`;
    - server-tool web searches: `45`;
    - official/open-web/prod-site reserve limits sufficient for lane minimums.
  - Keep all external calls bounded and visible; no unbounded fallback.
- Out of scope:
  - No new provider.
  - No UI changes.
  - No model-role evaluation.
  - No scoring relaxation.
  - No SIBUR-specific runtime branch.
- Implementation notes:
  - Added `src/power_web_os/application/radar_search_expansion_scheduler.py`.
  - Split expansion metadata/event helpers into
    `live_radar_search_expansion_payloads.py` so the executor remains below
    architecture size limits.
  - `RadarExternalCallBudget` now has a non-mutating
    `check_recall_expansion_openrouter_capacity` scheduler preflight.
  - `live_radar_staged_execution` now computes expansion variant cap from
    benchmark lane minimums when benchmark context is present.
- Tests:
  - Added scheduler unit tests for guaranteed lane ordering and unscheduled
    target diagnostics.
  - Added external-budget unit tests for recall-expansion and server-tool
    preflight blockers.
  - Updated benchmark smoke budget tests.
  - Regression passed:
    - `python -m pytest tests/test_radar_search_expansion.py tests/test_radar_external_call_budget.py tests/test_radar_benchmark.py -q`
    - `python -m pytest tests/test_radar_adaptive_execution.py tests/test_live_icp_radar.py -q`
    - `python -m pytest tests/test_backend_api.py tests/test_backend_architecture_contract.py -q`
- Docs:
  - Added TO BE Markdown/PDF for `0.7.6.3.6.5`.
  - Updated Radar AS IS Markdown/PDF.
  - Updated Developer Guide and demo README.
- Demo impact:
  - No UI change.
  - Benchmark report/dossier now have richer schedule/allocation diagnostics.
- Acceptance criteria:
  - Docker `benchmark_smoke` should either satisfy target-lane minimums or
    explain every missing lane with a specific scheduler/budget/policy blocker.
  - Remaining false negatives should be narrower than `expansion_not_selected`.
  - `review_recall` should not regress below `0.3333`.
  - `strict_recall` should not regress below `0.8889` unless provider-output
    drift is visible.
  - `benchmark_live` remains blocked until a fresh bounded smoke/evaluation
    confirms scheduler behavior.
- Risks:
  - Higher targeted server-tool capacity may increase smoke cost. Mitigation:
    only `benchmark_smoke` targeted expansion budgets changed, and all counters
    remain visible.
  - OpenRouter server-tool usage is reported after a provider response, so one
    call can still overrun a slice. Mitigation: scheduler preflights current
    capacity and reports post-call budget usage separately.

### Slice 0.7.6.3.6.5.1: Universal LLM call contract and backup-model routing

- Status: `Done`
- Goal: Stop fixing malformed OpenRouter JSON one role at a time. All
  pipeline-critical structured LLM calls must follow the same bounded
  primary/retry/backup contract and expose exact diagnostics.
- User value: A smoke or benchmark run should clearly answer: which role called
  which model, what failed, whether a retry happened, whether a backup model was
  tried, and whether budget prevented recovery.
- Problem statement:
  - Extraction already had primary retry and extraction backup recovery for
    non-JSON/schema-invalid payloads.
  - Planner still made a single structured OpenRouter request and then depended
    on the response being valid JSON and matching `RadarDiscoveryPlan`.
  - Runtime config showed role models, but not planner backup or per-role
    temperature settings.
  - The retry/backup rule was not captured as an ADR-level architecture
    requirement, so future structured LLM roles could repeat the same gap.
- Scope completed:
  - Added ADR `2026-06-28-universal-llm-call-contract.md`.
  - Added planner retry contract:
    primary planner model -> strict primary retry -> planner backup model.
  - Added planner backup selection:
    `OPENROUTER_PLANNER_BACKUP_MODEL`, falling back to
    `OPENROUTER_BACKUP_MODEL`.
  - Added configurable role temperatures:
    `OPENROUTER_PLANNER_TEMPERATURE`,
    `OPENROUTER_EXTRACTOR_TEMPERATURE`,
    `OPENROUTER_SIGNAL_TEMPERATURE`,
    `OPENROUTER_BACKUP_TEMPERATURE`.
  - Extraction/retrieval OpenRouter requests now pass role temperature into the
    provider request and technical trace.
  - Planner retry and backup attempts count through provider retry and
    OpenRouter planner budgets.
  - Runtime config report exposes planner backup model and role temperatures.
  - TO BE Markdown/PDF added for the corrective behavior.
- Tests:
  - Planner non-JSON primary and primary retry recover through backup.
  - Planner schema-invalid JSON triggers primary retry.
  - Existing extraction non-JSON primary/retry/backup recovery remains green.
  - Runtime config exposes backup/temperature fields and still redacts secrets.
- Manual acceptance required next:
  - Done: ran two bounded Docker `benchmark_smoke` + evaluation passes for
    `benchmark-sibur-holding-contour`.
  - Balanced preset:
    - run id: `radar-run-87a15759-c120-4d3d-94b7-868f420c5040`;
    - models: `deepseek/deepseek-v4-pro`,
      `google/gemini-3.1-pro-preview`, `openai/gpt-5-mini`,
      `anthropic/claude-sonnet-4.6`, `qwen/qwen3.7-max`;
    - outcome: `stopped_for_review`, verdict `budget_limited`;
    - strict recall `0.7778`, review recall `0.3333`;
    - retrieved sources `15`, diagnostic sources `72`;
    - checkpoint used `repair_extraction` twice and stopped on budget before
      signal search;
    - target guarantee failure remained
      `known_subsidiary_or_legal_entity_target` with
      `external_budget_limited`.
  - Light preset:
    - run id: `radar-run-edee22a0-b1ee-449a-94b9-5d258ec8ed70`;
    - models: `deepseek/deepseek-v4-pro`, `z-ai/glm-5.2`,
      `openai/gpt-5-mini`, `qwen/qwen3.7-max`, `moonshotai/kimi-k2.6`;
    - outcome: `stopped_for_review`, verdict `budget_limited`;
    - strict recall `0.4444`, review recall `0.6667`;
    - retrieved sources `9`, diagnostic sources `39`;
    - checkpoint used `revise_plan` twice because of
      `evidence_linking_failed`, then stopped on budget before signal search;
    - target guarantee failure remained
      `known_subsidiary_or_legal_entity_target` with
      `external_budget_limited`.
  - Comparison artifact:
    `demo/output/radar_model_preset_comparison.json`.
  - Verdict:
    - balanced preset is the safer default for the next smoke because strict
      legal-entity recall is materially higher;
    - light preset found more production-site review matches but lost too many
      legal entities and produced more evidence-linking/revision pressure;
    - neither preset is ready for broader `benchmark_live`;
    - next corrective work should still focus on target-lane budget allocation
      and post-extraction materialization/projection, not on model switching
      alone.
- Out of scope:
  - Choosing a permanent default model lineup.
  - Automatic production model switching without explicit config.
  - Fixing post-extraction materialization; that remains the next backlog slice
    `0.7.6.3.6.6`.

### Slice 0.7.6.3.6.6: Post-extraction fallback materialization and registry enrichment recheck

- Status: `Backlog`
- Goal: Fix the next blocker found by the TOIR Docker smoke after
  `0.7.6.3.6.5`: if extraction payloads fail, but retrieved/analyzed sources
  still contain source-backed candidates, Radar should materialize those
  candidates, run allowed identity enrichment for concrete names, and re-review
  checkpoints before declaring a final source-obligation/policy stop.
- User value: A smoke run should not look blocked only because the first
  extraction JSON was malformed when the system already has enough retrieved
  material to create review-needed candidates and try registry identity lookup.
- Evidence:
  - TOIR smoke `radar-run-ef74d8c0-8e19-43eb-9936-cfc0a44c383b` completed in
    Docker with API/worker parity, `source_cards_count=3`, 6 retrieved sources,
    18 diagnostic sources, and 2 promoted/review-needed candidates.
  - The primary outcome was still `blocked_by_policy` with
    `extraction_repair_exhausted`, `extraction_schema_failed`,
    `source_obligation_unmet`, and `weak_candidate_coverage`.
  - DaData/registry remained `attempted_insufficient` because the only runtime
    registry outcome was a broad `registry_lookup_insufficient` query. Concrete
    source-backed candidates appeared later through retrieved-source fallback,
    but gate/registry enrichment had already been skipped after the extraction
    stop.
  - Search expansion scheduling was not the active blocker in this TOIR run:
    expansion targets were empty because this was not a benchmark target-hint
    run and candidate materialization happened after the terminal extraction
    stop.
- Scope:
  - Add a post-extraction fallback checkpoint branch:
    - when `extraction_schema_failed` / `extraction_repair_exhausted` is present;
    - and retrieved/analyzed sources contain source-backed candidate or
      site/branch mentions;
    - materialize review-needed candidates from retrieved sources before final
      terminal stop.
  - Add a bounded post-materialization identity enrichment pass:
    - run only for concrete candidate names, INN/OGRN, or strong legal-name
      fragments;
    - use configured registry/identity connectors through source cards;
    - never send broad discovery text to lookup-only registries;
    - respect DaData/SPARK-like provider neutrality: behavior is driven by
      connector capability, not provider-specific branching.
  - Recompute source-obligation runtime outcomes after enrichment:
    - `required_for_identity` can become `satisfied` or
      `attempted_review_needed` when registry returns useful/review-needed
      observations;
    - if identity enrichment cannot run, record
      `not_executed_input_not_available`, `provider_unavailable`,
      `budget_limited`, or `identity_not_confirmed_after_all_terms`.
  - Re-run the pre-signal checkpoint after fallback materialization/enrichment.
  - Preserve terminal safety:
    - if extraction is truly unrecoverable and no fallback candidates exist,
      keep `stop_review_needed`;
    - if fallback candidates exist but identity/source obligations still fail,
      stop with a narrower reason than generic `extraction_repair_exhausted`;
    - signal search starts only if the re-reviewed checkpoint permits it.
- Out of scope:
  - No scoring relaxation.
  - No new provider adapter.
  - No SIBUR/DaData hardcode.
  - No broad `benchmark_live` claim.
- Expected diagnostics:
  - `fallback_candidate_materialization_records`;
  - `post_extraction_identity_enrichment_records`;
  - concrete `registry_lookup_terms` and `registry_lookup_attempts` for
    materialized candidates;
  - updated source-obligation decisions after the recheck;
  - explicit final reason:
    `fallback_identity_satisfied`, `fallback_identity_review_needed`,
    `fallback_identity_budget_limited`,
    `fallback_candidates_not_projected`, or `fallback_not_available`.
- Test plan:
  - Unit: malformed extraction + retrieved source-backed legal entity ->
    fallback materializes review-needed candidate.
  - Unit: fallback materialized concrete candidate triggers registry lookup
    through generic lookup-only connector capability.
  - Unit: broad query is still blocked for registry and does not satisfy
    identity.
  - Unit: registry match/review-needed observation updates
    `required_for_identity` outcome after recheck.
  - Pipeline fake: extraction repair exhausted, retrieved candidates present,
    fallback enrichment succeeds, final checkpoint no longer reports generic
    `source_obligation_unmet`.
  - Pipeline fake: extraction repair exhausted, no retrieved candidates, run
    remains `stop_review_needed` with `fallback_not_available`.
  - Regression:
    - `python -m pytest tests/test_live_icp_radar.py tests/test_radar_adaptive_execution.py -q`
    - `python -m pytest tests/test_backend_api.py tests/test_radar_search_expansion.py -q`
    - `python -m pytest tests/test_backend_architecture_contract.py -q`
    - `python -m pytest`
- Manual acceptance:
  - Rebuild Docker API/worker.
  - Run TOIR smoke with live DaData + `openrouter_perplexity`.
  - Expected: if retrieved-source fallback finds concrete candidates, dossier
    shows concrete registry lookup attempts after materialization; if the run
    still stops, the reason is identity/projection/budget-specific rather than
    the current broad-query `attempted_insufficient`.
  - Then rerun `benchmark-sibur-holding-contour` smoke/evaluation before
    considering `benchmark_live`.

### Slice 0.7.6.3.6.7: Central Radar work scheduler and budget admission control

- Status: `Done`
- Goal: Stop treating Radar budgets as independent local counters and introduce
  one application-layer admission owner for benchmark-critical work lanes.
- Problem statement:
  - Several previous corrective slices improved search expansion, semantic
    reserves, protected OpenRouter recall-expansion calls, and diagnostics.
  - Docker `benchmark_smoke` still showed late target-lane failures because
    planner/discovery/extraction/gate work could consume shared OpenRouter run
    budget before guaranteed recall probes executed.
  - The active failure mode was no longer "we do not know what happened"; it
    was "we know after the fact that important work could not run." That means
    admission had to move earlier.
- Scope completed:
  - Added TO BE Markdown/PDF:
    `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_0.7.6.3.6.7.md` and `.pdf`.
  - Added `RadarWorkScheduler` in the application layer.
  - Added work contracts:
    `RadarWorkItem`, `RadarWorkCostEstimate`,
    `RadarWorkAdmissionDecision`, `RadarWorkLedger`, and
    `RadarWorkPortfolio`.
  - `RadarExternalCallBudget` now supports scheduler-configured protected
    OpenRouter run capacity for recall expansion.
  - Regular OpenRouter web-task calls are rejected with
    `work_admission_reserved_capacity` when they would consume capacity reserved
    for guaranteed recall-expansion lanes.
  - Checkpoint search expansion and the regular post-coverage expansion path
    now pass scheduled variants through scheduler admission before provider
    execution.
  - Expansion diagnostics now expose:
    `work_scheduler_plan`, `work_scheduler_ledger`,
    `work_admission_decisions`, `work_lane_summary`,
    `work_guarantee_failures`, `work_execution_order`,
    `deferred_work_items`, and `rejected_work_items`.
  - Benchmark reports and dossier/API projection include the scheduler fields.
  - AS IS Markdown/PDF updated to describe central admission control and
    protected OpenRouter capacity.
- Tests:
  - Added `tests/test_radar_work_scheduler.py` for protected OpenRouter
    capacity, guaranteed lane admission, metadata merge, and pre-provider
    rejection.
  - Updated backend API and benchmark report tests for scheduler diagnostics.
  - Passed:
    - `python -m pytest tests/test_radar_work_scheduler.py tests/test_radar_external_call_budget.py tests/test_radar_search_expansion.py tests/test_radar_benchmark.py -q`
    - `python -m pytest tests/test_backend_api.py -q`
    - `python -m pytest tests/test_radar_adaptive_execution.py tests/test_live_icp_radar.py -q`
- Docker acceptance:
  - Rebuilt Docker API/worker/backend-init and ran
    `benchmark-sibur-holding-contour` with `benchmark_smoke`.
  - First run:
    `radar-run-4f6de9aa-7a53-4e89-8ac8-f9b37939a5c4`.
    Evaluation: `strict_recall=1.0`, `review_recall=0.6667`,
    one false negative: `tobolsk-site` as `expansion_not_selected`.
  - Autofix cycle 1: found that `work_scheduler_plan/ledger` was overwritten
    by the last expansion portfolio, so the dossier could show only late
    rejected work and hide earlier admissions. Fixed scheduler metadata merge
    and covered it with a unit test.
  - Second run:
    `radar-run-904cf50f-5551-40e8-9510-462f8383ca17`.
    Evaluation: `strict_recall=1.0`, `review_recall=0.6667`,
    one false negative: `gubkinsky-gpp` as `expansion_not_selected`.
  - Scheduler diagnostics are now interpretable:
    `work_scheduler_ledger.accepted_count=5`, `rejected_count=0`,
    no hidden scheduler rejection, source cards count is `3`.
  - Remaining issue is no longer hidden budget theft. The selector/scheduler
    contract admitted the selected work, but only one legal/subsidiary and one
    production-site lane item were scheduled, while the benchmark minimum asks
    for two of each. Dossier shows `target_probe_guarantee_failures` with
    `scheduled_below_minimum`.
  - Coverage probe for the remaining `gubkinsky-gpp` miss was inconclusive:
    the host-side probe command failed OpenRouter with `401 User not found`,
    while Docker API/worker OpenRouter calls worked. Treat this as a host
    diagnostic credentials issue, not a Docker smoke failure.
- Acceptance verdict:
  - Scheduler/admission ownership is implemented and observable.
  - `benchmark_smoke` is interpretable, but `benchmark_live` remains blocked:
    the next defect is target selection/scheduling below lane minimums, not
    late unknown budget consumption.
- Relationship to `0.7.6.3.6.6`:
  - `0.7.6.3.6.6` remains a valid post-extraction materialization backlog
    slice.
  - Broader budget tuning and `benchmark_live` remain blocked until bounded
    smoke proves the central scheduler makes target-lane failures
    interpretable.

### Slice 0.7.6.3.6.8: Guaranteed target selection before scheduler admission

- Status: `Done`
- Goal: Fix the remaining pre-admission blocker from `0.7.6.3.6.7`: the work
  scheduler can admit protected recall-expansion work, but the selector must
  first pass enough guaranteed lane work into the scheduler.
- User value:
  - The benchmark smoke no longer says "minimum failed" after the fact while
    hiding that the required tasks were never selected.
  - A user can see whether Radar generated too few targets, generated targets
    without executable queries, selected too few tasks, or hit a real budget
    blocker.
- Problem statement:
  - Docker smoke `radar-run-904cf50f-5551-40e8-9510-462f8383ca17` showed
    `work_scheduler_ledger.accepted_count=5`, so scheduler admission worked.
  - The same run still failed target minimums because only one
    legal/subsidiary and one production-site/branch variant were selected,
    while `benchmark_smoke` requires two of each.
  - Root cause: generic variant clipping happened before guaranteed lane
    selection, so required lanes could be clipped before scheduler admission.
- Scope completed:
  - Added TO BE Markdown/PDF:
    `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_0.7.6.3.6.8.md` and `.pdf`.
  - Added guarantee-aware variant selection before scheduler admission.
  - Effective expansion variant cap is now raised to at least the sum of
    benchmark target-lane minimums.
  - Selector chooses required lane targets first and fills optional variants
    only after those minimums.
  - Added selection diagnostics:
    `search_expansion_selection_summary` and
    `search_expansion_selection_diagnostics`.
  - Target probe failures now distinguish selection blockers such as
    `target_not_generated`, `no_executable_variant_for_target`, and
    `selection_below_minimum` from scheduler/budget blockers.
  - AS IS Markdown/PDF updated to describe guaranteed target selection before
    scheduler admission.
- Tests:
  - Added selector tests proving:
    - 1 holding, 2 legal/subsidiary, and 2 production-site/branch variants are
      selected before optional variants;
    - `max_variants` is raised when benchmark minimums require more slots;
    - generated targets without executable variants produce
      `no_executable_variant_for_target`.
  - Updated backend API and benchmark report tests for selection diagnostics.
- Docker acceptance:
  - Rebuilt Docker API/worker/backend-init and ran `benchmark_smoke` for
    `benchmark-sibur-holding-contour`.
  - First rerun after implementation exposed a local runtime defect:
    `name 'selection_diagnostics' is not defined`; fixed and covered by a
    targeted regression test.
  - Final smoke run: `radar-run-e8936402-b242-4d63-a076-7d563441b7b0`.
  - Result: `completed` / `stopped_for_review`, reason
    `Execution budget was exhausted before signal search`.
  - Selector acceptance passed: selected counts before scheduler/admission were
    holding/group `2` (minimum `1`), legal/subsidiary `4` (minimum `2`),
    production-site/branch `4` (minimum `2`).
  - Scheduler/admission accepted the required lane portfolio: holding/group
    `1`, legal/subsidiary `2`, production-site/branch `2`.
  - Execution acceptance did not fully pass: production-site/branch executed
    only `1` of required `2` because `openrouter_recall_expansion` budget was
    exhausted at `5`.
  - Evaluation for the same run: `strict_recall=1.0`, `review_recall=0.3333`.
    False negatives: `gubkinsky-gpp` with
    `expansion_global_budget_limited`, and `tobolsk-site` with
    `expansion_not_selected`.
  - Verdict: this slice fixed the pre-scheduler selection defect. The next
    blocker is execution-budget allocation for guaranteed recall-expansion
    work, not target selection.
  - `benchmark_live` remains blocked until the bounded smoke can execute the
    selected production-site lane minimum or explain a non-budget blocker.

### Slice 0.7.6.3.6.9: External recall-budget lane reservation and guaranteed expansion execution

- Status: `Done`
- Goal: Fix the blocker from `radar-run-e8936402-b242-4d63-a076-7d563441b7b0`:
  target selection and scheduler admission were sufficient, but the second
  production-site/branch probe was not executed because shared
  `openrouter_recall_expansion` budget was exhausted during execution.
- User value:
  - A user can trust that guaranteed benchmark probes are not merely selected
    and admitted, but have a protected first provider call.
  - If a guaranteed probe cannot execute, the report says whether external
    capacity was insufficient before provider spending or whether only optional
    retry/headroom was exhausted.
- Problem statement:
  - `0.7.6.3.6.8` fixed the pre-scheduler defect: final smoke selected
    holding/group `2`, legal/subsidiary `4`, production-site/branch `4`.
  - Scheduler admitted the required lane portfolio, but execution still ran
    only one production-site/branch probe out of the required two.
  - Root cause: retries and earlier protected recall-expansion work used the
    same flat `openrouter_recall_expansion` counter as the first call of later
    guaranteed tasks.
- Scope completed:
  - Added TO BE Markdown/PDF:
    `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_0.7.6.3.6.9.md` and `.pdf`.
  - `RadarExternalCallBudget` now tracks guaranteed recall-expansion tasks and
    first-call usage.
  - Accepted guaranteed recall-expansion work receives a protected first
    OpenRouter call. Retries and optional work cannot consume capacity reserved
    for another guaranteed task's first call.
  - Scheduler now rejects guaranteed work before provider execution with
    `guaranteed_external_reservation_insufficient` when the external
    recall-expansion or total OpenRouter budget cannot cover admitted work.
  - Runtime can report `guaranteed_external_reservation_protected` when a retry
    or optional task would steal a reserved guaranteed first call.
  - `benchmark_smoke` gets limited headroom: total OpenRouter calls `20`,
    web-task calls `10`, recall-expansion calls `7`, server-tool web searches
    `60`, source verification requests `40`.
  - Dossier and benchmark report expose
    `work_admission_reserved_capacity.guaranteed_recall_expansion`.
  - AS IS Markdown/PDF updated.
- Tests:
  - Added scheduler/budget tests proving a retry cannot steal the first call
    reserved for another guaranteed production-site task.
  - Added scheduler test for pre-provider
    `guaranteed_external_reservation_insufficient`.
  - Updated benchmark profile tests for the bounded smoke headroom.
  - Updated API and benchmark report tests for reservation metadata.
- Docker acceptance:
  - Rebuilt Docker API/worker/backend-init and ran
    `benchmark-sibur-holding-contour` with `benchmark_smoke`.
  - Smoke run: `radar-run-6e08ae16-87f5-4ef3-a313-1417d432ce3f`.
  - Result: `completed` / `stopped_for_review`, reason
    `Execution budget was exhausted before signal search`.
  - External settings applied as intended: total OpenRouter calls `20`,
    web-task calls `10`, recall-expansion calls `7`, server-tool searches `60`,
    DaData lookups `4`, source verification requests `40`.
  - Guaranteed first-call reservation worked:
    `reserved_task_count=6`, `first_call_used_count=6`,
    `first_call_remaining_count=0`.
  - Target-lane minimums were satisfied:
    holding/group selected `2`, executed `2`; legal/subsidiary selected `4`,
    executed `2`; production-site/branch selected `4`, executed `2`.
  - Scheduler ledger: accepted `6`, rejected `4`; rejected work is now
    explained before execution as `guaranteed_external_reservation_insufficient`
    for extra coverage-step expansion tasks, not as hidden budget loss.
  - Evaluation for the same run: `strict_recall=1.0`, `review_recall=0.6667`,
    false negatives: only `tobolsk-site`.
  - Remaining false negative diagnostic: `tobolsk-site` was generated but not
    selected/executed before the run stopped (`expansion_not_selected`).
  - Coverage probe for `tobolsk-site` from host CLI failed with OpenRouter
    `401 User not found`; Docker benchmark OpenRouter calls worked, so treat
    this as a host diagnostic credentials/runtime mismatch, not a Radar
    pipeline blocker.
- Verdict:
  - This slice fixed the hidden shared-budget loss for guaranteed expansion
    first calls.
  - Bounded `benchmark_smoke` is now interpretable and materially better than
    the previous run (`review_recall` improved from `0.3333` to `0.6667`,
    `strict_recall` stayed `1.0`).
  - `benchmark_live` should still wait for one small follow-up: either include
    the remaining `tobolsk-site` lane in the guaranteed site slots or explain
    why it is lower priority than already selected production-site targets.

### Slice 0.7.6.3.6.10: Coverage-aware expansion completion for uncovered targets

- Status: `Done`
- Goal: Fix the remaining post-`0.7.6.3.6.9` defect where an important target
  can be generated by recall expansion but still remain unselected after the
  lane minimums are satisfied.
- User value:
  - A user can see that Radar does not stop at "minimum lanes satisfied" while
    leaving a known generated target unexplored.
  - If a target still remains missed, the dossier/evaluation says whether it
    was completion-selected, budget/admission-limited, searched without support,
    or still not selected because the bounded completion cap was reached.
- Problem statement:
  - Docker smoke `radar-run-6e08ae16-87f5-4ef3-a313-1417d432ce3f` proved that
    target selection, scheduler admission, and protected first calls now work:
    holding/group, legal/subsidiary, and production-site/branch minimums were
    selected and executed.
  - The only false negative was `tobolsk-site`, classified as
    `expansion_not_selected`: the target existed in expansion context but did
    not receive an execution slot before the bounded run stopped.
  - Root cause: the selector optimized for lane minimums, not for completing
    coverage of still-uncovered generated targets after those minimums.
- Scope completed:
  - Added TO BE Markdown/PDF:
    `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_0.7.6.3.6.10.md` and `.pdf`.
  - Added bounded coverage-completion selection after guaranteed lane minimums
    and before generic optional variants.
  - `benchmark_smoke` now carries `coverage_completion_target_limit=2`.
  - Completion variants go through the same scheduler/admission/external budget
    guards as normal recall-expansion work; no new provider loop was added.
  - Added `search_expansion_target_coverage` to execution metadata, dossier,
    and benchmark report.
  - Evaluation now classifies completion-specific misses as
    `completion_not_selected` instead of collapsing them into generic
    `expansion_not_selected`.
  - AS IS Markdown/PDF updated.
- Tests:
  - Added unit tests proving completion selection adds a third uncovered
    production-site target after the lane minimums.
  - Added benchmark profile/report tests for `coverage_completion_target_limit`
    and target coverage projection.
  - Added evaluation test for `completion_not_selected`.
- Acceptance:
  - Fast tests prove the changed selector behavior without relying on live
    providers.
  - Docker `benchmark_smoke` acceptance was run for
    `benchmark-sibur-holding-contour` after rebuilding API/worker/backend-init:
    `radar-run-09ab8cee-e56e-48d7-85ed-a99b02a51d82`.
  - Result: terminal `completed` run with `execution_outcome=stopped_for_review`
    because execution budget was exhausted before signal search.
  - Evaluation: `strict_recall=0.5556`, `review_recall=0.6667`,
    `false_negative_count=5`.
  - `tobolsk-site` is no longer classified as the previous generic
    `expansion_not_selected`; it is now classified as
    `completion_not_selected`, meaning the target was generated but was not
    selected/executed within the bounded completion slots before the run
    stopped.
  - Verdict: the slice improved diagnostics but did not prove readiness for
    `benchmark_live`. The next correction should decide whether completion
    slots are too few, whether completion ranking should prefer remaining
    production-site baseline targets, or whether benchmark smoke needs a
    separate completion-lane minimum.

### Slice 0.7.6.3.6.11: Completion target prioritization for uncovered benchmark targets

- Status: `Done`
- Goal: Fix the remaining `benchmark_smoke_plus` failure where an explicit
  uncovered benchmark target can be generated and executable, but still lose
  completion slots to incidental production-site targets.
- User value:
  - Radar searches the important known benchmark gaps before spending bounded
    completion slots on lower-value incidental targets.
  - If a target remains missed, the dossier/report explains whether it was
    deprioritized, not executable, not admitted, budget-limited, searched
    without support, or lost in projection.
- Problem statement:
  - Budget sensitivity run `radar-run-eda7b48e-ac7c-4eae-ab5e-1c7e2db2889a`
    proved that broader bounded smoke budget materially improves recall:
    `strict_recall=1.0`, `review_recall=0.6667`, and only `tobolsk-site`
    remained false negative.
  - `tobolsk-site` was generated as an executable production-site target but
    stayed `completion_not_selected`.
  - Root cause: completion selection ranked targets mostly by lane, numeric
    priority, and query text. It did not distinguish explicit benchmark targets
    from incidental retrieved targets such as document-like labels or unrelated
    branch/site mentions.
- Scope completed:
  - Added TO BE Markdown/PDF:
    `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_0.7.6.3.6.11.md` and `.pdf`.
  - Added additive target/variant metadata:
    `target_origin`, `completion_rank_reason`, `deprioritized_reason`, and
    `uncovered_baseline_target`.
  - Updated selection ranking so explicit benchmark/baseline targets outrank
    incidental source-backed targets, and clean named targets outrank generic,
    document-like, or numeric-only labels.
  - Preserved the scheduler/admission boundary: selector only orders work; the
    central work scheduler and external-call budgets still decide whether work
    may execute.
  - Exposed ranking metadata through expansion payloads, target coverage,
    dossier, and benchmark report projection.
  - Updated AS IS Markdown/PDF.
- Tests:
  - Added selector test proving explicit benchmark completion target outranks
    incidental production-site targets.
  - Added expansion payload test proving target origin/rank metadata is visible.
  - Added benchmark report test proving ranking metadata is preserved.
- Acceptance:
  - Fast tests prove the ranking change without live providers.
  - Next practical acceptance: run bounded `benchmark_smoke_plus` again and
    verify that `tobolsk-site` is selected/executed or receives a more precise
    blocker than plain `completion_not_selected`.
  - `benchmark_live` remains blocked until the bounded smoke is interpretable.

### Slice 0.7.6.3.6.12: Review-needed entity projection and evaluation matcher parity

- Status: `Done`
- Goal: Fix the post-`0.7.6.3.6.11` gap where live smoke found source-backed
  Tobolsk production-site evidence, but evaluation still reported
  `tobolsk-site` as a false negative because review-needed entity type and
  source-backed name semantics were not preserved consistently across
  candidate-universe projection and evaluation.
- User value:
  - A user can trust the benchmark RCA: if Radar found a production site as a
    review-needed upstream entity, the evaluation report should count it as
    review recall instead of pretending it was missed.
  - Developers stop tuning budgets/search for a target that was already found;
    the next blocker becomes visible at the correct layer.
- Problem statement:
  - Docker `benchmark_smoke_plus`
    `radar-run-12727934-8686-4cc6-bb04-6ee450173775` completed with
    `strict_recall=0.8889`, `review_recall=0.6667`, and `tobolsk-site` as
    `expansion_source_found_not_projected`.
  - Dossier showed the Tobolsk industrial site as a source-backed
    review-needed / linked upstream entity, but `candidate_universe` could hold
    the same name as `unknown_entity`.
  - Root cause: projection can degrade known review-needed entity metadata to
    `unknown_entity`, and evaluation matching was too strict for source-backed
    production-site name variants such as suffixes in parentheses.
- Scope:
  - Preserve `entity_type`, `resolution_status`, `resolved_legal_name`,
    `not_candidate_reason`, `review_flags`, and `source_refs` when
    review-needed upstream entities enter or upgrade `candidate_universe`.
  - Let typed upstream entities upgrade duplicate unknown universe rows instead
    of being skipped as duplicates.
  - Make evaluation match non-legal review baseline entities against
    source-backed review-needed universe/upstream entities with tolerant,
    generic token-based name matching.
  - Add diagnostic bucket `projection_type_lost` when an entity-like row exists
    but was projected as `unknown_entity`.
- Out of scope:
  - Scheduler, budget, provider, model, scoring, UI, and source-policy changes.
  - SIBUR-specific runtime hardcode.
- Implementation notes:
  - Product `/candidates` remains strict; this slice affects review-needed
    universe projection and offline evaluation only.
  - Matching remains baseline-driven and provider-free.
- Tests:
  - Unit tests for preserving review-needed entity type without observation
    metadata.
  - Unit tests for upgrading existing duplicate `unknown_entity` universe rows
    from typed upstream disambiguation metadata.
  - Evaluation tests for Tobolsk-style production-site aliases with relation
    suffixes.
  - Evaluation diagnostics tests for `projection_type_lost`.
- Docs:
  - Added TO BE Markdown/PDF:
    `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_0.7.6.3.6.12.md` and `.pdf`.
  - Synced AS IS Markdown/PDF after implementation.
- Acceptance:
  - Bounded Docker `benchmark_smoke_plus` should no longer report
    `tobolsk-site` as false negative if source-backed Tobolsk production-site
    evidence is present.
  - `review_recall` should reach `1.0` when all production-site baseline
    entities are present as review-needed or linked upstream entities.
  - If `tobolsk-site` remains a false negative, the bucket must be narrower:
    `not_retrieved_in_run`, `present_not_projected`, `present_not_matched`, or
    `projection_type_lost`.
  - `benchmark_live` remains blocked until bounded smoke is fully
    interpretable.
- Validation:
  - Fast tests: `python -m pytest tests/test_radar_evaluation.py tests/test_live_icp_radar.py -q`.
  - API/report regression: `python -m pytest tests/test_radar_benchmark.py tests/test_backend_api.py -q`.
  - Documentation/architecture contract:
    `python -m pytest tests/test_radar_pipeline_documentation_contract.py tests/test_backend_architecture_contract.py -q`.
  - Full regression: `python -m pytest` -> `356 passed, 1 skipped`.
- Docker acceptance:
  - Run: `radar-run-136ecd8f-63a8-43a5-8542-e3016187d14f`.
  - Profile: Docker API/worker `benchmark_smoke_plus` with live DaData and
    OpenRouter Perplexity retrieval.
  - Result: `completed`, projected outcome `stopped_for_review` because
    execution budget was exhausted before signal search.
  - Evaluation: `strict_recall=0.7778`, `review_recall=1.0`,
    `false_negative_count=2`, `false_positive_count=0`.
  - Fixed acceptance target: `tobolsk-site` moved from false negative to
    `review_matches` as source-backed production-site evidence.
  - Remaining misses:
    - `nizhnekamskneftekhim`: `completion_not_selected`.
    - `kazanorgsintez`: `expansion_global_budget_limited`.
  - Probe caveat: local `probe-radar-coverage` failed with OpenRouter `401
    User not found`, while Docker API/worker OpenRouter calls succeeded. Treat
    this as CLI/probe environment parity, not as evidence that the targets are
    unavailable.
- Next correction:
  - Do not tune production-site projection further; that path now works for the
    bounded smoke.
  - Next small slice should address legal/subsidiary completion fairness and
    CLI coverage-probe environment parity, so `nizhnekamskneftekhim` and
    `kazanorgsintez` are either executed or receive a more actionable blocker.


### Slice 0.7.6.3.6.13: Legal/subsidiary completion fairness and coverage-probe runtime parity

- Status: `Done`
- Goal: Fix the remaining bounded SIBUR smoke gap after `0.7.6.3.6.12`: production-site review recall now works, but two legal/subsidiary targets still remain false negatives because the completion stage either does not select them or runs out of expansion budget before they receive a fair execution slot. Also make the diagnostic coverage probe use the same runtime/credential path as Docker API/worker or explicitly report an environment mismatch.
- User value:
  - A user can trust the benchmark report when it says a legal company was missed: the report should explain whether the target was generated, selected, admitted, executed, source-found, projected, or blocked by a specific budget/source-policy reason.
  - Developers stop guessing whether the miss is a search-quality issue, a completion selector issue, a budget issue, or a diagnostic-tool configuration issue.
- Current evidence:
  - Docker `benchmark_smoke_plus` run `radar-run-136ecd8f-63a8-43a5-8542-e3016187d14f` produced `review_recall=1.0`, so production-site projection and evaluation are no longer the blocker.
  - Remaining false negatives:
    - `nizhnekamskneftekhim`: `completion_not_selected`.
    - `kazanorgsintez`: `expansion_global_budget_limited`.
  - `probe-radar-coverage` failed locally with OpenRouter `401 User not found`, while the Docker API/worker path successfully used OpenRouter in the same acceptance run.
- Problem statement:
  - Completion currently treats many legal/subsidiary targets as a broad pool. After guaranteed production-site lanes are satisfied, legal/subsidiary targets can still lose selection to other legal variants or hit the global expansion budget without a clear per-target execution story.
  - The report says `completion_not_selected` or `expansion_global_budget_limited`, but it is not yet obvious which exact decision prevented a target from being executed: selector cap, completion cap, scheduler admission, OpenRouter budget, recall reserve, source policy, or projection.
  - The standalone coverage probe can run outside the Docker API/worker runtime and therefore may fail due to local credential/runtime mismatch. That makes RCA confusing because the main run can succeed with provider calls while the probe says provider failed.
- Scope:
  - Add legal/subsidiary completion fairness after mandatory target lanes are satisfied.
  - Reserve or fairly allocate completion slots for remaining high-priority legal/subsidiary benchmark-like targets before optional duplicate/alias variants.
  - Track every legal/subsidiary target through explicit states: `generated`, `selected`, `scheduled`, `admitted`, `executed`, `source_found`, `projected`, `not_selected`, `not_admitted`, `budget_limited`, `policy_limited`, `projection_gap`.
  - Add per-target completion reason fields so `completion_not_selected` becomes more specific: `completion_cap_exhausted`, `selector_priority_lost`, `completion_lane_quota_exhausted`, `scheduler_rejected`, `external_budget_limited`, `source_policy_limited`, or `source_found_not_projected`.
  - Make `probe-radar-coverage` runtime-safe by either:
    - executing provider probes through the API/worker path; or
    - loading and reporting the same runtime config/credentials path as Docker worker; or
    - failing early with `probe_environment_mismatch` when it cannot prove credential parity.
  - Update benchmark report and dossier with legal/subsidiary completion summaries.
- Out of scope:
  - No new provider adapter.
  - No UI changes.
  - No scoring relaxation.
  - No production hardcode for SIBUR names outside benchmark/evaluation fixtures/context.
  - No broad `benchmark_live` claim.
  - No model-role changes; those remain `0.7.6.3.7`.
- Implementation notes:
  - Keep the scheduler as the owner of budget admission. This slice should not move budget ownership back into the selector.
  - The selector/completion layer owns target ordering and fairness before scheduler admission.
  - Once production-site/branch minimums are satisfied, remaining production-site variants should not keep priority over uncovered legal/subsidiary baseline-like targets unless source policy or benchmark context says otherwise.
  - Legal/subsidiary fairness should use generic target metadata: target type, source profile/capability, benchmark/evaluation context, and source-backed hints. Do not special-case `nizhnekamskneftekhim` or `kazanorgsintez` in production runtime.
  - CLI coverage probe must not silently read a different credential source than Docker worker. If parity cannot be guaranteed, the report must say so explicitly.
- Tests:
  - Unit tests for completion selector fairness:
    - after production-site minimums are satisfied, at least two uncovered legal/subsidiary targets are selected before optional aliases;
    - one noisy legal target cannot consume all legal completion slots;
    - completion cap exhaustion records the target id, target type, lane, and exact reason;
    - uncovered legal/subsidiary benchmark-like targets outrank optional duplicate/source-backed-gap variants.
  - Scheduler/admission integration tests:
    - selected legal/subsidiary completion work is admitted when external budget exists;
    - insufficient OpenRouter budget is reported as `external_budget_limited`, not `completion_not_selected`;
    - scheduler rejection is reflected as `not_admitted`, not as selector failure.
  - Fake pipeline tests:
    - weak SIBUR contour fixture with legal misses selects and executes `nizhnekamskneftekhim`-like and `kazanorgsintez`-like targets without hardcoding those names in runtime logic;
    - if provider returns source evidence, the legal entity appears in candidate universe or receives `source_found_not_projected`;
    - if source evidence is absent, the target receives `searched_no_support`.
  - Coverage-probe tests:
    - probe using API/worker path succeeds with fake provider config;
    - local probe without matching credentials returns `probe_environment_mismatch` before provider call;
    - probe report never treats credential mismatch as evidence that the target is unavailable;
    - probe report contains no secrets, headers, raw prompts, or hidden reasoning.
  - Evaluation/report tests:
    - false negative diagnostics distinguish `completion_cap_exhausted`, `scheduler_rejected`, `external_budget_limited`, `source_found_not_projected`, and `searched_no_support`;
    - benchmark report exposes legal/subsidiary generated/selected/executed/projected counts;
    - existing production-site `review_recall=1.0` behavior does not regress in recorded fixtures.
- Docs:
  - Create TO BE Markdown/PDF before implementation because this changes the central Radar search pipeline.
  - Sync AS IS Markdown/PDF after implementation.
  - Update demo docs for coverage-probe runtime modes and how to interpret `probe_environment_mismatch`.
  - Update Roadmap with Docker acceptance run id and before/after metrics.
- Demo impact:
  - Demo benchmark report becomes easier to read: remaining legal misses should have a precise path-level explanation instead of generic budget/selection wording.
  - No UI demo change required.
- Validation commands:
  - `python -m pytest tests/test_radar_search_expansion.py tests/test_radar_adaptive_execution.py -q`
  - `python -m pytest tests/test_radar_benchmark.py tests/test_radar_evaluation.py -q`
  - `python -m pytest tests/test_live_icp_radar.py tests/test_backend_api.py -q`
  - `python -m pytest tests/test_radar_pipeline_documentation_contract.py tests/test_backend_architecture_contract.py -q`
  - `python -m pytest`
- Manual acceptance:
  - Rebuild Docker API/worker/backend-init.
  - Run `benchmark-sibur-holding-contour` with `benchmark_smoke_plus`.
  - Run evaluation.
  - Run coverage probe only through the corrected/parity-safe path.
- Acceptance criteria:
  - `review_recall` remains `1.0` or any regression is explained by provider-output drift.
  - `nizhnekamskneftekhim` and `kazanorgsintez` are either found/projected or receive precise non-generic blocker reasons.
  - No remaining legal/subsidiary false negative is reported only as broad `completion_not_selected` without selector/scheduler/budget details.
  - Coverage probe no longer reports OpenRouter `401 User not found` as a normal provider search failure; it either uses the same runtime path as Docker worker or returns `probe_environment_mismatch`.
  - `benchmark_live` remains blocked until bounded smoke is interpretable for legal/subsidiary misses.
- Risks:
  - Increasing fairness for legal/subsidiary targets could reduce optional exploration breadth in smoke. This is acceptable for bounded benchmark diagnostics, but should be explicit in the report.
  - If live provider output drifts, the acceptance should focus on diagnostic specificity, not on forcing a perfect recall score.
- Implementation completed:
  - Added TO BE Markdown/PDF for `0.7.6.3.6.13`.
  - Updated target selection so mandatory holding/legal/site lane minimums are selected first, then completion slots prefer uncovered benchmark/baseline targets. This preserves production-site completion behavior while giving legal/subsidiary misses a fair post-minimum slot.
  - Replaced vague completion diagnostics with more precise reasons such as `completion_cap_exhausted` and `selector_priority_lost`.
  - Added `legal_subsidiary_completion_summary` to execution metadata, dossier/API projection, and benchmark report.
  - Coverage probe now classifies OpenRouter auth/runtime mismatch as `probe_environment_mismatch` instead of a normal provider search failure.
  - Evaluation diagnostics now distinguish completion cap exhaustion, scheduler rejection, external budget limits, and source-found projection gaps.
  - Synced AS IS Markdown/PDF and demo documentation.
- Validation completed:
  - `python -m pytest tests/test_radar_search_expansion.py tests/test_radar_benchmark.py tests/test_radar_evaluation.py -q`
  - `python -m pytest tests/test_backend_api.py -q`
  - `python -m pytest tests/test_radar_pipeline_documentation_contract.py tests/test_backend_architecture_contract.py -q`
  - `python -m pytest` -> `358 passed, 1 skipped`.
- Docker acceptance:
  - Rebuilt Docker `api`, `worker`, and `backend-init`; restarted `redis`,
    `backend-init`, `api`, and `worker`.
  - CLI note: the current supported CLI profile name is `benchmark_smoke`.
    Its task-context budgets already include the expanded smoke-plus settings
    used by recent corrective slices (`max_openrouter_calls_per_run=20`,
    `max_recall_expansion_openrouter_calls_per_run=7`,
    `coverage_completion_target_limit=2`).
  - Run: `radar-run-12c8d936-4370-4187-b1cc-27fdcb511e76`.
  - Profile: Docker API/worker `benchmark_smoke` with live DaData and
    OpenRouter Perplexity retrieval.
  - Runtime: API healthy, OpenRouter key present, DaData live credentials
    present, retrieval provider `openrouter_perplexity`.
  - Result: `completed`, projected outcome `stopped_for_review`; benchmark
    verdict `budget_limited` because execution budget was exhausted before
    signal search.
  - Evaluation: `strict_recall=1.0`, `review_recall=1.0`,
    `false_negative_count=0`, `false_positive_count=0`.
  - `nizhnekamskneftekhim` became a true positive: observed as
    `Nizhnekamskneftekhim`, entity type `legal_entity`, source ref
    `retrieved_4`, evidence quality `strong`.
  - `kazanorgsintez` became a true positive: observed as `Казаньоргсинтез`,
    entity type `unknown_entity`, evidence quality `weak`, source refs empty.
    This is no longer a recall miss, but it remains an evidence-quality issue.
  - Legal/subsidiary completion summary: generated `44` legal/subsidiary
    targets, selected `3`, executed `2`; legal/subsidiary target-lane minimum
    was satisfied. Remaining skipped legal/subsidiary targets now have precise
    reasons such as `completion_cap_exhausted`,
    `guaranteed_external_reservation_insufficient`, and
    `optional_work_budget_limited`.
  - Budget counters: OpenRouter total `19/20`, OpenRouter web task `10/10`,
    recall-expansion OpenRouter `7/7`, server-tool web searches `61/60`,
    source verification `40/40`, DaData `2/4`.
  - Verdict: the old `completion_not_selected` blocker for the two legal
    baseline misses is fixed. The remaining blocker is different: bounded
    smoke still exhausts budgets before signal search, and one legal hit
    (`kazanorgsintez`) has weak/no-source-ref evidence.

### Slice 0.7.6.3.7: Model-role evaluation and extraction fallback policy

- Status: `Backlog`
- Goal: Stop guessing which OpenRouter model is suitable for planner,
  extraction, backup extraction, and signal tasks. Add a small model-role
  evaluation loop that measures JSON/schema/evidence-ref reliability on recorded
  Radar tasks before changing default role assignments.
- User value: A user can choose model settings based on measured role behavior
  instead of anecdotal impressions. If a model such as `minimax/minimax-m3`
  frequently breaks JSON, it should not silently remain the extraction backup.
- Problem statement:
  - Current local settings use `deepseek/deepseek-v3.2` for default, advanced,
    planner, and extractor roles, with `minimax/minimax-m3` as extraction backup
    and `qwen/qwen3.7-max` as generic backup.
  - Different roles need different qualities: planner needs strategy quality,
    extractor/backup needs strict JSON and schema discipline, signal search
    needs source-grounded evidence behavior.
  - Existing extraction recovery can name failure reasons, but there is no
    repeatable model-role comparison surface.
- Scope:
  - Add a model-role evaluation fixture set from recorded Radar tasks:
    - planner plan-shape task;
    - discovery extraction task;
    - coverage extraction task;
    - registry/cross-source relation extraction task;
    - signal extraction task;
    - malformed-output recovery task.
  - Add a provider-neutral model probe/evaluation command that can run in two
    modes:
    - recorded/fake default mode with no network calls;
    - explicit opt-in live OpenRouter mode with strict call limits.
  - Evaluate role candidates by:
    - valid JSON rate;
    - schema-valid rate;
    - evidence-ref resolution rate;
    - no hidden/forbidden key leakage;
    - retry recovery success;
    - token/call cost metadata when available;
    - latency metadata as informational only, not a hard failure.
  - Add model role policy:
    - `OPENROUTER_EXTRACTION_BACKUP_MODEL` has priority for extraction backup;
    - `OPENROUTER_BACKUP_MODEL` remains compatibility alias;
    - backup extraction must pass the extraction contract probe before it is
      recommended for smoke/benchmark settings;
    - planner and signal backup selection remain separate decisions.
  - Add runtime/dossier/report visibility:
    - model role assignments used by the run;
    - primary/retry/backup extraction attempts;
    - model failure reason buckets;
    - whether backup was skipped because not configured, budget-limited, or
      policy-disallowed.
- Out of scope:
  - Automatic production model switching without explicit config.
  - Provider price optimization logic.
  - A public leaderboard or benchmark quality claim.
  - Changing source strategy or budget reserves; that belongs to `0.7.6.3.6`.
- Implementation notes:
  - Treat model settings as role-specific runtime config, not secrets.
  - Do not rely on one live run to judge a model. Use recorded contract fixtures
    first, then optional bounded live probes.
  - Keep extraction backup strict: a cheaper/slower model is acceptable only if
    it reliably returns schema-valid JSON for the role.
  - After implementation, synchronize the AS IS Markdown/PDF because model-role
    routing and recovery policy are part of the Radar search pipeline.
- Tests:
  - Recorded model-probe tests:
    - valid extraction JSON passes;
    - non-JSON fails with `primary_non_json_http_200`/equivalent bucket;
    - schema-invalid JSON fails with field/path reason;
    - evidence refs that do not resolve are counted separately from JSON/schema
      validity;
    - hidden reasoning/secrets markers fail sanitization.
  - Role policy tests:
    - extraction backup uses `OPENROUTER_EXTRACTION_BACKUP_MODEL` when set;
    - compatibility alias `OPENROUTER_BACKUP_MODEL` is used only when
      extraction-specific backup is blank;
    - backup model is not used for planner or signal tasks unless explicitly
      configured in that role.
  - Budget tests:
    - live probes respect OpenRouter total and role-specific call caps;
    - backup probe is skipped with a clear budget reason when exhausted.
  - Report tests:
    - model-role evaluation report contains validity metrics and no raw prompts,
      provider dumps, secrets, headers, or hidden reasoning.
  - Manual acceptance:
    - run the recorded model-role evaluation;
    - optionally run a bounded live probe comparing current
      `deepseek/deepseek-v3.2`, `qwen/qwen3.7-max`, and `minimax/minimax-m3` for
      extraction backup suitability;
    - update recommended `.env.example` comments only after measured evidence.
- Docs:
  - Update Developer Guide and demo README with model-role evaluation commands
    and interpretation.
  - Update runtime config docs to distinguish default, planner, extractor,
    extraction backup, advanced, and generic backup models.
  - Update AS IS after implementation.
- Demo impact:
  - No UI change. Demo/benchmark operators get a repeatable way to choose model
    role settings before spending a long benchmark run.
- Acceptance criteria:
  - Extraction backup recommendation is backed by recorded and optional bounded
    live probe evidence.
  - A model that repeatedly fails strict extraction JSON/schema fixtures is not
    recommended as extraction backup.
  - Benchmark smoke reports show which models were used for each role and why
    extraction recovery succeeded or stopped.
- Risks:
  - Live model behavior can drift by provider. Mitigate with recorded tests as
    the gate and live probes as explicit diagnostics.
  - Too many model candidates can expand test cost. Mitigate with a small
    configured candidate list and call caps.

### Slice 0.7.6.3.6.6: Post-extraction fallback materialization and registry enrichment recheck

- Status: Blocked
- Goal: Superseded and merged into 0.7.6.4.18.1.2. Do not implement this slice independently.
- Problem statement: This older backlog item described the same post-extraction fallback/materialization problem now exposed by the live Docker/API smoke after 0.7.6.4.18.1.1. To avoid duplicate roadmap owners, its implementation scope is merged into 0.7.6.4.18.1.2.
- Scope: No independent scope remains. Implement 0.7.6.4.18.1.2 instead.
- Acceptance criteria: 0.7.6.4.18.1.2 is completed and validates post-extraction salvage/recovery without duplicate roadmap work.

### Slice 0.7.6.4.0: Radar pipeline split, model-profile separation, and documentation registry

- Status: Done
- Goal: Fix the architectural framing before implementing signal monitoring:
  Radar is not one search engine anymore. It is a family of separate search
  pipelines with different cadence, budgets, model roles, source use, tests, and
  documentation.
- User value:
  - A user can understand why candidate discovery is a heavier upstream process
    and why signal monitoring should be a frequent candidate-first process.
  - A developer can tune candidate discovery without accidentally changing
    signal monitoring behavior, and vice versa.
  - Future Power Web discovery can be added as its own pipeline instead of being
    hidden inside ICP Radar candidate search.
- Problem statement:
  - Recent corrective slices made candidate discovery mature and budget-heavy:
    source profiles, capability cards, search expansion, scheduler admission,
    recall evaluation, and AS IS/TO BE docs.
  - Signal monitoring has a different job: start from known candidates, look at
    a recent time window, find new intent signals, dedupe them, and notify sales
    when something changed.
  - Keeping both behaviors inside one implicit run kind makes budgets,
    scheduling, model tuning, and benchmark interpretation confusing.
- Out of scope:
  - No runtime signal-monitoring implementation yet.
  - No UI buttons or scheduling UI yet.
  - No DB migration.
  - No new provider adapter.
  - No benchmark-live claim.
- Acceptance:
  - Roadmap and architecture now clearly say that candidate discovery and signal
    monitoring are separate pipelines.
  - The current AS IS document is explicitly scoped to candidate discovery.
  - The next signal-monitoring implementation must start with a TO BE document,
    not with ad hoc runtime code.
- Architecture decision:
  - `candidate-discovery` is a recall-first upstream pipeline. It can be broad,
    slower, and budgeted for source expansion, registry enrichment, and
    candidate-universe construction.
  - `signal-monitoring` is a frequent monitoring pipeline. It should start from
    known product or review-needed candidates, reuse existing sources where
    useful, search recent signal evidence, and keep signal-specific budgets.
  - `power-web-discovery` is a future pipeline for people, roles, relationships,
    partner routes, influence paths, and buying-committee structure.
  - Combined discovery-plus-signal runs remain useful for smoke/debug
    compatibility, but should not be the production architecture.
  - Model-profile decision:
  - Each pipeline must own its own model-role profile.
  - Candidate-discovery model tuning must not silently change signal
    monitoring.
  - Signal-monitoring model tuning must not silently change candidate
    discovery.
  - Non-secret model-role defaults should move toward:
    - `config/radar/model_profiles/candidate_discovery.json`;
    - `config/radar/model_profiles/signal_monitoring.json`;
    - `config/radar/model_profiles/power_web_discovery.json`.
  - `.env` remains for credentials and deployment/runtime overrides.
- Docs updated:
  - `docs/adr/2026-06-30-radar-search-pipelines-are-separate.md`.
  - `docs/radar/pipelines/README.md`.
  - `docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md`.
  - `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md`.
  - `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.pdf`.
- Documentation decision:
  - Serious Radar pipelines must have separate AS IS Markdown/PDF documents.
  - Substantial changes must start with a pipeline-specific TO BE Markdown/PDF.
  - Existing pipeline documentation skills should become pipeline-aware instead
    of being duplicated per pipeline.
- Scope completed:
  - Added ADR:
    `docs/adr/2026-06-30-radar-search-pipelines-are-separate.md`.
  - Added pipeline documentation registry:
    `docs/radar/pipelines/README.md`.
  - Declared pipeline ids:
    - `candidate-discovery`;
    - `signal-monitoring`;
    - `power-web-discovery`.
  - Updated system architecture with the split between candidate discovery,
    signal monitoring, and future Power Web discovery.
  - Updated current Radar AS IS Markdown/PDF to state that it describes the
    current candidate-discovery pipeline, not the final signal-monitoring
    architecture.
- Validation:
  - Documentation-only architecture slice. Runtime behavior is unchanged.
  - Fast validation should cover architecture/doc contracts after the PDF is
    regenerated.

### Slice 0.7.6.4.0.1: SQLite slice tracker and generated Roadmap report

- Status: Done
- Goal: Stop using the 8k+ line `ROADMAP.md` as the primary editing interface.
  Keep it as a generated human-readable report, while the source of truth for
  slices becomes a small local SQLite-backed tracker with a CLI and text export
  for git review.
- User value:
  - The user and contributors still read `ROADMAP.md` as the project report.
  - The agent works through structured queries instead of scanning and patching
    a huge flat Markdown file.
  - Slice changes become less error-prone: missing ranges like
    `0.7.6.4.2-0.7.6.4.6` should be caught by structured data and tests.
- Problem statement:
  - `ROADMAP.md` has grown beyond 8,000 lines and now mixes current planning,
    historical delivery report, next actions, old decisions, and active slice
    details.
  - Manual Markdown patching creates risk: slices can be dropped, reordered, or
    reformulated without obvious validation.
  - Splitting the file into many hand-maintained Markdown files would add more
    navigation overhead. A small tracker is a cleaner working interface.
- Scope:
  - Add local project-tooling package boundaries:
    - `src/power_web_os/roadmap/__init__.py`;
    - `src/power_web_os/roadmap/models.py`;
    - `src/power_web_os/roadmap/repository.py`;
    - `src/power_web_os/roadmap/sqlite_repository.py`;
    - `src/power_web_os/roadmap/renderer.py`;
    - `src/power_web_os/roadmap/exporter.py`;
    - `src/power_web_os/roadmap/importer.py`;
    - `src/power_web_os/roadmap/cli.py`;
    - `src/power_web_os/roadmap/__main__.py`.
  - Add local SQLite database at `docs/roadmap/roadmap.sqlite`.
  - Add git-reviewable text export at `docs/roadmap/slices.export.jsonl`.
  - Add generated report metadata to `ROADMAP.md` header:
    - source database path;
    - export path;
    - render command;
    - warning that direct manual edits should be temporary.
  - Add SQLite schema:
    - `slices`:
      - `id`;
      - `title`;
      - `status`;
      - `sort_key`;
      - `parent_id`;
      - `track`;
      - `goal`;
      - `user_value`;
      - `problem_statement`;
      - `scope`;
      - `out_of_scope`;
      - `implementation_notes`;
      - `tests`;
      - `docs`;
      - `demo_impact`;
      - `acceptance_criteria`;
      - `risks`;
      - `created_at`;
      - `updated_at`.
    - `slice_events`:
      - `id`;
      - `slice_id`;
      - `event_type`;
      - `event_time`;
      - `note`.
    - `slice_links`:
      - `id`;
      - `slice_id`;
      - `link_type`;
      - `target`;
      - `label`.
    - `roadmap_meta`:
      - `key`;
      - `value`.
  - Add initial CLI:
    - `python -m power_web_os.roadmap init`;
    - `python -m power_web_os.roadmap import-current --from ROADMAP.md`;
    - `python -m power_web_os.roadmap list --status Ready`;
    - `python -m power_web_os.roadmap list --track radar`;
    - `python -m power_web_os.roadmap show 0.7.6.4.1`;
    - `python -m power_web_os.roadmap add-slice --id ... --title ...`;
    - `python -m power_web_os.roadmap update-status 0.7.6.4.1 Done`;
    - `python -m power_web_os.roadmap link 0.7.6.4.1 --type doc --target ...`;
    - `python -m power_web_os.roadmap export`;
    - `python -m power_web_os.roadmap render --output ROADMAP.md`;
    - `python -m power_web_os.roadmap check`.
  - Add deterministic renderer:
    - generated active/current roadmap section;
    - generated next recommended task section;
    - generated blocked items/open questions section;
    - preserved legacy historical report section for older completed content.
  - Add deterministic exporter:
    - one JSON object per line;
    - stable field ordering;
    - stable slice ordering by `sort_key`;
    - no timestamps changing unless data changes.
  - Add importer for the current active/future range first:
    - must import `0.7.6.4.0`;
    - must import `0.7.6.4.0.1`;
    - must import `0.7.6.4.1-0.7.6.4.6`;
    - may preserve older completed roadmap text as legacy report text without
      fully normalizing it in the first slice.
  - Add validation that generated `ROADMAP.md` and
    `docs/roadmap/slices.export.jsonl` are up to date with SQLite tracker.
- Out of scope:
  - No web UI.
  - No Jira-like workflow.
  - No multi-user server.
  - No production database dependency.
  - No complete manual cleanup of all old historical roadmap text unless it is
    mechanically safe.
  - No migration of every old completed slice into fully structured rows in
    this first slice.
  - No replacement of GitHub issues, PRs, or commit history.
- Implementation notes:
  - SQLite is the working database, but git review must use generated text
    artifacts. Do not rely on binary SQLite diffs for code review.
  - Keep the first schema deliberately small and boring. This is project
    tooling, not a product feature.
  - `ROADMAP.md` should clearly say it is generated and identify the generator
    command.
  - The CLI should use application/repository boundaries rather than ad hoc
    string manipulation.
  - The renderer should preserve the current slice format:
    Goal, User value, Scope, Out of scope, Implementation notes, Tests, Docs,
    Demo impact, Acceptance criteria, Risks.
  - Current `ROADMAP.md` content should be treated carefully: do not drop
    historical information during the first migration.
  - Keep repository boundaries simple:
    - `models.py` owns dataclasses/value objects;
    - `repository.py` owns the port/interface;
    - `sqlite_repository.py` owns SQL and migrations;
    - `renderer.py` owns Markdown output only;
    - `exporter.py` owns JSONL output only;
    - `importer.py` owns best-effort parsing of current Markdown;
    - `cli.py` owns argument parsing and calls application functions.
  - Use standard-library `sqlite3`; do not add a new dependency.
  - Treat the SQLite file as local project state that can be regenerated from
    JSONL export if needed. If both SQLite and JSONL are committed, JSONL is the
    review surface.
  - Do not silently overwrite manual `ROADMAP.md` changes. `render` should make
    this explicit and `check` should report drift.
  - Keep command output plain and human-readable for agents and contributors.
- Tests:
  - Schema/repository tests:
    - create slice;
    - update status;
    - add event;
    - add links to ADR/docs/runs/commits;
    - read next recommended task.
    - reject duplicate slice id;
    - reject invalid status;
    - preserve stable sort order.
  - CLI tests:
    - `init`;
    - `import-current`;
    - `list`;
    - `show`;
    - `add-slice`;
    - `update-status`;
    - `link`;
    - `export`;
    - `render`;
    - `check`;
    - invalid slice id returns actionable error.
  - Renderer tests:
    - deterministic Markdown output;
    - deterministic JSONL export;
    - generated ROADMAP contains all active/backlog slices in order;
    - generated report includes next recommended task, blocked items, and open
      questions.
  - Migration/import tests:
    - current `0.7.6.4.0-0.7.6.4.6` chain imports without dropping a slice;
    - historical text is preserved or explicitly marked as legacy report
      content.
    - imported `Next Recommended Task` points to `0.7.6.4.0.1`;
    - mojibake or non-ASCII text is preserved as UTF-8 in exported JSONL and
      generated Markdown.
  - Contract tests:
    - fail if `ROADMAP.md` differs from generated output after tracker changes;
    - fail if `slices.export.jsonl` is stale;
    - fail if a slice misses required fields.
    - fail if `0.7.6.4.0-0.7.6.4.6` are not all present.
  - Suggested validation commands:
    - `python -m pytest tests/test_roadmap_tracker.py -q`;
    - `python -m pytest tests/test_backend_architecture_contract.py -q`;
    - `python -m pytest`.
- Docs:
  - Update `README.md` or Developer Guide with the new roadmap workflow.
  - Add `docs/roadmap/README.md` explaining:
    - SQLite is the editing source of truth;
    - `ROADMAP.md` is generated for humans;
    - `slices.export.jsonl` is the reviewable text export;
    - exact commands for adding/updating/rendering slices.
  - Update agent guidance if needed so agents query the tracker before editing
    roadmap data.
  - Update `AGENTS.md` only if project workflow instructions need to change
    from "edit ROADMAP directly" to "use roadmap tracker first".
- Demo impact:
  - None. This is project tooling.
- Acceptance criteria:
  - A new slice can be added through the CLI and appears in generated
    `ROADMAP.md`.
  - Updating a slice status through the CLI updates SQLite, JSONL export, and
    generated ROADMAP deterministically.
  - `0.7.6.4.0-0.7.6.4.6` are present after import/render.
  - Tests catch stale generated ROADMAP/export artifacts.
  - Contributors can still read `ROADMAP.md` without knowing SQLite.
  - Agent workflow is clear: inspect/query tracker first, then render report.
  - Direct manual ROADMAP edits are no longer the normal path after this slice.
- Risks:
  - The migration can accidentally rewrite too much history. Mitigate by first
    importing only the active/future slice range and preserving old history as
    legacy generated/report text.
  - Binary SQLite in git can be awkward. Mitigate with JSONL/SQL text export as
    the review surface.
  - Tooling can become overbuilt. Keep the first version CLI-only and focused
    on slice tracking.
  - Generated report can hide useful editorial context if the renderer is too
    rigid. Mitigate by preserving a legacy report section and allowing structured
    free-text fields.

### Slice 0.7.6.4.1: Pipeline documentation registry and signal-monitoring TO BE

- Status: Done
- Goal: Create the documentation system for multiple Radar search pipelines and
  prepare the first reviewed TO BE design for signal monitoring.
- User value: A user and a developer can understand the signal-monitoring
  algorithm before implementation, instead of mixing it into the already large
  candidate-discovery AS IS document.
- Scope:
  - Keep `docs/radar/pipelines/README.md` as the registry for serious Radar
    pipelines.
  - Treat `candidate-discovery` as the current mature pipeline and keep the
    current `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md` as its legacy/current
    entrypoint until a later migration slice.
  - Create `docs/radar/pipelines/signal-monitoring/to-be/` and the first
    `RADAR_SIGNAL_MONITORING_TO_BE_<slice>.md` plus PDF.
  - Update existing Radar pipeline skills so they accept pipeline id:
    - `pipeline=candidate-discovery`;
    - `pipeline=signal-monitoring`;
    - `pipeline=power-web-discovery`.
  - Document the rule: each serious pipeline has its own AS IS and TO BE
    Markdown/PDF.
- Out of scope:
  - No runtime signal monitoring.
  - No new providers.
  - No broad benchmark.
- Implementation notes:
  - Do not create separate skill families for every pipeline. Extend the
    current generic skills.
  - The user should be able to say: "Сделай TO BE для signal-monitoring по
    слайсу 0.7.6.4.1".
- Tests:
  - Documentation contract tests for pipeline registry and required PDF/MD
    files.
  - Skill/path tests proving pipeline id maps to the right output folder.
- Docs:
  - Update `docs/radar/pipelines/README.md`, Developer Guide, and ROADMAP.
- Demo impact:
  - None.
- Acceptance criteria:
  - Signal-monitoring TO BE exists as Markdown and PDF.
  - The documentation skills are pipeline-aware.
  - Candidate-discovery AS IS is not overwritten.
- Risks:
  - Documentation can drift from implementation. Mitigate by requiring AS IS
    sync after every signal-monitoring runtime slice.

### Slice 0.7.6.4.2: Signal monitoring application contract and recorded harness

- Status: Done
- Goal: Create a fast no-live-provider test harness for signal monitoring
  before any OpenRouter/DaData/live source work.
- User value: The team can prove signal-monitoring behavior in seconds and
  catch JSON/schema/evidence-linking failures without paying for long live runs.
- Scope:
  - Add application contracts:
    - `SignalMonitoringRun`;
    - `SignalMonitoringPlan`;
    - `SignalSearchTask`;
    - `SignalObservation`;
    - `SignalEvidence`;
    - `SignalMonitoringOutcome`.
  - Define inputs:
    - candidate universe or accepted candidates from latest discovery;
    - signal rules;
    - lookback window;
    - known candidate sources;
    - signal-specific source policy.
  - Add fake/recorded tests for:
    - candidate exists and signal is found;
    - candidate exists and signal is searched-negative;
    - source is found but evidence is not linked;
    - budget exhausted;
    - duplicate old signal;
    - malformed JSON -> retry -> backup model.
- Out of scope:
  - No live OpenRouter by default.
  - No UI controls.
  - No production scheduler.
- Implementation notes:
  - This is the red/green contract layer for signal monitoring, similar to the
    adaptive candidate-discovery harness.
  - `not_observed` must mean "searched and no signal", not "not searched".
- Tests:
  - Unit tests for every contract mapper and state transition.
  - Recorded/fake provider tests for schema invalid, retry, backup, evidence
    ref linking, duplicate signal, budget-limited, and searched-negative states.
  - Secret/hidden-reasoning redaction tests.
- Docs:
  - Update signal-monitoring TO BE or AS IS draft with contracts and states.
- Demo impact:
  - None yet.
- Acceptance criteria:
  - The harness runs without network, Redis, Celery, DB server, or local API.
  - Every terminal state is explicit and diagnostic.
- Risks:
  - The contract may overfit to TOIR. Keep signal definitions generic and put
    TOIR examples in fixtures only.

### Slice 0.7.6.4.3: Signal source strategy and warm-start from known sources

- Status: Done
- Goal: Define and test the source strategy for signal monitoring: first reuse
  known useful candidate sources, then search official/company sources,
  signal-specific sources, and only then broader open web.
- User value: Signal monitoring becomes cheaper and more focused because it
  does not rediscover identity and does not ignore already collected evidence.
- Scope:
  - Add warm-start source selection from candidate-discovery results:
    - used sources;
    - retrieved/analyzed sources;
    - official/company sources;
    - candidate-specific source refs.
  - Add source strategy order:
    - known useful sources from discovery;
    - official/company sources;
    - signal-specific sources;
    - open web.
  - Use connector capabilities to decide whether a source can provide signal
    evidence.
  - Identity-only connectors must not be used as signal evidence unless their
    profile explicitly supports signal evidence.
- Out of scope:
  - No provider-specific hardcode such as "DaData cannot be used".
  - No UI.
  - No new connector marketplace.
- Implementation notes:
  - The rule is capability-based: current DaData profile is not signal-capable,
    but another registry/source plugin may be signal-capable later.
  - Source strategy should produce diagnostics when a configured required
    signal source is skipped or not executable.
- Tests:
  - Unit tests for source ordering and capability filtering.
  - Fake pipeline tests proving known sources are checked before new open-web
    search.
  - Tests proving identity-only connector is skipped for signal evidence by
    capability, not by provider id.
  - Dossier/report tests for source strategy decisions.
- Docs:
  - Update signal-monitoring TO BE/AS IS and connector-profile ADR notes.
- Demo impact:
  - None until runtime smoke.
- Acceptance criteria:
  - Signal monitoring can explain which sources it reused, searched, skipped,
    or rejected by capability.
- Risks:
  - Reusing old sources can miss fresh signals. Mitigate with lookback-aware
    new search after warm-start.

### Slice 0.7.6.4.4: Signal monitoring budgets and model profile isolation

- Status: Done
- Goal: Give signal monitoring its own budgets and model row so candidate
  discovery tuning cannot starve or break signal search.
- User value: A user can run frequent signal checks with predictable cost and
  without depending on candidate-discovery budget leftovers.
- Scope:
  - Add separate signal external-call budgets:
    - signal OpenRouter calls;
    - signal source verification;
    - signal extraction retries;
    - signal lookback queries.
  - Add signal model role settings:
    - signal planner;
    - signal extractor;
    - signal backup extractor;
    - signal evidence judge;
    - optional dedupe model.
  - Add role-specific temperature/default settings:
    - strict extraction;
    - slightly flexible monitoring query expansion;
    - strict evidence judge/dedupe.
  - Ensure changing candidate-discovery model profile does not change
    signal-monitoring profile.
- Out of scope:
  - No automatic model selection.
  - No price optimizer.
  - No broad model benchmark.
- Implementation notes:
  - Non-secret model profiles belong in config, not `.env`.
  - `.env` remains for credentials, endpoints, and emergency overrides.
- Tests:
  - Config tests proving candidate and signal profiles are independent.
  - Budget tests proving signal calls do not consume candidate-discovery
    expansion reserves.
  - Retry/backup tests for malformed signal JSON.
  - Runtime config redaction tests.
- Docs:
  - Update Developer Guide, `.env.example`, pipeline registry, and
    signal-monitoring docs.
- Demo impact:
  - None until signal smoke.
- Acceptance criteria:
  - Signal monitoring has independent budget counters and model-role
    configuration.
  - Candidate-discovery model/budget edits cannot silently change signal
    monitoring.
- Risks:
  - Too many model settings can confuse setup. Mitigate with named profile
    defaults and clear override precedence.

### Slice 0.7.6.4.4.1: Radar runtime config source-of-truth extraction from .env

- Status: Done
- Goal: Make config/radar the source of truth for non-secret Radar runtime defaults while keeping .env as secrets and override layer.
- Scope:
  - Add config-backed non-secret runtime defaults and run profiles.
  - Update candidate-discovery and signal-monitoring model profiles to match the current intended model row.
  - Keep legacy env variable names as compatibility overrides.
  - Wire runtime report, API settings, workflow defaults, OpenRouter provider, DaData provider, and preflight probes through the same effective runtime settings snapshot.
  - Update .env.example to contain only secrets, infrastructure URLs, and config path.
- Out of scope:
  - No UI settings editor.
  - No live provider benchmark.
  - No migration of actual local .env secrets.
  - No removal of compatibility env variable names.
- Tests:
  - Runtime config source-of-truth tests.
  - Env override precedence tests.
  - Workflow/provider config-consumer tests.
  - Model profile value tests.
  - Candidate-discovery regression tests around live Radar config and preflight.
- Docs:
  - Developer Guide explains config -> run profile -> .env -> process env -> explicit override precedence.
  - Application README and Radar pipeline registry name the runtime settings owner.
  - Universal LLM call ADR records that non-secret model and budget defaults live in config/radar.
- Acceptance criteria:
  - A clean environment without model/budget env vars resolves to the current intended OpenRouter, DaData, retrieval, and smoke budget values from config.
  - .env/process env values still override config.
  - Candidate-discovery live provider and workflow defaults use the same config-backed values as runtime config report.
  - Runtime reports remain redacted and do not expose secrets.
- Problem: Model rows, provider modes, DaData mode/base URL, and smoke budgets were split between .env.example, local .env, runtime report defaults, and model profile JSON. The values drifted, and signal/candidate profile isolation was only partial.

### Slice 0.7.6.4.5: First recorded TOIR signal monitoring loop

- Status: Done
- Goal: Build the first working signal-monitoring loop for TOIR using
  fake/recorded providers, without making a live benchmark claim.
- User value: The product can show the core signal-monitoring idea: known
  candidates are checked for new tenders, vacancies, implementation news, or
  other TOIR-relevant activity.
- Scope:
  - Use 3-5 found candidates from the SIBUR benchmark fixture/output.
  - Use TOIR signal rules.
  - Recorded/fake provider returns:
    - tender signal;
    - vacancy signal;
    - article about 1C/TOIR/EAM implementation;
    - empty search;
    - duplicate old signal.
  - Output shows:
    - new signals;
    - repeated signals;
    - no new signal;
    - not searched because budget-limited;
    - evidence refs.
- Out of scope:
  - No live quality claim.
  - No sales notification.
  - No CRM handoff.
  - No Power Web route update.
- Implementation notes:
  - This is a recorded product loop, not a benchmark.
  - Keep candidate-discovery output as input; do not rediscover candidates.
- Tests:
  - Recorded end-to-end signal-monitoring test.
  - Dedupe tests for repeated old signal.
  - Evidence-linking tests for every observed signal.
  - Product projection tests for new/repeated/no-signal/not-searched states.
- Docs:
  - Sync signal-monitoring AS IS Markdown/PDF after implementation.
  - Update demo README with the recorded TOIR signal loop.
- Demo impact:
  - Demo can show a separate technical command/API path for signal monitoring.
- Acceptance criteria:
  - Recorded signal-monitoring loop reaches terminal state.
  - At least one new signal, one repeated signal, one searched-negative, and
    one budget/not-searched state are represented.
- Risks:
  - Recorded examples may look too synthetic. Keep fixtures realistic and mark
    them as recorded/fake.

### Slice 0.7.6.4.6: UI controls for candidate discovery vs signal monitoring

- Status: Done
- Goal: Make the pipeline split visible to users in the Radar UI.
- User value: A user understands whether they are launching candidate search or
  signal monitoring, and can see separate cadence/status for both.
- Scope:
  - Add UI action for candidate discovery, for example "Запустить поиск
    кандидатов".
  - Add UI action for signal monitoring, for example "Проверить сигналы".
  - Add settings/display for:
    - candidate discovery schedule;
    - signal monitoring schedule;
    - last candidate discovery run;
    - last signal monitoring run;
    - next scheduled checks;
    - signal run status.
  - Keep old combined run only as compatibility/debug if still needed.
- Out of scope:
  - No production scheduler daemon unless already implemented by backend
    slices.
  - No notification center.
  - No CRM task generation.
- Implementation notes:
  - Use the existing Power Web OS design system.
  - UI copy must make clear that candidate discovery answers "кого
    мониторить", while signal monitoring answers "что нового произошло".
- Tests:
  - Frontend component/contract tests for two actions and two status areas.
  - API adapter tests for run kind.
  - Visual/smoke test for dense layout and no text overlap.
- Docs:
  - Update User Guide and demo docs.
- Demo impact:
  - User-facing Radar workflow becomes more honest: two separate searches are
    visible.
- Acceptance criteria:
  - User can launch or inspect candidate discovery and signal monitoring
    separately.
  - UI does not imply that signal monitoring was executed during a
    candidate-discovery-only run.
- Risks:
  - UI may get ahead of backend runtime. Only expose actions backed by real API
    behavior or clearly disabled/planned state.

### Slice 0.7.6.4.6.1: Radar operations tab for runs, checks, and diagnostics

- Status: Done
- Goal: Move Radar run controls, preflight checks, and diagnostics out of the found-accounts tab into a dedicated Operations tab; remove the obsolete duplicated live-run plaque while preserving candidate-discovery and recorded signal-monitoring controls.

### Slice 0.7.6.4.7: Radar backend architecture rescue plan and package contract

- Status: Done
- Goal: Stop the Radar backend from growing as a flat pile of `live_radar_*` modules. Define the target package architecture, component contract, migration order, and architecture tests before moving runtime code.
- User value: Developers and agents can understand where Radar backend logic belongs, extend the pipeline safely, and onboard without reverse-engineering dozens of unrelated-looking files.
- Problem statement:
  - `src/power_web_os/application` currently contains 38 `live_radar_*.py` modules with more than 10k lines in one flat namespace.
  - `live_radar_staged_execution.py` and `live_radar_service.py` remain large allowlisted exceptions.
  - Existing backend guardrails protect coarse layers such as API/application/integrations, but they do not protect internal Radar package boundaries.
  - `src/power_web_os/application/README.md` lists modules, but does not give a navigable package map, common component contract, or extension path for candidate discovery phases.
- Scope:
  - Add ADR: Radar backend package architecture and component contract.
  - Add `docs/architecture/RADAR_BACKEND_ARCHITECTURE.md` with AS IS inventory and TO BE package map.
  - Classify current `live_radar_*` files by responsibility: contracts, planning, retrieval, extraction, source/capability, registry/enrichment, expansion, scheduler, checkpoints, universe, execution, diagnostics, service facade.
  - Define target package layout under `src/power_web_os/application/radar/`.
  - Define common component contract naming: `Input`, `Result`, `Decision`, `Issue`, `Event`, `Service`, and pure `*_payload`/`*_summary` helpers.
  - Define allowed import direction inside Radar packages.
  - Add architecture tests that forbid new root-level `application/live_radar_*.py` modules outside an explicit migration allowlist.
  - Add architecture tests for package README presence, module fan-out, and large orchestration exceptions.
  - Update agent guidance so future Radar backend work starts from the package contract instead of adding a new `live_radar_*` module.
- Out of scope:
  - No behavioral runtime refactor yet.
  - No Docker smoke, benchmark, UI, provider, DB, or API changes.
  - No mass moving files in this slice.
  - No removal of existing compatibility imports yet.
- Implementation notes:
  - Treat this as the rescue design and guardrail slice. It should make the next code-moving slices safer.
  - Do not pretend that module docstrings alone solve discoverability; each target package needs a local README with ownership, allowed imports, extension path, and tests.
  - The architecture tests should initially allow current legacy files, but fail on new root-level `live_radar_*` modules.
  - Capture measured baseline numbers in docs: current count of `live_radar_*` files, total lines, largest modules, and allowlisted files.
- Tests:
  - `python -m pytest tests/test_backend_architecture_contract.py -q` must pass with new architecture assertions.
  - Add/extend tests that check no new root `application/live_radar_*.py` files can be introduced outside the migration allowlist.
  - Add/extend tests that `docs/architecture/RADAR_BACKEND_ARCHITECTURE.md` exists and names target Radar packages.
  - Add/extend tests that root-level large legacy allowlist is explicit and temporary.
- Docs:
  - New ADR under `docs/adr/`.
  - New backend Radar architecture document.
  - Update `docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md`.
  - Update `docs/developer/DEVELOPER_GUIDE.md`.
  - Update `src/power_web_os/application/README.md` to point to the detailed Radar backend architecture doc instead of trying to carry the whole map inline.
  - Update relevant agent skills/rules if they currently permit ad hoc root-level backend modules.
- Demo impact:
  - None. This slice is architecture governance only.
- Acceptance criteria:
  - The next backend Radar slice has a clear target package and component contract.
  - New root-level `live_radar_*` modules are prohibited by tests.
  - Current legacy exceptions are documented as temporary migration debt.
  - A developer can open one architecture document and understand where to place new Radar backend code.
  - The roadmap clearly prioritizes this refactor track before more large Radar backend features.
- Risks:
  - Too much design without code movement. Mitigate by keeping this slice narrow and immediately following with package skeleton/facade migration.
  - Overly strict tests may block small bugfixes. Mitigate with explicit temporary allowlists and clear migration notes.

### Slice 0.7.6.4.8: Candidate discovery package skeleton and compatibility facades

- Status: Done
- Goal: Create the target Radar package structure without changing runtime behavior.
- User value: Developers get real folders and local README files for candidate discovery phases instead of a flat `live_radar_*` namespace.
- Problem statement: The package contract from `0.7.6.4.7` needs to become visible in code before modules can be moved safely.
- Scope:
  - Add `src/power_web_os/application/radar/` package.
  - Add `shared/`, `candidate_discovery/`, `candidate_discovery/planning/`, `retrieval/`, `extraction/`, `sources/`, `universe/`, `checkpoints/`, `execution/`, and `diagnostics/` subpackages as needed.
  - Add local README files explaining ownership, allowed imports, and extension paths.
  - Add compatibility facade modules or re-export points so existing imports keep working while migration proceeds.
  - Add architecture tests that target packages exist and include README guidance.
- Out of scope:
  - No large logic moves yet.
  - No runtime behavior change.
  - No deletion of legacy files.
- Implementation notes:
  - Keep this slice mostly structural. The goal is a safe landing zone for later moves.
  - Prefer package-level `contracts.py` and `README.md` before moving phase logic.
- Tests:
  - Backend architecture contract tests.
  - Import smoke tests for new packages and compatibility facades.
  - Existing Radar unit/API tests should remain green.
- Docs:
  - Update Radar backend architecture doc with actual package paths.
  - Update Developer Guide with the new extension path.
- Demo impact:
  - None.
- Acceptance criteria:
  - New Radar backend package skeleton exists.
  - Existing runtime imports remain compatible.
  - New packages are documented close to code.
  - No behavior-changing refactor is hidden in the skeleton slice.
- Risks:
  - Creating folders without migration can look cosmetic. Mitigate by keeping the next migration slice immediately actionable.

### Slice 0.7.6.4.9: Move candidate discovery contracts, planning, and source capability modules

- Status: Done
- Goal: Move lower-risk candidate-discovery contracts and planning/source-capability modules into the new package structure first.
- User value: The most frequently extended planning/source-policy code becomes discoverable and package-owned before deeper execution refactors.
- Problem statement: The current flat namespace mixes contracts, planner input, source cards, connector capabilities, and execution helpers. Safe migration should start with modules that have clear boundaries and good tests.
- Scope:
  - Move or wrap `live_radar_contracts`, discovery planning, plan acceptance, source cards, connector/capability-facing helpers, retrieval-plan contracts, and related pure models into target packages.
  - Keep old import paths as compatibility shims during the migration.
  - Update tests and docs to prefer the new package imports.
- Out of scope:
  - No `live_radar_staged_execution.py` split yet.
  - No provider/integration adapter changes.
  - No scoring or benchmark quality changes.
- Implementation notes:
  - Move pure contracts before orchestration.
  - Avoid changing DTO fields unless tests prove compatibility.
  - Track each old module as moved, wrapped, or deferred.
- Tests:
  - Existing planner/source-card/connector/preflight tests.
  - Import compatibility tests for old paths.
  - Architecture tests proving new code imports from the target packages.
- Docs:
  - Update Radar backend architecture inventory and migration table.
  - Update AS IS pipeline docs only if behavior wording changes.
- Demo impact:
  - None.
- Acceptance criteria:
  - Planning/source capability code lives under the new package structure or has explicit compatibility wrappers.
  - Existing tests pass without changing product behavior.
  - The flat root-level `live_radar_*` count decreases or the remaining wrappers are clearly marked.
- Risks:
  - Import churn can break many tests. Mitigate with compatibility facades and narrow moves.

### Slice 0.7.6.4.10: Split candidate discovery staged execution into phase executors

- Status: Done
- Goal: Break `live_radar_staged_execution.py` into explicit candidate-discovery phase executors with a thin orchestrator.
- User value: The central live Radar execution path becomes understandable, testable by phase, and safer to modify.
- Problem statement: `live_radar_staged_execution.py` is the current worst hotspot: it is oversized, imports many application modules, and owns too many execution phases at once.
- Scope:
  - Introduce phase executor services for discovery, qualification/gate, coverage, expansion, enrichment/registry, checkpoint handling, universe freeze, and signal-compat suppression if still needed.
  - Keep one thin orchestrator that orders phases but does not own phase internals.
  - Replace broad helper-function imports with explicit service dependencies and phase result contracts.
  - Preserve current artifact shape and diagnostics.
- Out of scope:
  - No provider quality tuning.
  - No signal-monitoring production runtime.
  - No DB/API contract change unless unavoidable for compatibility.
- Implementation notes:
  - Do this after package skeleton and low-risk moves are complete.
  - Start with golden recorded/fake tests around current behavior.
  - Move one phase at a time inside the slice only if tests stay green; otherwise split further.
- Tests:
  - Recorded candidate-discovery pipeline tests before and after refactor.
  - Existing live Radar/adaptive/budget/API tests.
  - Architecture tests for module size and application import fan-out.
  - Artifact/dossier compatibility tests.
- Docs:
  - Update Radar backend architecture doc and candidate-discovery AS IS Markdown/PDF.
  - Document phase executor responsibilities close to code.
- Demo impact:
  - No intended visual/product change; demo should continue to read the same API outputs.
- Acceptance criteria:
  - `live_radar_staged_execution.py` is no longer a large allowlisted execution owner.
  - Execution phases have explicit package locations and contracts.
  - Runtime behavior and dossier/report outputs remain compatible.
  - Tests demonstrate phase-level behavior, not only end-to-end behavior.
- Risks:
  - This is the highest-risk code movement. Mitigate with recorded fixtures, compatibility output tests, and small internal phase moves.

### Slice 0.7.6.4.11: Candidate discovery phase service contract, validators, and agent rules

- Status: Done
- Goal: Turn the candidate-discovery phase split into a durable service-oriented execution contract, then enforce the Radar backend architecture rules with validators and agent workflows.
- User value: Future agents and developers get immediate feedback when they add code in the wrong place or recreate a hidden orchestration monolith.
- Problem statement: Slice 0.7.6.4.10 safely split the old staged execution monolith into package-owned phase modules, but the first split is still mostly procedural: public phase functions pass many state, budget, provider, and checkpoint arguments around. Written ADRs are not enough; without a concrete PhaseExecutor/Service contract and validators, the codebase can drift back into hidden orchestration sprawl.
- Scope:
  - Introduce explicit execution contracts for candidate discovery:
  - `CandidateDiscoveryExecutionContext`;
  - `CandidateDiscoveryExecutionState`;
  - `PhaseResult` / phase issue records where useful;
  - `CandidateDiscoveryOrchestrator`;
  - `DiscoveryPhaseExecutor`;
  - `GatePhaseExecutor`;
  - `CoveragePhaseExecutor`;
  - `ExpansionPhaseExecutor`;
  - `SignalCompatibilityPhaseExecutor`;
  - `FinalizationProjector`.
  - Convert the current procedural phase functions from 0.7.6.4.10 into classes/services without changing runtime behavior or artifact shape.
  - Make `CandidateDiscoveryExecutionState` the normal way to carry mutable execution data between phases instead of passing long argument lists.
  - Keep pure helpers only for small local transformations, `*_payload`, `*_summary`, and compatibility projections.
  - Extend `tests/test_backend_architecture_contract.py` with Radar-specific package rules.
  - Validate no new root-level `live_radar_*` modules.
  - Validate package README files, module docstrings for public services, max file size, max application import fan-out, and limited public top-level helper functions.
  - Add a rule that public top-level functions carrying provider, budget, checkpoint, source policy, or execution state are forbidden unless explicitly allowlisted as compatibility shims.
  - Update agent skills so backend Radar work must name the target package, service/phase contract, and architecture tests.
- Out of scope:
  - No product behavior changes.
  - No provider quality tuning.
  - No DB/API/UI contract changes.
  - No broad automated formatter/rewrite.
  - No style-only linting unrelated to architecture.
  - No removal of legacy wrappers; that remains 0.7.6.4.12.
- Implementation notes:
  - Do the service-contract refactor before writing strict validators, otherwise validators will either be too weak or fail on the current procedural phase modules.
  - Keep behavior-preserving compatibility: old imports and `run_staged_radar_execution` must continue to work.
  - Prefer constructor-injected dependencies and explicit context/state objects over long function signatures.
  - Keep validators precise and explainable. Tests should fail with actionable messages, not generic style complaints.
  - Allow explicit migration exceptions with expiry notes while legacy wrappers remain.
- Tests:
  - Regression tests proving the class-based phase services preserve adaptive execution, live ICP recorded behavior, external-call budgets, API behavior, and preflight behavior.
  - Architecture contract tests for every new rule.
  - Import compatibility tests proving old staged execution paths still work.
  - Negative fixture or temporary generated file test if practical for public top-level phase functions.
  - Roadmap/tracker check after docs updates.
- Docs:
  - Update Radar backend architecture doc with the concrete phase service contract.
  - Update execution package README with service classes, context/state ownership, and extension rules.
  - Update Developer Guide and agent skills so future Radar backend work follows the same service contract.
  - Update ADR notes if the component contract is tightened.
- Demo impact:
  - None.
- Acceptance criteria:
  - Candidate-discovery staged execution phases are represented by explicit service/projector classes, not only public procedural functions.
  - `CandidateDiscoveryExecutionState` or equivalent state object is the normal cross-phase state carrier.
  - `run_staged_radar_execution` remains compatible through the old import path.
  - A new ad hoc `application/live_radar_new_feature.py` would fail validation.
  - A new phase package without README would fail validation.
  - A large orchestration module, high fan-out module, or public stateful phase function would fail validation unless explicitly allowlisted.
  - Agent guidance points to the same rules as the tests.
- Risks:
  - Converting functions to classes can accidentally change mutation order or artifact shape. Mitigate with the existing adaptive/live/budget/API regression set.
  - Overly aggressive validators can slow delivery. Mitigate with migration allowlists and clear failure messages.

### Slice 0.7.6.4.11.1: Candidate discovery execution helper decomposition and strict service API

- Status: Done
- Goal: Convert candidate-discovery execution helpers into strict service-owned APIs, enforce guardrails, and preserve recorded/fake pipeline behavior.

### Slice 0.7.6.4.11.2: Candidate discovery execution architecture handbook, class docstrings, and service interface contract

- Status: Done
- Goal: Document candidate-discovery execution architecture, add service interface contracts, require class docstrings with handbook links, and enforce drift checks.

### Slice 0.7.6.4.12: Remove legacy live_radar allowlist and compatibility debt

- Status: Done
- Goal: Close the architecture rescue by removing temporary large-module exceptions and reducing old root-level `live_radar_*` files to thin compatibility shims or deleting them.
- User value: The backend no longer depends on undocumented legacy exceptions, and the Radar codebase has a stable structure for future candidate discovery, signal monitoring, and Power Web discovery work.
- Problem statement: A refactor is incomplete if the old oversized modules remain permanently allowlisted. The migration needs a cleanup slice that makes the new architecture the actual enforced default.
- Scope:
  - Remove `live_radar_service.py` and `live_radar_staged_execution.py` from the large-module allowlist once migrated.
  - Delete or shrink legacy root-level wrappers where imports have been migrated.
  - Update architecture docs to mark the rescue complete.
  - Run broad regression for candidate discovery and signal-monitoring recorded harness.
- Out of scope:
  - No new product features.
  - No benchmark quality claims.
  - No UI redesign.
- Implementation notes:
  - This slice should happen only after behavior-preserving migration and validators are green.
  - Keep compatibility imports only where external callers still need them, and document removal plan.
- Tests:
  - Full backend architecture contract.
  - Candidate discovery recorded/live relevant tests.
  - Signal monitoring recorded tests.
  - Backend API tests.
  - Roadmap tracker check.
- Docs:
  - Update Radar backend architecture doc, SAO, Developer Guide, and ADR status/notes.
  - Update AS IS pipeline docs if package names in the algorithm description changed.
- Demo impact:
  - No intended product change.
- Acceptance criteria:
  - Legacy large-module allowlist no longer contains the migrated Radar execution/service modules.
  - Root-level `live_radar_*` files are either gone or explicitly thin compatibility wrappers.
  - Architecture tests enforce the new structure without broad temporary exceptions.
  - Existing product behavior remains stable.
- Risks:
  - Removing wrappers too early can break hidden imports. Mitigate with import compatibility tests and staged deprecation.

### Slice 0.7.6.4.13: Candidate discovery staged execution options value object

- Status: Done
- Goal: Replace the large kwargs interface around `run_staged_radar_execution` with a named candidate-discovery execution options value object.
- User value: Developers can change Radar execution limits, reserves, and policy inputs through one typed contract instead of tracing dozens of optional keyword arguments.
- Problem statement: The rescue slices moved staged execution behind service classes, but the boundary between `LiveRadarRunService` and the execution orchestrator still exposes a procedural kwargs surface. That surface can drift, hides option ownership, and makes future pipeline fixes harder to review.
- Scope:
  - Introduce `CandidateDiscoveryExecutionOptions` or an equivalent value object in the candidate-discovery execution package.
  - Move staged execution option parsing from `LiveRadarTaskContextReader` into that value object or a factory returning it.
  - Change `run_staged_radar_execution` / `CandidateDiscoveryOrchestrator` to accept the options object while preserving the old compatibility wrapper if needed.
  - Keep `LiveRadarRunService` as a thin use-case facade that passes an options object, not a long kwargs list.
  - Add architecture tests that prevent a new broad staged-execution kwargs surface from returning.
- Out of scope:
  - No provider quality tuning.
  - No checkpoint, extraction, scoring, dossier, API, DB, or UI behavior changes.
  - No migration of unrelated root-level `live_radar_*` modules.
- Implementation notes:
  - Treat this as post-rescue hardening before the next behavior-changing Radar pipeline slice.
  - Keep old import paths compatible.
  - Prefer a Pydantic or frozen dataclass-style value object only if it matches existing execution contracts; do not add a validation framework solely for style.
  - Preserve AS IS pipeline order, checkpoint semantics, budget counters, and dossier contract.
- Tests:
  - `python -m pytest tests/test_backend_architecture_contract.py tests/test_radar_backend_package_contract.py tests/test_radar_live_run_service_components.py -q`
  - `python -m pytest tests/test_live_icp_radar.py tests/test_radar_adaptive_execution.py tests/test_radar_search_expansion.py tests/test_radar_external_call_budget.py -q`
  - `python -m pytest tests/test_backend_api.py tests/test_radar_preflight.py tests/test_persisted_live_radar.py tests/test_radar_jobs.py -q`
  - `python -m power_web_os.roadmap check`
  - `git diff --check`
- Docs:
  - Update `docs/architecture/RADAR_BACKEND_ARCHITECTURE.md`.
  - Update `src/power_web_os/application/radar/candidate_discovery/execution/README.md` or the execution handbook if the public execution contract changes.
  - Update `src/power_web_os/application/radar/candidate_discovery/README.md` if the service/component map changes.
- Demo impact:
  - None intended; existing Radar API/demo outputs should remain compatible.
- Acceptance criteria:
  - Staged execution options are represented by one named value object or equivalent service-owned contract.
  - `LiveRadarRunService` no longer passes a broad list of execution kwargs.
  - Existing compatibility imports and fake/recorded candidate-discovery behavior remain green.
  - Architecture tests catch reintroduction of broad procedural staged-execution option plumbing.
- Risks:
  - A mechanical signature change can alter default handling. Mitigate with budget/adaptive/API regression tests and focused tests for context-to-options parsing.
  - Over-designing the value object can slow future pipeline fixes. Keep it scoped to the current execution boundary.

### Slice 0.7.6.4.14: Live Radar run service composition factory

- Status: Done
- Goal: Move `LiveRadarRunService` dependency assembly into a package-owned composition/factory component so the service stays a use-case facade.
- User value: Developers can replace planner, provider wrapper, artifact projector, budget merger, event projector, and context/options factories intentionally without editing the facade constructor for every wiring change.
- Problem statement: `LiveRadarRunService` now delegates behavior to named components, but it still constructs most collaborators directly. That keeps composition decisions inside the use-case facade and makes future tests or alternate runtime wiring more awkward.
- Scope:
  - Introduce a narrow `LiveRadarRunServiceFactory`, `LiveRadarRunComposition`, or equivalent package-owned composition component.
  - Keep production workflow imports on the package-owned path.
  - Allow explicit injection of projector/merger/event/options dependencies for tests and alternate runtime assembly.
  - Preserve legacy import compatibility for `power_web_os.application.live_radar_service`.
- Out of scope:
  - No DI framework.
  - No API/worker/scheduler topology change.
  - No behavior change to planning, staged execution, signal search, scoring, or dossier projection.
- Implementation notes:
  - Do this after `0.7.6.4.13`, because the options object should be one of the factory-owned collaborators.
  - Keep the factory small; it should wire objects, not own pipeline decisions.
  - After this slice, resume the product corrective backlog, starting with `0.7.6.3.6.6`, before further migration waves unless architecture drift reappears.
- Tests:
  - Package import tests for factory/composition components.
  - Existing live ICP, adaptive, budget, API, persisted/job, and architecture tests.
  - A focused construction test proving default factory output and manually injected collaborators preserve service behavior.
- Docs:
  - Update Radar backend architecture doc and candidate-discovery README with composition ownership.
  - Update Developer Guide if service construction guidance changes.
- Demo impact:
  - None intended.
- Acceptance criteria:
  - `LiveRadarRunService` remains a use-case facade and no longer acts as its own composition root.
  - Default production workflow can construct the service through the package-owned composition path.
  - Tests prove compatibility with the legacy import path and existing runtime behavior.
- Risks:
  - Introducing a factory can become ceremonial. Keep only dependencies that already exist and are useful to test or replace.

### Slice 0.7.6.4.14.1: Radar root namespace closure plan and test import migration

- Status: Done
- Goal: Create the explicit closure plan for root-level Radar namespace debt before product behavior work: inventory all root `live_radar_*`, `radar_search_*`, and `signal_monitoring_*` modules, migrate behavior tests to package-owned imports where behavior already moved, add guardrails against new production/test imports through legacy paths, and create the missing follow-up slices.
- User value: A developer opening the repository can trust that `src/power_web_os/application` is a transition area with measured debt and a closure path, not the intended architecture.
- Problem statement: `src/power_web_os/application` still contains dozens of similarly named root-level Radar files. Some are thin compatibility shims, some are deferred behavior owners, and some tests still import old paths. That makes the project look architecturally unfinished and can mislead contributors about where new code belongs.
- Scope:
  - Generate and commit a full root namespace debt inventory for `live_radar_*`, `radar_search_*`, and `signal_monitoring_*`, with each file classified as `moved_shim`, `deferred_behavior`, `test_only_compatibility`, or `candidate_for_delete`.
  - Update `RADAR_BACKEND_ARCHITECTURE.md`, Developer Guide, and candidate/signal package READMEs with the inventory and closure policy.
  - Migrate behavior tests to package-owned imports where behavior has already moved, leaving old root imports only in explicit compatibility tests.
  - Add architecture tests that fail when new production code or new behavior tests import moved legacy paths.
  - Add or confirm follow-up roadmap slices for checkpoint migration, search expansion migration, signal monitoring package migration, shared budget decision, and final root namespace closure.
- Out of scope:
  - No broad behavior migration in this slice.
  - No checkpoint, search expansion, signal-monitoring algorithm, provider, scoring, dossier, API, DB, or UI behavior changes.
  - No deletion of compatibility shims before compatibility coverage and production imports are updated.
- Implementation notes:
  - Treat old root imports in tests as technical debt unless the test name and location are explicitly about compatibility.
  - Do not move a behavior-owning module by filename only; choose the package-owned service/contract first and keep old import compatibility only as a shim.
  - If a behavior test cannot migrate because the source of truth still lives in a root module, record that module in the inventory and link it to the owning migration slice.
  - This slice exists to make the architecture state honest before returning to product behavior work such as `0.7.6.3.6.6`.
- Tests:
  - `python -m pytest tests/test_backend_architecture_contract.py tests/test_radar_backend_package_contract.py -q`
  - Targeted tests touched by import migration, especially live ICP, search expansion, adaptive execution, signal monitoring contracts/source strategy/recorded tests.
  - `python -m power_web_os.roadmap check`
  - `git diff --check`
- Docs:
  - Update `docs/architecture/RADAR_BACKEND_ARCHITECTURE.md` with the full root namespace debt inventory and closure policy.
  - Update `docs/developer/DEVELOPER_GUIDE.md` with behavior-test import rules.
  - Update `src/power_web_os/application/radar/README.md` and relevant package READMEs if ownership wording changes.
  - Regenerate roadmap artifacts.
- Demo impact:
  - None intended. This is architecture and test-routing governance.
- Acceptance criteria:
  - The Roadmap and architecture docs list every root-level Radar-prefixed file and its migration status.
  - Behavior tests for already moved modules import package-owned paths; old imports remain only in compatibility tests.
  - Architecture tests prevent new behavior tests and production code from importing moved legacy paths.
  - Missing follow-up slices for signal monitoring migration and final root namespace closure exist in the tracker.
  - `0.7.6.3.6.6` can be resumed with an explicit understanding of remaining root namespace debt.
- Risks:
  - Over-tight guardrails can block legitimate compatibility tests. Mitigate with a small compatibility-test allowlist by test path/name.
  - Inventory can become stale. Mitigate by generating/checking it from the filesystem in architecture tests.
  - Migrating imports can accidentally alter behavior if old paths are not true shims. Mitigate by migrating only moved modules in this slice.

### Slice 0.7.6.4.15: Candidate discovery checkpoint package migration

- Status: Done
- Goal: Move checkpoint decision/action ownership out of root-level legacy modules into `radar/candidate_discovery/checkpoints` behind service/decision contracts.
- User value: Adaptive checkpoint behavior becomes easier to inspect and safer to change without editing root-level legacy files.
- Problem statement: Architecture docs still identify checkpoint modules such as `live_radar_checkpoint_actions.py`, `live_radar_checkpoint_execution.py`, and `live_radar_checkpoints.py` as deferred migration debt. Checkpoint behavior is central to bounded fallback semantics and should not remain a legacy hotspot indefinitely.
- Scope:
  - Define checkpoint package service/decision ownership.
  - Move or wrap checkpoint decision/action code behind package-owned classes.
  - Keep compatibility shims for old imports.
  - Add architecture tests that forbid new checkpoint behavior in root-level `live_radar_*` modules.
- Out of scope:
  - No change to checkpoint policy semantics.
  - No hidden broad fallback, unbounded retry, or signal-before-pre-signal checkpoint behavior.
  - No scoring or provider quality tuning.
- Implementation notes:
  - Run this before product corrective work resumes.
  - Preserve checkpoint policy semantics exactly; this is a package-ownership migration.
  - Use AS IS verification gates because checkpoint ordering is high-risk.
  - Keep old root imports only as thin compatibility shims or explicit compatibility assertions.
- Tests:
  - `python -m pytest tests/test_backend_architecture_contract.py tests/test_radar_backend_package_contract.py -q`
  - `python -m pytest tests/test_radar_adaptive_execution.py tests/test_live_icp_radar.py -q`
  - Checkpoint-related recorded/fake tests covering bounded fallback, retry limits, and no signal-before-pre-signal checkpoint behavior.
  - AS IS documentation contract if backend-role/package ownership docs change.
  - `python -m power_web_os.roadmap check`
  - `git diff --check`
- Docs:
  - Update Radar backend architecture migration table and checkpoint package README.
  - Update AS IS only if backend-role/package ownership wording changes.
- Demo impact:
  - None intended.
- Acceptance criteria:
  - Checkpoint behavior has a package-owned source of truth.
  - Old checkpoint import paths remain compatible or are explicitly retired.
  - Pipeline checkpoint semantics match the AS IS document.
- Risks:
  - Checkpoint moves can accidentally widen fallback. Mitigate with bounded-checkpoint tests and recorded fixtures.

### Slice 0.7.6.4.16: Candidate discovery search expansion package migration

- Status: Done
- Goal: Move search expansion execution and payload ownership into candidate-discovery package services without changing expansion scheduling behavior.
- User value: Search expansion becomes a package-owned execution capability with visible admission, payload, and diagnostics contracts.
- Problem statement: `live_radar_search_expansion_execution.py` and related payload modules remain documented Radar application hotspots. They should be migrated only after the options/composition cleanup and the next measured pipeline blocker work are not depending on root-level legacy shape.
- Scope:
  - Classify expansion execution, payload shaping, diagnostics, and scheduler admission responsibilities.
  - Move source-of-truth behavior into `radar/candidate_discovery/execution` or a narrower package if the code proves to be retrieval/expansion-owned.
  - Keep root-level compatibility shims where hidden imports still exist.
  - Add package/import/fan-out guardrails for expansion modules.
- Out of scope:
  - No new expansion strategy.
  - No benchmark quality claim.
  - No live-provider broad run as the first validation signal.
- Implementation notes:
  - Run after checkpoint ownership migration, before product corrective work resumes.
  - Do not combine migration with target-lane algorithm changes. If behavior must change, split that into a TO BE/AS IS pipeline slice.
  - Preserve expansion target coverage and budget metadata surfaces.
  - Root `radar_search_*` files should become package-owned modules or thin shims, not remain normal imports.
- Tests:
  - `tests/test_radar_search_expansion.py` and budget/adaptive/API regression.
  - Architecture/package compatibility tests.
  - Recorded fixtures for expansion payload and target coverage metadata.
- Docs:
  - Update Radar backend architecture doc, execution README/handbook, and AS IS backend-role ownership wording if paths change.
- Demo impact:
  - None intended.
- Acceptance criteria:
  - Search expansion behavior has a package-owned source of truth.
  - Root-level expansion files are thin compatibility shims or explicitly deferred.
  - Expansion metadata and budget surfaces remain compatible.
- Risks:
  - Mixing migration with scheduling changes can obscure benchmark regressions. Keep behavior-preserving migration separate.

### Slice 0.7.6.4.17: Radar shared budget contracts assessment and extraction

- Status: Done
- Goal: Decide and implement the minimal shared budget contract only if candidate discovery and signal monitoring both need the same budget semantics.
- User value: Budget behavior stays consistent where it is genuinely shared while avoiding a premature shared abstraction that hides pipeline-specific rules.
- Problem statement: Candidate discovery now has service-owned budget metadata merging, while signal monitoring has isolated budgets. Some budget records may belong in `radar/shared/budgets`, but moving them too early would couple pipelines that intentionally have different cadence and policy.
- Scope:
  - Compare candidate-discovery and signal-monitoring budget surfaces.
  - Extract only genuinely shared budget records/services to `radar/shared/budgets`.
  - Keep candidate-discovery-specific budget merge/projection behavior in candidate-discovery.
  - Add import-direction tests so shared budget code does not import pipeline packages.
- Out of scope:
  - No budget limit tuning.
  - No signal-monitoring behavior change.
  - No provider/model selection change.
- Implementation notes:
  - Run after search-expansion migration and before the remaining candidate-discovery root modules are moved.
  - This is now part of the mandatory cleanup corridor before product corrective work resumes.
  - Extract only truly shared budget contracts; keep pipeline-specific merge/projection behavior package-owned.
  - If assessment says no shared extraction is justified, record the decision and tighten import guardrails accordingly.
- Tests:
  - Shared package import tests.
  - Candidate-discovery and signal-monitoring budget isolation tests.
  - Backend architecture contract tests.
- Docs:
  - Update Radar backend architecture doc with the decision.
  - Add `radar/shared/budgets/README.md` only if shared code is introduced.
- Demo impact:
  - None intended.
- Acceptance criteria:
  - The decision is explicit: extract a minimal shared contract or keep budget behavior pipeline-owned.
  - Architecture tests enforce the chosen dependency direction.
  - Existing budget counters, reserve counters, exhaustion events, and source verification cache stats remain compatible.
- Risks:
  - Premature sharing can blur candidate-discovery vs signal-monitoring boundaries. Require concrete reuse before extraction.

### Slice 0.7.6.4.17.1: Candidate discovery retrieval and definition package migration

- Status: Done
- Goal: Move remaining root-level candidate-discovery definition and retrieval primitives into package-owned `radar/candidate_discovery/retrieval` modules before product work resumes.
- User value: Developers no longer have to start from root-level definition/retrieval files to understand how a live Radar definition becomes provider-neutral retrieval work.
- Problem statement: `live_radar_definition.py` and `live_radar_web_retrieval.py` still own real behavior in the flat application namespace even though planning/retrieval-plan modules have moved. That leaves the new package tree incomplete and keeps root imports alive in workflows, preflight, and demos.
- Scope:
  - Move live Radar definition-building behavior into `radar/candidate_discovery/retrieval/definition.py`.
  - Move provider-neutral web retrieval request/result records and recorded retrieval provider into `radar/candidate_discovery/retrieval/web_retrieval.py`.
  - Keep old root paths as thin compatibility shims only where hidden callers still need them.
  - Migrate production and behavior-test imports to package-owned paths.
  - Update root namespace debt inventory and architecture tests for the moved modules.
- Out of scope:
  - No retrieval algorithm change.
  - No provider SDK/HTTP integration change.
  - No scoring, checkpoint, expansion, dossier, API, DB, or UI behavior change.
  - No live-provider benchmark claim.
- Implementation notes:
  - Treat this as a behavior-preserving package migration.
  - Keep definition records and retrieval task cards provider-neutral.
  - Definition builders stay candidate-discovery-owned until another Radar pipeline proves a shared contract is needed.
- Tests:
  - Backend architecture/package compatibility tests.
  - Live ICP and preflight tests that exercise definition-to-payload and retrieval-plan wiring.
  - Import compatibility tests for old definition/retrieval paths.
  - `python -m power_web_os.roadmap check`
  - `git diff --check`
- Docs:
  - Update `RADAR_ROOT_NAMESPACE_DEBT.md` and `RADAR_BACKEND_ARCHITECTURE.md`.
  - Update retrieval/package README ownership guidance.
  - Update Developer Guide import examples if package-owned paths change.
- Demo impact:
  - None intended; demo commands should keep producing the same artifacts.
- Acceptance criteria:
  - `live_radar_definition.py` and `live_radar_web_retrieval.py` are thin shims or explicitly retired.
  - Production and behavior tests import definition/retrieval behavior from package-owned paths.
  - Existing preflight/live ICP behavior remains green.
  - Root namespace debt inventory points these files to completed migration status.
- Risks:
  - Definition helpers may later be useful to another pipeline. Mitigate by introducing a shared contract only when concrete reuse appears, not in this migration slice.

### Slice 0.7.6.4.17.2: Candidate universe and entity resolution package migration

- Status: Done
- Goal: Move candidate universe, retrieved-candidate extraction, entity resolution, candidate refs, upstream disambiguation, and cross-source disambiguation out of root-level modules into candidate-discovery package services.
- User value: The candidate universe becomes a visible package-owned concept rather than a cluster of root helper files, making future fallback and enrichment work safer.
- Problem statement: `live_radar_candidate_refs.py`, `live_radar_entity_resolution.py`, `live_radar_retrieved_candidates.py`, `live_radar_universe.py`, `live_radar_cross_disambiguation.py`, and `radar_upstream_disambiguation.py` still own core candidate-universe behavior in the flat namespace. Product work such as post-extraction fallback would otherwise keep extending that legacy cluster.
- Scope:
  - Create package-owned universe/entity-resolution services and value/helper modules under `radar/candidate_discovery/universe`.
  - Move retrieved-candidate extraction, candidate source-ref helpers, metadata/gap helpers, and candidate-universe projection behind package-owned APIs.
  - Move upstream registry ambiguity retention and cross-source disambiguation into universe-owned modules.
  - Keep old root paths as thin compatibility shims.
  - Migrate production and behavior-test imports to package-owned paths.
  - Add architecture tests that prevent new universe/entity-resolution behavior in root-level modules.
- Out of scope:
  - No new fallback materialization behavior.
  - No registry enrichment algorithm change.
  - No scoring, checkpoint, search expansion, provider, API, DB, or UI behavior change.
- Implementation notes:
  - This slice intentionally precedes `0.7.6.3.6.6` so fallback materialization can build on package-owned universe services.
  - Preserve current candidate ids, source refs, provider metadata merge semantics, review-needed entity projection, and disambiguation events.
  - Split service boundaries by role instead of replacing one root cluster with one large package module.
- Tests:
  - Existing live ICP, adaptive execution, search expansion, and API/job smoke tests that consume candidate universe metadata.
  - Focused tests for retrieved-candidate extraction, source refs, provider metadata merge, and entity-resolution outcomes.
  - Backend architecture/package compatibility tests.
  - `git diff --check`
- Docs:
  - Update universe README, `RADAR_ROOT_NAMESPACE_DEBT.md`, and `RADAR_BACKEND_ARCHITECTURE.md`.
  - Update AS IS only for backend-role/package ownership wording if needed.
- Demo impact:
  - None intended; live/demo candidate projections should remain shape-compatible.
- Acceptance criteria:
  - Root universe/entity-resolution/disambiguation files are thin shims or explicitly retired.
  - Candidate universe behavior has package-owned source-of-truth modules/classes.
  - Existing artifact/dossier/API surfaces remain compatible.
  - Architecture tests fail if new universe behavior is added to root-level Radar files.
- Risks:
  - This touches metadata that many projections consume. Mitigate with artifact compatibility and API smoke tests, not only unit tests.

### Slice 0.7.6.4.17.3: Candidate extraction and diagnostics package migration

- Status: Done
- Goal: Move extraction contract, extraction diagnostics, normalization, collection utilities, pipeline support, and source-risk helpers into candidate-discovery extraction/diagnostics/source packages.
- User value: Provider output repair, evidence normalization, diagnostics, and source-risk handling become discoverable package-owned responsibilities before product fallback work changes them.
- Problem statement: `live_radar_extraction_contract.py`, `live_radar_extraction_diagnostics.py`, `live_radar_normalization.py`, `live_radar_pipeline_support.py`, `live_radar_collection_utils.py`, and `live_radar_source_risk.py` still form a root-level diagnostics/extraction cluster. These are exactly the files likely to be touched by post-extraction fallback work, so they should move first.
- Scope:
  - Move extraction schema validation/repair and diagnostic-state helpers to `radar/candidate_discovery/extraction`.
  - Move product-safe normalization, collection helpers, trace/pipeline support, and source-risk projection to `radar/candidate_discovery/diagnostics` or `sources` as appropriate.
  - Keep root import paths as thin compatibility shims while hidden callers are supported.
  - Migrate production and behavior-test imports to package-owned paths.
  - Add guardrails against new root-level extraction/diagnostics behavior.
- Out of scope:
  - No new fallback behavior.
  - No provider prompt/schema tuning.
  - No scoring, checkpoint, expansion, signal-monitoring, API, DB, or UI behavior change.
  - No live quality claim.
- Implementation notes:
  - Preserve sparse-provider-output handling, evidence-linking diagnostics, candidate normalization shape, source lifecycle metadata, and technical trace safety.
  - Keep extraction repair policy separate from artifact/dossier projection.
  - Avoid creating another large diagnostics module; split by extraction contract, normalization, source risk, and event/trace projection.
- Tests:
  - Extraction contract validation/repair tests.
  - Live ICP and backend API regression that verify artifact/dossier shape.
  - Radar pipeline documentation contract if AS IS backend-role wording changes.
  - Backend architecture/package compatibility tests.
  - `git diff --check`
- Docs:
  - Update extraction/diagnostics/source README guidance.
  - Update `RADAR_ROOT_NAMESPACE_DEBT.md` and `RADAR_BACKEND_ARCHITECTURE.md`.
  - Update AS IS only for backend-role/package ownership wording if needed.
- Demo impact:
  - None intended; visible candidate evidence/qualification/signal projections remain compatible.
- Acceptance criteria:
  - Root extraction/diagnostics/source-risk files are thin shims or explicitly retired.
  - Package-owned extraction and diagnostics modules own the behavior.
  - Existing dossier/API/technical trace surfaces remain compatible.
  - Architecture tests prevent new root-level extraction/diagnostics behavior.
- Risks:
  - Normalization and diagnostics touch many output surfaces. Mitigate with API, persisted/job, live ICP, and artifact compatibility tests.

### Slice 0.7.6.4.18: Signal monitoring package migration

- Status: Done
- Goal: Move root-level signal monitoring contracts, executor, and source strategy into `radar/signal_monitoring` package-owned modules before serious signal-monitoring development continues.
- User value: Signal monitoring becomes a first-class Radar pipeline with clear package ownership instead of a root-level application add-on.
- Problem statement: `signal_monitoring_contracts.py`, `signal_monitoring_executor.py`, and `signal_monitoring_source_strategy.py` still own real behavior in the root application namespace while `radar/signal_monitoring` is mostly a skeleton. That contradicts the pipeline split architecture and will confuse future monitoring work.
- Scope:
  - Move signal-monitoring contracts, executor, and source strategy behind package-owned modules under `src/power_web_os/application/radar/signal_monitoring`.
  - Keep old root import paths as thin compatibility shims only where needed.
  - Migrate signal-monitoring behavior tests to package-owned imports, leaving root-path tests only for compatibility.
  - Add package README ownership guidance and import-direction guardrails.
- Out of scope:
  - No new signal-monitoring algorithm.
  - No provider/live search implementation.
  - No scheduling UI or persistence change.
  - No candidate-discovery behavior change.
- Implementation notes:
  - Run after candidate-discovery root debt is migrated or explicitly shimmed.
  - Preserve current recorded/no-network signal-monitoring behavior and product-safe report shape.
  - Keep source strategy separate from candidate discovery internals except through shared source-card/known-candidate records.
  - Run signal-monitoring recorded and contract tests before any live-provider work.
- Tests:
  - `python -m pytest tests/test_signal_monitoring_contracts.py tests/test_signal_monitoring_source_strategy.py tests/test_radar_signal_monitoring_recorded.py -q`
  - `python -m pytest tests/test_radar_model_profiles.py tests/test_radar_runtime_config.py -q`
  - Backend architecture/package import tests.
  - `git diff --check`
- Docs:
  - Update `src/power_web_os/application/radar/signal_monitoring/README.md`.
  - Update Radar backend architecture migration table.
  - Update Developer Guide import examples if needed.
- Demo impact:
  - Recorded signal-monitoring demo output should remain identical except for technical trace/module ownership if exposed.
- Acceptance criteria:
  - Root `signal_monitoring_*` files are thin shims or removed.
  - Production and behavior tests import signal-monitoring behavior from `radar/signal_monitoring`.
  - Recorded signal-monitoring report and runtime config tests remain green.
  - Architecture tests prevent new root-level signal-monitoring behavior modules.
- Risks:
  - Signal monitoring can accidentally start importing candidate-discovery internals. Mitigate with import-direction tests and shared contracts only.

### Slice 0.7.6.4.18.1: Candidate discovery and signal monitoring runtime split

- Status: Done
- Goal: Make candidate discovery and signal monitoring separate runtime products: candidate discovery stops owning inline signal search as the normal execution path, and signal monitoring owns signal execution semantics, budgets, and evaluation.
- User value: Radar users and developers can run candidate discovery to build/review a candidate universe, then run signal monitoring separately on accepted or review-allowed candidates without confusing discovery budget exhaustion with signal quality.
- Problem statement: The architecture says Radar is a family of pipelines, but candidate-discovery execution still plans and can run `signal_search` tasks inline. That legacy path makes live smoke diagnostics look like one monolithic Radar run and can project unsearched signals as if candidate discovery had evaluated them.
- Scope:
  - Introduce an explicit candidate-discovery execution mode that does not execute signal monitoring as the normal product path.
  - Keep any inline `signal_search` behavior only as a documented compatibility/test path while migration completes.
  - Move signal status projection for candidate discovery to honest handoff states such as `not_searched_pending_signal_monitoring` or `not_searched_policy_limited`, never `not_observed` unless a signal task actually ran.
  - Add guardrails that candidate-discovery budgets do not own signal-monitoring budgets.
  - Update AS IS docs to describe candidate discovery output as a handoff snapshot for signal monitoring.
- Out of scope:
  - No live signal-monitoring provider implementation.
  - No scheduler or recurring job yet.
  - No candidate-discovery quality tuning.
  - No deletion of compatibility imports until the closure slice.
- Implementation notes:
  - Run after `0.7.6.4.18` package migration so signal-monitoring code has a package-owned home.
  - Preserve existing candidate-discovery candidate/source/checkpoint behavior.
  - Treat the live-smoke finding where S2/S3 became `searched/not_observed` after pre-signal stop as a regression test for this slice.
  - Candidate discovery may still include intent signal definitions in the Radar definition, but it should not evaluate them as monitoring results.
- Tests:
  - Candidate-discovery regression proving pre-signal stop marks all unexecuted signals as `not_searched_*`.
  - Architecture test proving candidate-discovery runtime does not import signal-monitoring implementation except through explicit handoff contracts.
  - Existing live ICP/adaptive/API tests for candidate-discovery dossier shape.
  - Signal-monitoring recorded tests to prove the separate pipeline still runs.
- Docs:
  - Update `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md` for candidate-discovery handoff semantics.
  - Update `docs/radar/pipelines/README.md` with the product/runtime split.
  - Update Developer Guide runbook: candidate discovery run vs signal monitoring run.
- Demo impact:
  - Demo UI/copy should stop implying the candidate-discovery live run has completed recurring signal monitoring when no signal-monitoring run was launched.
- Acceptance criteria:
  - Candidate discovery can complete with candidate/source/checkpoint output without executing signal monitoring.
  - Inline signal-search compatibility, if retained, is explicitly marked non-normal and tested separately.
  - Unexecuted signals are never projected as `not_observed`.
  - Candidate-discovery and signal-monitoring budget settings are visibly separate in runtime config/reporting.
- Risks:
  - Existing tests expect inline signal search in candidate discovery. Migrate those tests either to compatibility assertions or signal-monitoring tests rather than preserving the mixed product model.

### Slice 0.7.6.4.18.1.1: Candidate discovery recall-first upstream semantics and benchmark target protection

- Status: Done
- Goal: Make candidate discovery actually recall-first after the signal-monitoring runtime split: retain source-backed upstream leads aggressively, stop downgrading all discovered entities into Monitor/weak review-only output, and protect explicit benchmark targets before continuing signal-monitoring live runtime work.
- User value: A user can trust candidate discovery as a broad upstream finder: it should keep extra plausible SIBUR/industrial targets for review instead of silently losing them, and benchmark reports should explain real misses by algorithmic decision rather than by generic budget symptoms.
- Problem statement: The 2026-07-06 benchmark_live SIBUR run proved that the code does not yet implement the intended false-positive-biased upstream behavior. It found 86 candidates, but all 86 were projected as Monitor; qualification checks produced 130 weak, 42 unknown, and 0 confirmed results; evaluation showed product_candidate_count=0; and three baseline targets were still false negatives. The causes are algorithmic: candidate scoring still depends on signal evidence after signal monitoring was split out; retrieved-source and registry observations are hardcoded as weak/requires-review; official SIBUR evidence is not promoted into upstream confirmation; benchmark_live lacks the protected target guarantees present in benchmark_smoke; and baseline entities present in source diagnostics can fail to project into observed upstream entities.
- Scope:
  - Introduce a package-owned candidate-discovery upstream admission policy that separates 'retain as upstream lead' from 'accept as product account'.
  - Replace or quarantine the current Monitor/Tier candidate-discovery scoring path so discovery outcomes no longer require signal evidence.
  - Promote source-backed official-domain evidence for configured high-trust sources such as SIBUR official pages into strong upstream relation/coverage evidence when the entity name or alias and industrial/asset context match.
  - Stop treating every retrieved-source legal entity and every structured registry observation as weak by construction; preserve recall-first leads with explicit review state instead of downgrading them into low-quality output.
  - Fix projection so a benchmark alias/canonical entity found in source diagnostics becomes an observed upstream entity or receives an explicit rejection reason.
  - Add protected benchmark target handling for benchmark_live: explicit baseline hints must become protected targets, retain their benchmark flags through dedupe, receive guaranteed selection/admission before optional duplicate/alias work, and appear in diagnostics if skipped.
  - Add RCA-grade report fields for selected/executed/projected status per explicit benchmark target.
- Out of scope:
  - No signal-monitoring live runtime/API implementation; that remains 0.7.6.4.18.2 after this correction.
  - No broad quality claim from one live run.
  - No production hardcode for specific SIBUR names outside benchmark fixtures/context; use source policy, official-domain trust, aliases, entity type, and benchmark hints.
  - No change to provider credentials, Docker ports, persistence schema, frontend UI, or recurring scheduler unless a test exposes a small local defect.
  - No lowering of downstream product precision: broad retention is upstream-only and must remain separated from accepted account projection.
- Implementation notes:
  - The immediate RCA run was radar-run-b75c73ee-437b-4040-b609-ec9b7096be71 on benchmark-sibur-holding-contour with benchmark_live.
  - Current code path to correct: candidate normalization computes Monitor from confirmed qualification plus observed signals, which is stale after the handoff split.
  - Current code path to correct: retrieved-source candidate observations are emitted with status=weak, confidence=low, and requires-review rationale by default.
  - Current code path to correct: registry observations are emitted as weak/company_registry_fact_requires_review even when structured identity evidence is present.
  - Current code path to correct: benchmark_live profile does not carry benchmark_target_probe_minimums, coverage_completion_target_limit, or protected recall-expansion reserve settings, so selection had selected_guaranteed_count=0 and selected_optional_count=6.
  - Treat false-positive-biased upstream as a domain/application contract, not a prompt-only instruction. The prompt may ask for broad recall, but deterministic admission/projection code must enforce retention.
- Tests:
  - Add unit tests for upstream admission: official SIBUR source plus matching legal entity/alias is retained as a strong upstream lead, not downgraded to generic weak Monitor output.
  - Add normalization tests proving candidate-discovery outcomes do not require signal observations after signal_execution_mode=handoff.
  - Add retrieved-source and registry observation tests proving source-backed entities are retained with review/acceptance separation rather than erased or classified as low-quality by default.
  - Add projection regression tests for Nizhnekamskneftekhim and Kazanorgsintez-style cases: if text appears in source diagnostics under benchmark aliases, it must become an observed upstream entity or have explicit rejection diagnostics.
  - Add search-expansion tests proving benchmark_live inherits target guarantees and that benchmark flags survive target dedupe.
  - Add selector/scheduler tests proving explicit benchmark targets outrank optional duplicates once required lane minimums are considered.
  - Run: python -m pytest tests/test_radar_search_expansion.py tests/test_radar_benchmark.py tests/test_radar_evaluation.py -q
  - Run: python -m pytest tests/test_live_icp_radar.py tests/test_radar_adaptive_execution.py tests/test_backend_api.py tests/test_persisted_live_radar.py tests/test_radar_jobs.py -q
  - Run a bounded Docker/API benchmark smoke or live probe only after fast tests are green; evaluate the latest run and report recall, source linkage, qualification fit, rejected/gap entities, and checkpoint reasons.
- Docs:
  - Update RADAR_SEARCH_PIPELINE_AS_IS if candidate-discovery outcome semantics change.
  - Update RADAR_BACKEND_ARCHITECTURE and CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE with the upstream admission policy owner.
  - Update Developer Guide benchmark/runbook notes: benchmark_live is not just larger budget; it must carry protected benchmark target guarantees.
  - Update demo/benchmark docs if report interpretation or run commands change.
- Demo impact:
  - No frontend redesign. Demo/report output should become clearer: candidate discovery should show retained upstream leads, review-needed leads, rejected/noise entities, protected benchmark targets, and explicit miss reasons instead of a flat list of Monitor rows.
- Acceptance criteria:
  - A recorded/fake fixture proves candidate discovery can retain source-backed false-positive-prone upstream leads without requiring signal evidence.
  - Official high-trust SIBUR evidence can promote upstream relation/coverage confidence where deterministic evidence rules match.
  - benchmark_live context includes protected target guarantees equivalent to the intended benchmark diagnostic path.
  - Nizhnekamskneftekhim/Kazanorgsintez-style present-not-projected false negatives are covered by tests.
  - The next SIBUR benchmark evaluation no longer reports product_candidate_count=0 merely because all source-backed leads were normalized into Monitor.
  - Any remaining false negatives have path-level reasons: not generated, no executable query, not selected, not admitted, not executed, source not found, present not projected, or explicitly rejected.
- Risks:
  - Aggressive upstream retention can increase false positives. This is acceptable upstream, but must not leak into downstream accepted accounts without review/acceptance gates.
  - Promoting official-source evidence too broadly can mask ambiguous legal-entity vs branch/site cases. Mitigate with entity-type-aware review states and source-linked evidence requirements.
  - Live provider output can drift. Acceptance should prioritize deterministic contract tests and diagnostic specificity, not a one-run quality claim.

### Slice 0.7.6.4.18.1.2: Live extraction robustness and post-extraction salvage

- Status: Done
- Goal: Make live candidate-discovery extraction robust enough to reach recall expansion and benchmark target protection: when live provider output violates the strict extraction schema but product-safe sources already contain source-backed entities, salvage review-needed upstream leads instead of ending the run as an opaque schema_failed stop.
- User value: A user can run a bounded live Radar smoke and get a useful candidate/target funnel diagnosis instead of paying for repeated OpenRouter attempts that stop before candidates, expansion, and benchmark baseline protection can be evaluated.
- Problem statement: After 0.7.6.4.18.1.1 the deterministic recall-first admission and benchmark target protection tests are green, but Docker/API benchmark smoke exposed an earlier live-provider failure: the run stopped with `Extraction repair limit reached before extraction recovered: schema_failed` before normal expansion/target-protection checks. Existing retry, useful-result retry, and backup-model logic can retry or ask another model for valid JSON, but they do not yet materialize candidates from already available product-safe source diagnostics when strict extraction shape remains invalid. This slice merges and supersedes the older backlog slice 0.7.6.3.6.6 so there is one owner for post-extraction salvage work.
- Scope:
  - Add recorded/no-secret fixtures for the live extraction schema-failure class seen in the Docker/API smoke.
  - Classify extraction failures into actionable states: no useful sources, schema invalid with usable source diagnostics, unlinked candidates/source refs, backup model schema invalid, and recovery budget exhausted.
  - Add package-owned post-extraction salvage under candidate discovery: from product-safe retrieved/analyzed source title/snippet/url/annotations and source lifecycle diagnostics, materialize review-needed upstream leads when names/aliases are source-backed.
  - Reuse the recall-first upstream admission policy for salvaged candidates; do not bypass product acceptance gates.
  - Re-run checkpoint review after salvage so a run with recovered source-backed upstream leads can continue to expansion and benchmark target funnel instead of stopping only because the original JSON was malformed.
  - Preserve explicit extraction repair/retry diagnostics, including which path recovered the run or why salvage could not recover it.
  - Run a bounded Docker/API benchmark smoke after fast tests are green and require it to reach expansion/target-funnel diagnostics before any longer benchmark_live run.
- Out of scope:
  - No signal-monitoring live runtime/API implementation; 0.7.6.4.18.2 resumes only after this slice is validated.
  - No quality claim from a single live run.
  - No broad prompt redesign or provider/model tuning beyond minimal targeted repair prompts if tests prove they are needed.
  - No hardcoded SIBUR production logic outside benchmark fixtures/hints.
  - No lowering of downstream product acceptance precision; salvaged entities are upstream review-needed unless deterministic evidence justifies stronger upstream status.
  - No unbounded retries or hidden broad fallback.
- Implementation notes:
  - Treat old 0.7.6.3.6.6 as merged into this slice: do not implement it separately.
  - The correction belongs after package ownership cleanup because candidate universe, extraction, diagnostics, and admission now have package-owned homes.
  - Salvage must use product-safe diagnostics only: source titles, snippets, URLs, annotations, lifecycle metadata, and candidate-universe source refs. Do not scan prompts, hidden provider reasoning, or raw private payload text.
  - Recovery should be explicit: if salvage creates candidates, metadata should say `post_extraction_salvage_recovered`; if not, metadata should say whether the miss was no usable source text, no source ref, no matching entity text, or explicit rejection.
  - Existing retry and backup-model attempts remain useful first-line recovery, but this slice adds the missing deterministic fallback after those bounded attempts fail.
  - Keep the module split small enough to satisfy backend architecture hotspot tests.
- Tests:
  - Unit tests for failure classification: schema invalid with no useful sources, schema invalid with usable source diagnostics, unlinked source refs, backup schema invalid, and retry budget exhausted.
  - Recorded fixture test proving malformed extraction output plus source-backed company text materializes review-needed upstream leads.
  - Checkpoint recovery test proving salvage can clear terminal schema_failed stop and continue to expansion/target-funnel diagnostics.
  - Regression tests proving no hidden broad fallback: no source text/ref means no product candidate and an explicit unrecovered reason.
  - Benchmark smoke gate: `python -m power_web_os.demo run-radar-benchmark --api-url http://127.0.0.1:8001 --profile benchmark_smoke --radar-id benchmark-sibur-holding-contour` followed by evaluation; acceptance is reaching expansion/target funnel, not a quality claim.
  - Regression commands: architecture/package tests, live ICP/adaptive/search-expansion/external-budget tests, API/preflight/persisted/jobs tests, roadmap check, and git diff check.
- Docs:
  - Update RADAR_SEARCH_PIPELINE_AS_IS if recovery/salvage states become implemented behavior.
  - Update candidate-discovery execution architecture with post-extraction salvage ownership and checkpoint interaction.
  - Update Developer Guide/demo benchmark runbook so live benchmark_live is not run until smoke reaches expansion/target-funnel diagnostics.
  - Update roadmap artifacts and explicitly note that 0.7.6.3.6.6 is superseded by this slice.
- Demo impact: Demo benchmark smoke should become more diagnostically useful: instead of stopping before candidate/target analysis on salvageable schema drift, it should show recovered upstream leads or explicit unrecovered source-level reasons.
- Acceptance criteria:
  - The old 0.7.6.3.6.6 scope is no longer an independent backlog item; it is merged into 0.7.6.4.18.1.2.
  - A recorded malformed live extraction fixture recovers source-backed upstream leads without requiring valid provider candidate JSON.
  - Checkpoint recovery distinguishes unrecoverable schema failure from salvage-recovered source-backed candidates.
  - Bounded retry/backup behavior remains bounded and visible; salvage is deterministic and diagnostic, not a hidden unlimited retry.
  - Docker/API benchmark_smoke reaches expansion/benchmark target-funnel diagnostics after fast tests are green.
  - benchmark_live is allowed only after smoke reaches the funnel; it remains a bounded diagnostic run without a quality claim.
  - Signal monitoring live runtime remains deferred until this candidate-discovery live extraction blocker is resolved.
- Risks:
  - Salvage can over-retain false positives. Mitigate by keeping salvaged entities as upstream review-needed unless official/registry evidence supports stronger upstream confidence.
  - Over-broad text scanning can leak unsafe provider text into decisions. Mitigate by limiting salvage inputs to product-safe source diagnostics.
  - Fixing recovery could accidentally mask real provider contract bugs. Mitigate by preserving extraction_validation_issues and explicit recovery path metadata.

### Slice 0.7.6.4.18.1.3: Candidate discovery outcome reconciliation and public result repair

- Status: Done
- Goal: Make candidate discovery reconcile raw upstream leads, public candidate rows, benchmark target matches, product acceptance, and rejected/not-promoted entities without silent drops, default Monitor output, or unexplained product_candidate_count=0.
- User value: A user can trust the Radar result surface: broad upstream discovery is visible, strict product acceptance remains explainable, and the report shows exactly why each found entity was retained, promoted, rejected, or left for review.
- Problem statement: The latest SIBUR benchmark_smoke run reached the benchmark target funnel, but the result still contradicted completed recall-first slices: the dossier retained broad upstream evidence and benchmark evaluation matched 10 of 12 targets, while the public candidates endpoint showed only 3 Monitor rows and product_candidate_count stayed 0 without a complete acceptance ledger. This means the pipeline can find evidence but still loses or flattens meaning between candidate universe, public rows, benchmark reporting, and product acceptance.
- Scope:
  - Add a candidate-discovery reconciliation report that links benchmark targets, source/evidence observations, retained upstream leads, public candidate rows, product candidates, rejected/not-promoted entities, explicit gaps, and unexplained drops.
  - Repair public candidate and dossier projection so source-backed handoff-mode discoveries expose upstream outcome, product acceptance status, confidence, reason, and public projection reason.
  - Stop using Monitor as the default visible outcome for source-backed candidate discovery after signal-monitoring handoff.
  - Make product_candidate_count=0 acceptable only with a per-entity product acceptance ledger.
  - Turn protected benchmark present_not_projected into a failing state by projecting source-backed aliases into observed upstream entities or recording explicit rejection reasons.
- Out of scope:
  - No signal-monitoring live runtime or API implementation.
  - No broad provider/model tuning or benchmark quality claim.
  - No lowering of downstream product precision; this slice explains and surfaces strict rejection instead of silently promoting weak leads.
  - No SIBUR-specific production hardcode outside benchmark fixtures/hints.
  - No attempt to make benchmark_smoke shorter; duration is not this slice's DoD.
- Implementation notes:
  - Treat candidate_universe as the broad upstream truth surface, public candidates as a capped/display surface, and product candidates as strict downstream acceptance.
  - Add additive API/dossier fields only; preserve compatibility for existing consumers.
  - Reuse existing upstream admission and benchmark funnel concepts rather than inventing a second scoring model.
  - Reconciliation must be machine-checkable and included in final artifact/dossier metadata.
  - The run cannot be considered successful if any source-backed entity disappears between upstream universe and public/product surfaces without an explicit reason.
- Tests:
  - Add red tests for no silent drops: retained upstream leads that do not appear as public candidates must have public_result_status and reason.
  - Add red tests that source-backed handoff-mode candidates cannot all be default Monitor.
  - Add red tests that product_candidate_count=0 requires a non-empty product_acceptance_ledger covering every strong/review upstream lead.
  - Add red tests that protected benchmark targets present in source diagnostics cannot remain present_not_projected.
  - Add API/dossier regression tests for the new reconciliation section and additive candidate fields.
  - Run focused candidate-discovery/evaluation/API tests, architecture/package tests, docs/static checks, and final Docker/API benchmark_smoke after docker compose rebuild.
- Docs:
  - Update RADAR_SEARCH_PIPELINE_AS_IS and generated PDF with outcome reconciliation, no-silent-drop invariant, and product acceptance ledger.
  - Update RADAR_BACKEND_ARCHITECTURE and candidate-discovery execution architecture with the reconciliation owner.
  - Update Developer Guide and demo benchmark runbook with the new post-slice DoD gate and interpretation of upstream/public/product counts.
  - Export/render/check roadmap artifacts.
- Demo impact: Demo benchmark reports become explainable: users see why broad upstream entities are retained, why some are hidden from the public top rows, and why strict product acceptance did or did not happen.
- Acceptance criteria:
  - For SIBUR Docker/API benchmark_smoke after docker compose up -d --build: terminal run, benchmark target funnel present, unexplained_drop_count=0, present_not_projected_count=0, and source-backed public candidates are not all Monitor.
  - Every retained upstream lead has one of confirmed_upstream_lead, review_needed_upstream_lead, retained_upstream_lead, rejected_noise, or not_promoted_to_public_candidate with reason.
  - If public candidates are fewer than candidate_universe entries, every hidden upstream lead has public_result_status and public_projection_reason.
  - If product_candidate_count=0, product_acceptance_ledger is non-empty and covers every strong/review upstream lead.
  - Nizhnekamskneftekhim/Kazanorgsintez-style protected benchmark fixtures no longer end as present_not_projected.
  - Handoff signal statuses remain not-searched/pending/limited without false not_observed.
  - Slice is not Done until a rebuilt Docker/API smoke run satisfies this DoD; passing unit tests alone is insufficient.
- Risks:
  - The reconciliation layer can expose many review/noise entities. Mitigate by separating upstream retention from product acceptance and keeping public top rows capped.
  - Product acceptance may remain strict and produce zero product candidates in some runs. Mitigate by requiring a complete acceptance ledger rather than weakening acceptance.
  - Live provider drift can change exact recall counts. Mitigate by gating on invariants such as no silent drops and no present_not_projected, not a single quality score.

### Slice 0.7.6.4.18.1.4: Candidate discovery public candidate surface and acceptance promotion tuning

- Status: Done
- Goal: Make the user-facing candidate surface reflect all source-backed relevant legal targets found by candidate discovery: accepted product candidates and review-needed visible candidates must be visible separately, with strict product acceptance preserved and Docker/API benchmark-smoke DoD mandatory before moving to signal monitoring runtime.
- User value: A user sees the real result of candidate discovery instead of a misleading short list: found legal targets are visible as accepted or review-needed candidates, while strict product acceptance remains explainable and not silently widened.
- Problem statement: After 0.7.6.4.18.1.3 the pipeline no longer silently drops upstream leads, but the product surface is still too narrow. The SIBUR benchmark smoke found 8 of 9 legal baseline targets in candidate_universe, while only 3 appeared as public/product candidate rows. This is better than the previous zero-product contradiction, but still product-poor: five source-backed legal targets are retained diagnostically instead of being visible to the user as review-needed candidate rows. The remaining false negative, ООО «Полиом», is generated but not selected before smoke budget/cap exhaustion. The next correction must tune public candidate surface and acceptance promotion, not signal monitoring.
- Scope:
  - Introduce or refine a user-facing candidate surface contract that separates `accepted_product_candidate`, `review_needed_candidate`, `universe_only_diagnostic`, and `not_promoted` states.
  - Promote source-backed legal entities from candidate_universe into user-visible review-needed candidate rows when they match protected benchmark/legal targets or have sufficient source/registry identity, even if they are not strict product candidates yet.
  - Keep strict product acceptance separate: accepted product candidates require deterministic qualification/evidence; review-needed candidates are visible but not counted as precision-positive product acceptance.
  - Add per-candidate promotion ledger fields explaining why each legal target is accepted, visible-for-review, universe-only, not selected, or not promoted.
  - Tune benchmark protected target selection so `Полиом` is either selected/executed/projected in benchmark_smoke or receives a more specific bounded reason than generic silent omission.
  - Update evaluation so it reports `visible_candidate_count`, `accepted_product_candidate_count`, `review_needed_candidate_count`, and `legal_baseline_visible_count` separately from strict precision.
  - Update API/dossier/candidates endpoint so the user-facing candidate list includes accepted and review-needed legal candidates with clear statuses.
- Out of scope:
  - No signal-monitoring live runtime/API implementation; 0.7.6.4.18.2 remains blocked until this DoD passes.
  - No broad live quality claim from one benchmark run.
  - No weakening of strict product precision: review-needed visible candidates must not be counted as accepted product candidates.
  - No SIBUR-specific production hardcode outside benchmark fixtures/hints.
  - No unbounded budget increase or hidden broad fallback; selection/budget tuning must remain bounded and explainable.
  - No frontend redesign unless API contract changes require a minimal fixture/docs update.
- Implementation notes:
  - Treat `candidate_universe` as the broad upstream truth, `user_visible_candidates` as the product-facing candidate surface, and accepted product candidates as a strict subset.
  - Public candidate rows should no longer mean only strict product acceptance; they should carry a `candidate_surface_status` or equivalent field that distinguishes accepted vs review-needed.
  - Existing `product_acceptance_status` must remain strict. Additive fields are preferred over breaking current consumers.
  - Benchmark evaluation should stop using `product_candidate_count` as the only user-facing success signal. It must show how many legal baseline targets are visible to the user, how many are accepted, and how many remain review-needed.
  - `Полиом` is the concrete regression probe for protected-target selection: generated-but-not-selected is now a known bounded selection defect.
  - Keep `unexplained_drop_count=0` and `present_not_projected_count=0` as non-negotiable inherited gates from 0.7.6.4.18.1.3.
- Tests:
  - Red test: when candidate_universe contains source-backed legal baseline matches that are not strict product candidates, the candidates API/dossier exposes them as review-needed visible candidates, not only diagnostic universe rows.
  - Red test: accepted product candidates and review-needed visible candidates are counted separately; review-needed candidates do not inflate precision.
  - Red test: SIBUR-style fixture with 8 legal baseline matches produces legal_baseline_visible_count >= 8 and accepted_product_candidate_count >= 3.
  - Red test: `Полиом` protected target cannot remain only `generated=true, selected=false` without a bounded, specific selection/cap reason; target selection must either execute it or report the exact cap/reserve that blocked it.
  - Red test: public surface cannot hide source-backed legal targets behind generic `universe_only` when entity type is legal_entity and source/registry identity is present.
  - Regression tests: no false `not_observed`, signal handoff remains pending/not-searched, product_acceptance_ledger remains complete, and no `present_not_projected` regressions.
  - Required fast gates: `python -m pytest tests/test_radar_evaluation.py tests/test_backend_api.py tests/test_live_icp_radar.py -q`; `python -m pytest tests/test_radar_search_expansion.py tests/test_radar_benchmark.py tests/test_radar_adaptive_execution.py -q`; architecture/package/docs/static checks.
  - Required final gate after fast tests: rebuild Docker, run SIBUR `benchmark_smoke`, evaluate latest run, and verify the DoD numbers below before marking Done.
- Docs:
  - Create TO BE doc/PDF for 0.7.6.4.18.1.4 before implementation.
  - Update RADAR_SEARCH_PIPELINE_AS_IS and generated PDF after implementation with the visible candidate surface contract.
  - Update RADAR_BACKEND_ARCHITECTURE and candidate-discovery execution architecture with the public-surface/promotion owner.
  - Update Developer Guide and demo benchmark runbook: success is accepted + review-needed visibility, not only strict product_candidate_count.
  - Export/render/check roadmap artifacts.
- Demo impact: Benchmark/demo output should become understandable to a user: instead of seeing only 3 accepted rows while 5 relevant legal targets are buried in diagnostics, the candidate surface should show accepted and review-needed legal candidates with reasons and source refs.
- Acceptance criteria:
  - Slice is not Done until a rebuilt Docker/API SIBUR `benchmark_smoke` run and evaluation satisfy this DoD; passing unit tests alone is insufficient.
  - `legal_baseline_visible_count >= 8` for the 9 legal baseline targets, where visible means accepted product candidate or review-needed user-visible legal candidate.
  - `accepted_product_candidate_count >= 3` and remains strict; review-needed candidates must not be counted as accepted product candidates.
  - `review_needed_candidate_count >= 5` or, if fewer, every missing legal target has a specific target-funnel reason and ledger explanation.
  - `product_candidate_count` / accepted product count is no longer the only public success signal; evaluation and dossier expose accepted vs review-needed counts separately.
  - `unexplained_drop_count == 0`.
  - `present_not_projected_count == 0`.
  - Protected benchmark targets such as ?????????????????? and ??????????????? remain projected/visible; they cannot regress to present_not_projected.
  - `Полиом` is either projected/visible or has a specific bounded reason such as `selection_cap_exhausted_for_protected_legal_target`, not a vague disappearance.
  - Handoff signal statuses remain not-searched/pending/limited; no candidate receives `not_observed` unless signal monitoring or explicit inline compatibility actually searched signals.
  - The final answer for implementation must include the benchmark run id and the DoD metric table.
- Risks:
  - Showing review-needed legal candidates can look like false positives if UI/copy treats them as accepted accounts. Mitigate with explicit surface status and strict product acceptance count.
  - Promoting more legal entities to visible review can increase list length. Mitigate with clear ordering: accepted first, protected benchmark/legal review-needed next, diagnostics after.
  - Fixing `??????` by simply raising budget could hide selection defects. Mitigate by requiring specific selection/reserve diagnostics and bounded tuning.
  - Live provider drift can change exact source names. Mitigate by gating on invariant counts and path reasons, not one brittle text snippet.

### Slice 0.7.6.4.18.1.4.1: Radar UI candidate surface wiring and benchmark result visibility

- Status: Done
- Goal: Expose backend benchmark candidate-discovery runs in the ICP Radar UI: benchmark radars stay visible, latest completed run artifacts open for any backend radar, and catalog counts match the candidates endpoint.

### Slice 0.7.6.4.18.1.4.2: Radar API catalog latency and fallback stability cleanup

- Status: Done
- Goal: Make the ICP Radar catalog deterministic from a user point of view: Benchmark / SIBUR holding contour must remain visible whenever the backend returns it, and the UI must not silently replace a slow backend response with demo fallback or local overrides.
- User value: A user can open Docker, go to ICP Radar, reliably see the backend Benchmark / SIBUR holding contour radar, open its latest completed run, and see candidate counts that match the backend API.
- Problem statement: After 0.7.6.4.18.1.4.1 the benchmark radar can still appear unstable in the UI. The likely causes are mixed catalog responsibilities: /api/radars latency, heavy latest-run artifact hydration, early demo fallback, localStorage demo overrides, and weak Docker seed/readiness checks. The slice is not complete until this instability is reproduced, fixed, and proven with 10 consecutive successful visibility checks.
- Scope:
  - Measure cold and warm /api/radars latency and identify whether the endpoint hydrates latest-run artifacts too deeply.
  - Split lightweight catalog summary from heavy latest-run artifact loading where needed.
  - Keep explicit backend loading state while /api/radars is pending; never show demo fallback as if it were backend data.
  - Allow demo fallback only after an explicit API failure, with a visible fallback indicator, error/retry path, and local reset action.
  - Make localStorage demo overrides unable to silently hide backend radars.
  - Add Docker/API readiness gate: rebuild/start, run backend seed/init to completion, verify /api/radars returns the seeded catalog including benchmark-sibur-holding-contour before UI checks.
  - Keep catalog card counters aligned with candidates endpoint or a lightweight candidate-surface summary.
  - Extend the Playwright DoD runner so it repeats the Benchmark / SIBUR holding contour catalog/detail visibility check 10 times in a row in one command.
- Out of scope:
  - No candidate-discovery admission/ranking/product acceptance tuning.
  - No signal-monitoring runtime/API implementation; that remains 0.7.6.4.18.2.
  - No new live quality claim.
  - No broad redesign of ICP Radar shell or visual language.
- Implementation notes:
  - Start with instrumentation: log or assert timing for /api/radars and latest-run artifact fetch separately.
  - Prefer fixing backend catalog payload cost over merely raising frontend timeout.
  - If fallback remains useful offline, keep it, but make it impossible to mistake for backend data.
  - Add a deterministic readiness script or npm target that fails before UI smoke if backend seed is incomplete.
  - The 10-run DoD should use a clean browser context or explicitly reset relevant localStorage before each iteration, then verify no silent fallback indicator is active.
  - Treat any failure in the 10-run sequence as slice failure; diagnose the failed iteration before retrying.
- Tests:
  - Backend/API: seeded /api/radars includes benchmark-sibur-holding-contour and returns lightweight catalog fields without requiring dossier/trace hydration.
  - Backend/API: candidate counts for Benchmark / SIBUR holding contour match candidates endpoint or explicit candidate-surface summary.
  - Frontend architecture: catalog loading cannot render demo fallback while backend request is still pending.
  - Frontend unit/contract: fallback state requires visible source indicator and retry/reset affordance.
  - Playwright DoD: run Benchmark / SIBUR holding contour visibility/detail/count check 10 consecutive times after Docker rebuild/start.
  - Negative Playwright: localStorage demo overrides cannot hide backend benchmark radar silently.
  - Regression: npm --prefix ./frontend run build, tests/test_frontend_architecture_contract.py, roadmap check, git diff --check.
- Docs:
  - Update frontend ICP Radar README with backend catalog loading, fallback, and local override rules.
  - Update Developer Guide/demo runbook with Docker readiness and 10-run Benchmark visibility DoD command.
  - Record the observed root cause and final 10/10 evidence in ROADMAP closeout notes before marking Done.
- Demo impact: After docker compose rebuild/start and seed, the ICP Radar catalog consistently shows Benchmark / SIBUR holding contour when the backend exposes it. Users can tell whether they are seeing backend data or an explicit demo fallback/error state.
- Acceptance criteria:
  - The slice cannot be marked Done until the Benchmark / SIBUR holding contour catalog/detail DoD passes 10 times in a row.
  - Each of the 10 runs must verify: catalog contains Benchmark / SIBUR holding contour; opening it shows latest completed benchmark run; UI shows 13 candidates, 3 accepted/product, and 10 review-needed; counts match backend candidates endpoint or documented summary endpoint; no silent demo fallback is active.
  - If backend is unavailable, UI must show explicit loading/error/fallback state instead of hiding the benchmark radar silently.
  - If local overrides are present, UI must show an explicit indicator/reset path and must not let overrides remove backend benchmark radars without notice.
  - /api/radars cold/warm latency is either reduced to an acceptable bounded value or explicitly handled by a stable loading state.
  - Docker readiness check fails loudly unless the seeded catalog contains benchmark-sibur-holding-contour before Playwright starts.
  - The final closeout must include the 10-run command, all 10 iteration results, backend/API counts used for comparison, and any remaining caveats.
- Risks:
  - A slow backend query may be the real source of UI flakiness; frontend timeout changes alone would hide the problem.
  - Demo fallback is useful offline, so removing it entirely would regress local demo behavior.
  - Docker seed/init race can masquerade as frontend instability; the readiness gate must isolate that cause.
  - Ten UI runs can be slow, but that cost is intentional because this slice is specifically about stability, not a single happy-path smoke.

### Slice 0.7.6.4.18.1.4.3: Candidate evidence completeness and duplicate-safe public surface

- Status: Done
- Goal: Make every user-visible candidate explainable: no public candidate row may appear without a visible source/provenance chain, no duplicate public rows may share the same candidate id, and review-needed candidates must render as review-needed evidence rather than empty zero-score accounts.
- User value: A user can open any candidate shown by Radar and understand why it is there: which source, registry fact, benchmark projection, or review reason produced it, and whether it is accepted or still requires human review.
- Problem statement: After 0.7.6.4.18.1.4.2 the benchmark radar is visible and shows 13 rows, but one row is a duplicate ?? ?????????????? projection and 10 review-needed rows have fit_score=0 and appear empty in the UI. The backend payload contains evidence refs such as dadata_7202116628 or benchmark/source refs, but those refs are not included in the public sources surface that the UI can resolve. The same entity can also be projected twice, as seen with АО СИБУРТЮМЕНЬГАЗ appearing twice with the same candidate_id and different projection reasons. The previous DoD checked candidate counts, not evidence completeness, duplicate safety, or detail-view readability.
- Scope:
  - Define a public-candidate evidence completeness contract: every visible candidate must carry at least one resolvable source, registry evidence object, or explicit projection chain that the API/UI can render.
  - Add backend projection logic that converts registry refs, benchmark-present refs, source lifecycle refs, and review-needed upstream refs into public evidence/source objects or documented non-public diagnostics.
  - Merge duplicate public candidate rows by stable candidate id and normalized name, preserving combined review flags, benchmark ids, source refs, projection reasons, and registry identity fields.
  - Change API/dossier/candidates projection so review-needed candidates expose `why shown`, source/provenance, and review reason instead of a blank detail surface.
  - Change frontend detail rendering so review-needed/no-strict-score candidates are displayed as `requires review` with provenance, not as empty zero-score candidates.
  - Add validation fixtures for АО СИБУРТЮМЕНЬГАЗ-style registry + benchmark duplicate projection.
- Out of scope:
  - No new candidate discovery retrieval/search algorithm.
  - No blind benchmark profile implementation; that is 0.7.6.4.18.1.4.4 after this evidence surface is trustworthy.
  - No signal-monitoring runtime/API implementation; that remains deferred.
  - No broad live quality claim.
  - No acceptance-promotion loosening: review-needed remains review-needed unless strict product acceptance evidence is present.
- Implementation notes:
  - Treat `candidate_universe` and `user_visible_candidates` as related but different surfaces: public rows must be deduped and enriched before reaching the API.
  - Do not hide source-less rows by silently dropping them if they are important; move them into diagnostics/gaps with an explicit reason.
  - A numeric `0` must not be the only user-facing explanation for a review-needed candidate. Use status/reason/provenance as the primary display semantics.
  - Registry refs such as `dadata_<inn>` need a renderable public evidence record with legal name, INN/OGRN where available, provider, match quality, lookup query, and review flags.
  - Benchmark-present projection refs must point to product-safe source diagnostics or become explicit gaps; they cannot render as blank candidates.
- Tests:
  - Backend red test: a visible review-needed candidate with `evidence_refs=[dadata_...]` produces a resolvable evidence/source object in the candidates or dossier API.
  - Backend red test: two projected rows with the same candidate_id are merged into one public row with combined reasons and refs.
  - Backend red test: a visible candidate with no resolvable provenance is rejected from public rows and appears as a diagnostic gap with a path-level reason.
  - Frontend test: opening each Benchmark / SIBUR holding contour candidate detail renders a non-empty provenance/reason section.
  - Playwright DoD: Benchmark / SIBUR holding contour shows 12 unique candidates after dedupe, 3 accepted/product and 9 review-needed, with zero blank detail pages and no duplicate candidate ids.
  - Regression: candidates endpoint counts still match catalog counters; signal handoff statuses remain pending/not-searched; no false `not_observed` is introduced.
  - Run: python -m pytest tests/test_backend_api.py tests/test_radar_evaluation.py tests/test_live_icp_radar.py -q
  - Run: npm --prefix ./frontend run build and the benchmark UI DoD/visual smoke after Docker rebuild.
- Docs:
  - Update Developer Guide and demo runbook to define evidence completeness as part of Radar candidate-surface DoD.
  - Update RADAR_SEARCH_PIPELINE_AS_IS if public projection/evidence surfaces change.
  - Update ROADMAP closeout with a candidate-by-candidate evidence completeness table for the benchmark run.
- Demo impact: The benchmark radar detail page should stop showing empty zero-score candidates. Review-needed rows should be visibly useful: they show the source/registry fact/projection reason and why human review is required.
- Acceptance criteria:
  - Slice is not Done until a rebuilt Docker/API Benchmark / SIBUR holding contour run or latest seeded benchmark artifact passes the public-surface DoD.
  - 12/12 unique visible candidates have a non-empty detail view unless another legitimate source-backed unique candidate is promoted.
  - 12/12 unique visible candidates have at least one resolvable provenance item: web source, registry evidence, source lifecycle entry, or explicit projection/gap reason rendered in UI, unless another legitimate source-backed unique candidate is promoted.
  - 0 duplicate public candidate ids.
  - АО СИБУРТЮМЕНЬГАЗ appears once, with merged registry/projection reasons and visible Dadata/registry evidence.
  - Review-needed candidates are not presented as unexplained score-0 accounts; they show review-required status and reason.
  - Catalog counters, candidates endpoint, and UI counts agree.
  - Any candidate that cannot satisfy provenance completeness is not public; it is reported as a diagnostic/gap with a path-level reason.
- Risks:
  - Over-eager evidence synthesis can make weak registry/projection rows look stronger than they are. Mitigate by rendering them as review-needed, not accepted.
  - Frontend detail changes can mask backend contract defects. Mitigate by backend contract tests first, UI rendering second.
  - Deduping by candidate_id alone can merge entities incorrectly if IDs are too coarse. Mitigate with normalized-name/entity-type checks and retained conflict diagnostics.
- Closeout:
  - Docker/API DoD passed against `radar-run-0bfe0ad6-c284-4142-9a6c-3115234626f3`: 10/10 UI iterations stable.
  - Public surface result: 12 unique visible candidates, 3 accepted/product, 9 review-needed, 0 duplicate candidate ids, 0 empty provenance rows.
  - Candidate evidence table:
  - `???-?????-???????` / ??? ?????? ???????? / accepted_product_candidate / refs: `retrieved_12`, `retrieved_2`, `retrieved_6` / detail non-empty.
  - `???-?????` / ??? ?????? / accepted_product_candidate / refs: `retrieved_2`, `s1`, `s2` / detail non-empty.
  - `???-?????????????` / ??? ??????????????? / accepted_product_candidate / refs: `retrieved_1`, `retrieved_4` / detail non-empty.
  - `??-??????????????` / ?? ???????????????? / review_needed_candidate / ref: `dadata_7202116628` / duplicate merged, registry/projection detail non-empty.
  - `??-?????-????????` / ?? "?????-????????" / review_needed_candidate / ref: `dadata_5249051203` / detail non-empty.
  - `??-?????-????` / ?? "?????-????" / review_needed_candidate / ref: `dadata_6903038398` / detail non-empty.
  - `???-?????-???????` / ??? ?????? ???????? / review_needed_candidate / ref: `src_1` / detail non-empty.
  - `???-??????????????` / ??? ???????????????? / review_needed_candidate / ref: `sibur_zapsib_about` / detail non-empty.
  - `??-???????????????????` / ?? ????????????????????? / review_needed_candidate / ref: `src_3` / detail non-empty.
  - `???-????????` / ??? ?????????? / review_needed_candidate / ref: `src_1` / detail non-empty.
  - `???-??????????????????` / ??? ???????????????????? / review_needed_candidate / ref: `src_3` / detail non-empty.
  - `???-???????????????` / ??? ????????????????? / review_needed_candidate / ref: `src_3` / detail non-empty.

### Slice 0.7.6.4.18.1.4.4: Blind benchmark profile and post-run baseline evaluation

- Status: Done
- Goal: Add a true blind benchmark mode for candidate discovery: run without baseline hints or protected benchmark targets, then compare the completed result against the curated SIBUR baseline only after the run.
- User value: A user can distinguish two different questions: whether the pipeline can pass a guided diagnostic smoke, and whether it can independently discover the expected SIBUR contour without being told the target names.
- Problem statement: Current benchmark_smoke is intentionally guided: it uses the curated SIBUR baseline as target hints and protected coverage probes. That is useful for diagnosing pipeline mechanics, but it is not a blind quality measurement. We need a separate mode that does not inject baseline names into planning, expansion, or projection, then evaluates the result post-factum against the same baseline.
- Scope:
  - Add a benchmark profile such as `blind_benchmark` or `benchmark_blind` with no `benchmark_target_hints`, no baseline-derived protected targets, and no `uncovered_baseline_target` scheduling.
  - Keep the evaluation baseline external to the run and use it only after completion in `evaluate-radar-benchmark`.
  - Add metadata proving whether benchmark hints were used: `benchmark_hints_used=false`, `benchmark_mode=blind`, and no benchmark-context expansion targets.
  - Add post-run evaluation fields that compare blind results against the 12-target SIBUR smoke baseline: strict legal recall, visible legal recall, accepted count, review-needed count, production-site review recall, false negatives, evidence completeness, duplicate count.
  - Add CLI/docs for running blind benchmark separately from guided smoke.
  - Keep benchmark_smoke as the fast guided diagnostic contour with 12 key targets.
- Out of scope:
  - No replacement of benchmark_smoke.
  - No expansion of the baseline to all 33 demo candidates in this slice.
  - No signal-monitoring live runtime/API implementation.
  - No one-run public quality claim; blind benchmark is diagnostic evidence, not a published benchmark number.
  - No unlimited budget or hidden fallback to baseline target hints.
- Implementation notes:
  - Proposed budget limits: max_total_web_tasks_per_run=55, max_openrouter_calls_per_run=36, max_openrouter_planner_calls_per_run=3, max_openrouter_web_task_calls_per_run=28, max_recall_expansion_openrouter_calls_per_run=10, max_openrouter_server_tool_web_searches_per_run=90, max_dadata_lookups_per_run=10, max_source_verification_requests_per_run=80.
  - Discovery limits: max_discovery_tasks_per_rule=5, max_web_tasks_per_subject=2, min_useful_sources_per_discovery_task=2, min_candidates_per_discovery_task=2, max_discovery_retries_per_task=1, max_provider_retries_per_task=1, max_checkpoint_revisions_per_run=2, max_checkpoint_retries_per_stage=1.
  - Reserves: recall_expansion=10, official_coverage_probe=8, open_web_coverage_probe=5, production_site_coverage_probe=3.
  - Disable smoke caps: smoke_max_candidates=0 and smoke_max_signals=0. Keep signal_execution_mode=handoff.
  - Disable guided-target fields: benchmark_target_hints=[], benchmark_target_probe_minimums={}, coverage_completion_target_limit=0 or generic-only without baseline target ids.
  - Use the same curated 12-target SIBUR baseline for evaluation to keep smoke and blind numbers comparable.
  - Add an explicit blind-run validation helper or CLI output section that prints the closeout DoD fields in one place, so the slice cannot be closed from scattered logs.
- Tests:
  - Unit/contract test: blind benchmark context contains no `benchmark_target_hints` and reports `benchmark_hints_used=false`.
  - Search-expansion test: blind benchmark produces no `target_origin=benchmark_context` and no `uncovered_baseline_target=true` records.
  - Evaluation test: baseline is loaded only by post-run evaluation, not by run task_context.
  - API/CLI test: `run-radar-benchmark --profile blind_benchmark` is accepted and persisted with blind metadata.
  - Public-surface regression: duplicate candidate ids = 0, visible candidates without provenance = 0, candidates endpoint/dossier counters agree, and handoff path does not emit `not_observed`.
  - Regression test: `benchmark_smoke` still carries guided target hints and protected target guarantees.
  - Final Docker/API gate: rebuild Docker, seed/check backend catalog, run SIBUR blind benchmark once, evaluate latest run, and report strict recall, visible recall, accepted/review-needed counts, false negatives, duplicate count, and evidence completeness.
  - If blind run reaches bounded terminal state instead of `completed`, evaluation must still be present and interpretable; otherwise the slice remains open.
- Docs:
  - Update Developer Guide and demo README with the difference between guided `benchmark_smoke` and blind benchmark.
  - Update benchmark/evaluation docs to state that blind mode is post-run comparison only and not a public quality claim.
  - Update roadmap closeout with exact budget limits, run id, hints-used proof, first observed blind benchmark numbers, and false-negative RCA table.
  - If the run exposes a process gap, add or update the relevant runbook/skill/check so future behavior-changing Radar slices automatically rebuild Docker, run the diagnostic, and propose roadmap corrections.
- Demo impact: Demo tooling gains a clearer quality diagnostic: users can run guided smoke for pipeline mechanics and blind benchmark for independent discovery behavior. UI does not need a new screen in this slice, but reports should label the mode clearly.
- Acceptance criteria:
  - `benchmark_smoke` remains guided and continues to use the 12-target diagnostic baseline.
  - New blind benchmark mode runs without baseline hints inside candidate discovery.
  - Run metadata proves baseline hints were not used: `benchmark_hints_used=false`, `benchmark_mode=blind`, and no baseline-derived protected target state.
  - Expansion diagnostics contain no `target_origin=benchmark_context`, no `uncovered_baseline_target=true`, and no protected-baseline scheduling.
  - Post-run evaluation compares the result against the 12-target SIBUR baseline and reports blind strict recall, visible recall, accepted/review-needed counts, false negatives, evidence completeness, duplicate count, and source quality.
  - Public surface remains evidence-complete: duplicate candidate ids = 0, visible candidates without provenance = 0, candidate/detail/API counters agree, and no `not_observed` appears in candidate-discovery handoff mode.
  - The slice is not Done until Docker is rebuilt and at least one API/CLI blind benchmark reaches `completed` or a bounded terminal state with artifact, candidate universe, public surface, and interpretable post-run evaluation report.
  - Terminal states that are not acceptable for closeout: schema/extraction failure without salvage, API/job failure, empty artifact, missing candidate universe, missing evaluation report, or failed baseline comparison.
  - Low recall is acceptable only as measured diagnostic evidence: if strict recall is 0, closeout must include a concrete follow-up RCA slice before this slice can be marked Done.
  - The result is not treated as a public quality claim.
- Risks:
  - Without hints the first blind run may look worse than guided smoke; that is expected and useful evidence.
  - Budget too low can under-measure recall; budget too high can hide poor search strategy. Start with the bounded intermediate profile and adjust only with explicit RCA.
  - If evidence completeness remains broken, blind results will be hard to read; therefore this slice depends on 0.7.6.4.18.1.4.3.
  - A technically successful blind run with unreadable misses is not useful; require path-level reasons before closing the slice.
  - If the first blind result is poor, do not tune blindly inside this slice. Record the evidence and create a separate corrective RCA slice unless the defect is a small implementation bug in the blind/evaluation plumbing.
- Completion DoD: Hard closeout formula: `run without hints -> artifact -> public surface -> post-run baseline comparison -> explicit miss diagnostics`.

Required proof before Done:
- Docker stack rebuilt and backend API available on `http://127.0.0.1:8001`.
- One SIBUR blind benchmark run executed through normal API/CLI path, not by direct fixture injection.
- Run metadata confirms no baseline hints entered planning, expansion, scheduling, projection, or candidate admission.
- Evaluation report lists all 12 baseline targets and gives each miss a path-level reason: `not_generated`, `no_executable_query`, `not_selected`, `not_admitted`, `not_executed`, `source_not_found`, `present_not_projected`, or `explicitly_rejected`.
- Roadmap closeout records run id, mode, hints-used flag, visible candidates, accepted candidates, review-needed candidates, duplicate ids, empty provenance count, strict recall, visible recall, false negatives, top miss reasons, and whether a follow-up corrective slice is required.
- `benchmark_smoke` is rechecked so the guided diagnostic contour remains intact.

### Slice 0.7.6.4.18.1.4.5: Radar run history selector and direct run inspection

- Status: Done
- Goal: Add a compact Radar run history selector so users can inspect a specific persisted run, including blind benchmark runs, instead of being forced to view only the latest run for a radar.
- User value: A user can open Benchmark / SIBUR holding contour, select the exact blind run `radar-run-3bbf9c0f-330e-4468-8901-966a751234a8`, and see the candidates, dossier, diagnostics, and counters for that run even after a newer smoke run becomes latest.
- Problem statement: The UI currently treats a radar detail as the latest-run surface. After running `benchmark_smoke` to validate guided diagnostics, the previous `blind_benchmark` result is still in the API/database but effectively disappears from the UI. This makes benchmark RCA confusing because the visible candidates may belong to a different run than the run being discussed.
- Scope:
  - Add a lightweight backend endpoint such as `GET /api/radars/{radar_id}/runs?limit=20` returning recent run summaries for a radar without full artifacts.
  - Include run id, status, queued/started/completed timestamps, profile/mode where available, and compact output counts.
  - Add a run selector/history control to Radar detail, defaulting to latest but allowing selection of an older completed run.
  - Support direct inspection by URL query parameter, for example `?runId=radar-run-3bbf9c0f-330e-4468-8901-966a751234a8`.
  - Reload candidates, dossier, diagnostics, artifact viewer, counters, and review overlays from the selected run id, not from latest.
  - Show an explicit selected-run identity: latest vs selected historical run, run id, status, profile/mode, and completion time.
- Out of scope:
  - No candidate-discovery pipeline, scoring, acceptance, benchmark, or signal-monitoring behavior changes.
  - No side-by-side run comparison screen.
  - No new benchmark execution from the selector.
  - No broad historical analytics, filtering, or retention policy changes.
- Implementation notes:
  - Keep the UI fix small: a selector/control inside the existing Radar detail screen, not a new product area.
  - Use the existing Power Web OS app shell and design-system tokens; run ids and counters use mono typography.
  - Do not silently fall back to latest when a requested run id is missing; show a readable error and keep the current run unchanged.
  - If the selected run belongs to another radar, reject it with a clear message.
  - Preserve current latest-run behavior when no run id is selected.
  - Use Lucide icons where an icon is needed and route all visible strings through EN/RU i18n resources.
- Tests:
  - Backend test: recent runs endpoint returns only runs for the requested radar, sorted newest-first, without full artifact payloads.
  - Backend test: unknown radar and wrong-radar run ids produce clear errors.
  - Frontend/API adapter test: default detail opens latest run.
  - Frontend test: selecting an older run reloads candidates/dossier/diagnostics for that selected run id.
  - Frontend test: direct URL with `?runId=...` opens the selected persisted run.
  - Frontend test: missing run id shows an error state instead of silently reverting to latest.
  - Regression commands: `python -m pytest tests/test_backend_api.py tests/test_radar_jobs.py -q`, frontend tests/build, and a browser/Playwright DoD check against local Docker.
- Docs:
  - Update Developer Guide/demo README with how to open a specific Radar run from UI and why benchmark diagnostics should cite run id.
  - Update Radar UI/docs notes to distinguish radar latest state from selected historical run state.
- Demo impact: The demo becomes inspectable after multiple benchmark runs: users can open the benchmark radar, choose the blind run, then switch back to the latest smoke run without rerunning either job.
- Acceptance criteria:
  - `Benchmark / SIBUR holding contour` is visible in the catalog when backend returns it.
  - Opening the radar still defaults to the latest completed run.
  - The UI can select and display `radar-run-3bbf9c0f-330e-4468-8901-966a751234a8` even if latest is `radar-run-3aa622ff-e137-48aa-9f2c-15e74f594bfc` or another newer run.
  - Selected run identity is visible: run id, status, profile/mode when available, and completion time.
  - Candidate table, counters, dossier, diagnostics, and artifact viewer all use the selected run id.
  - Direct URL with `?runId=...` opens that run and does not require rerunning benchmark.
  - Unknown or wrong-radar run id shows a clear error, not a silent latest fallback.
  - At 1280x720 and 1366x768 there is no text overlap or unusable selector layout.
- Risks:
  - If run selection state is mixed with latest-run polling state, UI may show counters from one run and candidates from another; tests must assert selected-run consistency.
  - If local demo overrides still mask backend radars, the selector may appear to work only on fixture data; use the backend mode DoD path.
  - Adding too much benchmark analytics here would expand scope; keep comparison/reporting for later slices.

### Slice 0.7.6.4.18.2: Signal monitoring live runtime and API wiring

- Status: Done
- Goal: Add the first bounded live/scheduled signal-monitoring runtime over accepted candidate-discovery snapshots with independent signal budgets, provider calls, persistence/API surfaces, and no candidate-discovery budget coupling.
- User value: A user can monitor intent changes for known candidates after discovery, with its own cadence, budget, and report, instead of rerunning full candidate discovery to refresh signals.
- Problem statement: Signal monitoring currently has contracts, source strategy, budgets, model profile isolation, and a recorded demo loop, but no first-class live/API/job runtime equivalent to candidate discovery. Therefore the product cannot yet launch or evaluate signal monitoring independently.
- Scope:
  - Build a signal-monitoring application service under `radar/signal_monitoring`.
  - Accept a candidate-discovery snapshot or persisted candidate set as input.
  - Execute bounded signal tasks with signal-monitoring budgets and provider-attempt records.
  - Persist/API expose a signal-monitoring run separately from candidate-discovery runs, or add an explicit pipeline discriminator if reusing generic run tables.
  - Add live provider probe/smoke for one small monitoring run after recorded tests are green.
- Out of scope:
  - No broad benchmark or quality claim.
  - No automatic recurring scheduler beyond the minimal job/API wiring needed for a manual run.
  - No candidate universe expansion.
  - No candidate-discovery scoring change.
- Implementation notes:
  - Reuse shared provider-level external-call contracts only where genuinely shared; keep signal task budgets signal-owned.
  - The input contract should not depend on candidate-discovery internals beyond product-safe candidate/source snapshot records.
  - Model profile should come from `signal_monitoring_default`, not candidate-discovery role settings.
  - Run after 0.7.6.4.18.1.1 so signal-monitoring live runtime starts from a recall-first candidate-discovery handoff instead of a flat Monitor/weak upstream snapshot.
  - Deferred until 0.7.6.4.18.1.2 is validated, because signal-monitoring live runtime should start from a candidate-discovery snapshot that can survive live extraction schema drift.
  - Deferred until 0.7.6.4.18.1.4 is validated, because signal monitoring should start from a user-facing candidate snapshot that exposes accepted and review-needed legal candidates, not only the strict accepted subset.
  - Deferred until 0.7.6.4.18.1.4.3 validates evidence-complete, duplicate-safe public candidate rows, because signal monitoring should not consume empty or duplicated candidate snapshots.
  - Deferred until 0.7.6.4.18.1.4.4 adds blind benchmark mode, so product work can separate guided diagnostic smoke from independent discovery quality evidence.
  - Deferred until 0.7.6.4.18.1.4.5 adds run history/direct run inspection, because benchmark and RCA evidence must be visible in UI by exact run id, not only as the latest radar state.
- Tests:
  - Recorded signal-monitoring tests for observed, searched-negative, not-searched, budget-limited, and review-needed states.
  - API/job smoke for starting and reading a signal-monitoring run.
  - Runtime config tests proving signal model profile and signal budgets are used.
  - One bounded live-provider probe only after recorded/API gates pass.
- Docs:
  - Update signal-monitoring AS IS docs.
  - Update Developer Guide commands for manual signal-monitoring run.
  - Update API/user docs if a new endpoint or pipeline discriminator is exposed.
- Demo impact:
  - Demo should show signal-monitoring output as a separate run/report over known candidates, not embedded as a completed part of candidate discovery.
- Acceptance criteria:
  - Signal monitoring can be launched independently from candidate discovery.
  - It has independent task/external-call budget reporting.
  - It stores or returns a separate signal-monitoring outcome/report.
  - Candidate discovery does not need to run again to monitor signals for existing candidates.
- Risks:
  - Persistence/API may be tempted to reuse candidate-discovery fields ambiguously. Require explicit pipeline id/type in persisted/API surfaces.

### Slice 0.7.6.4.18.2.1: Signal monitoring search planning, evidence validation and positive-control benchmark

- Status: Done
- Goal: Build an auditable multi-lane signal-search pipeline and prove it through an AS IS -> TO BE -> validation -> AS IS evidence loop.
- Scope: Multi-lane signal planning, plan acceptance, scheduling, retrieval receipts, evidence validation, checkpoints, initial/incremental windows, positive controls, acceptance validator and process gates.
- Tests: Mapped unit/recorded/API/job/architecture tests plus two persisted Docker/API quality runs and restart round-trip.
- Docs: Baseline RCA, TO BE Markdown/PDF, acceptance manifest, validation Markdown/JSON, ADR, procedural skills and finalized Signal Monitoring AS IS Markdown/PDF.
- Acceptance criteria: All mandatory SM-* requirements PASS; first live run finds at least two valid controls; second run proves per-lane incremental windows and dedupe; no opaque sources, orphan decisions, false not_observed or failed watermark advances.
- Acceptance manifest: docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.acceptance.json
- Behavior change: true
- Closeout: PASS. Baseline RCA: signal-run-c8adb584-da26-4c31-84d1-37c067e7cf89. Initial live quality run: signal-run-9d018757-a96c-4902-92ac-b0bdb4d3bb50; source radar-run-3bbf9c0f-330e-4468-8901-966a751234a8; 2 candidates, 2 criteria, 14 executed tasks/receipts, 4 observed outcomes, POLIEF negative control rejected. Incremental run: signal-run-863de7ce-cdab-456f-91f8-917c0a875452; 14 executed tasks/receipts, 16 lane watermarks and 35 previous source keys loaded, 2 repeats suppressed, 0 old events republished, 0 failed watermark advances. Both reports remained readable after API restart. All SM-* requirements PASS in validation report. Retrospective fixed provider aliases, lane collapse, cross-entity known-source evidence, unstable summary fingerprints and stale-image verification procedure.
- Pipeline: signal-monitoring
- Validation report: docs/radar/pipelines/signal-monitoring/validation/0.7.6.4.18.2.1/validation.json

### Slice 0.7.6.4.18.2.2: Signal event-time integrity, source capability binding and expanded live quality benchmark

- Status: Done
- Goal: Make Signal Monitoring recall-first but temporally honest: retain relevant unknown-date evidence for human review, prevent cross-entity source contamination, and prove live quality on a broader six-candidate benchmark.
- User value: Users see potentially useful evidence even when its publication date cannot be established, while confirmed fresh signals, unknown-date review items and known out-of-window evidence remain clearly distinguishable.
- Problem statement: The 0.7.6.4.18.2.1 live pair proved runtime and incremental mechanics but exposed a quality gap: retrieved_at was accepted as event freshness, identity/group sources were scheduled as candidate signal sources, three observed outcomes had score zero, and the live positive-control gate counted arbitrary observed pairs instead of matching curated event URLs and dates.
- Scope: Introduce separate retrieved_at, published_at and event_at semantics with extraction method/confidence; retain relevant unknown-date evidence as review_needed_date_unknown; reject known out-of-window evidence; add generic source capabilities and candidate/source ownership checks; strengthen multilingual query variants and bounded transport retries; normalize observed scoring; expand live controls to 6 candidates, at least 3 accepted and 3 review-needed, 2 criteria and at least 12 candidate-criterion pairs; run initial and incremental persisted quality benchmarks.
- Out of scope: No company-specific production hardcodes; no candidate rediscovery; no signal scheduling UI; no notification delivery; no public quality claim from one benchmark pair; no automatic acceptance of unknown-date evidence as confirmed observed.
- Implementation notes: Use generic source capabilities identity_only, official_press, event_feed, project_or_asset_history, registry, generic_web and unknown. Identity-only evidence may support entity linkage but not a fresh signal. Candidate ownership is resolved from candidate id, legal name, aliases, source candidate_id, URL/text identity and domain/path context. Unknown or conflicting dates are retained for review. Quality profile limits: 48 tasks, 60 provider calls, 8 extraction retries, 4 backup retries, 120 source verifications, 60 lookback queries, one query revision per candidate/criterion and at most two known sources per pair.
- Tests: Red tests for retrieved_at not satisfying freshness; missing date retained as review_needed_date_unknown; known out-of-window article rejected; generic cross-entity and identity-only source filtering without SIBUR/POLIEF/Wikipedia hardcodes; observed score contract; transport retry. Recorded controls must match explicit candidate, criterion, URL and date. Docker/API DoD uses 6 candidates and 2 criteria, then repeats incrementally and validates persistence after API restart.
- Docs: Create baseline RCA from signal-run-9d018757-a96c-4902-92ac-b0bdb4d3bb50 and signal-run-863de7ce-cdab-456f-91f8-917c0a875452; create TO BE Markdown/PDF and acceptance manifest; after PASS reconcile Signal Monitoring AS IS Markdown/PDF, validation JSON/Markdown, Developer Guide, demo runbook and process retrospective.
- Demo impact: The quality demo shows confirmed fresh signals, unknown-date review items and out-of-window rejections separately, with source ownership, date provenance and review reason visible for every retained item.
- Acceptance criteria: DoD is mandatory: at least 6 candidates (minimum 3 accepted and 3 review-needed), 2 criteria and 12 candidate-criterion pairs; all evidence is classified as confirmed in-window, review-needed unknown/conflicting date, or rejected out-of-window; missing date evidence remains visible for human review but never counts as confirmed positive control; retrieved_at never substitutes for publication/event time; January 2024 controls are rejected for a 2025-2026 window; zero cross-entity known-source tasks and zero identity-only sources used as fresh-signal evidence; zero production hardcodes for benchmark companies; at least 4 explicit positive controls matched by candidate, criterion, URL and expected date; at least 2 negative controls remain unconfirmed; at least 1 unknown-date control remains visible for review; every confirmed observed item has non-zero score and resolvable evidence; transport error exercises bounded retry; second run republishes zero old events; every miss/rejection has an explicit reason; Docker rebuild, two persisted API runs, restart round-trip and acceptance validator all PASS. Slice cannot close from unit/recorded tests alone.
- Risks: Recall may fall if source capabilities are too strict, so unknown and ambiguous evidence must be retained for review rather than discarded. Date extraction can conflict across metadata, URL and text, so provenance and confidence are mandatory. Expanded live benchmark costs more, so budgets remain bounded and fast recorded gates run before Docker live calls.
- Acceptance manifest: docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.acceptance.json
- Behavior change: true
- Pipeline: signal-monitoring
- Validation report: docs/radar/pipelines/signal-monitoring/validation/0.7.6.4.18.2.2/validation.json

### Slice 0.7.6.4.18.3: Radar pipeline split validation and UI contract

- Status: Done
- Goal: Validate and document that candidate discovery and signal monitoring are launched, budgeted, evaluated, persisted, and displayed as two separate Radar pipelines.
- User value: The product and codebase make it obvious which pipeline found candidates and which pipeline monitored signals, so users can trust budget/status explanations.
- Problem statement: Even after runtime separation, tests/docs/UI can drift back to a monolithic mental model unless there is a dedicated validation and contract slice.
- Scope:
  - Add end-to-end recorded/fake tests that run candidate discovery first, then signal monitoring against its output.
  - Verify separate budget summaries, statuses, timestamps, and report/dossier surfaces.
  - Update frontend contract/copy so discovery and monitoring controls/results are clearly distinct.
  - Add architecture tests preventing new code from treating candidate discovery as the owner of recurring signal evaluation.
- Out of scope:
  - No provider tuning.
  - No scoring model redesign.
  - No broad live benchmark.
- Implementation notes:
  - This is the acceptance gate before returning to product feature work.
  - Use recorded/fake first; live smoke is optional and bounded.
  - Keep root namespace closure `0.7.6.4.19` after this so final filesystem cleanup happens after both pipelines are package-owned and validated.
- Tests:
  - Candidate-discovery recorded/fake run.
  - Signal-monitoring recorded/fake run over candidate-discovery output.
  - API/job smoke for both pipeline ids.
  - Frontend contract test for separated controls and labels.
  - Architecture/package tests and `python -m power_web_os.roadmap check`.
- Docs:
  - Update pipeline registry, AS IS docs, Developer Guide, and relevant user/demo docs.
  - Record any remaining compatibility exceptions before root namespace closure.
- Demo impact:
  - Demo should show two separate artifacts/reports or clearly separated tabs: candidate discovery result and signal monitoring result.
- Acceptance criteria:
  - A developer can run candidate discovery and signal monitoring separately from documented commands.
  - API/UI/report surfaces identify the pipeline id.
  - Budgets and evaluation statuses are not mixed between the two.
  - Roadmap can safely move to root namespace closure and then product work.
- Risks:
  - UI and API may lag backend separation. Mitigate with contract tests that fail on ambiguous labels or merged budget/status fields.
- Behavior change: false
- Closeout: PASS: radar benchmark-sibur-holding-contour; candidate run radar-run-3bbf9c0f-330e-4468-8901-966a751234a8; signal runs signal-run-df00b3b8-267c-4091-a4dd-8167434e2cf3 and signal-run-010ef75d-c626-44e3-a025-56c95522c1a8; 6 candidates and 12 observations; source lineage, separate histories/budgets, direct URL, missing-run error, 1280x720 EN, 1366x768 RU, Docker rebuild and API restart round-trip validated.
- Validation report: docs/radar/pipelines/validation/0.7.6.4.18.3/validation.json

### Slice 0.7.6.4.18.3.1: Per-signal monitoring depth, cadence and source settings

- Status: Done
- Goal: Expose persisted per-signal initial lookback, incremental overlap, cadence and source policy settings after the split UI contract is validated.
- Scope: Persist per-criterion initial depth, overlap, cadence and source-lane policy; expose them through API and UI with validation.
- Acceptance criteria: Each criterion has explicit persisted monitoring settings, runtime uses them without hidden defaults, and UI/API round-trip is covered.

### Slice 0.7.6.4.18.3.1.1: Radar catalog counter reconciliation and API fallback recovery

- Status: Done
- Goal: Make Radar catalog counters use the same canonical candidate surface as run detail and recover automatically from temporary backend unavailability without leaving users on stale demo zeros.
- User value: A user sees one trustworthy set of candidate counters in the Radar catalog and in run detail. Temporary backend startup latency cannot strand the UI on demo data, and older persisted runs remain honestly classified instead of appearing empty.
- Problem statement: The Radar catalog is materially inconsistent with run detail. When the frontend catalog request fails once during startup, useRadarBackend switches to demo fallback and never retries; that fallback contains zero counts for Benchmark / SIBUR holding contour and TOIR Quick Live Radar while TOIR / SIBUR happens to show its static fixture count of 33. Separately, the new scalar radar_run_outputs summaries are computed from raw candidates_json, while /api/radar-runs/{run_id}/candidates can project a larger canonical public surface from the artifact. Current evidence: benchmark latest run radar-run-3aa622ff-e137-48aa-9f2c-15e74f594bfc has 10 public candidates (3 accepted, 7 review-needed), but the catalog API summary reports 3 candidates and internally inconsistent accepted=3/review=3; Quick Live latest run radar-run-ef74d8c0-8e19-43eb-9936-cfc0a44c383b has 2 public candidates, but legacy rows are reported as accepted=0/review=0. A user can therefore see candidates inside a Radar while its catalog card shows zeros or contradictory counters.
- Scope:
  - Introduce one canonical candidate-surface summary projection shared by the candidates endpoint, run summaries and catalog summaries.
  - Persist candidate_count, accepted_count and needs_review_count from the canonical visible public surface, not from raw extraction candidates_json.
  - Backfill existing radar_run_outputs scalar summaries from the same projection without rerunning Radar or calling providers.
  - Treat every visible legacy candidate that is not explicitly accepted as review-needed unless it is explicitly rejected and therefore absent from the public surface.
  - Enforce the invariant accepted_count + needs_review_count = visible_candidate_count and expose an explicit diagnostic if an artifact cannot be classified.
  - Refactor frontend catalog loading into a retryable operation. After a transient API failure, show an explicit demo/degraded state, retry with bounded backoff, provide a manual reconnect action, and atomically replace fallback data after API recovery without requiring a page reload.
  - Refresh lightweight catalog summaries after a candidate-discovery run completes and when the user returns to the catalog, without eager detail/artifact loading.
  - Keep local demo overrides unable to overwrite recovered backend counters silently.
- Out of scope:
  - No candidate-discovery search, admission, scoring, filtering, provider, checkpoint, budget or signal-monitoring behavior changes.
  - No new Radar or Signal Monitoring runs and no OpenRouter/registry token spend.
  - No redesign of the Radar catalog layout.
  - No change to historical-run selection semantics: the catalog represents the latest completed candidate-discovery run, while detail may display an explicitly selected historical run.
  - No public quality claim.
- Implementation notes:
  - Put canonical summary logic in a backend/application read-model helper used by persistence backfill and API mappers; do not duplicate classification rules in React or SQL migration code.
  - Reuse the exact candidate list projected by candidates_response, including artifact user_visible_candidates compatibility behavior.
  - Keep catalog endpoints lightweight: scalar summaries must remain queryable without loading dossier, journal, technical trace or all run metadata.
  - API mode always owns backend Radar counters. Demo fallback is allowed only as a visibly labeled degraded/offline surface.
  - Frontend reconnect should be cancellable, avoid overlapping requests, cap retry delay, ignore stale responses and stop retrying after successful API recovery.
  - Record this as a corrective retrospective for completed slice 0.7.6.4.18.1.4.2: its previous 10-run gate covered clean ready-backend startup but did not cover frontend-before-backend recovery, and it compared catalog counters with the scalar summary rather than independently with the candidates endpoint.
- Tests:
  - Backend unit/contract: canonical summary uses the same candidate ids and count as /api/radar-runs/{run_id}/candidates.
  - Backend compatibility: artifact public candidates override smaller raw candidates_json; legacy visible non-accepted candidates become review-needed.
  - Backend invariant: accepted + review-needed equals visible count; duplicate ids and source-less hidden rows do not inflate counts.
  - Migration/backfill test: existing outputs are reconciled correctly and survive API restart.
  - API integration: /api/radars, /api/radars/{id}/runs and /api/radar-runs/{run_id}/candidates agree for Benchmark and Quick Live.
  - Frontend contract: initial API failure shows an explicit degraded/demo indicator and reconnect action; successful retry replaces fallback catalog without reload.
  - Frontend race tests: retry is cancellable, stale fallback/API responses cannot overwrite newer backend data, and returning to catalog refreshes summaries without detail fanout.
  - Playwright Docker gate: 10 cold opens with backend already ready and 10 frontend-before-backend recovery cycles.
  - Required gates: python -m pytest tests/test_backend_api.py tests/test_radar_persistence.py tests/test_frontend_architecture_contract.py -q; npm --prefix ./frontend run build; targeted Playwright DoD; python -m power_web_os.roadmap check; git diff --check.
- Docs:
  - Update frontend ICP Radar README with canonical summary ownership, degraded fallback behavior and reconnect lifecycle.
  - Update Developer Guide and demo runbook with the frontend-before-backend recovery gate and catalog/detail counter comparison.
  - Add the retrospective finding to the slice closeout: the prior clean-start-only stability test was insufficient.
  - No Radar pipeline TO BE/AS IS update is required because pipeline behavior does not change.
- Demo impact: After Docker startup, Benchmark / SIBUR holding contour and TOIR Quick Live Radar show the candidate totals from their latest completed backend runs. If the frontend opens before the API is ready, the user briefly sees an explicit degraded/demo state and then the catalog repairs itself automatically when the API becomes available.
- Acceptance criteria: Hard DoD; the slice cannot be marked Done until all conditions pass:
- Catalog candidate_count equals the length and candidate-id set of /api/radar-runs/{latest_completed_run_id}/candidates for every Radar with a completed candidate-discovery output.
- accepted_count + needs_review_count = candidate_count for every catalog card backed by a completed run.
- On the current seeded database, Benchmark latest run radar-run-3aa622ff-e137-48aa-9f2c-15e74f594bfc shows 10 candidates, 3 accepted and 7 review-needed.
- On the current seeded database, Quick Live latest run radar-run-ef74d8c0-8e19-43eb-9936-cfc0a44c383b shows 2 candidates, 0 accepted and 2 review-needed.
- TOIR / SIBUR remains 33 candidates, 0 accepted and 33 review-needed.
- The catalog explicitly states that its counters belong to the latest completed candidate-discovery run; choosing a historical run in detail does not silently rewrite catalog counters.
- Docker is rebuilt and the API is restarted after backfill; reconciled counters persist.
- Ten consecutive cold UI opens with an already-ready backend show correct backend counts and no fallback state.
- Ten consecutive recovery cycles start the frontend before the backend, observe an explicit degraded/demo state, then start/restore the backend and reach correct API counts without page reload.
- No cycle leaves the UI permanently in fallback, performs catalog detail fanout or shows temporary zero backend counts as final state.
- Frontend build, backend/API/persistence tests, architecture contracts, Playwright, roadmap check and git diff check are green.
- Closeout records API counts, candidates-endpoint counts, 10+10 iteration evidence, restart persistence and any remaining caveats.
- Risks:
  - Reusing public-surface projection during migration can accidentally load large artifacts. Mitigate by backfilling once and keeping runtime reads scalar.
  - Legacy artifacts may lack modern acceptance fields. Mitigate with the conservative rule that a visible non-accepted row requires review, plus explicit diagnostics for genuinely unclassifiable data.
  - Automatic retries can create request storms or stale-response races. Mitigate with bounded backoff, cancellation, one in-flight catalog request and request-generation guards.
  - A newer run can complete during validation and change expected counts. Pin concrete run ids for fixture assertions and separately test latest-run semantics.
- Behavior change: false

### Slice 0.7.6.4.18.3.2: Signal monitoring evidence status language and report clarity

- Status: Done
- Goal: Build an honest cumulative Signal Monitoring product surface: show all candidate-criterion results, resolve source provenance, distinguish current-run delta from previously retained state, and project the selected monitoring state onto the candidate list without merging pipeline ownership.
- User value: A user sees what was actually found for each company, can open the supporting sources, understands what is new versus already known, and does not see false zero signal counts after a successful monitoring run.
- Problem statement: The completed split UI proves separate runtimes and lineage but the current report is materially misleading: 12 means candidate-criterion pairs rather than findings; the frontend silently truncates the report to 6 rows; backend source_refs are rendered as zero evidence; incremental runs show only the current delta and hide previously retained evidence; and the main candidate list still displays candidate-discovery signal zeros instead of a joined monitoring projection.
- Scope: 1. Replace ambiguous result count with explicit pair, candidate, criterion, new, retained-review, historical and searched-negative counts. 2. Remove hidden six-row truncation and render all rows or explicit pagination with shown/total counts. 3. Map source_refs and evidence_refs into resolvable product-safe evidence cards. 4. Add cumulative state per candidate and criterion with current delta, retained state and origin run. 5. Link duplicate rows to originating run and evidence. 6. Overlay selected monitoring state onto the main candidate list while keeping candidate-discovery artifacts immutable. 7. Mark candidates outside monitoring scope as not monitored. 8. Add human outcome labels while preserving technical statuses.
- Out of scope: No provider calls, planning changes, source-lane changes, scoring redesign, budget changes or live quality claim. No mutation of candidate-discovery artifacts or candidate universe. No per-signal cadence, depth, overlap or source settings; those remain in 0.7.6.4.18.3.1. No notification delivery or automatic scheduling.
- Implementation notes: Build the cumulative join in a backend/application projection or API read model rather than independently in React. Use signal-run-010ef75d-c626-44e3-a025-56c95522c1a8 as the initial fixture and signal-run-df00b3b8-267c-4091-a4dd-8167434e2cf3 as the incremental fixture. The initial run has 4 observed, 3 review/unclear and 5 searched-negative outcomes; the incremental run has 0 new confirmed signals but must retain prior confirmed/review evidence. Resolve source_refs/evidence_refs centrally. The selected signal run controls only the monitoring overlay. Evidence with an unverified date cannot be presented as confirmed fresh without a valid temporal basis.
- Tests: Backend read-model tests cover four human outcomes, cumulative state, origin lineage and source resolution. Contract tests prove 12 pairs are checks rather than 12 findings and source_refs do not render false zero evidence. Initial fixture proves 4 observed outcomes with sources. Incremental fixture proves 0 new while prior states remain visible. Main candidate overlay matches the selected signal run and out-of-scope candidates show not monitored. Playwright checks all 12 outcomes, sources, cumulative labels, RU/EN copy and no truncation. Signal runtime/API/persistence, candidate discovery, architecture, frontend build, roadmap check and diff check remain green.
- Docs: Update Signal Monitoring AS IS, RADAR_PIPELINE_SPLIT_UI_CONTRACT.md, Developer Guide, User Guide and demo runbook. Record the RCA for signal-run-df00b3b8-267c-4091-a4dd-8167434e2cf3 and the failed 0.7.6.4.18.3 acceptance assumption. Strengthen the split UI validation gate to check semantic values and evidence links, not only panel presence and counts.
- Demo impact: The demo shows six monitored companies and all twelve candidate-criterion outcomes, with four previously found signals from the initial run preserved in the incremental view, working source links, clear new-versus-known labels, and the same state visible in the main candidate table.
- Acceptance criteria: Hard DoD: all 12 candidate-criterion outcomes are accessible with no hidden truncation; UI says 6 candidates x 2 criteria = 12 checks and never calls them 12 found signals; initial run 010ef shows exactly 4 confirmed, 3 review/unclear and 5 searched-negative outcomes; incremental run df00 shows 0 new while preserving cumulative prior states and origin links; every retained/confirmed row has resolvable provenance and no false zero evidence where source_refs exist; duplicate rows link to origin evidence; main list and detail show the selected monitoring overlay; out-of-scope candidates show not monitored; four human outcomes are distinct; unknown-date evidence is not shown as confirmed fresh without temporal basis; candidate and signal ownership/budgets remain separate; Docker, backend/API tests, frontend build and Playwright pass at 1280x720 and 1366x768 in RU/EN; validation report records both run IDs, counts, source resolution, cumulative checks and PASS.
- Risks: Cumulative state could mix unrelated runs, so require the same radar and source candidate lineage. Historical evidence could look new, so always show origin run, novelty and checked window. Source refs are heterogeneous, so resolve through artifact sources, lifecycle and receipts with explicit unresolved diagnostics. The main-list overlay must keep identity and qualification from candidate discovery and signal outcomes from the selected monitoring run.
- Behavior change: false
- Pipeline: signal-monitoring

### Slice 0.7.6.4.19: Radar root namespace closure and compatibility sunset

- Status: Done
- Goal: Finish Radar root namespace migration and prove with a fresh live candidate-discovery plus initial/incremental Signal Monitoring chain that package relocation introduced no behavioral regression.
- User value: A new developer can open `src/power_web_os/application` without seeing the old flat Radar namespace as the apparent architecture.
- Problem statement: Even after individual migrations, old root-level Radar files can linger as real behavior owners or undocumented compatibility leftovers. The project needs a final closure slice that makes package-owned Radar architecture visibly true in the filesystem.
- Scope:
  - Move all remaining Radar behavior from power_web_os.application root into radar lifecycle, configuration, preflight and candidate source packages.
  - Keep legacy paths as thin documented identity-compatible shims and protect them with architecture tests.
  - Add machine-readable semantic trace comparison and live namespace-closure validation.
  - Run a fresh blind candidate benchmark, a fresh initial signal quality run and a fresh incremental signal run, then verify persistence after API/worker restart.
  - Diagnose every mismatch and either fix a migration defect within the bounded loop or create a blocking corrective slice.
- Out of scope:
  - No intentional candidate-discovery or Signal Monitoring algorithm redesign inside this migration slice.
  - No removal of compatibility paths before a major-version sunset.
  - No public quality claim from one live chain.
  - Algorithmic defects discovered by live validation are handled by an explicit corrective slice and keep this slice In Progress.
- Implementation notes:
  - Root shims are at most 8 lines, contain Source of truth and only explicit re-exports.
  - radar/compatibility.py is the canonical legacy-path registry.
  - Production and behavior tests use package-owned imports.
  - Compare normalized traces semantically, ignoring IDs, timestamps and natural provider text drift.
  - Autofix is bounded to five cycles and cannot weaken recall, control, provenance, trace or dedupe thresholds.
  - Current live blocker and evidence are recorded in docs/radar/pipelines/validation/0.7.6.4.19/BLOCKING_RCA.md; corrective slice 0.7.6.4.19.1 must pass before the full chain is repeated.
- Tests:
  - Full pytest plus backend architecture/package contracts and static checks.
  - Docker rebuild before live evidence.
  - Fresh blind candidate benchmark with post-run baseline evaluation and normalized trace comparison to radar-run-3bbf9c0f-330e-4468-8901-966a751234a8.
  - Fresh initial and incremental signal quality runs compared with signal-run-010ef75d-c626-44e3-a025-56c95522c1a8 and signal-run-df00b3b8-267c-4091-a4dd-8167434e2cf3.
  - API/worker restart round-trip and machine-generated validation.json PASS.
  - Roadmap check and git diff --check.
- Docs:
  - Update root namespace debt inventory, backend and pipeline architecture, package READMEs, Developer Guide, compatibility ADR and Radar validation skills.
  - Store final machine validation under docs/radar/pipelines/validation/0.7.6.4.19.
  - Keep BLOCKING_RCA.md until final PASS documents how the failed chain was corrected.
- Demo impact:
  - None intended.
- Acceptance criteria:
  - No root-level Radar file owns business behavior; every compatibility shim is thin, documented and identity-tested.
  - Full tests and architecture gates pass and Docker is rebuilt.
  - Fresh blind discovery has strict and visible recall at least 0.8889, at least 8 of 9 legal baseline targets, at least 54 visible and 72 retained leads, zero duplicate IDs, provenance gaps and unexplained drops.
  - Fresh signal scope has exactly 6 candidates with at least 3 accepted and 3 review-needed, 2 criteria and 12 pairs.
  - Initial signal run finds 4/4 positive controls, rejects at least 2 negative controls, retains an unknown-date review item and has zero source-binding, receipt, false-negative or budget violations.
  - Incremental run republishes zero old confirmed/review evidence and advances only successful per-lane watermarks.
  - Candidate and signal traces contain no behavior regression against accepted baselines.
  - Reports remain readable after API/worker restart and machine validation is PASS.
  - Any failed mandatory live criterion keeps the slice In Progress.
- Risks:
  - Hidden callers may use legacy imports; preserve identity-compatible shims.
  - Provider drift may hide regressions; use semantic trace comparison plus fixed quality thresholds.
  - A migration-only slice can expose algorithmic defects; do not hide them or change algorithms after five autofix cycles, create a blocking corrective slice instead.
- Behavior change: false
- Blocking live RCA: Resolved. Corrective slice 0.7.6.4.19.1 preserved the original strict acceptance failure, implemented criterion-owned search obligations and cross-criterion evidence reconciliation, and passed the approved reproducibility contour. The final parent validation reused the fresh blind candidate run and accepted initial/incremental signal runs and returned PASS for every NS-* requirement. Historical RCA remains at docs/radar/pipelines/validation/0.7.6.4.19/BLOCKING_RCA.md.
- Closeout: Machine validation PASS. Candidate live radar-run-b03fac86-7307-448f-8deb-c1ea1794956c: blind mode, hints disabled, strict recall 1.0, visible recall 0.8889, 8/9 legal baseline targets, 91 visible candidates, 110 retained upstream leads, zero duplicate IDs, provenance gaps and unexplained drops; the remaining Tobolsk miss is explicitly not_generated. Initial signal run signal-run-8eb6d673-a6f6-417a-8519-8cc50e7e94f8: 6 candidates (3 accepted, 3 review-needed), 12 pairs, positives 4/4, negatives 4/4, unknown-date 1/1, zero receipt gaps, false not_observed, rejected observed, score-zero confirmed or source-policy violations. Incremental signal-run-47e29772-8cbf-421e-8072-7c2d951ba611: 67 previous source keys, zero republished evidence, zero receipt gaps and zero illegal watermark advances. Candidate trace preserved phase order with no behavior regressions; provider trace count drift 172 to 190 is classified as expected provider drift within all quality thresholds. API/worker restart preserved reports. Full pytest passed with one expected skip; frontend production build passed. Search-result reproducibility beyond the approved contour is deferred to 0.7.6.4.19.2; independent-provider fallback remains conditional in 0.7.6.4.19.3.
- Pipeline: radar-cross-pipeline
- Validation report: docs/radar/pipelines/validation/0.7.6.4.19/validation.json

### Slice 0.7.6.4.19.1: Signal monitoring live benchmark reachability and cross-criterion evidence reconciliation

- Status: Done
- Goal: Restore reproducible live Signal Monitoring quality proof without benchmark-control leakage or source-policy weakening.
- User value: A user receives signal results that are both recall-first and defensible: relevant events found under one query are not lost for another criterion, while identity-only sources never masquerade as fresh evidence.
- Problem statement: Fresh live run signal-run-55a9cfb4-b0f1-48ee-8aef-df20a236266f reached 6 candidates and 12 pairs with complete receipts, but found only 2 of 4 positive controls and 1 negative control; it also confirmed one signal from an identity_only XLSX source. The previous accepted quality benchmark therefore is not reproducible enough to prove 0.7.6.4.19.
- Scope:
  - Reconcile evidence found for one candidate across all configured criteria through the existing entity, criterion, temporal and source validation rules; never auto-promote by keyword alone.
  - Preserve the originating task/criterion and add an auditable secondary criterion-validation decision when evidence is reused.
  - Ensure bounded query planning covers distinct S1/S2 evidence obligations instead of stopping after one generic result.
  - Enforce that identity_only and registry capabilities cannot confirm a fresh signal; keep relevant items as review evidence or reclassify capability only from product-safe content evidence.
  - Make positive-control matching URL-canonical and event-aware through a control set frozen before live execution, without passing controls into planning.
  - Make at least two negative controls reproducibly exercise live retrieval and temporal/binding rejection without production hardcodes.
  - Run two independently initialized live quality searches, then one normal incremental run, and compare all three with accepted baselines and the failed-run RCA.
- Out of scope: No candidate rediscovery or candidate-universe expansion; no benchmark company, URL or event hardcodes in production; no weakening of negative, provenance, temporal, source-binding or incremental-dedupe thresholds; no UI redesign or scheduling changes. Exact-URL provider stability beyond the approved v2 4/4 plus 3/4 aggregate contour is deferred to 0.7.6.4.19.2 and conditional 0.7.6.4.19.3.
- Implementation notes: The original v1 manifest SHA 9dfab1ee... and machine FAIL are preserved. After the five-cycle limit, the user approved acceptance amendment v2: each independent initial run must find at least 3/4 positives, one must find 4/4, their union must find 4/4, and the only accepted miss is explicit provider_search_drift. Controls, accepted URLs, dates and every semantic integrity requirement remain unchanged. Incremental C still must prove B-series watermarks and dedupe. Slice 0.7.6.4.19 remains In Progress until the complete chain is repeated.
- Tests: Recorded tests cover cross-criterion validation, identity-only rejection, task-scoped refs, query obligations and canonical URLs. Validator tests prove 4/4 plus 3/4 aggregate acceptance and reject two runs missing the same control. Live A signal-run-8eb6d673-a6f6-417a-8519-8cc50e7e94f8 and B signal-run-6754eba6-a43a-4594-8236-d7ed60f6d2c5 are independent; C must run incrementally from B5, then reports must survive API/worker restart. Full Signal Monitoring, architecture, persistence, API/jobs, documentation, roadmap and static regression remain mandatory.
- Docs: Keep the original v1 acceptance/freeze/validation artifacts as immutable FAIL evidence. Track the reviewed v2 amendment, new frozen SHA, all A/B/C run ids, provider_search_drift classification and cross-run matrix. Finalize Signal Monitoring AS IS Markdown/PDF only after incremental C, restart verification and machine PASS. Corrective stability work is tracked in 0.7.6.4.19.2 and conditional 0.7.6.4.19.3.
- Demo impact: No new demo surface. The existing Signal Monitoring quality run becomes reproducible and its evidence classifications remain visible through current reports.
- Acceptance criteria: The v1 two-times-4/4 criterion remains archived as FAIL. Under the explicitly approved v2 DoD, A and B each contain 6 evidence-complete candidates, 3 accepted and 3 review-needed, 2 criteria and 12 pairs; each finds at least 3/4 positive controls; at least one finds 4/4; their union finds 4/4; only the frozen Khimprom control may be a provider_search_drift miss; each independently passes at least 2 negative and 1 unknown-date controls with zero false positives, identity confirmations, receipt gaps, orphan decisions, false not_observed, score-zero confirmed or required-budget limits. C uses B5 history, republishes zero prior confirmed/review evidence and advances only successful watermarks. All reports survive restart, validation is PASS, TO BE is Implemented and AS IS is reconciled before Done.
- Risks: The accepted v2 DoD proves functional correctness but not exact-URL search stability. This limitation must remain explicit in AS IS and validation. 0.7.6.4.19.2 evaluates OpenRouter search mechanisms after the basic Power Web foundation; 0.7.6.4.19.3 is activated only if an independent provider is justified.
- Acceptance manifest: docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.19.1.acceptance.json
- Behavior change: true
- Closeout: Approved v2 PASS. Original v1 SHA 9dfab1ee6a2a449109d35b8cf53b097cae3a4b48797bfedfb4c7214df2d6d82e remains archived as FAIL. V2 SHA ab149a4f8d56a0565582a2bf2c1a786eb852bec0c4d60bb7d9b771c1d04963d2. Initial A signal-run-8eb6d673-a6f6-417a-8519-8cc50e7e94f8: positives 4/4, negatives 4/4, unknown 1/1. Initial B signal-run-6754eba6-a43a-4594-8236-d7ed60f6d2c5: positives 3/4, negatives 4/4, unknown 1/1; one accepted provider_search_drift. Incremental C signal-run-47e29772-8cbf-421e-8072-7c2d951ba611: 67 previous source keys, 2 confirmed and 3 review duplicates suppressed, 0 republished, 0 receipt gaps, 0 illegal watermark advances. API/worker restart preserved all report hashes. Full pytest and frontend build passed. Search stability follow-ups: 0.7.6.4.19.2 Backlog and 0.7.6.4.19.3 conditional Blocked.
- Pipeline: signal-monitoring
- Validation policy: A single successful initial live run is insufficient. Controls must be frozen before execution and pass in two independently initialized initial runs. The incremental run is a separate dedupe/watermark proof and cannot substitute for initial-search reproducibility.
- Validation report: docs/radar/pipelines/signal-monitoring/validation/0.7.6.4.19.1/validation.json

### Slice 0.7.6.5.1: Configurable candidate filtering policy and reversible public projection

- Status: Backlog
- Goal: Add a configurable, typed candidate-filtering policy to each Radar so users can choose how broadly source-backed upstream leads are shown without changing search depth, deleting the raw candidate universe, or weakening strict product acceptance.
- User value: A user can run candidate discovery once and choose a broad, balanced, or strict candidate view appropriate to the Radar use case. Broad mode preserves recall and exposes review-needed leads; strict mode keeps the working list focused; every hidden candidate remains traceable and can be recovered without another provider run.
- Problem statement: Candidate discovery is now intentionally recall-first and a blind run can return many provenance-backed leads. That is correct upstream behavior, but different Radars need different working-list precision. A single implicit projection rule cannot serve exploratory market mapping, normal ABM review, and high-confidence account selection. If filtering is implemented by tightening retrieval or deleting candidate-universe rows, the project will regress to false-negative-heavy behavior. If it is implemented as an untyped task_context flag, historical runs and UI counts will become ambiguous.
- Scope:
  - Add a frozen typed value object `CandidateFilteringPolicy` and enum-like mode contract with `broad`, `balanced`, and `strict` modes.
  - Persist the selected mode in Radar settings and snapshot the effective policy name, version, and resolved thresholds into every candidate-discovery run artifact/metadata.
  - Keep `candidate_universe` as the complete provenance-backed upstream truth. Apply filtering only when projecting the user-visible candidate surface.
  - Define deterministic mode semantics:
  - `broad`: show every unique provenance-backed legal candidate, including review-needed leads;
  - `balanced`: show accepted candidates plus review-needed candidates supported by an official/registry source or by at least two independent sources with medium/high upstream confidence;
  - `strict`: show accepted product candidates only.
  - Preserve strict product acceptance as an independent decision. Filtering mode may hide or show review-needed rows but must not promote them to `product_candidate`.
  - Add a policy decision record for every retained upstream lead: visible/hidden result, mode, policy version, matched rule, and product-safe reason.
  - Add backend projection/preview support so an existing completed run can report broad/balanced/strict counts and candidate ids without repeating retrieval, extraction, registry calls, or OpenRouter calls.
  - Add Radar settings UI for candidate filtering with clear RU/EN labels, concise consequences, and preview counts from the latest compatible completed run.
  - Show both `found upstream` and `visible under current filter` counts so strict mode cannot be mistaken for poor discovery.
  - Keep historical runs immutable: changing Radar settings affects future runs; previewing another mode over an old artifact does not rewrite that run.
- Out of scope:
  - No change to search depth, query planning, expansion budgets, provider model selection, retries, or source routing.
  - No deletion of filtered candidates from candidate_universe, artifacts, diagnostics, or acceptance ledgers.
  - No automatic product-acceptance promotion based only on a looser display mode.
  - No coupling between candidate filtering and signal-monitoring scope; monitoring input selection remains an explicit separate contract.
  - No arbitrary per-field advanced threshold editor in the first slice; the public contract is three versioned presets.
  - No public quality claim from one live run.
- Implementation notes:
  - Put the policy owner in a package-owned candidate-discovery module such as `radar/candidate_discovery/universe/filtering.py`; do not add root-level `live_radar_*` behavior.
  - `CandidateDiscoveryUpstreamAdmissionPolicy` remains recall-first and must not depend on filtering mode. `CandidateDiscoveryPublicSurfaceProjector` consumes the policy after reconciliation/evidence enrichment. `CandidateDiscoveryProductAcceptancePromoter` remains the owner of strict acceptance and must not infer acceptance from display mode.
  - Prefer an explicit result object such as `CandidateFilteringDecision` over booleans. It should carry candidate id, visibility, mode, reason code, evidence summary, and policy version.
  - Use stable generic reason codes, for example `visible_product_candidate`, `visible_source_backed_review`, `hidden_insufficient_independent_evidence`, `hidden_low_upstream_confidence`, and `hidden_not_product_accepted_in_strict_mode`.
  - The default mode for existing Radars and compatibility callers is `broad`, preserving the current recall-first public behavior.
  - Policy presets are domain configuration, not benchmark profiles and not execution-budget profiles. Do not encode them in `benchmark_smoke`, `blind_benchmark`, or provider model-profile configuration.
  - The same artifact projected under the three modes must satisfy strict subset monotonicity: `strict candidates <= balanced candidates <= broad candidates` by candidate id.
  - Add an ADR for the separation between discovery breadth, public filtering, strict product acceptance, and signal-monitoring input scope.
  - Schedule after `0.7.6.4.19`; it must not delay `0.7.6.4.18.2`, `0.7.6.4.18.3`, or root namespace closure.
- Tests:
  - Unit tests for each deterministic policy rule and reason code, including official source, registry evidence, two independent open-web sources, one weak source, invalid/unresolved provenance, and already accepted candidates.
  - Property/contract test on one fixed artifact: strict candidate ids are a subset of balanced ids, balanced ids are a subset of broad ids, and candidate_universe content/count/checksum is unchanged.
  - Regression test: accepted product candidate ids and accepted count are identical in all three modes.
  - Regression test: every visible row remains duplicate-safe and evidence-complete; duplicate ids and empty provenance counts stay zero.
  - Regression test: every hidden provenance-backed lead has a filtering decision and product-safe reason; unexplained drops stay zero.
  - API tests for Radar settings persistence, effective run-policy snapshot, historical immutability, and no-provider re-projection/preview.
  - Frontend tests for mode selection, found-vs-visible counters, preview counts, saved settings, RU/EN copy, and explicit distinction between review-needed and accepted candidates.
  - Signal-monitoring isolation test proving filtering mode does not silently redefine the monitored candidate set.
  - Required fast gates: candidate-discovery policy/public-surface/API tests, backend architecture/package contracts, frontend build and targeted UI tests, roadmap check, and `git diff --check`.
  - Final Docker gate: rebuild the stack, use a completed evidence-rich blind artifact to compare all three modes without provider calls, then run one bounded candidate-discovery smoke proving the configured policy snapshot is persisted.
- Docs:
  - Add an ADR documenting four separate concepts: search depth, upstream retention, public candidate filtering, and strict product acceptance.
  - Update Radar backend architecture and candidate-discovery execution handbook with policy ownership and dependency rules.
  - Update candidate-discovery README with the extension path and rule that upstream admission cannot depend on display filtering.
  - Update Developer Guide and user/demo documentation with the three modes, found-vs-visible counters, historical run immutability, and preview-without-rerun behavior.
  - Update AS IS Markdown/PDF only if implemented pipeline projection behavior changes.
- Demo impact: Radar settings gain a candidate-filtering control. On an evidence-rich blind result the demo can show, for example, a broad list of all reviewable leads, a smaller balanced working list, and a strict accepted-only list while the same upstream-found count remains visible. Switching the preview must not spend provider budget.
- Acceptance criteria:
  - Existing Radars default to `broad`; their current provenance-backed visible candidate behavior does not narrow after migration.
  - The same completed artifact can be evaluated under `broad`, `balanced`, and `strict` without executing any provider call.
  - Candidate-id sets are monotonic: `strict` is a subset of `balanced`, and `balanced` is a subset of `broad`.
  - Candidate universe count/content is identical across modes; filtering never deletes upstream evidence.
  - Accepted product candidate ids/counts are identical across modes; display policy never weakens strict acceptance.
  - Every visible candidate has resolvable provenance, and public output contains zero duplicate candidate ids.
  - Every hidden provenance-backed lead has an explicit filtering reason; unexplained-drop count is zero.
  - Run metadata/API/UI expose effective filtering mode and policy version, and historical run interpretation does not change when Radar settings are edited later.
  - UI simultaneously shows upstream-found count, visible count, accepted count, and review-needed count.
  - Changing or previewing filtering mode does not rerun candidate discovery and does not consume OpenRouter, registry, verification, or signal-monitoring budget.
  - Filtering mode does not silently alter the signal-monitoring input set.
  - Docker/UI DoD proves all three modes on one real persisted artifact and a bounded new run persists the configured mode.
  - The slice cannot be marked Done from unit tests alone; closeout must include the tested run/artifact id and the broad/balanced/strict metric table.
- Risks:
  - Users may interpret a strict visible count as low recall. Mitigate by always displaying upstream-found and hidden-by-filter counts.
  - Preset thresholds can drift if spread across UI, API, and execution code. Mitigate with one versioned backend policy owner and API-delivered descriptions/preview counts.
  - Re-projecting historical artifacts could be mistaken for rewriting history. Mitigate by keeping stored effective policy immutable and labeling alternative-mode results as preview.
  - Balanced thresholds may need later tuning. Keep reason codes and evaluation counters explicit so tuning is evidence-based and version the policy when semantics change.
  - Signal monitoring may need its own accepted-only vs accepted-plus-review scope. Keep that as a separate future setting rather than deriving it from candidate display filtering.

### Slice 0.7.6.6: Power Web discovery pipeline

- Status: Backlog
- Goal: Build the third independent Radar pipeline that discovers buying-committee people, roles, external influencers and evidence-backed relationships for already selected accounts, then hands a reviewable Power Web to Access Planner.
- User value: ABM teams move from knowing which companies matter and what signals they show to understanding who influences the purchase, which roles are missing and which explainable access routes are available.
- Problem statement: Candidate discovery and signal monitoring exist, but Power Web Lite only renders roles and people already supplied to it. There is no runtime for people search, anonymous-profile resolution, current-employment validation, influence mapping or evidence-complete Access Planner handoff.
- Scope:
  - Create a package-owned power-web-discovery pipeline with independent planning, retrieval, extraction, identity resolution, role validation, relationship inference, budgets, checkpoints, persistence, API/jobs, evaluation and UI.
  - Establish first-class versioned product, semantic buying-role and access-playbook configuration before account handoff.
  - Use immutable handoff from completed candidate-discovery runs and optional signal-monitoring context without importing either pipeline internals.
  - Treat HH.ru public web as a mandatory people-search lane through a compliant connector and explicit capability contract; licensed HH API remains deferred.
  - Retain broad source-backed profiles and identity hypotheses while keeping confirmed identity merges strict, explainable and reversible.
  - Produce an evidence-complete graph and stable Access Planner handoff through slices 0.7.6.6.0-0.7.6.6.10.
- Out of scope:
  - No automated outreach, private-data scraping or CRM replacement.
  - No company rediscovery inside Power Web discovery.
  - No authentication, CAPTCHA, robots or provider-terms bypass.
  - Cross-photo biometric identification is not part of the core pipeline.
- Implementation notes:
  - Normal extension path is src/power_web_os/application/radar/power_web_discovery; root-level behavior files are forbidden.
  - Preserve API/CLI/jobs -> application -> domain/ports -> persistence/integrations dependency direction.
  - PowerWebRole remains a compatibility/read-model projection; richer profile, identity, employment, relationship and evidence contracts become source of truth.
  - Every behavior-changing child follows AS IS -> RCA/fixtures -> TO BE/manifest -> tests/live evidence -> validation PASS -> finalized AS IS.
  - Start after 0.7.6.4.18.3.1.1 and 0.7.6.4.19; candidate filtering 0.7.6.5.1 is not a prerequisite.
- Tests:
  - Each child has config/preflight, recorded fixtures, malformed-output fixtures and architecture tests before live runs.
  - Blind benchmark measures role/person recall, identity-link quality, current employment, relationship provenance, missing-role diagnostics and Access Planner readiness.
  - No runtime/UI child closes from unit tests alone when persisted or browser evidence is required.
- Docs:
  - Maintain Power Web discovery AS IS Markdown/PDF and slice-specific TO BE Markdown/PDF, manifests and validation reports.
  - Add ADRs for pipeline boundaries, identity resolution, public-person-data governance, source capabilities and Access Planner handoff.
  - Keep architecture, Developer Guide, User Guide, demo runbook and pipeline registry synchronized.
- Demo impact: Demonstrate the complete chain: discover account, monitor signals, discover/review its Power Web and generate explainable access routes.
- Acceptance criteria: Hard DoD; the slice cannot be marked Done until all conditions pass:
- Power Web discovery has its own run id, lineage, model profile, budgets, artifact and diagnostics.
- HH.ru is an actually executed auditable lane, not documentation-only intent.
- Every visible person, role and edge has provenance or an explicit review/gap reason.
- Anonymous profiles are retained; weak evidence may retain a hypothesis but cannot silently confirm a merge.
- Current/former employment is distinguished and title alone does not prove influence.
- Blind controls never enter planning or production hardcodes; every miss has a path-level reason.
- Reviewed graph reaches Access Planner without manual technical translation.
- All mandatory child validations are PASS and final AS IS matches implementation.
- Risks:
  - People data and images create privacy/legal/ToS risk; use capability cards, minimization, product-safe evidence and human review.
  - False identity fusion is worse than retained duplicate hypotheses; merge confirmation must be stricter than retention.
  - HH/professional-network access may require licensing; validate capability before dependency.
  - Role-scoped plans, bounded expansion and independent budgets must prevent an unbounded OSINT crawler.
- Behavior change: false
- Pipeline: power-web-discovery

### Slice 0.7.6.6.0: Power Web discovery AS IS, benchmark contract and architecture

- Status: Done
- Goal: Define the current gap, target architecture, benchmark format, source governance and hard acceptance process before production implementation.
- User value: The team agrees what a trustworthy Power Web result means before spending provider budget or encoding unsafe identity assumptions.
- Problem statement: There is no people-discovery AS IS, identity contract, HH capability proof, benchmark schema or accepted boundary between broad discovery and strict identity confirmation.
- Scope:
  - Document current Account, PowerWebRole, PowerWebBoard and Access Planner behavior and all missing search/runtime capabilities.
  - Create full TO BE Markdown/PDF and ADR for the third pipeline.
  - Define RoleDemand, PersonProfile, PersonIdentity, IdentityHypothesis, EmploymentClaim, RelationshipClaim, InfluenceHypothesis, SourceEvidence, PowerWebGap and PowerWebArtifact.
  - Define guided/blind benchmark schema for accounts, roles, people, aliases, same/different-person controls, current/former employment, relationships, sources and as-of dates.
  - Create source capability/compliance matrix and perform an early HH.ru feasibility probe.
  - Define privacy, retention, image, human-review and no-automated-outreach rules.
- Out of scope:
  - No production retrieval, merging, persistence, API, jobs or UI.
  - No face recognition implementation.
  - No quality claim before the user benchmark is accepted.
- Implementation notes:
  - Derive TO BE from current contracts and gap analysis, not from a desired module tree alone.
  - Blind baseline stays in validation fixtures only.
  - Exact/near-duplicate image fingerprints may be non-biometric evidence; cross-photo facial similarity remains separately gated.
- Tests:
  - Documentation contract checks AS IS, TO BE, PDF, ADR and traceability.
  - Benchmark-schema tests reject missing provenance, ambiguous expected identity and planner-visible blind hints.
  - Architecture tests protect package isolation; connector probe stores no secrets/private payloads.
- Docs:
  - Create initial Power Web AS IS and RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.0 Markdown/PDF.
  - Add boundary/governance ADRs and pipeline registry entry.
- Demo impact: Publish the agreed target flow and benchmark interpretation; no runtime yet.
- Acceptance criteria: Hard DoD; the slice cannot be marked Done until all conditions pass:
- AS IS honestly states that Power Web Lite does not discover people.
- TO BE defines roles, context, lanes, budgets, checkpoints, evidence/identity states, graph and handoff.
- User benchmark is normalized into the accepted schema or the slice remains open.
- Blind controls are unavailable to planning by contract.
- HH integration feasibility and compliant route are proven; absence blocks implementation rather than silently omitting HH.
- Broad retention plus strict confirmed merge and biometric/outreach boundaries are explicit and testable.
- Documentation and architecture gates pass.
- Risks:
  - Benchmark truth can be uncertain; require source-backed controls and unknown states.
  - Provider assumptions may be wrong; verify before coding.
  - Keep the first TO BE architectural and delegate behavior deltas to children.
- Acceptance manifest: docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.0.acceptance.json
- Behavior change: false
- Implementation evidence: Implemented provider-neutral Power Web contracts, AS IS/TO BE Markdown and visually verified PDFs, source capability matrix, bounded HH public-web probe, privacy/governance ADRs, benchmark schema and validation tooling. User workbook sibur_priority_contacts.xlsx normalized without private contacts into accepted sibur-priority-power-web@1.0.0: 10 profiles including 1 anonymous HH profile, 8 identity pairs (4 same-person and 4 different-person), current/former/unknown employment controls and 4 relationship controls. Canonical benchmark SHA-256 b3c851e1bf56a3ee6808267e2619f678295843cc3fa3bacd16a19f3f28d4114b; source workbook SHA-256 a1281d4372d2fcc9a0df8107d28c504a4209ed590a382036cc6a76b97a8fc476. Blind leakage 0, private contact retention false, HH API calls 0, machine validation 11/11 PASS, full pytest PASS with one existing skip.
- Pipeline: power-web-discovery
- Validation report: docs/radar/pipelines/power-web-discovery/validation/0.7.6.6.0/validation.json

### Slice 0.7.6.6.0.1: Product catalog, semantic buying roles and Playbook foundation

- Status: Done
- Goal: Create a versioned product and semantic buying-role configuration that owns what Power Web must discover before account-specific people-search planning begins.
- User value: ABM teams can define what they sell, which decision-making functions matter for that product and why, without hardcoding account-specific job titles or asking an LLM to invent the buying committee.
- Problem statement: The production Playbook currently owns only routes, channels, assets and review rules. The product, its value context and the semantic buying-role policy that must precede people discovery have no persisted owner, while RoleDemand exists without an authoritative configuration source.
- Scope:
  - Add versioned ProductDefinition with product name, short description, customer problem, value context, use context, lifecycle state and immutable version identity.
  - Add versioned BuyingRolePolicy composed of semantic role definitions: stable role code, business responsibility, decision rights, required/optional state, priority, account scope, reason, expected evidence and exclusions.
  - Separate ProductDefinition, BuyingRolePolicy and AccessPlaybook ownership while keeping a versioned SalesPlaybookDefinition that references their compatible versions.
  - Preserve current Playbook route/channel/asset/review semantics as AccessPlaybook and keep Playbook Analysis compatible.
  - Add Product/Playbook persistence, API and a backend-backed Playbook UI with distinct Product, Buying roles and Access rules views.
  - Define the future AccountRoleTitleHypothesis contract so account-specific title variants can be proposed later without mutating semantic role requirements.
  - Create a versioned benchmark amendment: planning context references the accepted SmartDiagnostics product/role-policy version, while people, URLs and expected answers remain evaluator-only blind controls.
- Out of scope:
  - No people search, provider calls, profile extraction, identity resolution or employment/influence decisions.
  - No LLM generation of account-specific job-title hypotheses in this slice; execution belongs to 0.7.6.6.2 after deterministic role demand exists.
  - No Access Planner scoring or route recommendation algorithm change.
  - No multi-product opportunity composition; one active product/playbook context per Power Web run is sufficient for the first perimeter.
- Implementation notes:
  - Product and sales configuration are first-class shared business configuration, not provider or Power Web artifact fields.
  - Semantic roles describe functions and decision responsibility, not titles such as CIO, chief engineer or procurement director.
  - Stable semantic role IDs survive account-specific naming; generated title hypotheses may expand search terms but cannot add, remove, reprioritize or confirm required roles.
  - 0.7.6.6.1 must consume an immutable ProductDefinition and BuyingRolePolicy snapshot instead of a universal hardcoded role list.
  - Existing Playbook and Access Planner contracts remain compatibility projections until their later migration.
  - Use normal API -> application -> domain/ports -> persistence dependency direction; browser-local overrides cannot be the source of truth.
- Tests:
  - Product, buying-role policy and SalesPlaybook contract validation, version immutability and invalid/dangling role-reference tests.
  - API/persistence round-trip through restart, optimistic version conflict and archive behavior tests.
  - Tests proving required semantic roles cannot be changed by an AccountRoleTitleHypothesis payload.
  - Existing Playbook Analysis, Power Web Board and Access Planner regression tests.
  - Benchmark amendment/freeze tests with blind leakage 0 and no people or source URLs in product configuration.
  - Frontend build and Playwright tests for product editing, semantic role editing, access-rule separation, loading/error states, RU/EN and 1280x720/1366x768 layouts.
  - Fail-on-call proof that no candidate, signal, people-search or LLM provider is invoked.
- Docs:
  - Create slice TO BE Markdown/PDF, acceptance manifest and machine validation report.
  - Update Power Web Discovery AS IS after validation and add an ADR separating product, semantic buying roles and access rules.
  - Update system architecture, package ownership guidance, Developer Guide, User Guide, demo runbook and benchmark amendment record.
- Demo impact: The Playbook workspace becomes a real backend-backed configurator: users select SmartDiagnostics, inspect its description, edit semantic buying roles and separately inspect access rules. Account-specific titles and people are explicitly shown as future run output, not configuration.
- Acceptance criteria: Hard DoD; the slice cannot be marked Done until all conditions pass:
- A product can be created, edited through a new immutable version, activated and archived.
- Every active product has a valid versioned BuyingRolePolicy with at least one required semantic role.
- Every role has a stable code, business responsibility, decision rights, required/optional state, priority, scope, reason, expected evidence and exclusions.
- Product configuration does not require account-specific job titles, person names, benchmark URLs or blind controls.
- Access rules reference semantic role IDs and cannot contain dangling role references.
- The UI clearly separates Product, Buying roles and Access rules and uses persisted backend state rather than silent local overrides.
- Product and role settings survive UI -> API -> DB -> API restart -> UI without loss; historical versions remain immutable.
- SmartDiagnostics has an accepted working product and semantic-role configuration suitable for the supplied SIBUR benchmark.
- AccountRoleTitleHypothesis cannot add, remove, reprioritize or confirm a required semantic role.
- The benchmark amendment preserves blind leakage 0 and does not change frozen identity/employment/relationship answers silently.
- Existing Playbook Analysis, Power Web Board and Access Planner behavior remains green.
- Provider calls and new Radar/Power Web runs equal 0.
- Backend, persistence, API, architecture, frontend build and Playwright gates pass.
- Validation report has validation_status=PASS; TO BE is marked Implemented and Power Web Discovery AS IS is reconciled.
- Only after full PASS may 0.7.6.6.1 become Ready.
- Risks:
  - Semantic roles may collapse back into title lists; contracts and UI must require responsibility and decision-rights language instead.
  - A global taxonomy may not fit every product; roles are product-policy owned and versioned, with no universal mandatory list.
  - Product settings can overlap Radar qualification/signals; this slice links product identity but does not migrate existing Radar semantics.
  - Replacing the artifact-only Playbook screen can regress route analysis; preserve it as a separate Access rules/account preview surface.
- Acceptance manifest: docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.0.1.acceptance.json
- Behavior change: true
- Dependencies: 0.7.6.6.0 is Done; this slice blocks 0.7.6.6.1.
- Pipeline: power-web-discovery
- Validation report: docs/radar/pipelines/power-web-discovery/validation/0.7.6.6.0.1/validation.json

### Slice 0.7.6.6.1: Power Web account handoff and buying-committee role demand

- Status: Done
- Goal: Create a versioned Radar-to-product Power Web policy and an immutable multi-product account handoff that compiles explainable RoleDemand sets without rerunning candidate discovery or signal monitoring.
- User value: The system knows which internal and external roles must be found for a product/account before searching for people.
- Problem statement: Radars discover a reusable account universe, while products own different semantic buying roles. The system currently has no authoritative many-to-many Radar/product binding, no immutable handoff of exact product versions, and no run contract that can later support initial, incremental and full-rediscovery Power Web work without fragmenting one account graph by product.
- Scope:
  - Add a versioned RadarPowerWebPolicy to the existing Radar settings, persisted independently from candidate-discovery and signal-monitoring definitions.
  - Bind each Radar to zero, one or many product IDs; one product may be used by many Radars. Roles remain owned by the product and are never copied into Radar settings.
  - Resolve active published product and buying-role-policy versions at handoff and persist their exact immutable snapshots.
  - Allow a Power Web handoff to use all Radar-bound products or an explicit subset; reject products not bound to that Radar.
  - Create one account-centric preparation/run context for all selected products, with a separate ProductRoleDemandSet per product.
  - Compile RoleDemand from product version, role code, responsibility, requiredness, scope and effective priority; do not silently merge similar roles across products.
  - Snapshot candidate identity, product-safe provenance, source candidate run, Radar policy version, selected products, optional signal context, as_of and lineage.
  - Mark the first handoff as run_kind=initial with previous_power_web_run_id=null.
  - Persist and expose a pre-search brief grouped by product; this slice performs no people retrieval.
- Out of scope:
  - People-search provider calls, profile extraction, identity resolution, employment validation and graph construction.
  - Recurring scheduler or automatic cadence execution.
  - Per-product, per-account or per-source-lane cadence overrides.
  - Merging equivalent roles across products.
  - Rerunning candidate discovery or signal monitoring during handoff.
  - Access Playbook or access-route constraints.
- Implementation notes:
  - Product owns product meaning and semantic roles; Radar owns which products apply to its discovered accounts; each Power Web run owns an immutable effective snapshot.
  - Radar settings expose product bindings, while backend storage versions the Power Web policy separately so unrelated Radar edits do not silently change it.
  - Version resolution is explicit at handoff with basis=active_at_handoff. Historical runs never follow later product activation changes.
  - A run may cover all bound products or a validated subset. One future person may satisfy roles for several products, but the demands remain product-scoped and independently explainable.
  - Signal observations are optional context only and cannot add, remove or reprioritize semantic roles.
  - The scheduler is intentionally deferred to 0.7.6.6.7.1 after incremental semantics and persisted runtime exist.
- Tests:
  - One Radar binds two products; one product binds to two Radars without copied configuration.
  - RadarPowerWebPolicy survives API/DB/restart round-trip and has immutable versions.
  - Handoff resolves and snapshots exact active product and role-policy versions.
  - All-products and valid-subset handoffs work; an unbound product is rejected.
  - Archived, unpublished or missing products produce explicit preflight blockers.
  - A later product publication does not mutate an old handoff; a new handoff resolves the new active version.
  - Similar roles from two products remain two product-scoped RoleDemand records.
  - Wrong Radar, unfinished/source-less candidate run and invalid signal lineage are rejected explicitly.
  - Fail-on-call providers prove zero candidate, signal and people-search calls.
  - Docker/UI test verifies persisted policy, grouped pre-search brief and restart round-trip.
- Docs:
  - Create slice TO BE/PDF, manifest and validation report.
  - Document handoff and role-taxonomy ownership; finalize AS IS.
- Demo impact: Seed a Radar bound to at least two published products. From one evidence-complete candidate, create an initial handoff for all products and another for a subset. Show grouped role-demand counts, exact version lineage, readiness and blockers without starting people search.
- Acceptance criteria:
  - Radar-to-product binding is explicit, versioned and many-to-many.
  - Editing bindings creates zero candidate-discovery and signal-monitoring runs.
  - A handoff can select all bound products or a subset, but never an unbound product.
  - Exact product and role-policy versions are snapshotted with source candidate lineage and as_of.
  - Every RoleDemand references exactly one product and one semantic role.
  - Similar roles across products are not silently merged.
  - Historical handoffs remain unchanged after product activation or Radar-policy edits.
  - Missing, unpublished, archived or incompatible inputs produce explicit blockers.
  - Persisted handoff has run_kind=initial and no hidden recurring schedule.
  - RoleDemand has no AccessPlaybook, expected-evidence, title or query dependency.
  - Provider calls and new candidate/signal runs equal zero.
  - UI -> API -> DB -> restart -> UI round-trip passes.
  - Power Web evidence loop and validation report have PASS before Done.
- Risks: Multi-product fan-out can multiply future retrieval work; product-version drift can make runs incomparable; role overlap can cause duplicate future tasks; and optional signal context can be mistaken for role ownership. The slice controls these risks through immutable snapshots, product-scoped demands, explicit lineage and no provider execution.
- Acceptance manifest: docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.1.acceptance.json
- Behavior change: true
- Dependencies: Ready after 0.7.6.6.0.2 PASS.
- Pipeline: power-web-discovery
- Validation report: docs/radar/pipelines/power-web-discovery/validation/0.7.6.6.1/validation.json

### Slice 0.7.6.6.2: Power Web people search planning, source lanes and HH retrieval

- Status: Ready
- Goal: Plan, accept, schedule and execute auditable role-scoped people searches, including a compliant mandatory HH.ru lane.
- User value: Users see where/how each role was searched and whether HH and official sources were actually covered.
- Problem statement: There is no people source strategy, accepted query plan, HH connector or ledger preventing selected lanes from disappearing.
- Scope:
  - Add planning input, deterministic planner, plan acceptance, retrieval compiler and scheduler.
  - Translate each immutable semantic RoleDemand into bounded account-specific title/function hypotheses using account, industry, geography, language and organization context.
  - Allow LLM query/title variants only as auditable proposals; backend acceptance preserves semantic role IDs and cannot change requiredness, priority or scope.
  - Support official, HH.ru public web, professional-network, publication/event, procurement/patent, industry and generic-web lanes.
  - Make HH public web, official and generic web mandatory when capability/policy permits; otherwise record explicit outcomes.
  - Generate role/account/geography/language-aware bounded queries from accepted title hypotheses.
  - Implement approved public-web HH adapter, capability cards, independent budgets and decision ledger.
- Out of scope:
  - No final identity or influence decision.
  - No access-control/ToS bypass.
  - No unbounded social crawling.
- Implementation notes:
  - Reuse mature Radar patterns through shared contracts, not source-pipeline internals.
  - Semantic role requirements come only from the immutable 0.7.6.6.1 handoff.
  - LLM may creatively propose how a semantic role is named in the concrete account, but every proposal requires deterministic acceptance and keeps its originating role ID.
  - Identity-only refs cannot masquerade as people-search execution.
  - Bound variants to control cost and preserve a complete proposal/acceptance ledger.
- Tests:
  - Recorded semantic-role-to-title-hypothesis, planner, lane, scheduler and budget fixtures.
  - Tests proving LLM proposals cannot add/remove required roles or alter priority/scope.
  - Multilingual/account-specific title mapping fixtures and rejection of unrelated or duplicate variants.
  - Malformed plan, unknown source, opaque ref and provider failure fixtures.
  - Targeted live HH public-web, official and generic-web probes after fast gates.
- Docs:
  - Create TO BE/PDF, manifest and source-capability docs.
  - Finalize AS IS with real connector behavior.
- Demo impact: Diagnostics show role-by-role queries, receipts, coverage, limits and unexecuted reasons.
- Acceptance criteria: Hard DoD; the slice cannot be marked Done until all conditions pass:
- 100% selected decisions have scheduled/executed/not-executable/policy/budget outcomes.
- Every search task traces to one immutable semantic RoleDemand and an accepted account-specific title/function hypothesis.
- LLM proposals change 0 required-role, priority or scope decisions.
- HH public web executes through compliant domain-restricted web search in targeted live validation; HH API remains deferred.
- Mandatory lanes never silently disappear.
- Every task has a product-safe receipt; no secret/raw payload/hidden reasoning is persisted.
- Budgets are independent and validation/AS IS are complete.
- Risks:
  - HH may require paid/licensed access.
  - Bound variants to control cost.
  - Unsupported professional networks must surface unavailable/manual states.
- Acceptance manifest: docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.2.acceptance.json
- Behavior change: true
- Pipeline: power-web-discovery
- Validation report: docs/radar/pipelines/power-web-discovery/validation/0.7.6.6.2/validation.json

### Slice 0.7.6.6.2.1: HH.ru authorized API integration and licensed resume access

- Status: Backlog
- Goal: Add licensed HH resume access only after credentials, budget and an approved usage model exist.
- Problem statement: Public-web HH results are useful source leads but cannot provide licensed resume coverage; authorized API access is currently unavailable and expensive.
- Scope: Confirm contractual/privacy terms; add an integration-layer HH OAuth/API adapter behind the Power Web source port; add explicit budgets, rate limits, retained-field policy and audit; compare licensed coverage with hh_public_web without changing identity rules.
- Out of scope: No work before credentials, budget and approved usage exist; no scraping or authorization bypass; no automatic identity confirmation from one resume; no private-contact export or automated outreach.
- Implementation notes: Keep disabled by default; integration adapter owns OAuth/transport only; application owns capability/evidence semantics; public-web lane remains independently available.
- Tests: Contract/licensing preflight and fail-closed credential tests; recorded adapter fixtures before bounded live API tests; budget, redaction, retention and architecture checks.
- Docs: Create TO BE/PDF/acceptance manifest only after access approval; add provider/compliance ADR and update Power Web AS IS only if implemented.
- Acceptance criteria: Hard DoD: approved access and use model; bounded licensed calls; no secrets or private contacts in artifacts; source receipts and budget audit complete; identity rules unchanged; validation PASS. Otherwise the slice remains Backlog/Blocked and does not block 0.7.6.6.1-0.7.6.6.9.
- Risks: API terms may not permit ABM usage; licensed access may be cost-prohibitive; resume data requires stricter retention and access controls.
- Behavior change: true
- Pipeline: power-web-discovery

### Slice 0.7.6.6.3: Power Web person profile extraction and evidence completeness

- Status: Backlog
- Goal: Extract source-owned person profiles and claim-level provenance without prematurely declaring cross-source identity.
- User value: Every named or anonymous profile is inspectable with its source facts and uncertainties.
- Problem statement: Raw pages cannot safely become people without schema validation, source linking, anonymous-profile support and evidence-complete projection.
- Scope:
  - Extract names/anonymous ids, titles, employers/units, geography, timeline, education, skills, responsibilities, publications, events and public business channels.
  - Keep one PersonProfile per source and one evidence link per claim.
  - Preserve HH anonymous/partial profiles without invented names.
  - Capture product-safe image descriptors and exact/near-duplicate fingerprints without face embeddings.
  - Add validation, bounded repair/backup, deterministic salvage and explicit gaps.
- Out of scope:
  - No identity confirmation.
  - No cross-photo face recognition.
  - No private contact harvesting/outreach.
- Implementation notes:
  - A source proves only claims present in it.
  - Persist sanitized metadata, not raw provider/HTML/image data.
  - Unknown stays unknown.
- Tests:
  - Named, anonymous, publication, event and conflicting-source fixtures.
  - Malformed output/ref/date recovery fixtures.
  - Evidence completeness and non-biometric image-fingerprint contracts.
- Docs:
  - Create TO BE/PDF/manifest and extraction schema docs.
  - Finalize AS IS with recovery behavior.
- Demo impact: Inspect named and anonymous profiles with claim-level evidence before identity linking.
- Acceptance criteria: Hard DoD; the slice cannot be marked Done until all conditions pass:
- Every visible profile/claim resolves to evidence.
- Anonymous profiles remain anonymous until supported.
- Source-less claims remain diagnostics, not public truth.
- Recovery is bounded and fully diagnosed.
- No biometric template/raw image/secret/raw provider payload is persisted.
- Validation is PASS and AS IS reconciled.
- Risks:
  - Models may over-normalize titles/employers; keep raw and normalized claims.
  - Visual artifacts are optional and volatile.
- Acceptance manifest: docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.3.acceptance.json
- Behavior change: true
- Pipeline: power-web-discovery
- Validation report: docs/radar/pipelines/power-web-discovery/validation/0.7.6.6.3/validation.json

### Slice 0.7.6.6.4: Power Web cross-source person identity resolution

- Status: Backlog
- Goal: Build an explainable identity graph linking anonymous and named profiles while preventing unsafe automatic merges.
- User value: Users can enrich one person from several incomplete sources and understand why profiles were linked, separated or sent to review.
- Problem statement: Name matching misses anonymous profiles and creates homonym errors; identity needs blocking, positive/negative evidence, temporal conflicts and reversible decisions.
- Scope:
  - Generate profile pairs from names/aliases, employer/unit, role, geography, timeline, education, skills, publications, contacts and image fingerprints.
  - Model positive evidence, contradictions and missing evidence independently.
  - Support separate, possible, probable, confirmed and rejected states.
  - Require stricter evidence for confirmed merges than retained hypotheses.
  - Preserve original profiles and reversible merge/unmerge history.
  - Allow bounded gap-driven enrichment only after accepted hypotheses.
- Out of scope:
  - No cross-photo face recognition/reverse-face search.
  - No title/employer-only or LLM-opinion confirmation.
  - No action from unresolved identity.
- Implementation notes:
  - Deterministic pairing/decision service owns merge semantics.
  - False-positive bias applies to retaining hypotheses, not confirming equality.
  - Image match is supporting evidence only.
- Tests:
  - Same/different-person controls including homonyms, anonymous HH, former/current conflicts and reused images.
  - Merge/unmerge preservation property tests.
  - Weak-feature negative tests and explainability assertions.
- Docs:
  - Create TO BE/PDF/manifest and reversible-identity ADR.
  - Finalize AS IS with confusion matrix and thresholds.
- Demo impact: Compare profiles side by side with evidence and contradictions.
- Acceptance criteria: Hard DoD; the slice cannot be marked Done until all conditions pass:
- All benchmark same-person controls are retained or explicitly contradicted.
- Zero different-person controls auto-merge.
- Confirmed merges have multiple compatible dimensions and no unresolved hard conflict.
- Ambiguous hypotheses stay reversible and reviewable; original profiles remain intact.
- No benchmark hardcodes enter production.
- Validation is PASS and AS IS reconciled.
- Risks:
  - Strict confirmation leaves duplicates, which is preferable to false fusion.
  - Sparse anonymous resumes may remain unresolved.
  - Name/transliteration diversity needs benchmark coverage.
- Acceptance manifest: docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.4.acceptance.json
- Behavior change: true
- Pipeline: power-web-discovery
- Validation report: docs/radar/pipelines/power-web-discovery/validation/0.7.6.6.4/validation.json

### Slice 0.7.6.6.5: Power Web employment, role and influence validation

- Status: Backlog
- Goal: Validate current affiliation, map identities to buying roles, infer evidence-backed relationships and expose missing influence positions.
- User value: Sales sees who is relevant now, who is former, which roles are dark and which influence claims need review.
- Problem statement: A resolved person is not automatically a current employee, role occupant, champion or blocker.
- Scope:
  - Validate current/former/unknown employment from dated claims.
  - Map identities/profiles to RoleDemand with fit, confidence, evidence and alternatives.
  - Represent internal people and external integrators, partners, suppliers and competitors in one typed graph.
  - Create evidence-backed relationship/influence hypotheses with fact/hypothesis/review states.
  - Compute coverage and explicit missing-role gaps.
- Out of scope:
  - No title-only authority/stance confirmation.
  - No outreach or route execution.
  - No graph editing UI.
- Implementation notes:
  - Keep identity, employment, role-fit and influence confidence separate.
  - Use as-of temporal semantics.
  - Preserve competing hypotheses.
- Tests:
  - Current/former/concurrent/subsidiary/external/title-conflict controls.
  - Role coverage and influence provenance tests.
  - Graph integrity and duplicate checks.
- Docs:
  - Create TO BE/PDF/manifest and temporal/role docs.
  - Finalize AS IS decision tables.
- Demo impact: Show confirmed people, review hypotheses, former employees, external influencers and missing roles distinctly.
- Acceptance criteria: Hard DoD; the slice cannot be marked Done until all conditions pass:
- Every mapped person has current/former/unknown employment.
- Every occupied role has identity/profile evidence and rationale.
- Every confirmed edge has evidence; hypotheses remain visibly separate.
- Title alone confirms zero influence/champion/blocker/economic-buyer states.
- Every required unfilled role has coverage and miss reason.
- Validation is PASS and AS IS reconciled.
- Risks:
  - Public sources lag changes; preserve dates/uncertainty.
  - Influence is partly unobservable and must remain a hypothesis until feedback.
- Acceptance manifest: docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.5.acceptance.json
- Behavior change: true
- Pipeline: power-web-discovery
- Validation report: docs/radar/pipelines/power-web-discovery/validation/0.7.6.6.5/validation.json

### Slice 0.7.6.6.6: Power Web checkpoints, recovery, budgets and incremental discovery

- Status: Backlog
- Goal: Make initial, incremental and full-rediscovery Power Web runs bounded, recoverable and temporally correct while preserving account/product/role/source coverage and evidence integrity.
- User value: Source failures do not erase the map, repeat runs do not duplicate people and coverage stops are understandable.
- Problem statement: Multi-source people search becomes unbounded/fragile without independent budgets, checkpoints, bounded revision, salvage, fingerprints and watermarks.
- Scope:
  - Define run kinds initial, incremental and full_rediscovery inside one Power Web Discovery pipeline.
  - Persist previous-run lineage and watermarks per account + product + role + source lane.
  - Build incremental windows from the last successful lane watermark with a configurable overlap; the initial default overlap is 7 days.
  - Do not advance watermarks for failed, policy-limited or budget-limited lanes.
  - Detect new profiles, evidence, title/employment changes, newly public sources and previously unfilled role gaps.
  - Make full rediscovery re-plan broad source coverage while preserving historical identities and claims.
  - Add explicit no-change, stale, coverage-incomplete, recovery and terminal states.
  - Keep checkpoints, retries and budgets bounded and auditable.
- Out of scope:
  - Recurring scheduler, cadence persistence or scheduling UI; these are owned by 0.7.6.6.7.1.
  - Unlimited retries or provider budgets.
  - Treating a disappeared page or absent evidence as proof that employment ended.
  - Per-account/product/lane cadence overrides.
  - Signal Monitoring or candidate-discovery scheduling changes.
- Implementation notes: Every incremental or full-rediscovery run points to the previous Power Web run. Absence is a gap or stale-evidence state, never an automatic former-employment conclusion. Unknown-date evidence remains reviewable. The temporal mechanics implemented here are consumed by the recurring scheduler in 0.7.6.6.7.1.
- Tests:
  - Recorded initial -> incremental -> full-rediscovery sequence preserves lineage and immutable history.
  - Successful lanes advance watermarks and apply overlap; failed/policy/budget-limited lanes do not.
  - Existing confirmed and review evidence is not republished as new.
  - A disappeared source cannot by itself change current employment to former.
  - A no-change incremental run completes successfully with auditable coverage.
  - Product/role/source lane coverage and budget decisions remain explicit.
- Docs:
  - Create TO BE/PDF/manifest and state-machine docs.
  - Finalize AS IS with actual limits.
- Demo impact: Diagnostics show coverage, budgets, retries, salvage, duplicates and gaps.
- Acceptance criteria:
  - One Power Web pipeline supports all three run kinds with explicit previous-run lineage.
  - Per-lane watermarks and overlap are deterministic and persisted.
  - Failed or limited lanes never advance freshness.
  - Incremental runs expose additions, changes, retained evidence and unresolved gaps.
  - Full rediscovery re-plans broadly without erasing history.
  - No missing source is interpreted as dismissal or former employment.
  - No recurring scheduler is hidden in this slice.
  - Recorded validation passes before the scheduling slice may start.
- Risks:
  - Merge corrections complicate incremental graphs; version decisions.
  - Reserve tuning must be benchmark-driven.
- Acceptance manifest: docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.6.acceptance.json
- Behavior change: true
- Pipeline: power-web-discovery
- Validation report: docs/radar/pipelines/power-web-discovery/validation/0.7.6.6.6/validation.json

### Slice 0.7.6.6.7: Power Web persisted runtime, API, jobs and lineage

- Status: Backlog
- Goal: Run Power Web discovery as an independent persisted pipeline with output contract, API, worker, history and restart-safe report.
- User value: Users can launch, monitor and reopen a historical Power Web run with proven source lineage.
- Problem statement: Recorded behavior is not a product runtime until lineage, artifacts, budgets and failures persist independently.
- Scope:
  - Persist Power Web runs, artifacts, jobs and reports with source candidate/signal lineage, RadarPowerWebPolicy version and exact product/role versions.
  - Persist run_kind=initial|incremental|full_rediscovery and previous_power_web_run_id.
  - Provide API/job/manual execution paths for all three run types.
  - Persist watermarks, freshness summaries, change sets and terminal diagnostics.
  - Add scheduler-ready scalar summary fields so future due-run scans do not load full artifacts.
  - Preserve restart, idempotency and separate Power Web provider budgets.
- Out of scope:
  - Recurring scheduler, cadence calculation and automatic due-run creation; these belong to 0.7.6.6.7.1.
  - Power Web review UI and graph UX.
  - Candidate-discovery or Signal Monitoring execution changes.
- Implementation notes:
  - Routes are transport-only, jobs pass run ids, persistence stores but does not decide.
  - Other pipeline latest/history/counters must not switch.
  - Keep history lightweight and heavy resources lazy.
- Tests:
  - Persistence/API/job round-trip for all three run kinds and previous-run chains.
  - Historical product/policy snapshots remain immutable after configuration edits.
  - Watermarks, freshness and change summaries survive API/worker restart.
  - Idempotency prevents duplicate manual jobs.
  - Scheduler-ready summaries are readable without loading artifacts.
  - Live initial plus explicitly triggered incremental run prove runtime without recurring execution.
- Docs:
  - Create TO BE/PDF/manifest and update backend/API/job/runbook docs.
  - Finalize runtime AS IS.
- Demo impact: Launch and inspect a real persisted third-pipeline run.
- Acceptance criteria:
  - Persisted Power Web runtime remains one pipeline with three explicit run kinds.
  - Every non-initial run has valid previous-run lineage.
  - Run summaries expose enough scalar freshness data for 0.7.6.6.7.1.
  - Manual API/jobs survive restart and do not mix candidate, signal or Power Web budgets.
  - No recurring job is created before 0.7.6.6.7.1.
  - Live initial and manual incremental artifacts are readable and evidence-complete.
- Risks:
  - People artifacts can be large; use scalar summaries/lazy endpoints.
  - Shared lifecycle migration needs cross-pipeline regression.
- Acceptance manifest: docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.7.acceptance.json
- Behavior change: true
- Pipeline: power-web-discovery
- Validation report: docs/radar/pipelines/power-web-discovery/validation/0.7.6.6.7/validation.json

### Slice 0.7.6.6.7.1: Power Web refresh policy, recurring scheduler and freshness diagnostics

- Status: Backlog
- Goal: Turn Power Web from a one-time people search into a controlled recurring account-graph refresh with separate initial, incremental and full-rediscovery cadences.
- User value: Users keep account Power Webs current as people change employers and titles, new profiles and publications appear, and previously missing buying roles become discoverable, without repeatedly launching uncontrolled full searches.
- Problem statement: People and public evidence are temporally unstable. A single cadence is either too expensive or too incomplete: incremental monitoring should be frequent and narrow, while full rediscovery should be rarer and broad. The product needs explicit policy, deterministic due-run calculation, idempotent scheduling and honest freshness diagnostics.
- Scope:
  - Extend RadarPowerWebPolicy in Radar settings with automatic-refresh enablement and separate initial, incremental and full-rediscovery policies.
  - Initial trigger: manual or on_candidate_accepted; default manual.
  - Incremental cadence: manual, weekly, monthly or quarterly; default monthly when automatic refresh is enabled.
  - Full-rediscovery cadence: manual, quarterly or semiannual; default quarterly when automatic refresh is enabled.
  - Automatic refresh is disabled by default and supports pause/resume without deleting history.
  - Persist effective overlap, initially 7 days, with value and basis in run snapshots.
  - Schedule only evidence-complete accounts with a valid handoff and successful initial run.
  - Create due runs through persisted idempotent jobs, never direct provider calls from the scheduler.
  - Product/role-policy changes mark affected account graphs stale and full-rediscovery-due.
  - Calculate freshness per account, product, role and source lane.
  - Expose last/next timestamps, stale reasons, due reason, policy version and idempotency key.
  - Keep manual initial, incremental and full refresh available at any time.
  - Use a deterministic clock and explicit Radar timezone.
  - Expose policy in Radar settings and freshness in the Power Web surface.
- Out of scope:
  - Separate global Power Web configuration UI.
  - Per-account, per-product or per-lane cadence overrides.
  - Automatic refresh triggered by Signal Monitoring events.
  - Treating a missing profile/page as evidence that employment ended.
  - Changes to candidate-discovery or Signal Monitoring schedules.
  - Unbounded retries, concurrency or provider budgets.
- Implementation notes: Cadence ownership stays with the Radar because the Radar defines the reusable account universe and products to pursue. Power Web remains one pipeline with three run kinds. Due dates anchor to the last successful run of the relevant kind; failed runs do not postpone the next due run or advance watermarks. Full rediscovery re-plans source coverage, while incremental runs use per-lane watermarks and overlap. A scheduler tick creates at most one idempotent run per eligible account chain and reads scalar summaries rather than full artifacts.
- Tests:
  - Policy API/DB/restart round-trip with defaults, pause/resume and explicit timezone.
  - Deterministic due-date tests across month boundaries and time zones.
  - Ten scheduler ticks create exactly one due run per account chain.
  - Concurrent schedulers and worker restart create no duplicate runs.
  - on_candidate_accepted is opt-in; manual remains the default.
  - Product/role-policy activation marks affected graphs stale and full-rediscovery-due.
  - Successful no-change incremental runs update freshness; failed/limited runs do not.
  - Manual refresh works while automatic refresh is disabled.
  - Candidate and signal schedules/counters remain unchanged.
  - Docker gate executes one genuinely scheduled incremental run and verifies persisted report after restart.
  - Playwright verifies Radar policy, pause/resume, next refresh and stale diagnostics in RU/EN.
- Docs: Create TO BE Markdown/PDF and acceptance manifest before code. After validation PASS, update Power Web AS IS Markdown/PDF, scheduler ADR, Developer Guide, User Guide, demo runbook and roadmap closeout with actual scheduled run IDs and freshness evidence.
- Demo impact: The demo Radar exposes two bound products, automatic Power Web refresh disabled by default, and a controlled example where enabling monthly incremental plus quarterly full rediscovery creates one due incremental run. The UI shows last/next refresh, stale roles and pause state.
- Acceptance criteria:
  - One Radar policy controls Power Web cadence for its bound products without a separate configuration surface.
  - Initial discovery is manual by default; automatic refresh is opt-in.
  - Incremental and full-rediscovery cadences are independent and persisted.
  - Ten repeated scheduler ticks and concurrent workers create zero duplicate runs.
  - Every automatic run has due reason, policy version, previous-run lineage and idempotency key.
  - Successful lanes advance freshness; failed, policy-limited and budget-limited lanes do not.
  - Product/role changes make affected graphs explicitly stale.
  - Missing sources never automatically create former-employment claims.
  - Manual refresh works when scheduling is paused or disabled.
  - Candidate-discovery and Signal Monitoring schedules are unchanged.
  - A real Docker scheduled incremental run completes within bounded budgets and survives restart.
  - Validation report has PASS and contains scheduler ledger, run IDs, freshness matrix and retrospective.
- Risks: Recurring people search can multiply cost, duplicate jobs, amplify stale evidence and create false employment changes. Defaults therefore remain opt-in, cadence is bounded, scheduling is idempotent, freshness is per lane, and absence never becomes a confirmed personnel change.
- Acceptance manifest: docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.7.1.acceptance.json
- Behavior change: true
- Dependencies: Blocked until 0.7.6.6.6 incremental semantics and 0.7.6.6.7 persisted runtime/API/jobs are Done.
- Pipeline: power-web-discovery
- Validation report: docs/radar/pipelines/power-web-discovery/validation/0.7.6.6.7.1/validation.json

### Slice 0.7.6.6.8: Power Web guided and blind quality benchmark

- Status: Backlog
- Goal: Measure real Power Web quality against hidden user controls with explicit miss diagnostics and persisted guided/blind evidence.
- User value: The team knows whether the system finds the right roles/people, avoids false merges and produces a useful access graph.
- Problem statement: Completion/profile count does not prove retrieval, identity, employment, role, relationship or handoff quality.
- Scope:
  - Add guided smoke and blind profiles with separate metadata/budgets.
  - Load blind baseline only after run.
  - Measure role/person recall, identity precision/recall, false merges, employment accuracy, relationship provenance, lane coverage, review/gap rates and handoff readiness.
  - Report per-control funnel from planning through role/relationship projection.
  - Run Docker/API guided and blind benchmarks and one consolidated closeout.
- Out of scope:
  - No public market-wide claim.
  - No blind hints or production hardcodes.
  - No silent benchmark-fitting threshold changes.
- Implementation notes:
  - Thresholds are accepted in 0.7.6.6.0.
  - False confirmed merge is a hard failure.
  - Separate review hypotheses, confirmed identities and planner-ready roles.
- Tests:
  - Blind-isolation contracts.
  - Evaluator coverage for every funnel state and evidence/duplicate invariants.
  - Recorded before live; validator reads persisted artifacts.
- Docs:
  - Create TO BE/PDF/manifest with approved thresholds.
  - Document dataset version/metrics/non-claim wording and finalize AS IS with run ids/RCA.
- Demo impact: Benchmark report explains each found, missed, merged, rejected or review-needed control.
- Acceptance criteria: Hard DoD; the slice cannot be marked Done until all conditions pass:
- Docker rebuilt; at least one guided and one blind persisted run complete or reach accepted bounded terminal state.
- Blind metadata proves zero controls entered pipeline behavior.
- All approved metric thresholds pass and zero different-person controls auto-merge.
- Zero visible graph elements lack provenance; every miss has a path reason.
- Access Planner consumes reviewed graph without manual translation.
- Validation/process retrospective/AS IS reconciliation are complete.
- Risks:
  - One-industry overfit; keep generic production rules and add later datasets.
  - Source volatility requires versioned as-of and accepted equivalent URLs.
- Acceptance manifest: docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.8.acceptance.json
- Behavior change: true
- Dependencies: Blocked until 0.7.6.6.7.1 proves recurring scheduling, temporal run lineage and freshness diagnostics.
- Pipeline: power-web-discovery
- Validation report: docs/radar/pipelines/power-web-discovery/validation/0.7.6.6.8/validation.json

### Slice 0.7.6.6.9: Power Web UI, human review and Access Planner handoff

- Status: Backlog
- Goal: Expose the third pipeline as an evidence-first graph with reversible review and direct Access Planner handoff.
- User value: Users inspect who was found, resolve profiles, approve roles/relationships, see gaps and understand route changes.
- Problem statement: A graph is unusable if identities/relations cannot be checked or corrected and unresolved hypotheses silently become Access Planner facts.
- Scope:
  - Show account-centric Power Web results grouped or filtered by product and semantic role.
  - Show run kind, previous-run lineage, last initial/full discovery, last incremental refresh and change summary.
  - Show next scheduled refresh, paused/disabled state, stale accounts/roles/source lanes and coverage gaps from 0.7.6.6.7.1.
  - Support human review of identities, employment and evidence without losing product provenance.
  - Keep manual refresh available for eligible accounts.
- Out of scope:
  - A separate global scheduler settings screen.
  - Per-account/product/lane cadence overrides.
  - Inferring employment termination from missing evidence.
  - Access-strategy workflow.
- Implementation notes: Cadence is edited only in Radar settings. Power Web UI consumes the effective policy and run freshness contracts, and renders missing or old evidence as stale/unverified rather than false certainty.
- Tests:
  - Multi-product graph preserves product/role provenance.
  - Initial, incremental and full-rediscovery histories are distinguishable.
  - Last/next refresh, pause state, stale reasons and change sets match backend summaries.
  - Manual refresh works while automatic refresh is disabled.
  - Review actions target the selected Power Web run and identity.
  - RU/EN and desktop viewports have no overlap or body scrolling.
- Docs:
  - Create TO BE/PDF/manifest and update user/developer/demo/frontend/handoff docs.
  - Finalize UI/handoff AS IS.
- Demo impact: Show the complete company -> signal -> Power Web -> Access Plan product chain.
- Acceptance criteria:
  - A user can understand which products and roles each person supports.
  - Freshness, next refresh and stale coverage are explicit and cannot be mistaken for confirmed current employment.
  - Scheduler settings are not duplicated outside Radar settings.
  - Manual refresh and human review remain available.
  - UI counters and histories agree with persisted Power Web endpoints.
  - Benchmark and restart gates pass.
- Risks:
  - Dense graphs need groups/filters/focus/evidence panel, not decorative layout.
  - Review overlays must not rewrite source truth.
- Acceptance manifest: docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.9.acceptance.json
- Behavior change: true
- Dependencies: Blocked until 0.7.6.6.8 benchmark PASS; consumes cadence and freshness contracts from 0.7.6.6.7.1.
- Pipeline: power-web-discovery
- Validation report: docs/radar/pipelines/power-web-discovery/validation/0.7.6.6.9/validation.json

### Slice 0.7.6.6.10: Optional biometric-assisted identity matching governance and pilot

- Status: Backlog
- Goal: Only with explicit approval, pilot cross-photo facial similarity as human-review assistance without allowing it to confirm identity alone.
- User value: An authorized reviewer may receive an additional clue for profiles using different photos while retaining control.
- Problem statement: Cross-photo similarity may help where image fingerprints fail, but creates biometric, legal, privacy, ToS, bias and false-match risks.
- Scope:
  - Complete legal/ToS/privacy impact assessment and explicit approval first.
  - Define opt-in scope, jurisdictions/sources, retention/deletion/audit and reviewer permissions.
  - Evaluate approved embeddings on consented/synthetic benchmark.
  - Expose similarity only with non-biometric evidence and human review.
  - Provide fail-closed disable/delete path.
- Out of scope:
  - No broad reverse-face internet search.
  - No covert/private-image identification.
  - No production rollout without approved assessment/thresholds.
- Implementation notes:
  - Optional and outside core critical path.
  - Prefer local ephemeral processing/minimal persistence.
  - Human review and corroboration are mandatory.
- Tests:
  - Governance fail-closed tests.
  - Representative false-match/nonmatch benchmark.
  - Similarity cannot set confirmed_same_person; deletion/audit/security tests if persisted.
- Docs:
  - Create TO BE/PDF/manifest only after explicit approval.
  - Add biometric ADR/privacy assessment; update AS IS only if accepted.
- Demo impact: None by default; approved pilot shows a clearly labeled review clue, never a verdict.
- Acceptance criteria: Hard DoD; the slice cannot be marked Done until all conditions pass:
- Explicit user/product and legal/ToS/privacy approval exists before code.
- Feature is disabled by default outside approved scope.
- Facial similarity alone confirms zero identities.
- Accepted false-match threshold and reviewer workflow pass.
- Retention/deletion/audit pass end to end.
- Otherwise slice stays Backlog/Blocked without affecting core completion.
- Risks:
  - Biometrics may be disproportionate; rejecting the feature is valid.
  - Demographic/image-quality bias requires conservative review-only use.
- Acceptance manifest: docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.10.acceptance.json
- Behavior change: true
- Pipeline: power-web-discovery
- Validation report: docs/radar/pipelines/power-web-discovery/validation/0.7.6.6.10/validation.json

### Slice 0.7: Human review queue loop

- Status: `Backlog`
- Goal: Add a minimal human-review state for Access Plans and route drafts.
- User value: A user can approve, reject, or request changes for a recommended route before it becomes an executable task.
- Scope:
  - Add review state: pending, approved, rejected, needs_changes.
  - Add deterministic review actions in a local artifact or in-memory store.
  - Add a review queue/demo panel showing pending Access Plan routes.
  - Add a review action that changes the visible route/task status in the demo.
- Out of scope:
  - Production authentication.
  - Multi-reviewer assignment.
  - Real notification flows.
- Implementation notes:
  - Follow the `langgraph-document-ai-platform` HITL pattern conceptually, but keep the first demo local and small.
  - Keep review history explicit in the artifact.
- Tests:
  - Unit tests for review transitions.
  - Smoke test for approve/reject/needs_changes demo actions or CLI simulation.
  - Contract test that review history is present in the artifact.
- Docs:
  - Update user guide with review queue behavior.
  - Update architecture docs with HITL boundary.
- Demo impact:
  - Demo shows that AI/planner recommendations are not automatically executed.
- Acceptance criteria:
  - A route can move from pending to approved or rejected in the demo.
  - Review history is visible and test-covered.
  - Approved route can be presented as a next task candidate.
- Risks:
  - Browser-only state may not persist; acceptable for this slice if documented.

### Slice 0.8: CRM feedback simulation loop

- Status: `Backlog`
- Goal: Simulate CRM task export and outcome feedback without integrating a real CRM.
- User value: A user can see how an approved Access Plan move becomes a task and how an outcome updates the Power Web state.
- Scope:
  - Add local CRM task artifact with owner, due date/status, route, account, and expected state change.
  - Add synthetic outcomes: replied, no_reply, intro_made, meeting_booked, blocker_found, champion_found.
  - Add a feedback application service that updates role state and board summary from outcome data.
  - Add frontend task/outcome section in the demo.
- Out of scope:
  - Real CRM API.
  - Two-way sync.
  - Scheduling or reminders.
- Implementation notes:
  - Treat CRM as a simulated system of record using local artifacts.
  - Keep Power Web OS as system of strategy: it recommends and updates strategy state from outcomes.
- Tests:
  - Unit tests for task creation and outcome-to-state update.
  - Smoke test for approved route -> local task -> outcome -> updated artifact.
  - Frontend smoke check for task/outcome sections.
- Docs:
  - Update user guide with the simulated feedback loop.
  - Update architecture overview with CRM boundary.
- Demo impact:
  - Demo becomes a closed loop: recommend, approve, create task, apply outcome, update board.
- Acceptance criteria:
  - Applying a synthetic outcome visibly changes account/Power Web state.
  - The task artifact is generated and documented.
  - No live CRM is required.
- Risks:
  - Simulated CRM can be mistaken for production integration; mitigate with clear UI/docs labeling.

### Slice 0.9: Local persistence loop

- Status: `Backlog`
- Goal: Persist the demo state locally so the user can rerun the product loop without losing approved routes, tasks, and outcomes.
- User value: A user can treat the demo as a small working product session rather than a regenerated static page.
- Scope:
  - Add local persistence using SQLite or JSON state files, choosing the smallest maintainable option.
  - Persist accounts, generated plans, review actions, tasks, and outcomes.
  - Add reset/reseed command for deterministic demo data.
  - Add UI state restoration where applicable.
- Out of scope:
  - Production Postgres migrations.
  - Multi-user tenancy.
  - Cloud deployment.
- Implementation notes:
  - Prefer JSON files if static demo architecture remains dominant; prefer SQLite if query/update complexity justifies it.
  - Keep reset command simple and documented.
- Tests:
  - Unit tests for repository read/write/reset.
  - Smoke test for generate -> persist -> reload.
  - Existing product-loop tests remain green.
- Docs:
  - Document local state location and reset command.
  - Update architecture persistence section.
- Demo impact:
  - Demo can show state continuity across runs.
- Acceptance criteria:
  - Demo state survives a rerun.
  - Reset returns to known synthetic baseline.
  - Persistence is isolated from domain logic behind a small interface.
- Risks:
  - Persistence can pull the project toward infrastructure work; keep it local and demo-oriented.

### Slice 0.10: Account Radar batch loop

- Status: `Backlog`
- Goal: Run the portfolio loop as a batch workflow over all synthetic accounts and produce a weekly-style recommendations artifact.
- User value: A user can see the product act as an account radar, not only as a manual single-account analyzer.
- Scope:
  - Add batch runner for all fixture accounts.
  - Produce ranked weekly recommendations with top changed accounts and recommended next actions.
  - Add frontend section for latest radar run.
  - Include partial-failure handling for bad fixtures.
- Out of scope:
  - Celery/Redis production async.
  - Live scheduled jobs.
  - Email/slack notifications.
- Implementation notes:
  - Use the `async_batch` pattern conceptually, but keep local execution deterministic.
  - Emit per-account item status and aggregate summary.
- Tests:
  - Unit tests for batch summary and partial failure.
  - Smoke test for portfolio batch artifact generation.
  - Demo smoke check for radar run section.
- Docs:
  - Update developer guide with batch command.
  - Update user guide with weekly radar concept.
- Demo impact:
  - Demo shows portfolio-level recommendations generated in one run.
- Acceptance criteria:
  - Batch output contains item-level status and aggregate counters.
  - One bad fixture does not break the full demo if `continue_on_error` is enabled.
  - User can inspect batch recommendations and drill into an account.
- Risks:
  - Batch scope can grow toward production orchestration; keep live scheduling out of scope.

### Slice 0.11: Evidence/source governance loop

- Status: `Backlog`
- Goal: Make source provenance, quality notes, and compliance restrictions visible in the demo.
- User value: A user can trust why a recommendation exists and see where the system refuses or warns.
- Scope:
  - Add source metadata: source type, collected_at, confidence, allowed_usage, compliance notes.
  - Add quality gates for weak or missing evidence.
  - Add UI evidence drawer or section per route/signal.
  - Add visible warnings for restricted channels or low-confidence evidence.
- Out of scope:
  - Legal policy engine.
  - Real PII governance.
  - Automated scraping compliance.
- Implementation notes:
  - Keep governance rules simple and explicit.
  - Reuse evidence refs already present in Access Plan artifacts.
- Tests:
  - Unit tests for evidence quality classification.
  - Contract tests that low-confidence evidence affects warnings/review flags.
  - Frontend smoke check for evidence/governance sections.
- Docs:
  - Update user guide with evidence and compliance language.
  - Update architecture docs with source governance boundary.
- Demo impact:
  - Demo shows white-box source traceability instead of only route cards.
- Acceptance criteria:
  - Each recommendation links to visible evidence metadata.
  - Weak/restricted evidence changes UI warnings or review flags.
  - The demo remains deterministic.
- Risks:
  - Compliance wording can overpromise; keep labels scoped to demo rules.

### Slice 0.12: Controlled first live input loop

- Status: `Backlog`
- Goal: Add one controlled, user-provided input path that turns real-ish local data into the same product loop.
- User value: A user can bring a small CSV/JSON export and see it flow through Account Radar, Power Web Lite, Access Plan, review, and task simulation.
- Scope:
  - Support import of a local CSV/JSON file with account names, URLs, CRM notes, known contacts, or signal notes.
  - Validate and normalize imported data into the existing fixture contract.
  - Show import results and validation warnings in the demo.
  - Generate the same artifacts and UI views as synthetic data.
- Out of scope:
  - Direct CRM API.
  - Web scraping.
  - Bulk enrichment.
  - Sensitive data handling beyond local files.
- Implementation notes:
  - Prefer local file import over live API as the first real-user loop.
  - Keep sample import file committed for repeatable tests.
- Tests:
  - Parser tests for valid/invalid import files.
  - Smoke test from sample import -> portfolio -> selected Access Plan.
  - Demo smoke check for import status.
- Docs:
  - Document import format and limitations.
  - Update user guide with sample import walkthrough.
- Demo impact:
  - Demo can run with synthetic data or a local imported file.
- Acceptance criteria:
  - Sample import produces the same product loop as synthetic fixtures.
  - Invalid rows produce clear validation messages.
  - No external services are required.
- Risks:
  - User data may contain sensitive content; document local-only behavior and ignore real secrets.

### Slice 0.13: First CRM adapter spike as a product loop

- Status: `Backlog`
- Goal: Replace the simulated CRM export with one real but optional CRM/file adapter path while keeping the same review-first product flow.
- User value: A user can take approved demo tasks out of Power Web OS into a real working system or a portable file.
- Scope:
  - Choose the first adapter based on open question resolution: file export, HubSpot, Salesforce, Bitrix24, or amoCRM.
  - Add adapter interface and one implementation.
  - Keep credentials out of repo and document setup.
  - Add an optional demo path that exports approved tasks.
- Out of scope:
  - Full two-way sync.
  - Production OAuth app.
  - Multiple CRM adapters.
- Implementation notes:
  - Prefer file export if CRM choice is unresolved.
  - Use tool/executor-style boundaries for auditability.
  - Never execute export before human review approval.
- Tests:
  - Unit tests for adapter payload mapping.
  - Smoke test with file/mock adapter.
  - External CRM test only behind explicit opt-in env flag if added.
- Docs:
  - Document adapter setup and safety constraints.
  - Update architecture connector section.
- Demo impact:
  - Demo shows approved route -> exportable task.
- Acceptance criteria:
  - Export is optional, reviewed, and test-covered.
  - No secrets are committed.
  - Existing synthetic loop still works without CRM setup.
- Risks:
  - CRM choice can block implementation; mitigate with file export fallback.

### Slice 0.14: First source connector spike as a product loop

- Status: `Backlog`
- Goal: Add one controlled source connector that enriches account signals while preserving source provenance and review.
- User value: A user can see the product ingest a real source-like feed and improve Account Radar or Access Plan recommendations.
- Scope:
  - Choose one source: procurement fixture/API, HH export, company site notes, news feed, or CRM history export.
  - Add connector interface and one implementation.
  - Normalize connector output into existing signal/evidence contracts.
  - Show new/updated signals in the same demo UI.
- Out of scope:
  - Broad scraping.
  - Multiple source connectors.
  - Automated outreach or contact harvesting.
- Implementation notes:
  - Prefer file/API source with stable test data.
  - Keep source provenance mandatory.
  - Do not weaken compliance/governance rules.
- Tests:
  - Unit tests for connector normalization.
  - Smoke test for source input -> signal -> Access Plan change.
  - Fixture-based tests for failures/empty results.
- Docs:
  - Document source setup, limitations, and provenance.
  - Update user guide with source-enriched demo path.
- Demo impact:
  - Demo can show before/after signal enrichment for one account or portfolio.
- Acceptance criteria:
  - Connector output changes at least one visible recommendation or evidence note.
  - Source refs are visible in UI.
  - Demo remains runnable without the live connector by using fixture fallback.
- Risks:
  - Live source instability; mitigate with committed fixture fallback and optional live mode.

### Slice 0.15: Pilot package loop

- Status: `Backlog`
- Goal: Package the current product as an ABM Access Pilot demo suitable for a 50-100 account pilot narrative.
- User value: A stakeholder can understand what a real pilot would include, how to run it, and what success metrics are tracked.
- Scope:
  - Add a pilot summary report artifact from current synthetic/batch state.
  - Add KPI counters: relevant accounts, generated Access Plans, approved moves, tasks created, outcomes applied, missing roles surfaced.
  - Add demo screen/section for pilot summary.
  - Add docs for pilot workflow and acceptance criteria.
- Out of scope:
  - Real customer deployment.
  - Billing/packaging.
  - Production analytics warehouse.
- Implementation notes:
  - Keep the report generated from existing artifacts.
  - Use the product's own concepts: Account Radar, Power Web, Access Plan, review, feedback.
- Tests:
  - Unit tests for KPI aggregation.
  - Smoke test for pilot report generation.
  - Demo smoke check for pilot summary section.
- Docs:
  - Add pilot walkthrough to user guide.
  - Update README with current demo maturity.
- Demo impact:
  - Demo tells a complete pilot story, not just a feature story.
- Acceptance criteria:
  - Pilot report is generated from current demo data.
  - KPI values are traceable to artifacts.
  - User can present the current product loop end to end.
- Risks:
  - Pilot narrative can overstate readiness; label synthetic/demo status clearly.

## Completed Slices

- `Slice 0.1: Bootstrap Power Web OS repository`
  - Created product-specific documentation baseline.
  - Added Python package skeleton and deterministic Access Planner.
  - Added demo fixture and demo runner.
  - Added pytest baseline.
  - Initialized Git, created the private GitHub repository, and pushed `main`.
- `Slice 0.2: First closed Access Planning loop`
  - Added `AccessPlanningWorkflow` with typed state, optional `langgraph-dai` integration, and local fallback.
  - Added Access Plan artifact generation to `demo/output/access_plan.json` and `frontend/public/demo/access_plan.json`.
  - Added React TypeScript Vite frontend demo using `ui-design-system`.
  - Added Python workflow/artifact tests and frontend smoke contract tests.
  - Updated README, developer guide, user guide, architecture overview, and demo docs.
- `Slice 0.2.1: Product app shell for Access Planning demo`
  - Moved the frontend demo into a durable Power Web OS app shell with sidebar navigation and top bar account context.
  - Added active `Access Plans` screen plus planned placeholders for `Accounts`, `Account Map`, `Signals`, `Playbook`, `My Tasks`, and `Signals Inbox`.
  - Split frontend into layout, screen, and primitive component boundaries.
  - Updated frontend contract tests and docs.
- `Slice 0.3.1: Playwright visual smoke and documentation screenshots`
  - Added Playwright visual smoke as a frontend npm script.
  - Added reproducible screenshots for ICP Radar, Accounts, Account Map, Access Plans, and Playbook.
  - Captured screenshots at `1280x720` and `1366x768`.
  - Documented QA screenshot workflow under `docs/qa/`.
- `Slice 0.3.2: GitHub Wiki documentation publishing`
  - Changed repository visibility to public.
  - Enabled GitHub Wiki and published generated documentation pages.
  - Added wiki publisher script with dry-run support.
  - Published visual smoke screenshots into wiki assets.
- `Slice 0.3.3: Curated GitHub Wiki and screenshot walkthrough`
  - Replaced filename-driven Wiki screenshot sections with a curated screenshot walkthrough manifest.
  - Embedded product screenshots into the user guide narrative.
  - Split Wiki navigation into product and engineering sections.
  - Kept QA screenshots as technical source assets with dry-run publication coverage.
- `Slice 0.4: Account Radar portfolio loop`
  - Added a six-account synthetic portfolio fixture.
  - Added deterministic `AccountRadar` scoring and ranking over generated Access Plans.
  - Added `generate-account-radar` demo command and Vite artifacts for portfolio plus per-account plans.
  - Replaced the `Accounts` placeholder with a ranked portfolio screen and click-through into selected-account `Access Plans`.
  - Updated backend/frontend tests and synchronized README, user, developer, architecture, and demo docs.
- `Slice 0.4.1: SPA frame and bilingual UI correction`
  - Bounded the frontend shell to the viewport and moved scrolling into workspace panes.
  - Fixed Accounts table overflow behavior for smaller desktop monitors.
  - Added EN/RU i18n resources, topbar language switcher, and local locale persistence.
  - Updated frontend contract tests, docs, and local frontend agent/design-system instructions.
- `Slice 0.4.2: RU localization for visible demo data`
  - Added presentation-layer localization for deterministic demo artifact values.
  - Localized visible stages, owners, route titles, rationale, risks, state changes, signals, evidence, and role/gap labels in RU mode.
  - Preserved raw IDs, source refs, company names, person names, workflow names, and runtime names.
  - Updated frontend contract tests and docs.
- `Slice 0.5: Power Web Lite board loop`
  - Added deterministic `PowerWebBoardBuilder` and non-breaking `power_web_board` artifact payloads.
  - Regenerated portfolio and single-account Access Plan artifacts with board summary, nodes, edges, and route path.
  - Replaced the `Account Map` placeholder with a working board screen for the selected account.
  - Added board localization, frontend contracts, backend board tests, and synchronized docs.
- `Slice 0.5.1: Enterprise-sized Power Web demo account`
  - Expanded the default top account, now displayed as `Северные Роботы`, to a richer eight-figure Power Web.
  - Added technical, procurement, security, operations, partner, and missing economic-buyer roles.
  - Added blocker stance support for board nodes and test coverage for the richer demo board.
- `Slice 0.6: Playbook rules explanation loop`
  - Added deterministic `PlaybookAnalysisBuilder` and non-breaking `playbook_analysis` artifact payloads.
  - Added current and `no_partner_motion` route previews generated by the Python planner.
  - Replaced the `Playbook` placeholder with a working read-only screen inside the Power Web OS shell.
  - Connected Access Plans review-rule explanation to `playbook_analysis.current`.
  - Added backend, frontend contract, build, and documentation coverage for the loop.
- `Slice 0.6.1: ICP Radar terminology and ТОиР fixture contract`
  - Renamed the upstream ABM radar concept to `ICP Radar` in docs and product architecture.
  - Documented account discovery vs signal monitoring as separate processes.
  - Recorded the SIBUR-style ТОиР workbook as the first ICP Radar fixture source.
  - Added planned contracts for criteria, observations, validation, scoring, candidates, and take-into-work handoff.
  - Added follow-up slices for XLSX import, signal validation, and ICP Radar to Power Web handoff.
- `Slice 0.6.2: ICP Radar XLSX fixture import loop`
  - Added `ICPRadar` contracts and `ICPRadarXlsxImport` for the ТОиР/SIBUR workbook fixture.
  - Added `generate-icp-radar` with backend, frontend, and normalized fixture artifacts.
  - Added the `ICP Radar` frontend screen as the default demo screen inside the existing shell.
  - Renamed visible accepted-account demo company/person names to Russian-language examples while preserving stable IDs.
  - Added Python importer/smoke tests, frontend contract tests, and docs updates.
- `Slice 0.6.2.1: ICP Radar table-first UX correction`
  - Reworked `ICP Radar` from split-view into a broad ranked table with a sticky account column.
  - Added bounded inline candidate previews under selected rows.
  - Added an in-shell read-only candidate detail view with breadcrumbs back to the shortlist.
  - Kept signal validation and take-into-work handoff clearly planned for later slices.
- `Slice 0.6.2.2: ICP Radar UX repair`
  - Removed nested scrolls from the ICP Radar inline candidate preview.
  - Kept score and tier values in the table row instead of duplicating them inside the preview.
  - Limited preview content to main signal, short recommendation, top evidence refs, and top criteria.
  - Fixed ICP Radar scroll ownership and added a sticky candidate detail header.
  - Localized remaining Russian ICP Radar UI labels for fit, intent, trigger, tier, evidence, source URLs, and confidence.
- `Slice 0.6.2.3: ICP Radar evidence-backed criteria contract`
  - Added `criteria_evidence` to ICP Radar candidates without removing `criteria_scores`, `evidence_refs`, or `source_urls`.
  - Added curated synthetic demo annotations for the top five ТОиР/SIBUR candidates and high-impact criteria.
  - Added fallback explanations for all C1-C20 criteria: `supported`, `inferred`, or `not_observed`.
  - Updated the candidate detail view to show criterion status, confidence, rationale, facts, source refs, and origin labels.
  - Fixed ICP Radar `account_id` generation to use stable workbook legal-entity numbers instead of Python `hash()`.
- `Slice 0.6.2.4: ICP Criteria review UX correction`
  - Reworked candidate criteria detail into a compact table-first review surface.
  - Added filters, sorting, expandable criterion rows, and local accept/reject/edit controls with comments.
  - Removed oversized origin/confidence blocks from expanded criteria; origin is now a small note and confidence is a tag.
  - Made candidate detail breadcrumbs and compact account header sticky during criteria scrolling.
  - Kept review decisions as frontend-only demo state until the durable Slice 0.6.3 validation loop.
- `Slice 0.6.2.6: ICP Radar laptop-readable inline preview`
  - Reworked expanded shortlist preview so it anchors to the visible table/workspace area instead of the horizontally scrolled table columns.
  - Removed the separate preview left rail and moved the detail action below preview content.
  - Increased preview height and kept a single vertical scroll owner for the whole preview.
  - Documented the anchored preview rule in the table-first UX ADR and frontend docs.
- `Slice 0.6.2.7: ICP Radar catalog list-first UX correction`
  - Replaced the three-column radar catalog card grid with wide list-first rows.
  - Moved radar metrics into a compact strip instead of narrow metric tiles.
  - Kept configured radar status, run mode, owner, cadence, last run, and counts visible in each row.
  - Documented list-first catalogs for dense configurable objects.
- `Slice 0.6.5: Editable ICP Radar configuration loop`
  - Added frontend-local create/edit configuration flow for ICP Radars before durable signal validation and take-into-work.
  - Added `View` / `Edit` settings modes, draft validation, save/discard/duplicate/reset actions, and catalog-level reset of demo changes.
  - Stored created/edited radar definitions in browser `localStorage` under `power-web-os-icp-radar-config-overrides`.
  - Labelled local/demo drafts explicitly and kept generated artifacts, live execution, and shortlist recalculation out of scope.
- `Slice 0.6.5.1: ICP Radar definition model correction`
  - Replaced flat radar settings with structured `RadarDefinition` blocks: metadata, global search policy, account qualification, intent signals, monitoring, scoring, and validation.
  - Added typed sources, source policies, rule groups, atomic rules, signal trigger rules, and `0/1/2` signal scoring rubrics.
  - Added `RadarDefinitionValidator` for structural checks and obvious contradictions.
  - Rebuilt Settings into block-level editing with rule/source/signal editors and validation report.
  - Updated ICP Radar artifacts to version `0.6.5.1`.
- `Slice 0.6.5.2: ICP Radar settings UX and scoring model correction`
  - Reworked Settings for business-language rule editing: generated IDs/codes are visible only as compact references and are not manually edited.
  - Removed user-facing target-field/operator/value controls from rule and signal editors.
  - Added source selection by name, local source entities, global search base checkbox, and additional-source checkbox.
  - Replaced trigger/total scoring settings with Fit, Intent, and Tier models plus scoring preset dropdowns.
  - Updated ICP Radar artifacts to version `0.6.5.2`.
- `Slice 0.6.5.3: ICP Radar settings UX simplification`
  - Removed the duplicate Overview/Description settings block and moved radar name, description, active status, owner, duplicate, and delete actions into the selected radar header.
  - Replaced visible nested rule groups with flat natural-language qualification criteria and intent-signal detection rules.
  - Simplified source policies to global-base usage, optional local sources, cross-validation, and HITL additional-source switches.
  - Reworked global sources into a bounded table and fixed source editor focus by keeping source IDs stable while typing.
  - Replaced monitoring free-text fields with dedupe dropdowns and number/unit duration controls.
  - Added a global signal scoring scale table with optional per-signal override and fixed touched RU Settings labels that contained `???`.
- `Slice 0.6.5.4: ICP Radar settings layout and signal editor polish`
  - Moved Settings-level actions into the selected radar header and removed the standalone Settings action row.
  - Kept radar description visible in the header while configuring a radar.
  - Reworked the global search base into bounded keyword/exclusion lists plus a numbered source table.
  - Reworked account qualification rules and intent signals into aligned table summaries with operator/source/check columns.
  - Moved signal scale into a separate compact Settings block and standardized boolean controls as switches.
- `Slice 0.6.5.5: ICP Radar settings header and switch polish`
  - Aligned selected-radar header actions in the top-right row and moved status/local/read-only metadata to the left header content.
  - Removed run-mode copy from the selected-radar header so monitoring mode is shown only in the Monitoring settings block.
  - Kept header edit mode close to view mode and fixed bounded keyword/exclusion heading alignment.
  - Corrected active switch thumb geometry and guarded disabled switches from firing changes.
  - Pinned the SPA shell to the viewport and constrained hidden switch inputs so switch clicks cannot move the browser document scroll and visually blank the app.
  - Normalized legacy/incomplete browser-local radar overrides before rendering Settings.
  - Added a repeatable Playwright `settings:toggle-smoke` command that opens RU Settings, saves/reloads the global-search switch, injects a legacy override, clicks every switch in every editable block twice, and fails if `.app-shell` leaves the viewport.
- `Slice 0.6.3: ICP Radar signal validation loop`
  - Made `radar.definition.intent_signals` the canonical C1-C20 source for Settings, candidate `criteria_scores`, and `criteria_evidence`.
  - Added deterministic `ICPRadarValidationScorer` with `unreviewed`, `confirmed`, `corrected`, `rejected`, and `stale` status semantics.
  - Added browser-local signal validation overlay under `power-web-os-icp-radar-signal-validation`.
  - Updated shortlist ranking and candidate detail score grids to use effective score and visible score deltas.
  - Replaced criteria review UI with signal validation actions: confirm, correct, reject, mark stale, selected evidence refs, confidence override, and comments.
  - Regenerated ICP Radar demo artifacts so the top-level `criteria` alias is generated from `intent_signals` and no longer diverges.
- `Slice 0.6.3.1: Live mini ICP Radar run with OpenRouter web search`
  - Added `ТОиР Quick Live Radar` as a small live-search radar beside the stable XLSX radar.
  - Added `LiveICPRadarRunWorkflow` with optional `langgraph-dai` runtime metadata and local fallback runner.
  - Added provider-neutral `WebSearchProvider`, OpenRouter live provider, and recorded provider for tests.
  - Added dry-run and live CLI commands for search plan and provider-backed artifact generation.
  - Added frontend empty/present live artifact states, live run metadata, live shortlist, qualification, signals, evidence, and review flags.
  - Added source reachability filtering so model-produced fake URLs cannot support live candidates.
- `Slice 0.6.3.2: Align Live ICP Radar UX with table-first shortlist pattern`
  - Reworked `ТОиР Quick Live Radar` to use the same wide table, sticky identity column, inline preview, and in-shell detail view as fixture-backed ICP Radars.
  - Removed the live-only split/grid/detail visual pattern.
  - Updated ADRs, developer docs, user docs, demo docs, frontend contract tests, and visual smoke coverage for provider-backed shortlist UX.
- `Slice 0.6.3.3: Canonical Radar UX contract and live radar detail alignment`
  - Added a canonical ICP Radar UX contract and ADR.
  - Mapped fixture-backed and live radars into the same canonical shortlist columns, four-block preview, and tabbed detail view.
  - Removed provider/runtime metadata from the live shortlist and moved it into the candidate `Journal` tab.
  - Added frontend contract coverage for canonical columns, preview sections, status mapping, detail tabs, and journal-only runtime metadata.
- `Slice 0.6.3.4: Qualification evidence and review contract`
  - Extended live qualification results with source usage, source origin, trust/check policy, evidence findings, cross-validation, requirement evaluation, final assessment, and review-decision fields.
  - Replaced raw Q1/Q2 candidate detail rows with a table-first qualification review surface.
  - Added local approve/reject/correct actions for qualification assessment, plus backend and frontend contract coverage.
- `Slice 0.6.3.5: ICP Radar frontend feature decomposition`
  - Replaced the 4,000+ line ICP Radar screen with a thin screen wrapper plus a feature module under `frontend/src/features/icp-radar/`.
  - Split candidate views, live candidate views, criteria breakdown, settings, settings fields, header editor, detail primitives, and model helpers.
  - Lazy-loaded Settings into a separate frontend chunk and split i18n runtime initialization from the resource dictionary.
  - Added frontend architecture contract tests and documented the module boundary in ADR/developer/architecture docs.
- `Slice 0.6.3.6: Frontend CSS, i18n, and model boundary modularization`
  - Moved ICP Radar CSS into `frontend/src/features/icp-radar/icpRadar.css` while preserving design-system token import order.
  - Split i18n runtime initialization from EN/RU resource modules.
  - Split ICP Radar model helpers into focused model files for constants/types, validation scoring, radar metadata, live helpers, and settings definition helpers.
  - Expanded architecture and frontend contract tests to guard CSS ownership, i18n runtime/resource separation, Settings lazy loading, and model barrel boundaries.
- `Slice 0.6.3.7: ICP Radar component granularity and commentary pass`
  - Split remaining large ICP Radar view modules into fixture shortlist, fixture preview, fixture detail, live shortlist, live detail, settings block, settings search, qualification, monitoring, signals, scoring, and validation modules.
  - Kept public `candidateViews.tsx`, `liveCandidateViews.tsx`, and `model.tsx` as small barrel modules for stable imports.
  - Added module-boundary comments around non-obvious scan/preview/detail/settings responsibilities.
  - Added architecture tests for component file-size limits, barrel boundaries, and required module comments.
- `Slice 0.6.3.8: ICP Radar application boundary and adapter cleanup`
  - Added explicit `domain`, `adapters`, `application`, and `components` boundaries inside the ICP Radar feature.
  - Moved radar navigation, local demo overlays, settings draft actions, and review actions into application hooks.
  - Added fixture/live/empty radar adapters and canonical view-model contracts for future radar source types.
  - Moved catalog and radar detail header presentation out of the feature entrypoint.
  - Tightened architecture tests so screen orchestration cannot re-own storage, scoring, or provider-specific mapping.
- `Slice 0.6.3.9: ICP Radar CSS decomposition`
  - Split ICP Radar feature CSS into surface-owned modules under `frontend/src/features/icp-radar/styles/`.
  - Kept `icpRadar.css` as a small import entrypoint and added architecture tests for CSS ownership.
- `Slice 0.6.3.10: Frontend documentation and onboarding comments`
  - Added `frontend/src/features/icp-radar/README.md` with ownership map, data flow, and a guide for adding radar types through adapters.
  - Added boundary comments and architecture tests so onboarding documentation remains present and useful.
- `Slice 0.6.3.11: Qualification detail UX and requirement evaluation cleanup`
  - Cleaned up the live candidate qualification tab so collapsed rows stay scan-first and requirement fit moves into expanded detail.
  - Separated source refs, source names, source origin, trust/check policy, evidence findings, cross-validation, and human review controls.
  - Added localized requirement-fit and cross-validation copy plus contract tests for the new review panel.
- `Slice 0.6.3.12: Qualification evidence cards and integrated requirement fit`
  - Merged qualification evidence and source usage into self-contained evidence cards with optional excerpts.
  - Moved cross-validation into requirement-fit summary so expanded rows read as one evidence-backed decision chain.
  - Kept old live artifacts compatible through no-excerpt fallback copy.
- `Slice 0.6.3.13: Signal evidence cards and score evaluation cleanup`
  - Replaced the minimal live signal expanded view with a score-evaluation summary, evidence cards, and a review panel.
  - Added optional live signal evidence fields for source usages, source-linked facts, excerpts, cross-validation, and score rationale.
  - Reused the browser-local signal validation overlay for confirm, reject, stale, and correction decisions.
  - Kept old live artifacts compatible through fallback signal evidence cards.
- `Slice 0.7.0.1: Backend architecture guardrails`
  - Added a backend boundary ADR and documented backend ownership in architecture, developer, and contributor docs.
  - Updated local agent skills so backend slices must check OOP boundaries, repository isolation, and architecture contract tests.
  - Added `tests/test_backend_architecture_contract.py` with layer import checks, module-size guardrails, and temporary legacy-large Radar module allowlist.
  - Added a follow-up backlog slice for decomposing legacy-large Radar modules after persistence boundaries exist.
- `Slice 0.7.1: Persistence foundation`
  - Added SQLAlchemy/Alembic schema for `radars`, `radar_definitions`, and `radar_runs`.
  - Added application records, repository ports, async job ports, and SQLAlchemy repository adapters.
  - Added deterministic Radar catalog database seed command and SQLite migration/repository tests.
- `Slice 0.7.1.1: Backend developer onboarding guardrails`
  - Added local application and persistence README files with ownership, dependency, and extension rules.
  - Added backend module docstrings and comments for non-obvious persistence decisions.
  - Updated ADR, SAO, Developer Guide, agent skills, and architecture contract tests to require backend onboarding docs.
- `Slice 0.7.1.2: Live Radar backend extraction`
  - Split live Radar contracts, definition, normalization, service, OpenRouter adapter, and workflow wrapper into backend-owned layers.
  - Kept `live_icp_radar.py` as a compatibility facade and removed it from the legacy-large allowlist.
  - Preserved the existing live Radar CLI/artifact contract and added integration/workflow onboarding docs.

## Blocked Items

None.

## Open Questions

- Which CRM should be the first integration target: file export, HubSpot, Salesforce, Bitrix24, amoCRM, or another system?
- Which Russian/CIS data source should be first: procurement, HH, company websites, news, CRM history, or a partner ecosystem file?
- Should the first durable UI be static demo, lightweight local web app, or API-backed app after Slice 0.2?
- Should local persistence use JSON files or SQLite when Slice 0.9 starts?
- Should the repository remain public long term, or return to private after Wiki/documentation publication is validated?

## Next Recommended Task

Slice 0.7.6.6.1: Account handoff and role demand
