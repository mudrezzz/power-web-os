# ADR: ICP Radar Definition Separates Qualification Rules And Intent Signals

## Status

Accepted

## Context

ICP Radar configuration was initially represented as a mostly flat settings object: profile text, discovery fields, monitoring fields, criteria, and scoring guidance. That was enough to show a read-only radar, but it blurred several different domain concepts:

- human-facing radar name and description;
- account qualification rules that decide whether a legal entity belongs in the searched universe;
- intent signals that decide whether a qualified account is interesting now;
- sources and connector references that should be reusable, typed, and validated;
- scoring formulas that aggregate qualified evidence and signal strength.

The product needs many ICP Radars running in parallel. Each radar must be inspectable, locally editable in the demo, and eventually executable by agents and source connectors. A textarea-based configuration would hide contradictions and make future execution unsafe.

## Decision

`RadarDefinition` is an executable domain configuration, not a flat UI settings object.

It is split into:

- `metadata`: name, description, owner, and status for human catalog usage;
- `global_search_policy`: shared sources, keywords, exclusions, and whether the system may use additional sources;
- `account_qualification`: rule groups for filtering legal entities into the radar universe;
- `intent_signals`: signal definitions with trigger rules and a fixed `0/1/2` scoring rubric;
- `monitoring_policy`: cadence, lookback window, run mode, dedupe, and stale settings;
- `scoring_model`: fit model, intent model, tier model, formula preset, optional custom formula, tier thresholds, and confidence penalties;
- `validation_report`: structural and obvious contradiction findings.

Rules and sources are first-class objects:

- `RuleGroup` uses `AND`, `OR`, or `NOT`;
- `AtomicRule` carries system-generated id, human rule description, requirement level, source policy, and optional generated technical fields for future agent execution;
- `SourceDefinition` represents `url`, `search_engine`, `api`, `mcp`, or `manual_dataset`;
- `SourcePolicy` may reference shared sources internally by id, but the UI exposes a simpler policy: use global search base, optional local sources, cross-validation, and HITL-governed additional sources.

The frontend must expose a business-language configuration surface:

- do not make users edit internal ids;
- show generated rule ids and signal codes only as compact references for custom formulas;
- do not expose target-field/operator/value triples as user-authored controls;
- do not expose nested rule groups, source ids, source boolean logic, or fallback-confidence labels as the primary UX;
- use source entities and bounded source tables, not textarea-only source lists;
- define shared signal scoring once and allow per-signal overrides only explicitly;
- use scoring presets for normal configuration;
- expose custom formula text only when the custom preset is selected;
- keep radar Settings limited to `Fit`, `Intent`, and `Tier`, not `trigger` or `total` formulas.

The validator catches structural issues and obvious contradictions, but does not attempt semantic industry dictionary reasoning in this slice.

## Consequences

Positive:

- Radar setup is closer to an executable rule/signal engine.
- UI can edit settings by block instead of one global edit mode.
- Future agent execution can consume structured rules and source policies.
- Qualification filters and intent signals are explainable separately.
- Obvious invalid configurations can be surfaced before a radar is run.

Trade-offs:

- The artifact contract changes intentionally to `0.6.5.2`.
- The frontend editor becomes more complex than a simple form.
- Existing XLSX scores remain historical/imported values; the new definition explains how future radar runs should be configured.

## Alternatives Considered

- Keep a flat `RadarDefinition` and add more fields.
  - Rejected because it would keep search filters, signals, sources, and scoring guidance mixed together.
- Add a parallel `definition_v2` while keeping the old contract.
  - Rejected because this is still a PoC artifact contract and carrying both shapes would slow iteration without protecting production users.
- Use only free-text prompts for criteria and sources.
  - Rejected because radar execution, validation, source trust, and evidence review require structured objects.
