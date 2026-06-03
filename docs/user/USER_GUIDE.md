# User Guide

## What Power Web OS Does

Power Web OS helps a sales or ABM team answer four questions for a target account:

1. Why is this account relevant now?
2. Who influences the buying decision?
3. Which access routes are allowed by our playbook?
4. What next move should a human review and execute?

## Current Demo

The current demo uses a fictional account, `Vitamin Bank`, with:

- hiring signal for data platform roles;
- procurement signal for BI consulting;
- identified Head of Data;
- partner/integrator hypothesis;
- missing economic buyer and security gatekeeper.

Run:

```bash
python demo/run_demo.py generate-access-plan
npm --prefix ./frontend run dev
```

Open the Vite URL printed by the frontend command. The demo screen shows:

- account context and ICP fit;
- signal evidence with confidence;
- Power Web Lite roles;
- unresolved buying-committee gaps;
- top Access Plan routes;
- route rationale, risk, owner, evidence refs, and expected state change;
- human review status from the playbook.

The generated JSON artifact is also available at:

- `demo/output/access_plan.json`
- `frontend/public/demo/access_plan.json`

## Current Limitations

- No live CRM integration yet.
- No live source connectors yet.
- No production API server yet.
- No persisted review or feedback loop yet.
