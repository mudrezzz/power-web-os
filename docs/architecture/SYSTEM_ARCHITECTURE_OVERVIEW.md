# System Architecture Overview

## Product Context

Power Web OS is a strategy layer for complex B2B sales. It runs ABM-oriented ICP Radars to discover and qualify target accounts, builds a dynamic influence map around accepted accounts, applies customer-specific sales playbook rules, and recommends explainable access routes.

The product must use `mudrezzz/langgraph-document-ai-platform` for the AI-agent workflow layer.

## Architectural Goals

- Keep recommendations white-box and evidence-backed.
- Keep ICP/account selection explicit, configurable, and aligned with ABM profile strategy.
- Keep CRM as system of record and Power Web OS as system of strategy.
- Keep humans in control of sensitive commercial actions.
- Support async batch analysis for 50-100 account MVP pilots.
- Preserve source provenance, route explanations, task audit, and review history.

## Current Product Perimeter

The current baseline has:

- domain entities for account access planning;
- deterministic Access Planner;
- deterministic Account Radar portfolio read model for the current demo, to be evolved into the ICP Radar funnel;
- deterministic Power Web Board selected-account read model;
- deterministic Playbook Analysis selected-account read model;
- `AccessPlanningWorkflow` with optional `langgraph-dai` integration and local fallback;
- generated Account Radar and Access Plan artifacts;
- React TypeScript Vite demo inside the Power Web OS workspace shell using `ui-design-system`;
- pytest baseline and frontend build check.

## Major Components

| Component | Responsibility | Owned data / behavior | Depends on |
|---|---|---|---|
| Web UI / BFF | Product screens and user workflow | Account workspace, review queue, demo UX | Product API |
| Frontend demo | Local product shell with active Accounts, Access Plans, Account Map, and Playbook screens | Reads generated Account Radar and Access Plan artifacts and renders planned workspace placeholders | Vite, design system |
| ICP Radar | Configurable ABM account-search and signal-monitoring layer | ICP profile, discovery rules, signal criteria, scoring formula, candidate queue, signal validation state | Source connectors, evidence layer, domain scoring |
| Account Radar | Deterministic portfolio read model | Portfolio score, top reason, best route, owner, review status | Domain services, Access Plan artifacts |
| Power Web Board | Deterministic selected-account read model | Board summary, people/partner/missing nodes, account edges, highlighted route path | Account, Access Plan artifact |
| Playbook Analysis | Deterministic selected-account read model | Current and what-if playbook snapshots, route policy decisions, review policy, route previews | Account, Playbook, Access Plan artifact |
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

Target ICP Radar flow:

```text
ICP profile
  -> account discovery rules
  -> account universe / legal entities
  -> signal monitoring runs
  -> evidence-backed signal observations
  -> human signal validation
  -> transparent ICP score and tier
  -> radar candidate queue
  -> take into work
  -> Power Web discovery
```

```text
Target accounts
  -> synthetic portfolio fixture
  -> account radar
  -> access planning workflow per account
  -> account radar artifact + access plan artifacts
  -> power web board data inside each access plan artifact
  -> playbook analysis data inside each access plan artifact
  -> local frontend workspace shell
  -> Accounts screen
  -> selected Access Plans screen / Account Map screen / Playbook screen
```

Target production-oriented flow:

```text
ICP profile / radar definition
  -> account discovery
  -> source collection and monitoring
  -> canonical ingestion / indexing
  -> signal extraction and validation
  -> ICP score / candidate decision
  -> Power Web draft
  -> playbook rule evaluation
  -> access route generation
  -> compliance / HITL review
  -> CRM task export
  -> outcome feedback
  -> Power Web state update
```

## ICP Radar Boundary

An ICP Radar is not the Power Web itself. It is the ABM funnel layer that decides which accounts are worth taking into work for a specific product and ICP profile.

An ICP Radar owns:

- `ICPProfile`: product, target industries, company-size thresholds, geography, exclusions, and qualification assumptions.
- `RadarDefinition`: search scope, sources, run cadence, full/incremental mode, and radar-specific overrides.
- `AccountDiscoveryRule`: stable legal-entity discovery and filtering rules, such as revenue, holding membership, asset type, and whether buying decisions are likely made independently.
- `SignalCriterion`: configurable signal definitions, such as ТОиР/EAM, predictive diagnostics, tenders, hiring, modernization, incidents, import substitution, or ESG/safety.
- `SignalObservation`: a concrete found signal with source, date, confidence, strength, evidence refs, novelty fingerprint, and validation status.
- `ICPScoringFormula`: transparent fit/intent/trigger aggregation and tier thresholds.
- `RadarCandidate`: a scored account candidate before it is accepted into Power Web work.

The first realistic demo ICP profile should use the attached SIBUR-style ТОиР automation analysis as a fixture. It should discover Russian legal entities inside a holding, score them against ТОиР criteria, and only send accepted candidates into the existing Power Web / Access Plan loop.

Signal validation is part of the ICP Radar boundary. A human must be able to confirm, correct, reject, or mark a signal as stale. Validation changes must affect the score and preserve an audit trail explaining why the candidate score changed.

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
3. React frontend workspace shell over generated artifact.
4. Account Radar batch over multiple fixtures.
5. Power Web Lite board for the selected account.
6. Playbook Analysis for current and no-partner-motion route previews.
7. ICP Radar fixture using the ТОиР/SIBUR-style analysis and Russian-language demo companies.
8. ICP Radar signal validation with score recalculation.
9. Review queue and approved CRM task export.

## Trade-Offs

- Start with Postgres-friendly edge tables instead of a graph database. This keeps MVP infrastructure small.
- Start with deterministic planner rules before LLM orchestration. This keeps explanations testable.
- Keep external source connectors behind tools. This prevents scraping/vendor concerns from leaking into the domain.
- Split account discovery from signal monitoring. Legal-entity discovery changes slowly and can be imported or run manually; signal monitoring is recurring and should support incremental dedupe.
- Treat ICP Radar scoring as configurable but constrained. Formulas should be transparent and auditable, not arbitrary executable code.

## Open Questions

- First CRM target.
- First live source target.
- Whether a graph database becomes necessary after MVP.
- UI technology choice.
