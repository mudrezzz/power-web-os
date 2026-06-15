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
- deterministic ICP Radar XLSX fixture import read model;
- deterministic Account Radar accepted-portfolio read model for the current demo;
- deterministic Power Web Board selected-account read model;
- deterministic Playbook Analysis selected-account read model;
- `AccessPlanningWorkflow` with optional `langgraph-dai` integration and local fallback;
- generated ICP Radar, Account Radar, and Access Plan artifacts;
- React TypeScript Vite demo inside the Power Web OS workspace shell using `ui-design-system`;
- pytest baseline and frontend build check.

## Major Components

| Component | Responsibility | Owned data / behavior | Depends on |
|---|---|---|---|
| Web UI / BFF | Product screens and user workflow | Account workspace, review queue, demo UX | Product API |
| Frontend demo | Local product shell with active ICP Radar, Accounts, Access Plans, Account Map, and Playbook screens | Reads generated ICP Radar, Account Radar, and Access Plan artifacts and renders planned workspace placeholders | Vite, design system |
| ICP Radar | Configurable ABM account-search and signal-monitoring layer | ICP profile, structured radar definition, source policies, qualification rule groups, intent signals, scoring model, validation report, candidate queue; current demo imports XLSX fixture into a deterministic read model | Source connectors, evidence layer, domain scoring |
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

## Frontend Module Boundaries

The React frontend follows the same boundary rule as the Python domain: a screen should not become a god object. Once a product area contains its own state model, adapters, tables, previews, settings, and review controls, it must move into `frontend/src/features/<feature>/`.

`frontend/src/screens/ICPRadarScreen.tsx` is now a thin wrapper. The ICP Radar feature owns:

- screen orchestration and local navigation state;
- fixture and live artifact adapters;
- canonical shortlist, preview, and detail views;
- C1-C20 signal evidence and validation review;
- block-editable radar settings;
- localStorage overlays and score normalization helpers.

The Settings editor is lazy-loaded so the default catalog/shortlist path does not pull the whole editor into the initial JavaScript chunk. Contract tests guard this boundary and fail if ICP Radar collapses back into one monolithic screen file.

ICP Radar CSS is owned by `frontend/src/features/icp-radar/icpRadar.css`, while `frontend/src/styles.css` remains the app shell and shared primitive stylesheet. Runtime i18n initialization is separated from EN/RU resource modules. ICP Radar model helpers are also split by role: constants/types, validation scoring, radar metadata, live-radar helpers, and settings definition helpers.

The canonical ICP Radar UI is split by interaction surface: fixture/live shortlist modules own table scan and inline preview, fixture/live detail modules own tabbed evidence review, settings modules own block-level editing, and the feature entrypoint owns only screen-level state and orchestration.

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

Current demo ICP Radar flow:

```text
demo/fixtures/icp_radar/sibur_icp_pass1.xlsx
  -> ICPRadarXlsxImport
  -> deterministic imported workbook score fields
  -> structured radar definition with fit / intent / tier configuration
  -> demo/output/icp_radar.json
  -> frontend/public/demo/icp_radar.json
  -> ICP Radar screen
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
  -> ICP Radar screen
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

- `RadarDefinition`: executable radar configuration with metadata, global search policy, account qualification rules, intent signals, monitoring policy, scoring model, and validation report.
- `SourceDefinition` and `SourcePolicy`: typed source/API/MCP/search/manual-dataset references and the logic for how rules or signals can use them.
- `RuleGroup` and `AtomicRule`: stable legal-entity qualification rules, such as holding membership, industry, revenue, asset type, and whether buying decisions are likely made independently. Rules are description-first for users; optional generated technical fields may support future agent execution.
- `IntentSignalDefinition`: configurable interest signals, such as TOiR/EAM, predictive diagnostics, tenders, hiring, modernization, incidents, import substitution, or ESG/safety, each with detection rules and a `0/1/2` scoring rubric.
- `RadarScoringModel`: fit model, intent model, tier model, formula preset, optional custom formula, tier thresholds, and confidence penalties.
- `RadarDefinitionValidator`: conservative structural validation for required fields, duplicate ids, source-policy misuse, `NOT` misuse, simple numeric contradictions, and invalid custom formula references.

Older conceptual names such as account discovery rules and signal criteria map into the structured `RuleGroup` / `AtomicRule` and `IntentSignalDefinition` contracts. Qualification filters and intent signals are intentionally separate domain concepts.

- `ICPProfile`: product, target industries, company-size thresholds, geography, exclusions, and qualification assumptions.
- `RadarDefinition`: search scope, sources, run cadence, full/incremental mode, and radar-specific overrides.
- `AccountDiscoveryRule`: stable legal-entity discovery and filtering rules, such as revenue, holding membership, asset type, and whether buying decisions are likely made independently.
- `SignalCriterion`: configurable signal definitions, such as ТОиР/EAM, predictive diagnostics, tenders, hiring, modernization, incidents, import substitution, or ESG/safety.
- `SignalObservation`: a concrete found signal with source, date, confidence, strength, evidence refs, novelty fingerprint, and validation status.
- `ICPScoringFormula`: transparent fit/intent aggregation and tier thresholds.
- `RadarCandidate`: a scored account candidate before it is accepted into Power Web work.

Radar configuration is a first-class product boundary. There can be many ICP Radars running in parallel for different products, markets, holdings, or source scopes. Each radar owns its definition and can produce its own candidate shortlist; only approved candidates should flow into the shared `Accounts` portfolio and then into Power Web work. The current implementation exposes this through an `icp_radar_catalog` artifact and a block-editable selected-radar settings editor backed by browser-local demo state. The settings editor exposes business-language rules, source entities, generated codes, and scoring presets; it does not require users to edit internal IDs or field/operator/value triples. Production persistence, scheduling, live connector execution, and run history are planned as later concentric slices.

The first realistic demo ICP profile uses `demo/fixtures/icp_radar/sibur_icp_pass1.xlsx` as a fixture. It discovers Russian legal entities inside a holding, scores them against ТОиР criteria, and shows a ranked candidate shortlist for the active `ТОиР / SIBUR` radar. The catalog also includes configured/planned radar examples without generated candidates yet. Numeric C1-C20 scores come from the XLSX. `radar.definition.intent_signals` is the canonical C1-C20 dictionary; top-level `criteria` is generated from it only as a backward-compatible alias. Criterion-level evidence is added by a separate curated synthetic fixture, `demo/fixtures/icp_radar/toir_sibur_criterion_evidence.json`, so the demo can exercise evidence-backed score explanation before production source extraction exists.

The first live ICP Radar path is intentionally separate from the stable XLSX fixture. `ТОиР Quick Live Radar` uses a small definition with two qualification rules and three intent signals, runs from the CLI, and writes a separate `icp_radar_live_run` artifact only when a provider returns usable evidence. The live workflow is `LiveICPRadarRunWorkflow`, which follows the same optional `langgraph-dai` `BaseWorkflow` pattern as other workflows and delegates search to a provider-neutral `WebSearchProvider`. `OpenRouterWebSearchProvider` is the first implementation; `RecordedWebSearchProvider` supports tests. OpenRouter is therefore the first provider, not the domain boundary. Live outputs are reviewable artifacts, not accepted accounts, and the system must not fabricate candidates when provider evidence is missing.

Live qualification results use a richer review contract than the radar settings rule definition. Each candidate-level qualification result carries the rule snapshot, operator, requirement level, source usages, source origin, trust/check policy, evidence findings, cross-validation status, requirement evaluation, final assessment, and optional human review decision. The backend normalizer may enrich simpler provider output into this contract, but the frontend must not render raw Q1/Q2 labels without evidence, source, trust, and final-assessment context.

The current criterion evidence contract is deliberately explicit:

- `supported`: curated synthetic demo facts exist for this candidate and criterion;
- `inferred`: the XLSX score is nonzero, but the demo does not yet contain criterion-level facts;
- `not_observed`: the XLSX score is zero.

This read model is not a substitute for production extraction. It defines the UI and artifact surface that future source ingestion should populate. The current demo adds browser-local signal validation on top of the generated artifact: confirmed and unreviewed signals keep their score, corrected signals use an adjusted score, and rejected/stale signals remain visible but contribute `0`.

Signal validation is part of the ICP Radar boundary. A human must be able to confirm, correct, reject, or mark a signal as stale. Validation changes must affect the score and preserve an audit trail explaining why the candidate score changed. In this slice that audit trail is browser-local demo state under `power-web-os-icp-radar-signal-validation`; durable persistence, multi-user audit, and live source re-checking remain future boundaries.

The frontend ICP Radar workspace should be table-first. The main screen is a broad shortlist table with a sticky account column, bounded inline candidate preview, effective score deltas, and a separate candidate detail screen. The detail screen is the intended surface for signal validation actions; the shortlist should stay optimized for scanning and comparison.

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
9. Take-into-work handoff from ICP Radar candidates to Power Web.
10. Review queue and approved CRM task export.

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
