# Contributing

## Development Principles

- Work in small roadmap slices.
- Keep the project runnable after each change.
- Keep domain logic separate from infrastructure.
- Keep backend code split by responsibility: API entrypoints, application use
  cases, domain rules, persistence adapters, integrations, workflows, and jobs.
- Do not put SQLAlchemy queries in FastAPI routes or external provider calls in
  domain services.
- Treat worker tasks and schedulers as entrypoints that call application
  services, not as places for scoring, normalization, or persistence logic.
- Keep recommendations explainable and evidence-backed.
- Do not commit secrets, `.env` files, or `.external/` research checkouts.

## Before Opening a Change

```bash
python -m pytest
python -m power_web_os.demo
```

When backend boundaries change, also run:

```bash
python -m pytest tests/test_backend_architecture_contract.py
```

Update documentation when changing architecture, setup, public behavior, demo behavior, or user-facing functionality.

## Source Requirements

Use `power_web_os_concept.md` and the product PDF as the product source of truth. Record assumptions in `ROADMAP.md` or architecture docs.
