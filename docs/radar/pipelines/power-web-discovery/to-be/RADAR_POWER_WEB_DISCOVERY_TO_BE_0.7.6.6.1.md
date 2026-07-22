# Power Web Discovery TO BE 0.7.6.6.1

Status: Implemented.

Pipeline id: `power-web-discovery`.

AS IS: `../RADAR_POWER_WEB_DISCOVERY_AS_IS.md`

Baseline: `../validation/0.7.6.6.1/BASELINE_DIAGNOSTIC.md`

Acceptance manifest: `RADAR_POWER_WEB_DISCOVERY_TO_BE_0.7.6.6.1.acceptance.json`

## Intent

Create the immutable boundary between an evidence-complete Radar candidate and future people discovery:

`Radar candidate -> Radar product policy -> account snapshot -> product-scoped role demands -> optional linked signals -> Power Web handoff`.

The result is a ready search brief, not a people-search run. It makes no provider calls and does not depend on Access Playbook.

## Radar product policy

Radar owns a separately persisted, versioned list of zero or more published active products. A product may belong to multiple Radars. Each update creates an immutable policy version; ordinary Radar definition updates cannot overwrite it.

All bound products are selected by default for handoff. A user may select a non-empty subset. Product order is retained. Archived, draft, missing or unbound products block new handoffs while existing snapshots remain readable.

## Candidate and account admission

Handoff reads the canonical evidence-complete public candidate surface. Accepted candidates are eligible immediately. Review-needed candidates require an explicit persisted acknowledgement. Rejected, missing or source-less rows are ineligible.

Account identity is stable by INN, then OGRN. Without either identifier it is provisional and scoped to the source candidate run and candidate id. Provisional records are never silently merged across runs.

## Product and role snapshots

At handoff time the application resolves each selected product's active immutable Sales Playbook version and snapshots its ProductDefinition and BuyingRolePolicy identifiers and content.

Each semantic role produces one product-scoped `RoleDemand` containing product/version lineage, semantic role code, display name, responsibility, requiredness, effective priority and scope. Titles, names, aliases, queries, URLs, authored expected evidence, required reasons and access-strategy constraints are excluded. Similar roles from different products remain separate.

## Signal context

The selector may attach the latest completed Signal Monitoring run for the same Radar and source candidate run when its immutable scope contains the candidate. Only product-safe outcomes, temporal states and evidence refs are retained. Missing signals are a warning, not a blocker, and never change required roles.

## Handoff lifecycle

`power_web_handoff.v1` stores the Radar policy version, candidate lineage, account snapshot, exact product snapshots, product role-demand sets, optional signal snapshot, acknowledgement, actor and timestamps. It is immutable and idempotent.

The handoff carries `run_kind=initial` and `previous_power_web_run_id=null` as future run intent. It is not inserted into `radar_runs` and does not claim that people discovery executed.

## UI contract

Radar Settings contains an independently loaded and saved Power Web product block. Candidate detail and the expanded candidate row expose `Prepare Power Web`. The Power Web tab defaults to all bound products, requires a non-empty selection, requests acknowledgement for review-needed candidates and shows linked signal context.

After creation the UI says `Ready for people discovery` and renders immutable account, product/version, role count and source lineage. It does not display invented people or search results.

## Architecture

Power Web application code owns contracts and decisions behind provider-neutral ports. API is transport-only; persistence stores immutable records; adapters read canonical candidate, Sales Playbook and Signal Monitoring data. The package imports no candidate-discovery or signal-monitoring internals, FastAPI, SQLAlchemy, Celery, HTTP clients or provider SDKs.

## Requirement traceability

- `PW-HO-POL-01`: Radar-product policy is immutable, ordered and many-to-many.
- `PW-HO-PROD-01`: handoff resolves and freezes exact active product versions.
- `PW-HO-ELIG-01`: accepted and acknowledged review-needed eligibility is enforced.
- `PW-HO-PROV-01`: only evidence-complete canonical candidates are admitted.
- `PW-HO-ID-01`: stable and provisional account identity rules are deterministic.
- `PW-HO-ROLE-01`: RoleDemand contains semantic policy, not search inventions.
- `PW-HO-ROLE-02`: product role sets are retained without silent merging.
- `PW-HO-SIG-01`: optional signal context is correctly linked and product-safe.
- `PW-HO-IDEM-01`: handoffs are immutable and idempotent.
- `PW-HO-API-01`: policy and handoff survive API restart.
- `PW-HO-UI-01`: Radar settings and candidate UI expose the handoff honestly.
- `PW-HO-ARCH-01`: package and pipeline boundaries remain intact.
- `PW-HO-BENCH-01`: blind benchmark controls never enter planning or snapshots.
- `PW-HO-NET-01`: no provider calls or pipeline runs occur.
- `PW-HO-PROC-01`: TO BE, tests, runtime evidence, validation and AS IS are traceable.

## Hard acceptance

The benchmark Radar binds SmartDiagnostics with eight roles and Industrial Energy Optimization with six. An all-product accepted handoff contains exactly fourteen demands; a SmartDiagnostics-only handoff contains eight. Review-needed admission without acknowledgement fails. Signal lineage selection, stable/provisional identity, immutable versioning, idempotency, Docker persistence, RU/EN UI and zero-network evidence all pass. Every mandatory requirement must be `PASS` before this design becomes AS IS.
