# User Guide

## What Power Web OS Does

Power Web OS helps a sales or ABM team answer four questions for a target account:

1. Why is this account relevant now?
2. Who influences the buying decision?
3. Which access routes are allowed by our playbook?
4. What next move should a human review and execute?

## Current Demo

The current demo uses a six-account fictional portfolio. It includes `Vitamin Bank` plus five additional accounts with varied signal strength, missing roles, and access routes.

The portfolio is ranked by Account Radar using deterministic ICP fit, signal strength, best Access Plan route score, and missing-role penalty.

Run:

```bash
python demo/run_demo.py generate-account-radar
npm --prefix ./frontend run dev
```

Open the Vite URL printed by the frontend command. The demo opens in the Power Web OS workspace shell with `Accounts` active. It shows:

- sidebar navigation for `Accounts`, `Account Map`, `Access Plans`, `Signals`, and `Playbook`;
- Account Radar ranking across six target accounts;
- radar score, stage, signal count, missing roles, best route, owner, and review status;
- account context, route count, workflow runtime, and ICP fit for the selected account in the top bar;
- planned placeholder states for product areas that are not implemented yet;
- click-through from an account row to that account's `Access Plans` screen;
- board coverage with visible and missing power figures;
- signal evidence with confidence and source refs;
- top Access Plan routes;
- route rationale, risk, owner, evidence refs, and expected state change;
- human review status from the playbook.

The generated JSON artifact is also available at:

- `demo/output/access_plan.json`
- `demo/output/account_radar.json`
- `frontend/public/demo/access_plan.json`
- `frontend/public/demo/account_radar.json`
- `frontend/public/demo/access_plans/{account_id}.json`

## Current Limitations

- No live CRM integration yet.
- No live source connectors yet.
- No production API server yet.
- No persisted review or feedback loop yet.
