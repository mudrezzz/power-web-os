# Power Web Discovery TO BE 0.7.6.6.2

Status: Implemented.

Pipeline id: `power-web-discovery`.

AS IS: `../RADAR_POWER_WEB_DISCOVERY_AS_IS.md`

Baseline: `../validation/0.7.6.6.2/BASELINE_DIAGNOSTIC.md`

Acceptance manifest: `RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.2.acceptance.json`

Implemented stage: `people-search-stage-9b8e0bac39a759b264af`.

Validation: `../validation/0.7.6.6.2/VALIDATION_REPORT.md` (`PASS`).

## Intent

Turn one immutable `power_web_handoff.v1` into an auditable people-source
search stage without creating identities, employment claims or graph edges:

```text
handoff -> planning input -> title hypotheses -> deterministic acceptance
        -> lane strategy -> bounded retrieval -> source leads
        -> role coverage checkpoints -> people_search_stage.v1
```

The stage writes a product-safe JSON artifact and validation report. Persisted
`power-web-run-*`, APIs, jobs, history and product UI remain owned by later
slices.

## Ownership and boundaries

The Power Web application package owns planning input, hypothesis acceptance,
source obligations, budget decisions, receipt semantics, lead normalization,
coverage checkpoints and artifact projection. Integrations own OpenRouter HTTP
transport and response normalization. CLI composition loads the existing
handoff and writes an explicit artifact file.

Application code imports no candidate-discovery or signal-monitoring internals,
FastAPI, SQLAlchemy, Celery, HTTP client or provider SDK. It consumes the
existing handoff and source evidence through provider-neutral ports. Existing
`AccountRoleTitleHypothesis` remains a compatibility contract; runtime uses
proposal and accepted-hypothesis records with exact demand/product/version
lineage.

## Planning and hypothesis acceptance

The input contains the immutable handoff, account aliases, verified official
domains with product-safe source evidence refs, language/geography context,
capability cards and the execution-profile snapshot. A bare domain without
provenance is invalid. The input never contains blind controls.

One batch provider call proposes at most five title/function variants per role;
one schema retry is allowed. The deterministic acceptance service retains at
most three normalized variants per role and records every rejection. A proposal
cannot add or remove RoleDemand, change product lineage, requiredness, priority
or scope. Person names, contacts, URLs, benchmark controls, empty values,
duplicates and unrelated variants are rejected. A deterministic fallback from
display name and responsibility guarantees one accepted hypothesis per role.
Original account language is preserved; unprovided transliteration is not
invented.

## Source-lane strategy

The quality profile selects three independent mandatory lanes per role when
their capabilities are available:

- `official_company`: requires a verified account-owned domain;
- `hh_public_web`: normal web search restricted to `hh.ru`;
- `generic_web`: unrestricted public-web search.

Professional-network, publication/event, procurement/patent and industry lanes
are supported as conditional decisions but disabled in the acceptance profile.
Every selected decision terminates as `scheduled`, `executed`,
`not_executable`, `unsupported`, `policy_limited` or `budget_limited`.
Mandatory decisions may not disappear between strategy and execution.

HH access is public-search-only. The stage performs no HH API/OAuth call,
authentication, direct mass crawling, CAPTCHA/robots bypass or contact
extraction. An inaccessible page may remain a limited lead using its public
search citation; a snippet never confirms identity or employment.

## Retrieval, receipts and leads

Every executed task produces a `PeopleSearchExecutionReceipt` with task,
demand, product, hypothesis and lane lineage; sanitized query and restrictions;
configured provider/engine; timestamps; result count; normalized source refs;
attempt outcome and retry count. Raw response, prompt, headers, credentials,
HTML and hidden reasoning are never retained.

`PeopleSourceLead` stores a canonical URL, title, product-safe snippet, optional
public name/title/employer/geography hints, lane, source capability and reason.
It is not a `PersonProfile`, identity decision, employment claim, influence
hypothesis or Power Web node.

Provider timeout/error receives one same-engine retry. It never becomes
`searched_no_results`. Coverage is one of `complete_with_leads`,
`complete_no_leads`, `incomplete_capability`, `incomplete_provider`,
`incomplete_budget` or `incomplete_policy`. `complete_no_leads` requires a
successful receipt from every applicable mandatory lane.

## Budgets

Profile `people_search_quality` snapshots independent settings and counters:

- 8 role demands;
- 2 hypothesis-provider calls;
- 5 proposed and 3 accepted variants per role;
- 24 initial tasks, 40 total tasks and 48 provider calls;
- 80 source verifications;
- one query revision per role/lane and one provider retry per task;
- reserves: 8 HH, 8 official, 8 generic and 16 revision/recovery tasks.

One configured OpenRouter primary engine is used. Retry does not switch engine.
Candidate-discovery and Signal Monitoring budgets are neither read nor changed.

## Artifact and evaluation

`people_search_stage.v1` contains stage execution ID, handoff/account/product
lineage, planning input summary, proposal and acceptance ledgers, source-lane
ledger, tasks, attempts, receipts, leads, coverage checkpoints, model/provider
metadata, budgets, diagnostics and terminal state. It is file-based and not a
persisted Power Web run.

After execution the evaluator loads the frozen benchmark. It reports each blind
profile control as retrieved or with a path-level miss reason while proving
`controls_in_planning_count=0`. This slice validates retrieval coverage only;
identity quality remains outside its claims.

## Test and live acceptance

Recorded tests exercise all fourteen demands from the two-product handoff,
malformed proposals, duplicates, policy mutation, unknown lanes, missing
official domain, retries, budget exhaustion, searched-negative semantics,
privacy filtering and blind leakage. The live gate uses the eight-role
SmartDiagnostics handoff from the baseline diagnostic and executes exactly 24
initial mandatory-lane decisions through the remote contour.

The slice passes only with receipts for every executed task, no orphan decision
or silent drop, at least one retained lead from each mandatory lane, relevant
lead coverage for at least four roles, zero unrecovered mandatory-lane provider
errors, provider calls within 48 and planner calls within 2. Candidate, Signal
and persisted Power Web runs remain zero.

## Out of scope

- No person profile extraction or cross-source identity resolution.
- No employment, relationship or influence decision.
- No database migration, API, job, run history or UI.
- No HH authorized API and no comparison of OpenRouter search engines.
- No public quality claim from this single acceptance run.

## Requirement traceability

The adjacent manifest defines `PW-PS-ASIS-01`, `PW-PS-IN-01`,
`PW-PS-HYP-01`, `PW-PS-HYP-02`, `PW-PS-LANE-01`, `PW-PS-LANE-02`,
`PW-PS-HH-01`, `PW-PS-AUD-01`, `PW-PS-NEG-01`, `PW-PS-BUD-01`,
`PW-PS-SEC-01`, `PW-PS-BENCH-01`, `PW-PS-ARCH-01`, `PW-PS-LIVE-01` and
`PW-PS-PROC-01`. Every mandatory
requirement must pass recorded tests and the declared remote live evidence
before this design becomes AS IS.
