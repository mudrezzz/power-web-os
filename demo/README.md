# Demo

## Purpose

The demo shows the current Power Web OS loop: a six-account portfolio fixture is ranked by Account Radar, each account is converted into a workflow-backed Access Plan artifact, and the result is rendered inside the local Power Web OS workspace shell.

## What The Demo Shows

- Account Radar ranking across six synthetic accounts.
- Account signals with evidence refs.
- Power Web Lite roles and missing roles.
- Sales playbook routes and human review policy.
- Ranked Access Plan routes per selected account with score, reason, risk, owner, and expected state change.
- Workflow metadata showing whether `langgraph-dai` was available.
- A React TypeScript frontend using the committed design system.
- A durable app shell with sidebar navigation, top bar account context, active `Accounts`, clickable `Access Plans`, and planned placeholders for future workspaces.
- A bounded SPA frame with internal workspace scrolling and EN/RU switching for UI chrome plus visible deterministic demo data.

## How To Run

```bash
python -m pip install -e ".[dev]"
python -m power_web_os.demo generate-account-radar
npm install --prefix ./frontend
npm --prefix ./frontend run dev
```

Or run directly from the checkout:

```bash
python demo/run_demo.py generate-account-radar
npm --prefix ./frontend run dev
```

Single-account debug artifact:

```bash
python demo/run_demo.py generate-access-plan
```

## Expected Result

The Python command prints and writes JSON for the ranked portfolio. The output should include six ranked accounts and a matching generated Access Plan artifact for every account.

The frontend command prints a local Vite URL. Open it to inspect Account Radar, switch the UI between EN/RU from the top bar if needed, then click an account row to inspect that account's Access Plan visually inside the Power Web OS shell.

## Demo Data

- `demo/sample_account.json`
- `demo/sample_portfolio.json`
- `demo/output/access_plan.json`
- `demo/output/account_radar.json`
- `frontend/public/demo/access_plan.json`
- `frontend/public/demo/account_radar.json`
- `frontend/public/demo/access_plans/{account_id}.json`

## Known Limitations

- The planner is deterministic.
- No live source connectors yet.
- No CRM export yet.
- No persisted review or feedback loop yet.
