# Developer Guide

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m power_web_os.demo
```

Direct checkout demo without installing:

```bash
python demo/run_demo.py
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

This deterministic planner is the product baseline used to lock domain behavior before wrapping it in LangGraph.

## LangGraph Workflow Direction

The next slice should add an `AccessPlanningWorkflow` following the referenced platform's extension rules:

1. Add typed workflow state.
2. Implement a workflow based on `BaseWorkflow`.
3. Keep domain scoring in domain services.
4. Emit evidence refs, unresolved gaps, and review flags.
5. Preserve deterministic tests.

Do not put CRM/source connector logic directly inside domain classes. Add ports/tools and keep connector calls auditable.

## Test Commands

```bash
python -m pytest
python -m power_web_os.demo
python demo/run_demo.py
```

## Documentation Rules

Update `ROADMAP.md`, architecture docs, demo docs, and user docs in the same slice when behavior changes.
