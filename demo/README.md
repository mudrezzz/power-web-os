# Demo

## Purpose

The demo shows the smallest current Power Web OS flow: a target account fixture is converted into a ranked, explainable Access Plan.

## What The Demo Shows

- Account signals with evidence refs.
- Power Web Lite roles and missing roles.
- Sales playbook routes and human review policy.
- Ranked Access Plan routes with score, reason, risk, owner, and expected state change.

## How To Run

```bash
python -m pip install -e ".[dev]"
python -m power_web_os.demo
```

Or run directly from the checkout:

```bash
python demo/run_demo.py
```

## Expected Result

The command prints JSON for the `Vitamin Bank` sample account. The output should include three ranked routes and unresolved gaps for missing roles.

## Demo Data

- `demo/sample_account.json`

## Known Limitations

- The planner is deterministic and local.
- No LangGraph workflow wrapper yet.
- No live source connectors yet.
- No CRM export yet.
