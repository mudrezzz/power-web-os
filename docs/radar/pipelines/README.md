# Radar Pipeline Documentation Registry

This folder is the registry for serious Radar search pipelines. Each pipeline
must have its own AS IS document and generated PDF. Substantial changes must
start with a TO BE Markdown/PDF pair and finish by syncing the AS IS document.

The registry is also the path contract for the Radar pipeline documentation
skills. Use `pipeline=<pipeline_id>` in requests when the target pipeline is not
the current candidate-discovery default.

## Pipeline ids

| Pipeline id | Purpose | Cadence | Current state |
|---|---|---|---|
| `candidate-discovery` | Find and qualify legal entities, sites, branches, projects, and review-needed upstream entities. | Infrequent: manual, monthly, quarterly, or after Radar settings change. | Implemented through the current Radar search pipeline; docs still live at `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md` until the migration slice splits the file. |
| `signal-monitoring` | Monitor configured intent signals for known candidates over a recent time window. | Frequent: weekly or another product-configured monitoring cadence. | No-network application contracts, recorded TOIR loop, capability-driven source strategy, independent signal budgets, config-backed signal model profile, AS IS docs, and recorded UI preview exist. Live runtime, scheduler, and production UI execution are still planned. |
| `power-web-discovery` | Discover people, roles, relationships, partner paths, buying committee structure, and access routes for accepted accounts. | Event-driven or account-workflow driven. | Planned. |

## Required files

Target structure:

```text
docs/radar/pipelines/
  candidate-discovery/
    RADAR_CANDIDATE_DISCOVERY_AS_IS.md
    RADAR_CANDIDATE_DISCOVERY_AS_IS.pdf
    to-be/
      RADAR_CANDIDATE_DISCOVERY_TO_BE_<slice>.md
      RADAR_CANDIDATE_DISCOVERY_TO_BE_<slice>.pdf

  signal-monitoring/
    RADAR_SIGNAL_MONITORING_AS_IS.md
    RADAR_SIGNAL_MONITORING_AS_IS.pdf
    to-be/
      RADAR_SIGNAL_MONITORING_TO_BE_<slice>.md
      RADAR_SIGNAL_MONITORING_TO_BE_<slice>.pdf

  power-web-discovery/
    RADAR_POWER_WEB_DISCOVERY_AS_IS.md
    RADAR_POWER_WEB_DISCOVERY_AS_IS.pdf
    to-be/
      RADAR_POWER_WEB_DISCOVERY_TO_BE_<slice>.md
      RADAR_POWER_WEB_DISCOVERY_TO_BE_<slice>.pdf
```

The current `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md` remains the canonical
candidate-discovery AS IS document until a later migration slice moves it into
the per-pipeline folder.

`power-web-discovery` does not get an AS IS document until its first runtime
implementation exists. Before that, its TO BE documents are reviewed design
inputs, not claims about implemented behavior.

For `signal-monitoring`, the first AS IS document now lives at
`docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md`.
The current implemented surface is intentionally limited to application
contracts, no-network tests, and a recorded TOIR loop over known candidates.
Source strategy is capability-driven: known candidate-discovery sources are
checked first, then official/company, signal-specific, and open-web lanes are
selected only when source policy and source cards allow signal evidence.
Signal budgets and model-role defaults are isolated from candidate-discovery
through `config/radar/model_profiles/signal_monitoring.json`.

## Skill invocation examples

Use the existing generic skills with a pipeline id instead of creating separate
skill families:

```text
Сделай TO BE для signal-monitoring по слайсу 0.7.6.4.1
Синхронизируй AS IS для candidate-discovery после слайса 0.7.6.3.6.13
Финализируй TO BE в AS IS для signal-monitoring после реализации 0.7.6.4.2
```

Path mapping:

| Pipeline id | Current AS IS path | TO BE path |
|---|---|---|
| `candidate-discovery` | `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md` | `docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_<slice>.md` |
| `signal-monitoring` | `docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md` | `docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_<slice>.md` |
| `power-web-discovery` | planned: `docs/radar/pipelines/power-web-discovery/RADAR_POWER_WEB_DISCOVERY_AS_IS.md` | `docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_<slice>.md` |

## Documentation rule

For every substantial pipeline change:

1. Create a TO BE Markdown and PDF for the target `pipeline_id`.
2. Review the intended algorithm, roles, context handoffs, budgets, model
   roles, source capabilities, diagnostic states, and tests.
3. Implement the slice.
4. Sync the pipeline AS IS Markdown and PDF.
5. Record validation evidence in `ROADMAP.md`.

## Model-profile rule

Each pipeline owns its model-role profile. Candidate discovery model tuning
must not silently change signal monitoring behavior, and signal monitoring
model tuning must not silently change candidate discovery.

Non-secret model-role defaults should move toward config files such as:

```text
config/radar/model_profiles/candidate_discovery.json
config/radar/model_profiles/signal_monitoring.json
config/radar/model_profiles/power_web_discovery.json
```

General Radar runtime defaults and bounded run profiles live next to them:

```text
config/radar/runtime_defaults.json
config/radar/run_profiles/smoke.json
config/radar/run_profiles/live.json
```

`.env` remains for credentials, infrastructure URLs, and explicit
deployment/runtime overrides.

## Planned rollout

The roadmap currently tracks the pipeline split through these slices:

| Slice | Purpose |
|---|---|
| `0.7.6.4.0` | Accepted architecture decision: Radar is a family of separate pipelines, not one monolithic search run. |
| `0.7.6.4.0.1` | Add SQLite slice tracker and generated Roadmap report before continuing the signal-monitoring sequence. |
| `0.7.6.4.1` | Create the pipeline documentation registry, make documentation skills pipeline-aware, and prepare the first signal-monitoring TO BE. |
| `0.7.6.4.2` | Define signal-monitoring application contracts and a no-live-provider recorded harness. |
| `0.7.6.4.3` | Define signal source strategy and warm-start from known candidate-discovery sources. |
| `0.7.6.4.4` | Add signal-monitoring budgets and isolate signal model profiles from candidate-discovery profiles. |
| `0.7.6.4.5` | Build the first recorded TOIR signal-monitoring loop over known candidates. |
| `0.7.6.4.6` | Add UI controls for candidate discovery versus signal monitoring. |
