# Power Web Discovery AS IS

Status: implemented through runtime slice `0.7.6.6.2`.

## Executive statement

Power Web OS now converts an immutable, evidence-complete account handoff into
an auditable people-source search stage. It proposes account-specific
title/function hypotheses for every semantic role, accepts them
deterministically, executes bounded official-company, public HH and generic-web
lanes, and retains product-safe source leads, receipts and coverage decisions.

The stage deliberately does not claim that a source lead is a person. It has no
person-profile extraction, cross-source identity resolution,
employment validation or relationship discovery. The existing product can
also display already supplied roles and build access routes from those supplied
records, but those downstream read models do not own retrieval decisions.

Power Web OS now has a persisted global discovery-configuration foundation. A
product owns versioned semantic buying roles. This foundation defines what a
future Power Web Discovery run must look for without hardcoding account job
titles, search hints or benchmark people into production configuration. Access
strategy is not an input to people discovery.

## Sales playbook foundation

The production path is:

```text
Playbook UI -> Products API -> SalesPlaybookService -> SQL repository
            -> mutable draft -> immutable published version -> active pointer
```

`ProductDefinition` and `BuyingRolePolicyVersion` are independent snapshots.
`SalesPlaybookDefinitionVersion` atomically references one compatible version
of each. New versions have no AccessPlaybook dependency. Historical access
snapshots remain readable for compatibility but cannot be changed or restored
into active discovery configuration. Draft updates use optimistic revision
checks; published versions are read-only and can only be activated or restored
into a new product-and-role draft.

The basic semantic-role policy contains a human name, responsibility in the
purchase or implementation, requiredness and organizational scope. Stable role
codes are system-owned. Decision rights, priority override and exclusions are
optional advanced guidance. Historical reason and expected-evidence values are
readable, but are not authored in the current UI and are not required by the
future RoleDemand contract. Roles do not contain people, job titles, source
URLs or search queries.

The global Playbook UI uses separate catalog and full-width product-detail
states. Product detail has Product, Buying roles and Versions tabs. A role
editor expands below its table row and shows four basic fields; optional fields
are collapsed under Advanced. Historical access rules appear only inside the
read-only detail of an old version and are labelled as compatibility data. The
existing account-specific explanation of route decisions remains available
under Access Plans as Rule analysis. `SmartDiagnostics` is seeded as an active
product with eight semantic roles.

## Account handoff and role demand

The implemented pre-search boundary is:

```text
completed Radar candidate run
  -> canonical evidence-complete candidate
  -> versioned Radar product policy
  -> immutable account identity snapshot
  -> product-scoped semantic RoleDemand sets
  -> optional correctly linked signal snapshot
  -> power_web_handoff.v1
```

A Radar owns an ordered, immutable-versioned list of published products. The
same product may be shared by several Radars. A handoff selects all bound
products by default or an explicit non-empty subset and freezes their active
Sales Playbook and Buying Role Policy versions. Similar roles from different
products remain separate and retain product lineage.

Accepted candidates are eligible immediately. Review-needed candidates require
an explicit persisted acknowledgement. The account identity is stable by INN,
then OGRN; without either it is provisional and scoped to the source candidate
run. Source-less, rejected and wrong-Radar candidates are blocked.

Signal context is optional and may only come from the latest completed Signal
Monitoring run for the same Radar, source candidate run and candidate scope.
The handoff copies only product-safe outcomes and evidence refs. It does not
change role policy or claim that people were searched.

The Radar Settings UI owns product bindings. Candidate detail has a Power Web
tab that shows readiness, product versions, signal lineage and review-needed
acknowledgement. A successful action says `Ready for people discovery` and
shows the immutable brief. It creates no `power-web-run-*`, candidate run,
signal run or provider call.

## Current data flow

