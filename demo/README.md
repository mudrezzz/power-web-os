# Demo

## Purpose

The demo shows the first closed Power Web OS loop: a target account fixture is converted into a workflow-backed Access Plan artifact and rendered inside the local Power Web OS workspace shell.

## What The Demo Shows

- Account signals with evidence refs.
- Power Web Lite roles and missing roles.
- Sales playbook routes and human review policy.
- Ranked Access Plan routes with score, reason, risk, owner, and expected state change.
- Workflow metadata showing whether `langgraph-dai` was available.
- A React TypeScript frontend using the committed design system.
- A durable app shell with sidebar navigation, top bar account context, active `Access Plans`, and planned placeholders for future workspaces.

## How To Run

```bash
python -m pip install -e ".[dev]"
python -m power_web_os.demo generate-access-plan
npm install --prefix ./frontend
npm --prefix ./frontend run dev
```

Or run directly from the checkout:

```bash
python demo/run_demo.py generate-access-plan
npm --prefix ./frontend run dev
```

## Expected Result

The Python command prints and writes JSON for the `Vitamin Bank` sample account. The output should include three ranked routes and unresolved gaps for missing roles.

The frontend command prints a local Vite URL. Open it to inspect the same Access Plan visually inside the Power Web OS shell.

## Demo Data

- `demo/sample_account.json`
- `demo/output/access_plan.json`
- `frontend/public/demo/access_plan.json`

## Known Limitations

- The planner is deterministic.
- No live source connectors yet.
- No CRM export yet.
- No persisted review or feedback loop yet.
