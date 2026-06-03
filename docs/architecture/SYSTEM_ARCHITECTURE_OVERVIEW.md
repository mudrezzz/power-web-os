# System Architecture Overview

## Product Context

Power Web OS is a strategy layer for complex B2B sales. It finds account signals, builds a dynamic influence map around a target account, applies customer-specific sales playbook rules, and recommends explainable access routes.

The product must use `mudrezzz/langgraph-document-ai-platform` for the AI-agent workflow layer.

## Architectural Goals

- Keep recommendations white-box and evidence-backed.
- Keep CRM as system of record and Power Web OS as system of strategy.
- Keep humans in control of sensitive commercial actions.
- Support async batch analysis for 50-100 account MVP pilots.
- Preserve source provenance, route explanations, task audit, and review history.

## Current Product Perimeter

The current baseline has:

- domain entities for account access planning;
- deterministic Access Planner;
- `AccessPlanningWorkflow` with optional `langgraph-dai` integration and local fallback;
- generated Access Plan artifact;
- React TypeScript Vite demo using `ui-design-system`;
- pytest baseline and frontend build check.

## Major Components

| Component | Responsibility | Owned data / behavior | Depends on |
|---|---|---|---|
| Web UI / BFF | Product screens and user workflow | Account workspace, review queue, demo UX | Product API |
| Frontend demo | Local single-account demo screen | Reads generated Access Plan artifact | Vite, design system |
| Product API | External HTTP boundary | Auth, request validation, task start/status | Application services |
| Power Web Domain | Sales domain model and policies | Account, Signal, Evidence, PowerWebRole, Playbook, AccessPlan | None |
| Agent Workflows | AI orchestration and audit | LangGraph state, node events, HITL checkpoints | `langgraph-dai`, domain services |
| Evidence Layer | Source ingestion and retrieval | Canonical docs, evidence packs, source refs | `langgraph-dai`, pgvector |
| Connectors / Tools | CRM and source integrations | Tool calls, retry/idempotency/audit | Tool executor, external systems |
| Persistence | Product state and read models | Postgres tables, vectors, artifacts | PostgreSQL, pgvector |

## Dependency Direction

```text
UI / API
  -> Application services
    -> Agent workflows
      -> Domain model
      -> Ports / tools
        -> Infrastructure adapters
```

Domain logic must not depend on transport, database, UI, or vendor APIs.

## Main Data Flow

```text
Target accounts
  -> synthetic fixture
  -> access planning workflow
  -> access plan artifact
  -> local frontend demo
```

Target production-oriented flow:

```text
Target accounts
  -> source collection
  -> canonical ingestion / indexing
  -> signal extraction
  -> Power Web draft
  -> playbook rule evaluation
  -> access route generation
  -> compliance / HITL review
  -> CRM task export
  -> outcome feedback
  -> Power Web state update
```

## LangGraph Platform Usage

The referenced platform should be used as follows:

- `BaseWorkflow` and typed state for access planning workflows.
- `ToolExecutor` policy for source and CRM connector calls.
- task lifecycle for queued/running/waiting_human/completed/failed states.
- HITL pattern for reviewable Access Plans and outreach drafts.
- canonical ingestion/retrieval and `EvidencePack` for evidence-backed recommendations.
- async batch pattern for account radar workloads.
- MCP boundaries for reusable repository, retrieval, configuration, and future CRM tools.

## Testing Strategy

- Unit tests for deterministic domain scoring and state transitions.
- Workflow tests for LangGraph state, audit, and resume behavior.
- Integration tests for persistence and connectors once added.
- Smoke tests for demo and API startup once API exists.
- E2E tests for signal-to-Access-Plan workflow once UI/API exists.

## Demo Implications

The demo should evolve through these stages:

1. Local deterministic Access Plan from fixture data.
2. LangGraph workflow output with node audit.
3. React frontend demo over generated artifact.
4. Account Radar batch over multiple fixtures.
5. Review queue and approved CRM task export.

## Trade-Offs

- Start with Postgres-friendly edge tables instead of a graph database. This keeps MVP infrastructure small.
- Start with deterministic planner rules before LLM orchestration. This keeps explanations testable.
- Keep external source connectors behind tools. This prevents scraping/vendor concerns from leaking into the domain.

## Open Questions

- First CRM target.
- First live source target.
- Whether a graph database becomes necessary after MVP.
- UI technology choice.