```mermaid
flowchart LR
  Handoff[power_web_handoff.v1]
  Plan[Role and lane planning]
  Retrieve[Bounded public-web retrieval]
  Stage[people_search_stage.v1]
  Review[Source leads for profile extraction]
  Handoff --> Plan --> Retrieve --> Stage --> Review
  Input[Caller-supplied PowerWebRole records]
  Board[PowerWebBoard read model]
  Planner[Access Planner]
  Output[Graph view and suggested routes]
  Input --> Board
  Input --> Planner
  Board --> Output
  Planner --> Output
```

The new discovery sequence stops at reviewable source leads. The compatibility
sequence remains caller-supplied `Account` and `PowerWebRole` records ->
`PowerWebBoard` read model and Access Planner -> graph view and suggested
routes. Source leads are not silently projected into that compatibility path.

### `PowerWebRole`

`PowerWebRole` is a flat passed-in record containing role, optional person name,
state, influence and optional relation. It has no source references, provenance,
employment interval, identity decision or review history.

### `PowerWebBoard`

`PowerWebBoardBuilder` creates a deterministic read model from roles and missing
roles already present on `Account`. It does not search, retrieve, extract or
validate people.

### Access Planner

The deterministic Access Planner trusts roles and signals supplied by its
caller. It can suggest a partner introduction, technical benchmark,
procurement discovery or missing-stakeholder research. It does not prove that a
named person exists, currently works for the account or has the inferred
influence.

## Missing capabilities

- No persisted `power-web-run-*`, database output, API or job lifecycle; the
  current stage artifact is an explicit file produced by CLI composition.
- No source-native `PersonProfile` retention.
- No reversible identity hypotheses or confirmed identity contract.
- No current/former/unknown employment validation.
- No evidence-backed relationship or influence projection.
- No database, API, job, history or UI for the people-search runtime.
- No quality claim for profile-control recall; the accepted live run found zero
  of ten evaluator-only profile controls.

## Implemented people-search stage

The application package now owns planning input, title-hypothesis proposals,
deterministic acceptance, source-lane decisions, independent budgets, task
scheduling, lead normalization, receipts, coverage checkpoints and artifact
projection. OpenRouter transport and public-web response normalization remain
in an integration adapter. The CLI composes these ports around an existing
handoff and writes an explicit file artifact; there is still no people-search
output table, API, worker task or run lifecycle.

The current executable boundary is:

```text
power_web_handoff.v1
  -> planning input
  -> account-specific title/function proposals
  -> deterministic acceptance with role lineage
  -> official_company + hh_public_web + generic_web decisions
  -> bounded provider execution and one bounded revision
  -> product-safe receipts and source leads
  -> role coverage checkpoints
  -> people_search_stage.v1
```

The `people_search_quality` profile starts three mandatory tasks for each of
eight roles. `official_company` requires an account-owned domain with a
product-safe evidence ref. `hh_public_web` uses normal web search restricted to
`hh.ru`; it performs no HH API, OAuth, authentication or crawling. `generic_web`
is a separate lane. Professional network, publication/event,
procurement/patent and industry lanes remain capability contracts but are not
enabled in this acceptance profile.

The profile permits 2 planner calls, 40 search tasks, 48 provider calls, 80
source verifications, one query revision per role/lane and one provider retry
per task. Candidate-discovery and signal-monitoring counters are neither read
nor changed. A provider failure has a distinct outcome and cannot become
`searched_no_results`; every selected lane keeps a terminal ledger state.

The accepted remote execution used handoff
`power-web-handoff-be8763ab-00ad-4cbf-8ff5-d5a84990d285`. It belongs to
`Benchmark / SIBUR holding contour`, candidate
`ao-sibur-him-prom-demo`, account `account-inn-5905001527`, and contains exactly
eight SmartDiagnostics `RoleDemand` records. Stage
`people-search-stage-9b8e0bac39a759b264af` executed all 24 mandatory lane
decisions and 2 bounded query revisions, producing 26 receipts and 80 retained
leads: 29 official, 22 HH and 29 generic-web. Four of eight roles had at least
one account/role-relevant lead. It used 1 planner call and 26 search-provider
calls, with no receipt gaps, orphan decisions, silent drops, mandatory-lane
provider errors or HH API calls.

