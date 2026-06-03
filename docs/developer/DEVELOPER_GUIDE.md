# Developer Guide

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m power_web_os.demo generate-access-plan
npm install --prefix ./frontend
npm --prefix ./frontend run dev
```

Direct checkout demo without installing:

```bash
python demo/run_demo.py generate-access-plan
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
- `AccessPlanningState`
- `AccessPlanningWorkflow`

The deterministic planner owns route scoring. `AccessPlanningWorkflow` orchestrates typed state, planner invocation, artifact shaping, and workflow metadata. It uses `langgraph-dai` when the optional `agent` extra is installed and falls back to a local runner for base tests.

## Access Planning Workflow

The first product loop is:

```text
demo/sample_account.json
-> AccessPlanningWorkflow
-> demo/output/access_plan.json
-> frontend/public/demo/access_plan.json
-> Vite demo UI
```

Do not put CRM/source connector logic directly inside domain classes. Add ports/tools and keep connector calls auditable.

## Frontend Demo

The frontend is a local React + TypeScript + Vite app in `frontend/`.

Rules:

- Import `ui-design-system/colors_and_type.css`.
- Use `lucide-react` for icons.
- Keep UI copy sentence case, with uppercase only for mono eyebrow labels.
- Load the artifact from `/demo/access_plan.json`.

## Test Commands

```bash
python -m pytest
python -m power_web_os.demo generate-access-plan
python demo/run_demo.py generate-access-plan
npm --prefix ./frontend run build
```

## Documentation Rules

Update `ROADMAP.md`, architecture docs, demo docs, and user docs in the same slice when behavior changes.
