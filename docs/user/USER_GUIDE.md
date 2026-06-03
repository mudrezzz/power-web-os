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
python demo/run_demo.py
```

The output is a JSON Access Plan with ranked routes, evidence refs, risks, owners, expected state changes, and human review flags.

## Current Limitations

- No web UI yet.
- No live CRM integration yet.
- No live source connectors yet.
- LangGraph workflow wrapper is the next planned slice.
