# Power Web OS

Power Web OS is a white-box account access planning platform for complex B2B sales.

It turns public and first-party account signals into explainable account plays: which ICP-matching account matters now, who influences the deal, which access route is allowed by the sales playbook, and what next move should be reviewed and executed by a human.

The proposed repository name is `power-web-os`.

## Product Scope

Power Web OS is not a CRM, contact database, or outreach automation tool. It is a strategy layer above CRM:

```text
ICP Radar + Dynamic Power Web + Sales Playbook + Access Plan + CRM Feedback = managed account access.
```

The source requirements are:

- [power_web_os_concept.md](power_web_os_concept.md)
- [Power Web OS - product concept PDF](<Power Web OS — концепция продукта.pdf>)

The AI-agent runtime must use [`mudrezzz/langgraph-document-ai-platform`](https://github.com/mudrezzz/langgraph-document-ai-platform). A local research checkout may exist in `.external/langgraph-document-ai-platform`, but `.external/` is intentionally excluded from Git.

## Current Status

Slice 0.6 is implemented. The repository contains:

- documented product and architecture baseline;
- Python domain skeleton for `Account`, `Signal`, `PowerWebRole`, `Playbook`, and `AccessPlan`;
- deterministic Access Planner baseline wrapped by `AccessPlanningWorkflow`;
- deterministic Power Web Lite board read model added to Access Plan artifacts;
- deterministic Playbook Analysis read model with current and no-partner-motion route previews;
- deterministic ICP Radar XLSX import for the ТОиР/SIBUR-style fixture;
- experimental `ТОиР Quick Live Radar` CLI flow that runs a small provider-backed ICP Radar through OpenRouter web search when `.[agent]` and local credentials are available;
- initial Python/FastAPI backend boundary with health and OpenAPI contracts;
- SQLAlchemy/Alembic persistence foundation for Radar catalog, Radar definitions, and durable Radar run state;
- backend architecture guardrails for API, application, domain, persistence, integrations, workflows, jobs, and long-running Radar execution;
- browser-local editable ICP Radar definitions with structured sources, natural-language account qualification rules, intent signals, fit/intent/tier scoring presets, and validation;
- realistic portfolio demo input, Account Radar artifact, and generated Access Plan artifacts;
- React + TypeScript + Vite frontend demo inside a bounded Power Web OS workspace shell with ICP Radar, Accounts, Access Plans, Account Map, and Playbook screens;
- EN/RU UI and visible demo data switching;
- pytest baseline.

The current product direction is an ABM-oriented `ICP Radar` layer before Power Web work: configurable ICP profiles, account discovery, recurring signal monitoring, human validation of found signals, transparent scoring, and a `take into work` handoff into Power Web discovery. The first realistic fixture uses the ТОиР/SIBUR-style analysis workbook.

The next recommended product slice is `Slice 0.6.4: Take-into-work handoff from ICP Radar to Power Web`. `Slice 0.7.1` added the first backend persistence foundation, and `Slice 0.6.3` added browser-local ICP Radar signal validation: users can confirm, correct, reject, or mark C1-C20 signals stale, and the visible shortlist score/ranking updates without mutating generated artifacts.

## Quick Start

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m power_web_os.demo generate-icp-radar
python -m power_web_os.demo generate-icp-radar-catalog
python -m power_web_os.demo generate-account-radar
npm install --prefix ./frontend
npm --prefix ./frontend run dev
```

Optional local Radar persistence seed:

```bash
python -m alembic upgrade head
python -m power_web_os.demo seed-radar-db
```

The default local database URL is `sqlite:///./demo/output/power_web_os.sqlite3`. Set `POWER_WEB_OS_DATABASE_URL=postgresql+psycopg://user:password@host:5432/power_web_os` for a PostgreSQL-backed environment.

Without installing the package, run the checkout demo directly:

```bash
python demo/run_demo.py generate-icp-radar
python demo/run_demo.py generate-icp-radar-catalog
python demo/run_demo.py generate-account-radar
npm --prefix ./frontend run dev
```

For the single-account debug path:

```bash
python -m power_web_os.demo generate-access-plan
```

To install the required LangGraph document AI framework for agent workflow work:

```bash
python -m pip install -e ".[agent,dev]"
```

To run the first local backend API boundary:

```bash
python -m pip install -e ".[api,dev]"
power-web-os-api
# Open http://127.0.0.1:8000/health or http://127.0.0.1:8000/docs
```

Optional live mini ICP Radar run:

```bash
copy .env.example .env
# Fill OPENROUTER_API_KEY and OPENROUTER_MODEL locally.
python -m power_web_os.demo run-live-mini-icp-radar --dry-run-plan
python -m power_web_os.demo run-live-mini-icp-radar --live
```

The live command writes `demo/output/live_mini_icp_radar_run.json` and `frontend/public/demo/live_mini_icp_radar_run.json` only from actual provider output. It does not fabricate candidates when OpenRouter returns no usable evidence or rejects the credentials.

Build checks:

```bash
python -m pytest
npm --prefix ./frontend run build
npm --prefix ./frontend run visual:smoke
```

## Documentation

- [Roadmap](ROADMAP.md)
- [System Architecture Overview](docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md)
- [Architecture Decision Records](docs/adr/README.md)
- [Contributor Guide](docs/contributor/CONTRIBUTING.md)
- [Developer Guide](docs/developer/DEVELOPER_GUIDE.md)
- [User Guide](docs/user/USER_GUIDE.md)
- [Demo](demo/README.md)
- [QA screenshots and wiki publishing](docs/qa/README.md)

## GitHub Wiki

Local documentation and screenshots are the source of truth. To build the GitHub Wiki package locally:

```bash
python scripts/publish_github_wiki.py --dry-run
```

To publish it to the repository Wiki:

```bash
python scripts/publish_github_wiki.py
```

The current Wiki target is:

```text
https://github.com/mudrezzz/power-web-os/wiki
```

## Development Model

Development proceeds through small vertical slices. Each slice should leave the product runnable, tested, documented, and demonstrable.
