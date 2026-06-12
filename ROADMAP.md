# ROADMAP.md

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
  - Real editing remains `Slice 0.6.5`.
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

- Status: `Backlog`
- Goal: Add human validation for found ICP Radar signals and make validation affect the candidate score.
- User value: A user can prevent wrong, distorted, or stale information from driving account prioritization.
- Scope:
  - Add `SignalValidation` states: `unreviewed`, `confirmed`, `corrected`, `rejected`, `stale`.
  - Add correction fields for criterion, strength, confidence, summary, and evidence mapping.
  - Add a deterministic rescore service that uses validated signal state.
  - Add UI controls to confirm, correct, reject, or mark a signal stale.
  - Show before/after score impact and audit history.
  - Keep validation local/demo-state only until persistence slice.
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
  - The action history is preserved in the artifact or local state.
- Risks:
  - Browser-only validation can be mistaken for persisted workflow; label it as local demo state until persistence exists.

### Slice 0.6.4: Take-into-work handoff from ICP Radar to Power Web

- Status: `Backlog`
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

- Status: `Backlog`
- Goal: Add the first editable radar configuration workflow over a local/demo radar definition.
- User value: A user can adjust ICP Radar criteria, score weights/thresholds, source scope, and run cadence, then preview how the shortlist would change.
- Scope:
  - Add edit mode for radar name/profile, source selection, run cadence, lookback window, and full/incremental mode.
  - Add editable criteria weight/strength settings while preserving C1-C20 criterion identity.
  - Add editable tier thresholds with validation.
  - Add a read-only preview of scoring impact on the current fixture candidates.
  - Store edited configuration in local demo state or a generated local JSON artifact.
- Out of scope:
  - Multi-user configuration governance.
  - Production database persistence.
  - Live connector configuration secrets.
  - Arbitrary formula scripting.
- Implementation notes:
  - Use constrained form controls, not free-form executable formulas.
  - Keep original fixture configuration recoverable.
  - Clearly separate source workbook scores from user-adjusted scoring simulation.
- Tests:
  - Unit tests for configuration validation and scoring preview.
  - Frontend contract tests for edit mode, validation errors, reset, and preview impact.
  - `python -m pytest`.
  - `npm --prefix ./frontend run build`.
- Docs:
  - Update user/developer docs with editable configuration and preview rules.
- Demo impact:
  - Demo shows radar setup as a controllable ABM object, not only a report.
- Acceptance criteria:
  - User can edit constrained radar settings locally.
  - Invalid thresholds/cadence values are rejected.
  - Preview shows candidate score/tier changes without mutating source artifact.
  - User can reset to fixture configuration.
- Risks:
  - Users may expect production persistence; label local/demo persistence clearly.

### Slice 0.6.6: ICP Radar run history and monitoring schedule loop

- Status: `Backlog`
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

## Blocked Items

None.

## Open Questions

- What is the first persistence mechanism for signal validation decisions before Slice 0.9: browser local state, generated JSON artifact, or lightweight local state file?
- Which CRM should be the first integration target: file export, HubSpot, Salesforce, Bitrix24, amoCRM, or another system?
- Which Russian/CIS data source should be first: procurement, HH, company websites, news, CRM history, or a partner ecosystem file?
- Should the first durable UI be static demo, lightweight local web app, or API-backed app after Slice 0.2?
- Should local persistence use JSON files or SQLite when Slice 0.9 starts?
- Should the repository remain public long term, or return to private after Wiki/documentation publication is validated?

## Next Recommended Task

Implement `Slice 0.6.3: ICP Radar signal validation loop`.