The source-verification counter reached its limit after all mandatory tasks had
executed, so the artifact completion state is `completed_with_limits`; the
limit only prevented retaining additional citations. Blind controls were
loaded after execution and did not enter planning. None of the ten profile
controls was retrieved: five disabled-lane controls report
`lane_not_enabled_in_acceptance_profile`, while the enabled official/HH controls
report `source_not_found`. This is a diagnosed retrieval-quality gap, not an
identity failure and not a public quality claim. The slice proves bounded,
auditable retrieval wiring; later slices must extract profiles and improve
benchmark recall without weakening provenance.

## Preserved compatibility boundary

Future discovery must hand reviewed results to the existing `PowerWebRole`,
`PowerWebBoard` and Access Planner contracts. Those contracts remain downstream
read models and must not become owners of retrieval or identity decisions.

## Slice 0.7.6.6.0 architecture change record

Slice `0.7.6.6.0` adds architecture contracts and documentation only. It does
not claim a runtime. The requirement mapping is:

- `PW-ASIS-01`: this document states the current absence explicitly.
- `PW-ARCH-01`: the reviewed target flow is defined in the TO BE document.
- `PW-ID-01`: confirmed identity requires corroboration and is reversible.
- `PW-GOV-01`: people-data boundaries are explicit.
- `PW-HH-01`, `PW-HH-02`: public-web feasibility is separate from HH API.
- `PW-BENCH-01`, `PW-BENCH-02`: the user benchmark is normalized, privacy-filtered, accepted and hash-frozen; it remains evaluator-only and no production search exists yet.
- `PW-CAP-01`: source lanes have capability outcomes.
- `PW-COMPAT-01`: Board and Access Planner remain compatible.
- `PW-PROC-01`: architecture validation is green only while all mandatory evidence and the accepted freeze remain intact.

## Slice 0.7.6.6.0.1 implementation change record

- `PWF-PROD-01`: product lifecycle, mutable drafts and persistence are implemented.
- `PWF-ROLE-01`: published roles require semantic responsibility and evidence fields.
- `PWF-ROLE-02`: account title hypotheses cannot mutate role-policy fields.
- `PWF-ACCESS-01`: access routes reference existing semantic role codes only.
- `PWF-VERS-01`: published versions are immutable and stale drafts return a conflict.
- `PWF-API-01`: API state survives backend restart.
- `PWF-UI-01`: Product, Buying roles, Access rules and Versions are separate backend-backed views.
- `PWF-UI-02`: account-specific Playbook analysis is owned by Access Plans.
- `PWF-DEMO-01`: SmartDiagnostics has eight seeded semantic roles.
- `PWF-BENCH-01`: the benchmark amendment references configuration only and preserves blind leakage zero.
- `PWF-COMPAT-01`: legacy Playbook, Power Web Board and Access Planner remain compatible.
- `PWF-NET-01`: this slice performs no provider calls and creates no search runs.
- `PWF-PROC-01`: TO BE, manifest, validation report and this AS IS record are traceable.

The next runtime slice must consume an immutable active product and semantic
role-policy snapshot. It must not invent the required buying committee or read
account-specific job titles from this configuration.

## Slice 0.7.6.6.0.2 implementation change record

- `PWS-CFG-01`: the canonical discovery configuration is product plus semantic-role policy, without access strategy.
- `PWS-ROLE-01`: a role publishes with four basic business fields and empty advanced guidance.
- `PWS-ROLE-02`: requiredness provides deterministic priority defaults; manual override is advanced.
- `PWS-PLAN-01`: authored expected evidence and title/query hints are not required RoleDemand inputs.
- `PWS-ACCESS-01`: new publications create no access snapshot and access mutation is rejected.
- `PWS-ACCESS-02`: historical access snapshots remain readable but are not reactivated by restore.
- `PWS-API-01`: simplified configuration survives API, database and restart round-trips.
- `PWS-UI-01`: product catalog and full-width product detail are separate navigation states.
- `PWS-UI-02`: the role editor expands inline at the table width and exposes four basic controls.
- `PWS-TABS-01`: workspace sections share one underline-tab component; pills remain filters and mode controls.
- `PWS-COMPAT-01`: legacy Playbook, Power Web Board and Access Planner remain operational.
- `PWS-BENCH-01`: the accepted benchmark remains evaluator-only with blind leakage zero.
- `PWS-NET-01`: the slice performs no provider calls and creates no search runs.
- `PWS-PROC-01`: TO BE, tests, machine validation and this finalized AS IS record are traceable.

