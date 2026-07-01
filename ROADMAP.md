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

- Status: Ready
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

- Status: Backlog
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

- Status: Backlog
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

- Status: Backlog
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

### Slice 0.7.6.4.5: First recorded TOIR signal monitoring loop

- Status: Backlog
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

- Status: Backlog
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

The next recommended task is Slice 0.7.6.4.1: Pipeline documentation registry and signal-monitoring TO BE. Use the roadmap tracker first, then regenerate ROADMAP.md and docs/roadmap/slices.export.jsonl before committing.
