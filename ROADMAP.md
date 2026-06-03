# ROADMAP.md

## Product Vision

Power Web OS helps B2B sales and ABM teams stop working target accounts blindly. It gathers account signals, builds a dynamic Power Web around the deal, applies the customer's sales playbook, and produces explainable Access Plans with human review before execution.

## Source Requirements

Primary requirements:

- `power_web_os_concept.md`
- `Power Web OS — концепция продукта.pdf`

Reference framework:

- `mudrezzz/langgraph-document-ai-platform`
- local research checkout: `.external/langgraph-document-ai-platform` when present

## Status Legend

- `Backlog`: known but not ready or not prioritized
- `Ready`: ready to implement
- `In Progress`: currently being worked on
- `Blocked`: cannot proceed without clarification or dependency
- `Done`: completed and validated

## Current Iteration

### Iteration 0: Product foundation

Goal:

- Establish repository structure, product documentation, architecture baseline, demo baseline, tests, Git, and GitHub.

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
- Tests:
  - `python -m pytest`
- Docs:
  - README and docs skeleton updated for Power Web OS.
- Demo impact:
  - `python -m power_web_os.demo` prints a sample Access Plan.
- Acceptance criteria:
  - Project has clear entry point.
  - Baseline tests pass.
  - Git repository exists with initial commit.
  - GitHub setup completed or manual command documented.

### Slice 0.2: LangGraph Access Planning workflow

- Status: `Ready`
- Goal: Wrap the deterministic planner in a `langgraph-dai` workflow with typed state and node audit.
- User value: Access planning becomes compatible with the required AI-agent runtime.
- Scope:
  - Add workflow state contracts.
  - Add `AccessPlanningWorkflow` based on the framework's `BaseWorkflow` pattern.
  - Preserve deterministic local execution for tests.
  - Emit node-level evidence and gaps.
- Out of scope:
  - External source scraping.
  - CRM writes.
- Tests:
  - Unit tests for workflow state and route ranking.
  - Smoke demo still works.
- Docs:
  - Developer guide workflow section.
- Demo impact:
  - Demo command can choose deterministic or workflow runtime.
- Acceptance criteria:
  - The project imports and uses `langgraph-dai` in the agent workflow layer.
  - The workflow output includes evidence refs, unresolved gaps, and review flags.

### Slice 0.3: Account Radar ingestion stub

- Status: `Backlog`
- Goal: Add a typed ingestion path for account signals from local fixture files.
- User value: The product can show signal-to-plan flow from input data, not hand-built objects.
- Scope:
  - Fixture schema for accounts, signals, roles, and evidence.
  - Parser/normalizer.
  - Validation errors and quality notes.
- Out of scope:
  - Live web/API connectors.

### Slice 0.4: Power Web Lite read model

- Status: `Backlog`
- Goal: Store and expose a minimal graph-like read model for roles, people, partners, competitors, and missing stakeholders.
- User value: Users can inspect why a route was recommended.
- Scope:
  - Domain model expansion.
  - Postgres-ready repository interface.
  - In-memory repository for tests.

### Slice 0.5: Human review gate for Access Plans

- Status: `Backlog`
- Goal: Add HITL approval semantics for Access Plans and outreach drafts.
- User value: Sensitive recommendations are not executed without review.
- Scope:
  - Review status model.
  - Approval/rework/reject transitions.
  - Audit trail.

### Slice 0.6: Frontend design-system validator

- Status: `Backlog`
- Goal: Add an automated validator that catches frontend deviations from `ui-design-system/`.
- User value: UI implementation stays consistent with the Power Web OS design system instead of relying only on manual review.
- Scope:
  - Add a script such as `scripts/check_frontend_design_system.py`.
  - Detect hardcoded hex colors in frontend code.
  - Detect direct `box-shadow`, `border-radius`, `font-family`, and common color declarations when `var(--*)` should be used.
  - Detect emoji and exclamation marks in UI strings.
  - Check that frontend entry styles import `ui-design-system/colors_and_type.css`.
  - Add tests or smoke fixtures for the validator.
- Out of scope:
  - Full visual regression testing.
  - Pixel-perfect screenshot comparison.
- Tests:
  - Unit tests for allowed and disallowed snippets.
  - Smoke command documented in developer guide.
- Docs:
  - Document validator usage in the developer guide once implemented.
  - Mention it in frontend contribution rules.

## Completed Slices

- `Slice 0.1: Bootstrap Power Web OS repository`
  - Created product-specific documentation baseline.
  - Added Python package skeleton and deterministic Access Planner.
  - Added demo fixture and demo runner.
  - Added pytest baseline.
  - Initialized Git, created the private GitHub repository, and pushed `main`.

## Blocked Items

None.

## Open Questions

- Which CRM should be the first integration target: HubSpot, Salesforce, Bitrix24, amoCRM, or file export?
- Which Russian/CIS data source should be first: procurement, HH, company websites, news, or CRM history?
- Should the first UI be a web app, notebook-style analyst workspace, or API-first backend?
- Should the repository remain proprietary/private long term?

## Next Recommended Task

Complete `Slice 0.2: LangGraph Access Planning workflow`.
