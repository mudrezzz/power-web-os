# Contributing

## Development Principles

- Work in small roadmap slices.
- Keep the project runnable after each change.
- Keep domain logic separate from infrastructure.
- Keep recommendations explainable and evidence-backed.
- Do not commit secrets, `.env` files, or `.external/` research checkouts.

## Before Opening a Change

```bash
python -m pytest
python -m power_web_os.demo
```

Update documentation when changing architecture, setup, public behavior, demo behavior, or user-facing functionality.

## Source Requirements

Use `power_web_os_concept.md` and the product PDF as the product source of truth. Record assumptions in `ROADMAP.md` or architecture docs.
