# ADR: Radar search pipelines are separate

## Status

Accepted

## Context

Radar work has grown beyond one live run that searches for everything. The
candidate-discovery pipeline now has source profiles, capability cards,
checkpoint recovery, search expansion, scheduler admission, budget diagnostics,
evaluation, and AS IS/TO BE documentation. It is a heavier upstream process
that changes the candidate universe: which legal entities, sites, branches, or
assets should be monitored for a product and ICP.

Signal monitoring has a different operating model. It starts from known or
review-needed candidates and asks what changed recently: tenders, hiring,
modernization, implementation news, incidents, official updates, procurement
events, or other intent signals. It should run more often than candidate
discovery and must not lose its budget to candidate expansion. Future Power Web
discovery is different again: it searches for people, roles, influence paths,
partner routes, and account-specific access structure.

The old "one Radar run does discovery and signals together" shape is still
useful as a smoke/debug mode, but it is no longer the right architecture for
production operation or meaningful benchmark interpretation.

## Decision

Radar will be treated as a family of separate search pipelines:

- `candidate-discovery`: finds and qualifies candidate accounts and upstream
  review-needed entities.
- `signal-monitoring`: monitors configured intent signals for already known
  candidates over a time window.
- `power-web-discovery`: future pipeline for account access structure, roles,
  relations, and influence paths.

Each serious pipeline must have independent:

- run kind and schedule/cadence;
- task and external-call budgets;
- model-role profile and model fallback policy;
- source capability usage rules;
- AS IS Markdown/PDF documentation;
- TO BE Markdown/PDF documents for substantial changes;
- fast recorded/fixture test harness before long live runs.

Model tuning must not be shared implicitly across pipelines. Non-secret model
role configuration should move toward pipeline-specific config files, while
`.env` remains for credentials and deployment/runtime overrides.

Existing Radar pipeline documentation skills should become pipeline-aware
instead of being duplicated per pipeline. They should accept a pipeline id such
as `candidate-discovery`, `signal-monitoring`, or `power-web-discovery` and
write the corresponding AS IS/TO BE documents.

## Consequences

- Candidate discovery can remain broad, slower, and recall-first upstream.
- Signal monitoring can become frequent, incremental, candidate-first, and
  time-window based.
- Signal monitoring receives protected budget and model settings independent
  from discovery.
- A full combined Radar run remains available only as a smoke/debug
  compatibility mode until explicit product behavior says otherwise.
- Benchmark interpretation becomes clearer: candidate recall benchmarks should
  not be judged by missing signal search, and signal monitoring benchmarks
  should not spend most of their budget rediscovering legal entities.
- Documentation will move from one large Radar search document toward a
  registry of per-pipeline AS IS/TO BE documents.

## Alternatives considered

- Keep one monolithic Radar execution pipeline and add more budgets inside it.
  This was rejected because recent benchmark work showed that discovery and
  signal search compete for budget and diagnostics become hard to read.
- Fork provider-specific logic for signals, for example treating DaData or one
  web source specially. This was rejected because connector profiles and
  capability cards should decide whether a source is suitable for identity,
  coverage, signal evidence, or future Power Web discovery.
- Create separate skills for every pipeline. This was rejected because a
  pipeline-aware documentation skill is simpler and keeps one maintenance path.
