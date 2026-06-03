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
- `AccessPlanningState`
- `AccessPlanningWorkflow`

The deterministic planner owns route scoring. `AccessPlanningWorkflow` orchestrates typed state, planner invocation, artifact shaping, and workflow metadata. `AccountRadar` builds the portfolio read model from generated Access Plans and owns deterministic account ranking. It uses `langgraph-dai` when the optional `agent` extra is installed and falls back to a local runner for base tests.

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

Do not put CRM/source connector logic directly inside domain classes. Add ports/tools and keep connector calls auditable.

## Frontend Demo

The frontend is a local React + TypeScript + Vite app in `frontend/`.

Current structure:

```text
frontend/src/App.tsx                  App state and artifact loading
frontend/src/components/              Token-based UI primitives
frontend/src/i18n.ts                  EN/RU UI resources and locale initialization
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
- Keep unfinished navigation entries visible only as planned placeholders; do not fake unavailable functionality.

The frontend default locale is `en`. The supported locales are `en` and `ru`, and the selected locale is stored in browser `localStorage`. UI chrome is localized; generated account, signal, evidence, and route text remains artifact data unless a future slice adds translated artifacts.

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
