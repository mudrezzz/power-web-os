# Developer Guide

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m power_web_os.demo generate-account-radar
npm install --prefix ./frontend
npm --prefix ./frontend run dev
```

Direct checkout demo without installing:

```bash
python demo/run_demo.py generate-account-radar
npm --prefix ./frontend run dev
```

Install the required LangGraph document AI framework when working on agent workflows:

```bash
python -m pip install -e ".[agent,dev]"
```

## Repository Layout

```text
src/power_web_os/      Product domain and application baseline
tests/                 Unit and smoke tests
demo/                  Demo fixtures and run instructions
frontend/              React TypeScript Vite demo app
docs/                  Architecture, ADRs, user and contributor docs
.external/             Local research/vendor checkouts, not committed
```

## Domain Baseline

The current Python package contains:

- `Account`
- `Signal`
- `Evidence`
- `PowerWebRole`
- `Playbook`
- `AccessRoute`
- `AccessPlan`
- `DeterministicAccessPlanner`
- `AccountRadar`
- `PowerWebBoardBuilder`
- `PlaybookAnalysisBuilder`
- `AccessPlanningState`
- `AccessPlanningWorkflow`

The deterministic planner owns route scoring. `AccessPlanningWorkflow` orchestrates typed state, planner invocation, artifact shaping, and workflow metadata. `AccountRadar` builds the portfolio read model from generated Access Plans and owns deterministic account ranking. `PowerWebBoardBuilder` builds the selected-account board read model from the generated Access Plan and current account roles/missing roles. `PlaybookAnalysisBuilder` builds a read-only explanation of playbook effects over the generated routes, including the current playbook and the deterministic `no_partner_motion` what-if variant. The workflow uses `langgraph-dai` when the optional `agent` extra is installed and falls back to a local runner for base tests.

## ICP Radar Funnel

The next ABM layer is `ICP Radar`. It sits before the current Account / Power Web / Access Plan loop.

Terminology:

- `ICP Radar`: product/ICP-specific radar that discovers and monitors candidate accounts.
- `AccountRadar`: current deterministic portfolio read model in code. It may remain as an internal compatibility name until the ICP Radar layer is implemented.
- `Account discovery`: stable or manually imported legal-entity discovery, for example companies inside a holding.
- `Signal monitoring`: recurring search for current evidence and buying signals against discovered accounts.
- `Radar candidate`: an account that has been scored but has not yet been accepted into Power Web work.

Expected first fixture:

- Use the SIBUR-style ТОиР automation spreadsheet as the source fixture.
- Model the `Criteria` sheet as `SignalCriterion` records.
- Model the `ICP Matrix` sheet as legal entities, evidence refs, criterion scores, fit/intent/trigger totals, and tier.
- Model `Sources` as evidence-source metadata.
- Convert demo company names and people to Russian-language examples when the UI moves to this fixture.

Expected future domain objects:

```text
ICPProfile
RadarDefinition
AccountDiscoveryRule
SignalCriterion
SignalObservation
SignalValidation
ICPScoringFormula
RadarCandidate
RadarRun
```

Discovery and monitoring must stay separate. Discovery can be run once or imported manually because legal-entity structure changes slowly. Monitoring should run repeatedly and support incremental mode through evidence fingerprints so previously seen facts are not scored as new signals.

Signal validation is a first-class domain concern. A user must be able to:

- confirm a found signal;
- correct its criterion, strength, confidence, summary, or evidence mapping;
- reject it as wrong or distorted;
- mark it stale when it is no longer actionable.

Validated signals feed the final score. Rejected and stale signals must reduce or remove their scoring contribution while preserving evidence and audit history. The score explanation must show raw observations, validation decisions, and the resulting fit/intent/trigger contribution.

## Access Planning Workflow

The first product loop is:

```text
demo/sample_portfolio.json
-> AccountRadar
-> AccessPlanningWorkflow per account
-> demo/output/account_radar.json
-> frontend/public/demo/account_radar.json
-> frontend/public/demo/access_plans/{account_id}.json
-> Vite demo UI
```

The single-account debug path remains available:

```bash
python -m power_web_os.demo generate-access-plan
```

Portfolio fixture entries use the existing `{ account, playbook }` shape with a small `stage` field for Account Radar display.

Access Plan artifacts include a non-breaking `power_web_board` field:

```text
power_web_board.summary
power_web_board.nodes[]
power_web_board.edges[]
power_web_board.route_path[]
```

The board read model is deterministic and belongs to `src/power_web_os/board.py`. It should stay presentation-friendly but source-of-truth-neutral: do not put graph database behavior, editing state, CRM state, or live source extraction in this builder.

Access Plan artifacts also include a non-breaking `playbook_analysis` field:

```text
playbook_analysis.contract_version
playbook_analysis.current
playbook_analysis.variants[]
*.route_decisions[]
*.route_preview.routes[]
```

The playbook read model is deterministic and belongs to `src/power_web_os/playbook_analysis.py`. It explains allowed routes, blocked channels, available assets, review rules, policy decisions, and generated route previews. The `no_partner_motion` variant is generated at artifact-build time by disabling `partner_intro` and partner-case assets, then running the Python planner again. Frontend code must render this payload; it must not duplicate planner scoring or policy logic.

Do not put CRM/source connector logic directly inside domain classes. Add ports/tools and keep connector calls auditable.

## Frontend Demo

The frontend is a local React + TypeScript + Vite app in `frontend/`.

Current structure:

```text
frontend/src/App.tsx                  App state and artifact loading
frontend/src/components/              Token-based UI primitives
frontend/src/i18n.ts                  EN/RU UI resources and locale initialization
frontend/src/demoLocalization.ts      Presentation-layer localization for deterministic demo data
frontend/src/layout/                  Power Web OS shell, sidebar, top bar
frontend/src/screens/                 Product screens and planned placeholders
frontend/src/styles.css               Design-system-based app styling
```

Rules:

- Import `ui-design-system/colors_and_type.css`.
- Use `ui-design-system/app-prototype/AppShell.jsx` for product shell structure.
- Use the relevant `ui-design-system/app-prototype/*Screen.jsx` file before implementing a screen.
- Use `lucide-react` for icons.
- Keep UI copy sentence case, with uppercase only for mono eyebrow labels.
- Add visible UI strings through `frontend/src/i18n.ts` and keep English/Russian resources synchronized.
- Keep the app shell viewport-bounded; `body` should not be the normal scroll container for product screens.
- Put scrolling inside workspace panes and dense table/card wrappers.
- Use `min-width: 0`, wrapping, ellipsis, or owned horizontal scroll so text never overlaps neighboring columns.
- Load the portfolio artifact from `/demo/account_radar.json`.
- Load selected-account plans from `/demo/access_plans/{account_id}.json`.
- Render the selected account's Power Web Lite board from `artifact.power_web_board` on `Account Map`.
- Render the selected account's playbook analysis from `artifact.playbook_analysis` on `Playbook`.
- Keep unfinished navigation entries visible only as planned placeholders; do not fake unavailable functionality.

The frontend default locale is `en`. The supported locales are `en` and `ru`, and the selected locale is stored in browser `localStorage`. UI chrome is localized through `i18n.ts`; visible deterministic artifact values such as stages, owners, route titles, rationale, risks, state changes, signal summaries, and missing-role labels are localized in `demoLocalization.ts`. Keep raw source refs, IDs, company names, and person names as artifact data unless a slice explicitly changes that policy.

## Test Commands

```bash
python -m pytest
python -m power_web_os.demo generate-account-radar
python -m power_web_os.demo generate-access-plan
python demo/run_demo.py generate-account-radar
python demo/run_demo.py generate-access-plan
npm --prefix ./frontend run build
```

## Documentation Rules

Update `ROADMAP.md`, architecture docs, demo docs, and user docs in the same slice when behavior changes.
