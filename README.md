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
- browser-local editable ICP Radar definitions with structured sources, natural-language account qualification rules, intent signals, fit/intent/tier scoring presets, and validation;
- realistic portfolio demo input, Account Radar artifact, and generated Access Plan artifacts;
- React + TypeScript + Vite frontend demo inside a bounded Power Web OS workspace shell with ICP Radar, Accounts, Access Plans, Account Map, and Playbook screens;
- EN/RU UI and visible demo data switching;
- pytest baseline.

The current product direction is an ABM-oriented `ICP Radar` layer before Power Web work: configurable ICP profiles, account discovery, recurring signal monitoring, human validation of found signals, transparent scoring, and a `take into work` handoff into Power Web discovery. The first realistic fixture uses the ТОиР/SIBUR-style analysis workbook.

The next recommended product slice is `Slice 0.6.3: ICP Radar signal validation loop`. `Slice 0.6.5.2` corrected the radar settings UX before durable validation and take-into-work: qualification filters and intent signals remain structured objects, but the UI now exposes business-language rules, source entities, generated codes, scoring presets, and a compact validator summary instead of developer-facing field/operator/value controls.

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