## Slice 0.7.6.6.1 implementation change record

- `PW-HO-POL-01`: Radar-product bindings are a separate ordered immutable policy.
- `PW-HO-PROD-01`: each handoff freezes exact active product and role-policy versions.
- `PW-HO-ELIG-01`: accepted and acknowledged review-needed admission is explicit.
- `PW-HO-PROV-01`: only canonical evidence-complete candidates enter the handoff.
- `PW-HO-ID-01`: stable INN/OGRN and provisional scoped account identities are deterministic.
- `PW-HO-ROLE-01`: RoleDemand contains semantic policy and no titles, queries or expected answers.
- `PW-HO-ROLE-02`: product role sets are never silently merged.
- `PW-HO-SIG-01`: signal context is optional and lineage-checked.
- `PW-HO-IDEM-01`: persisted handoff snapshots are immutable and idempotent.
- `PW-HO-API-01`: policy and handoffs survive API/worker restart.
- `PW-HO-UI-01`: Radar Settings and candidate detail expose the same backend truth.
- `PW-HO-ARCH-01`: Power Web application logic remains provider-neutral and package-owned.
- `PW-HO-BENCH-01`: blind controls remain evaluator-only with leakage zero.
- `PW-HO-NET-01`: provider calls and new pipeline runs are zero.
- `PW-HO-PROC-01`: TO BE, manifest, tests, Docker evidence, validation and AS IS are traceable.

## Slice 0.7.6.6.2 implementation change record

- `PW-PS-ASIS-01`: the pre-code baseline and real eight-role handoff are retained in the slice evidence.
- `PW-PS-IN-01`: planning accounts for all RoleDemand records with exact product, version and account lineage; the recorded two-product path preserves all fourteen demands.
- `PW-PS-HYP-01`: provider proposals cannot mutate role policy or lineage, and schema recovery is bounded to two planner calls.
- `PW-PS-HYP-02`: duplicate, unrelated and private-value proposals are rejected with explicit reasons; deterministic role-based fallback remains available.
- `PW-PS-LANE-01`: every quality-profile role receives independent official, HH public-web and generic-web decisions; an unverified official domain is not replaced by generic search.
- `PW-PS-LANE-02`: every selected lane has a terminal scheduling or execution outcome in the ledger.
- `PW-PS-HH-01`: HH retrieval is domain-restricted public web search with zero HH API, OAuth, authentication or crawler calls.
- `PW-PS-AUD-01`: every executed task has a product-safe receipt with task, role, product, hypothesis, source and provider lineage.
- `PW-PS-NEG-01`: provider errors remain provider errors and never become searched-negative outcomes.
- `PW-PS-BUD-01`: planner, retrieval, retry, revision and verification counters are independent, bounded and included in the stage artifact.
- `PW-PS-SEC-01`: artifacts retain no raw provider payload, HTML, credentials, headers, private contacts or hidden reasoning.
- `PW-PS-BENCH-01`: blind controls are loaded only by the evaluator; planning leakage is zero and every miss has a path-level reason.
- `PW-PS-ARCH-01`: people-search application services remain provider-neutral and isolated from Candidate Discovery, Signal Monitoring, transport, persistence and worker frameworks.
- `PW-PS-LIVE-01`: remote stage `people-search-stage-9b8e0bac39a759b264af` passed the eight-role, 24-lane, receipt, lead, relevance and budget acceptance thresholds.
- `PW-PS-PROC-01`: baseline, TO BE/PDF, acceptance manifest, recorded tests, remote live artifact, PASS validation and this finalized AS IS record are traceable.
