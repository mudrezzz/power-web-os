# Developer Guide

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m power_web_os.demo generate-icp-radar
python -m power_web_os.demo generate-icp-radar-catalog
python -m power_web_os.demo generate-account-radar
npm install --prefix ./frontend
npm --prefix ./frontend run dev
```

Direct checkout demo without installing:

```bash
python demo/run_demo.py generate-icp-radar
python demo/run_demo.py generate-icp-radar-catalog
python demo/run_demo.py generate-account-radar
npm --prefix ./frontend run dev
```

Install the required LangGraph document AI framework when working on agent workflows:

```bash
python -m pip install -e ".[agent,dev]"
```

## Repository Layout

```text
src/power_web_os/      Product domain and application baseline
tests/                 Unit and smoke tests
demo/                  Demo fixtures and run instructions
frontend/              React TypeScript Vite demo app
docs/                  Architecture, ADRs, user and contributor docs
.external/             Local research/vendor checkouts, not committed
```

## Frontend Feature Structure

Large product screens must be split into feature modules. A file under `frontend/src/screens/` can stay as the route/shell compatibility wrapper, but feature implementation should live under `frontend/src/features/<feature>/`.

Current ICP Radar structure:

```text
frontend/src/screens/ICPRadarScreen.tsx          Thin wrapper
frontend/src/features/icp-radar/README.md        Feature onboarding, data flow, and new-radar checklist
frontend/src/features/icp-radar/ICPRadarScreen.tsx   Thin feature coordinator
frontend/src/features/icp-radar/icpRadar.css     CSS entrypoint importing feature style modules
frontend/src/features/icp-radar/styles/          CSS modules by ICP Radar UI surface
frontend/src/features/icp-radar/domain/         Pure score, status, validation, qualification helpers
frontend/src/features/icp-radar/adapters/       Raw artifacts -> canonical radar/candidate view models
frontend/src/features/icp-radar/application/    Hooks for navigation, overlays, drafts, and actions
frontend/src/features/icp-radar/components/     Catalog/header presentation components
frontend/src/features/icp-radar/model.tsx        Barrel over focused model modules
frontend/src/features/icp-radar/modelTypes.ts
frontend/src/features/icp-radar/validationModel.ts
frontend/src/features/icp-radar/radarMetaModel.ts
frontend/src/features/icp-radar/liveModel.ts
frontend/src/features/icp-radar/settingsModel.ts
frontend/src/features/icp-radar/candidateViews.tsx   Barrel for fixture candidate views
frontend/src/features/icp-radar/fixtureShortlist.tsx
frontend/src/features/icp-radar/fixturePreview.tsx
frontend/src/features/icp-radar/fixtureDetail.tsx
frontend/src/features/icp-radar/liveCandidateViews.tsx  Barrel for live candidate views
frontend/src/features/icp-radar/liveShortlist.tsx
frontend/src/features/icp-radar/liveDetail.tsx
frontend/src/features/icp-radar/criteriaBreakdown.tsx
frontend/src/features/icp-radar/settings.tsx
frontend/src/features/icp-radar/settingsBlocks.tsx
frontend/src/features/icp-radar/settingsSearch.tsx
frontend/src/features/icp-radar/settingsQualification.tsx
frontend/src/features/icp-radar/settingsMonitoring.tsx
frontend/src/features/icp-radar/settingsSignals.tsx
frontend/src/features/icp-radar/settingsScoring.tsx
frontend/src/features/icp-radar/settingsValidation.tsx
frontend/src/features/icp-radar/settingsFields.tsx
frontend/src/features/icp-radar/settingsHeader.tsx
frontend/src/features/icp-radar/detailPrimitives.tsx
```

Rules:

- Start ICP Radar frontend changes from `frontend/src/features/icp-radar/README.md`; it documents the data flow, ownership map, and checklist for adding radar types without creating new UI paradigms.
- Keep route/screen wrappers thin once a screen grows beyond a simple view.
- Keep the feature entrypoint thin; it should not own localStorage, raw fixture/live mapping, or score calculation.
- Put new radar source types behind an adapter that emits the canonical radar/candidate view model.
- Put browser-local state in application hooks, not in presentation components.
- Keep model/normalization/scoring helpers separate from JSX-heavy view components.
- Keep feature-specific CSS next to the feature module; leave `frontend/src/styles.css` for app shell and shared primitives.
- Keep large feature CSS split by surface. ICP Radar styles use `icpRadar.css` only as an import entrypoint, with catalog, shortlist, preview, detail, settings, criteria, and responsive rules in `frontend/src/features/icp-radar/styles/`.
- Keep expensive or rarely used panels, such as ICP Radar Settings, behind `React.lazy` and `Suspense`.
- Add short module-boundary comments and comments for non-obvious data shaping, storage migration, scoring, or UX invariants.
- Do not add comments that repeat obvious JSX.
- Run `python -m pytest` after feature-structure changes; `tests/test_frontend_architecture_contract.py` guards the ICP Radar decomposition, application/adapters/domain/components boundaries, model barrel boundaries, feature CSS module ownership, lazy Settings loading, and i18n runtime/resource split.

When adding ICP Radar UI, prefer the existing module boundary instead of adding new logic to `ICPRadarScreen.tsx`: source-specific artifact mapping goes to `adapters/`, browser-local workflows go to `application/`, domain decisions go to `domain/`, shortlist/table changes go to `fixtureShortlist.tsx` or `liveShortlist.tsx`, preview-only changes go to `fixturePreview.tsx`, detail/review changes go to `fixtureDetail.tsx` or `liveDetail.tsx`, and settings block changes go to the relevant `settings*` module.

## Domain Baseline

The current Python package contains:

- `Account`
- `Signal`
- `Evidence`
- `PowerWebRole`
- `Playbook`
- `AccessRoute`
- `AccessPlan`
- `DeterministicAccessPlanner`
- `AccountRadar`
- `PowerWebBoardBuilder`
- `PlaybookAnalysisBuilder`
- `AccessPlanningState`
- `AccessPlanningWorkflow`
- `ICPRadar`
- `ICPRadarXlsxImport`

The deterministic planner owns route scoring. `AccessPlanningWorkflow` orchestrates typed state, planner invocation, artifact shaping, and workflow metadata. `ICPRadarXlsxImport` normalizes the ТОиР/SIBUR workbook into an `ICPRadarArtifact`. `AccountRadar` builds the accepted-portfolio read model from generated Access Plans and owns deterministic account ranking. `PowerWebBoardBuilder` builds the selected-account board read model from the generated Access Plan and current account roles/missing roles. `PlaybookAnalysisBuilder` builds a read-only explanation of playbook effects over the generated routes, including the current playbook and the deterministic `no_partner_motion` what-if variant. The workflow uses `langgraph-dai` when the optional `agent` extra is installed and falls back to a local runner for base tests.

## ICP Radar Funnel

The next ABM layer is `ICP Radar`. It sits before the current Account / Power Web / Access Plan loop.

Terminology:

- `ICP Radar`: product/ICP-specific radar that discovers and monitors candidate accounts.
- `AccountRadar`: current deterministic portfolio read model in code. It may remain as an internal compatibility name until the ICP Radar layer is implemented.
- `Account discovery`: stable or manually imported legal-entity discovery, for example companies inside a holding.
- `Signal monitoring`: recurring search for current evidence and buying signals against discovered accounts.
- `Radar candidate`: an account that has been scored but has not yet been accepted into Power Web work.

Implemented first fixture:

- Use `demo/fixtures/icp_radar/sibur_icp_pass1.xlsx` as the source workbook fixture.
- Write the normalized artifact to `demo/fixtures/icp_radar/toir_sibur_icp_radar.json`.
- Model the `Criteria` sheet as `SignalCriterion` records.
- Model the `ICP Matrix` sheet as legal entities, evidence refs, criterion scores, fit/intent/trigger totals, and tier.
- Model `Sources` as evidence-source metadata.
- Keep numeric C1-C20 scores sourced from the XLSX.
- Add criterion-level explanation from `demo/fixtures/icp_radar/toir_sibur_criterion_evidence.json` where curated demo facts exist.
- Mark curated criterion explanations as `evidence_origin: synthetic_demo_annotation`; they are demo annotations, not fields extracted from the XLSX.
- Fill every candidate and every C1-C20 criterion with `criteria_evidence`:
  - `supported` when curated demo facts exist;
  - `inferred` when score is nonzero but no criterion-level facts exist;
  - `not_observed` when score is zero.
- Use Russian-language company names and people in generated accepted-account demo data.

Radar catalog and configuration loop:

- Since Slice 0.6.5.2, `RadarDefinition` is an executable structured model:
  - `metadata`: name, description, owner, status;
  - `global_search_policy`: reusable typed sources, keywords, exclusions, and whether the system may use additional sources;
  - `account_qualification.rule_group`: rules that decide whether a legal entity belongs in the radar universe;
  - `intent_signals[]`: signals that decide why a qualified account is interesting now;
  - `intent_signals[].scoring_rubric`: fixed `0/1/2` signal scoring rules;
  - `monitoring_policy`: cadence, lookback window, run mode, dedupe, and stale settings;
  - `scoring_model`: fit model, intent model, tier model, preset choice, optional custom formula, tier thresholds, and confidence penalties;
  - `validation_report`: structural and obvious contradiction findings from `RadarDefinitionValidator`.
- Settings are edited by block: selected radar header, Global search base, Account qualification rules, Monitoring, Signal scale, Intent signals, Scoring model, and Validation. Do not reintroduce one global edit mode or a standalone Settings action row.
- The selected radar header owns human metadata and lifecycle controls: name, description, active/inactive status, read-only owner, duplicate, local delete, and reset. Keep actions in the top-right header row, and keep status/local/read-only metadata with the radar description on the left.
- Do not repeat monitoring run mode in the selected radar header; run mode belongs to the Monitoring settings block.
- Sources are entities, not textarea blobs. The UI shows the global source base as a bounded numbered table, can add local per-rule/per-signal sources, and stores generated source ids only as internal contract fields.
- Rule and signal IDs/codes are generated by the system. They may be displayed compactly for custom formula references, but they must not be manually edited in the UI.
- Account qualification rules and signal detection rules are description-first. The UI must not expose `target field`, `comparison operator`, or `value` as user-authored controls. Optional generated technical fields may remain in the artifact for future agent execution and validator support.
- The visible qualification editor is intentionally flat: no nested group editor. It may use a root `RuleGroup` internally, but users only edit natural-language criteria, `AND` / `OR`, optional `NOT`, requirement level, global-base usage, local sources, cross-validation, and HITL additional-source switches. View mode should be an aligned table with operator, rule, source, cross-check, additional-source, and requirement columns.
- The visible source policy editor must not expose source IDs, source logic, or fallback confidence. Use user-facing trust policies: trusted, cross-check, and HITL required.
- Boolean source policies and active/inactive state use the shared switch control. Disabled switches are read-only indicators and must not fire state changes; active switch thumbs must remain inside the track.
- Monitoring duration fields are stored as strings in the artifact for compatibility, but the UI edits them as number plus unit.
- Intent signals use a separate global scoring rubric table by default. Per-signal rubric editing is hidden behind an explicit override switch. View mode should be an aligned table with code, detection rule, source, cross-check, additional-source, and scale-override columns.
- Qualification filters and intent signals are different domain concepts and must remain separate.
- Treat `RadarDefinition` as a first-class configuration contract, not only metadata inside a generated report.
- `generate-icp-radar` writes the active shortlist artifact and includes `radar.definition`.
- `generate-icp-radar-catalog` writes the portfolio artifact for multiple configured ICP Radars.
- The frontend loads `/demo/icp_radars.json` for radar cards and `/demo/icp_radar.json` for the active fixture-backed `ТОиР / SIBUR` shortlist.
- Editable configuration uses constrained controls. Formula presets are preferred; custom formulas are allowed only through an explicit preset and should reference generated rule IDs or signal codes.
- Generated artifacts remain read-only. The frontend stores created/edited radar definitions in browser `localStorage` under `power-web-os-icp-radar-config-overrides`.
- The localStorage overlay shape is keyed by `radar_id` and stores `{ override_type, radar, saved_at }`. `override_type` is `created`, `edited`, or `deleted`; UI-only radar statuses may be `local_draft` or `modified_locally`. `deleted` hides a generated radar until demo changes are reset and does not mutate generated artifacts.
- Normalize radar definitions loaded from both generated artifacts and `localStorage` before rendering Settings. Local browser drafts can outlive artifact-contract changes; missing arrays, source policies, rule groups, monitoring fields, scoring fields, or validation arrays must be defaulted rather than allowed to crash a switch interaction.
- Edited settings do not call a production API, do not write JSON artifacts, do not run live connectors, and do not recalculate the fixture shortlist in this slice.
- The catalog must expose reset behavior so a user can return to generated artifact state.
- Run history and monitoring schedule come after configuration, with explicit separation between one-time account discovery and recurring signal monitoring.

Imported workbook scoring fields:

```text
fit_score = C13 + C14 + C15 + C16 + C17
intent_score = C1..C9 + C18 + C19
trigger_score = C10 + C11 + C12 + C20
total_score = sum(C1..C20)
tiers = >=38 Tier 1, >=25 Tier 2, >=15 Tier 3, else Monitor
```

These fields remain on imported candidates for backward compatibility with the XLSX fixture. They are not the editable radar settings model. Radar Settings expose only:

```text
Fit model: aggregate account qualification criteria
Intent model: aggregate intent signals
Tier model: classify candidates by thresholds
```

Generated command:

```bash
python -m power_web_os.demo generate-icp-radar
python -m power_web_os.demo generate-icp-radar-catalog
```

It writes:

```text
demo/output/icp_radar.json
demo/output/icp_radars.json
frontend/public/demo/icp_radar.json
frontend/public/demo/icp_radars.json
demo/fixtures/icp_radar/toir_sibur_icp_radar.json
```

The generated ICP Radar artifact version is `0.6.5.2`. It keeps `criteria_evidence_contract_version: "0.6.2.3"` and writes the structured `radar.definition` model. `radar.definition.intent_signals` is the canonical C1-C20 dictionary for Settings, candidate scores, and evidence explanations. The top-level `criteria` field is generated from `intent_signals` as a backward-compatible alias and must not diverge. Each candidate keeps the backward-compatible fields `criteria_scores`, `evidence_refs`, and `source_urls`, and adds:

```text
candidates[].criteria_evidence[criterion_code]
candidates[].criteria_evidence[criterion_code].evidence_status
candidates[].criteria_evidence[criterion_code].confidence
candidates[].criteria_evidence[criterion_code].rationale
candidates[].criteria_evidence[criterion_code].facts[]
```

## Live Mini ICP Radar

`Slice 0.6.3.1` adds the first provider-backed ICP Radar run without changing the stable XLSX fixture radar. The live radar is intentionally small: `toir-quick-live`, two qualification criteria, and three intent signals.

The backend boundary is provider-neutral:

- `WebSearchProvider` is the interface used by the workflow.
- `OpenRouterWebSearchProvider` is the first live provider.
- `RecordedWebSearchProvider` is used by tests and mocked runs.
- `LiveICPRadarRunWorkflow` follows the optional `langgraph-dai` / `BaseWorkflow` pattern used elsewhere in the project.

Environment variables are loaded from the process environment or local `.env`:

```text
OPENROUTER_API_KEY=
OPENROUTER_MODEL=
OPENROUTER_WEB_MODE=auto
```

For local CLI demo runs, explicit constructor arguments are strongest, then project `.env`, then ambient OS environment variables. This prevents an old Windows/user `OPENROUTER_API_KEY` from silently overriding the key in the repository-local `.env`.

Supported web modes are `auto`, `server_tools`, `plugin_web`, and `model_native`. `auto` tries OpenRouter server-side web search first and falls back to the OpenRouter web plugin if server tools are unsupported.

Commands:

```bash
python -m power_web_os.demo run-live-mini-icp-radar --dry-run-plan
python -m power_web_os.demo run-live-mini-icp-radar --live
```

`--dry-run-plan` does not call the network and does not create fake candidates. `--live` requires `OPENROUTER_API_KEY` and writes:

```text
demo/output/live_mini_icp_radar_run.json
frontend/public/demo/live_mini_icp_radar_run.json
```

Live artifacts must never contain API keys, authorization headers, bearer tokens, or raw provider dumps. Model-supplied URLs are filtered by HTTP reachability before they can support candidates. If OpenRouter rejects the credentials or no usable sources are returned, the frontend should show the live radar empty state rather than fabricated candidates.

Frontend rendering for live radar results must go through the canonical ICP Radar UX contract. Treat `icp_radar_live_run` as a different data adapter, not as permission to create a separate live-only grid, side panel, table column set, preview, or detail surface. Runtime provider metadata belongs in the candidate `Journal` tab.

Candidate qualification results must use the shared qualification evidence contract before they reach the UI. Provider output can be sparse, but the backend normalizer must shape each Q-rule result into rule snapshot, operator, requirement level, source usages, source origin, trust/check policy, evidence findings, optional short excerpt, cross-validation, requirement evaluation, final assessment, and optional review decision. The candidate detail qualification tab renders that contract as a table-first review surface with expandable rows and browser-local approve/reject/correct decisions. Keep the collapsed row scan-first: code, rule, operator, assessment, source count, cross-validation, and local decision. In expanded rows, render evidence as cards that combine source ref/title/origin/trust with fact, excerpt, and why-it-matches text; do not duplicate a separate sources table there. Requirement level, evidence strength, cross-validation status, confidence, and recommended action belong inside the expanded `Requirement fit` section. Reject/correct decisions must require a comment. Do not render provider-specific raw Q1/Q2 rows directly.

Live signal results follow the same evidence-card rule, but they evaluate intent score rather than qualification fit. The backend normalizer may accept sparse provider output, but the frontend view model must see source usages, source-linked evidence findings, optional excerpt/excerpt type, cross-validation, and score evaluation when available, with controlled fallbacks when missing. The candidate detail signals tab must expand each signal into `Signal score evaluation` -> evidence cards -> human review. Do not render the old summary plus source-list shape as the main expanded signal content. Confirm/reject/stale/correct decisions reuse the browser-local signal validation overlay, and reject/stale/correct require comments.

Expected future domain objects:

```text
ICPProfile
RadarDefinition
RuleGroup
AtomicRule
SourceDefinition
SourcePolicy
IntentSignalDefinition
SignalObservation
SignalValidation
RadarScoringModel
RadarCandidate
RadarRun
```

Current catalog artifact:

```text
artifact_type = icp_radar_catalog
artifact_version = 0.6.5.2
radars[].radar_id
radars[].name
radars[].status
radars[].profile
radars[].summary
radars[].definition
radars[].artifact_path
```

Discovery and monitoring must stay separate. Discovery can be run once or imported manually because legal-entity structure changes slowly. Monitoring should run repeatedly and support incremental mode through evidence fingerprints so previously seen facts are not scored as new signals.

Signal validation is a first-class domain concern. A user must be able to:

- confirm a found signal;
- correct its criterion, strength, confidence, summary, or evidence mapping;
- reject it as wrong or distorted;
- mark it stale when it is no longer actionable.

Validated signals feed the final score. Rejected and stale signals must reduce or remove their scoring contribution while preserving evidence and audit history. The score explanation must show raw observations, validation decisions, and the resulting fit/intent/tier contribution.

The current demo stores validation decisions in browser-local state under:

```text
power-web-os-icp-radar-signal-validation
```

The decision key is `radar_id + account_id + signal_code`. The decision payload contains status, original score, adjusted score, confidence override, corrected summary, selected evidence refs, comment, and `reviewed_at`. The frontend applies this overlay with the same deterministic semantics as `ICPRadarValidationScorer`: `unreviewed` and `confirmed` keep the original score, `corrected` uses the adjusted score, and `rejected` / `stale` contribute `0`. Generated JSON artifacts are not mutated by local validation.

## Access Planning Workflow

The first product loop is:

```text
demo/sample_portfolio.json
-> AccountRadar
-> AccessPlanningWorkflow per account
-> demo/output/account_radar.json
-> frontend/public/demo/account_radar.json
-> frontend/public/demo/access_plans/{account_id}.json
-> Vite demo UI
```

ICP Radar demo flow:

```text
demo/fixtures/icp_radar/sibur_icp_pass1.xlsx
-> ICPRadarXlsxImport
-> demo/output/icp_radar.json
-> frontend/public/demo/icp_radar.json
-> ICP Radar screen
```

The single-account debug path remains available:

```bash
python -m power_web_os.demo generate-access-plan
```

Portfolio fixture entries use the existing `{ account, playbook }` shape with a small `stage` field for Account Radar display.

Access Plan artifacts include a non-breaking `power_web_board` field:

```text
power_web_board.summary
power_web_board.nodes[]
power_web_board.edges[]
power_web_board.route_path[]
```

The board read model is deterministic and belongs to `src/power_web_os/board.py`. It should stay presentation-friendly but source-of-truth-neutral: do not put graph database behavior, editing state, CRM state, or live source extraction in this builder.

Access Plan artifacts also include a non-breaking `playbook_analysis` field:

```text
playbook_analysis.contract_version
playbook_analysis.current
playbook_analysis.variants[]
*.route_decisions[]
*.route_preview.routes[]
```

The playbook read model is deterministic and belongs to `src/power_web_os/playbook_analysis.py`. It explains allowed routes, blocked channels, available assets, review rules, policy decisions, and generated route previews. The `no_partner_motion` variant is generated at artifact-build time by disabling `partner_intro` and partner-case assets, then running the Python planner again. Frontend code must render this payload; it must not duplicate planner scoring or policy logic.

Do not put CRM/source connector logic directly inside domain classes. Add ports/tools and keep connector calls auditable.

## Frontend Demo

The frontend is a local React + TypeScript + Vite app in `frontend/`.

Current structure:

```text
frontend/src/App.tsx                  App state and artifact loading
frontend/src/components/              Token-based UI primitives
frontend/src/features/                Feature modules with owned screens, models, and CSS
frontend/src/i18n.ts                  Locale initialization
frontend/src/i18n/                    EN/RU UI resource modules
frontend/src/demoLocalization.ts      Presentation-layer localization for deterministic demo data
frontend/src/layout/                  Power Web OS shell, sidebar, top bar
frontend/src/screens/                 Product screens and planned placeholders
frontend/src/styles.css               App shell and shared primitive styling
```

Rules:

- Import `ui-design-system/colors_and_type.css`.
- Use `ui-design-system/app-prototype/AppShell.jsx` for product shell structure.
- Use the relevant `ui-design-system/app-prototype/*Screen.jsx` file before implementing a screen.
- Follow the frontend workspace UX ADR family, starting with `2026-06-12-frontend-workspace-ux-principles.md`, for bounded SPA behavior, table-first dense data, sticky identity, evidence-first drilldown, explicit settings state, local draft boundaries, i18n, responsive constraints, and the canonical ICP Radar UX contract.
- Use `lucide-react` for icons.
- Keep UI copy sentence case, with uppercase only for mono eyebrow labels.
- Add visible UI strings through `frontend/src/i18n/en.ts` and `frontend/src/i18n/ru.ts`; keep English/Russian resources synchronized.
- Keep the app shell viewport-bounded; `body` should not be the normal scroll container for product screens.
- Put scrolling inside workspace panes and dense table/card wrappers.
- Use `min-width: 0`, wrapping, ellipsis, or owned horizontal scroll so text never overlaps neighboring columns.
- Load the portfolio artifact from `/demo/account_radar.json`.
- Load selected-account plans from `/demo/access_plans/{account_id}.json`.
- Render the selected account's Power Web Lite board from `artifact.power_web_board` on `Account Map`.
- Render the selected account's playbook analysis from `artifact.playbook_analysis` on `Playbook`.
- Load the ICP Radar artifact from `/demo/icp_radar.json`.
- Keep `ICP Radar` as a separate upstream screen; do not merge it with `Accounts`.
- Treat the ICP Radar catalog as list-first: one configured radar per wide row with stable columns for identity, status, metrics, run mode, and action, not a three-column card grid or floating metric layout that truncates names and counts on laptop screens.
- Treat the main `ICP Radar` screen as a table-first workspace:
  - account/company identity belongs in the first sticky column;
  - horizontal scroll is owned by the table wrapper;
  - the sticky column must keep its own background and z-index so scrolled columns do not bleed through;
  - candidate row preview expands inline under the selected row and has one bounded scroll area for the whole preview;
  - expanded preview content is anchored to the visible table wrapper, not to the horizontally scrolled column grid;
  - preview blocks start at the left of the visible workspace and must not require horizontal scrolling on laptop widths;
  - preview actions sit below the content blocks instead of using a separate left rail;
  - do not put nested scroll containers inside the preview lists;
  - preview is intentionally short: top-5 evidence refs, top-5 criteria, main signal, and short recommendation;
  - score/tier values stay in the table row and should not be repeated inside the preview;
  - full candidate evidence/criteria work belongs on a separate candidate detail screen with breadcrumbs back to `ICP Radar`;
  - the candidate detail view keeps a compact sticky header so account identity remains visible while criteria scroll.
- Apply that same table-preview-detail pattern to every ICP Radar shortlist source, including live/provider-backed radars:
  - map each source into a canonical radar/candidate view model before rendering;
  - use the canonical shortlist columns: company, total, fit, intent, trigger, tier, evidence, action;
  - unsupported score slots render as `—`, not as a changed table shape;
  - preview always has four blocks: summary, tier, qualification, signals;
  - preview never renders source lists or runtime/provider metadata;
  - detail always uses tabs: overview, qualification, signals, sources, journal;
  - runtime provider metadata, queries, warnings, and structured trace render only in the journal tab;
  - do not add provider-specific split grids, custom shortlist columns, custom previews, or always-visible side detail panels.
- Treat candidate signal validation as table-first inside the detail view:
  - C1-C20 initially render as compact rows, not fully expanded evidence cards;
  - filter by signal validation status before drilling into detail;
  - sort by score, status, or confidence;
  - expand one signal row at a time for rationale, facts, source refs, and validation controls;
  - local confirm/correct/reject/stale controls must be clearly labelled as browser-local demo state until durable persistence exists.
- Keep `ICP Radar` navigation local to `ICPRadarScreen` until a broader routing need appears:
  - `expandedCandidateId` owns inline preview state;
  - `detailCandidateId` owns the read-only candidate detail view;
  - do not introduce React Router only for ICP Radar candidate drilldown.
- Treat `Take into work` as planned until Slice 0.6.4 implements the handoff.
- Keep unfinished navigation entries visible only as planned placeholders; do not fake unavailable functionality.

The frontend default locale is `en`. The supported locales are `en` and `ru`, and the selected locale is stored in browser `localStorage`. UI chrome is localized through `i18n.ts`; visible deterministic artifact values such as stages, owners, route titles, rationale, risks, state changes, signal summaries, and missing-role labels are localized in `demoLocalization.ts`. Keep raw source refs, IDs, company names, and person names as artifact data unless a slice explicitly changes that policy.

## Test Commands

```bash
python -m pytest
python -m power_web_os.demo generate-icp-radar
python -m power_web_os.demo generate-icp-radar-catalog
python -m power_web_os.demo generate-account-radar
python -m power_web_os.demo generate-access-plan
python demo/run_demo.py generate-icp-radar
python demo/run_demo.py generate-icp-radar-catalog
python demo/run_demo.py generate-account-radar
python demo/run_demo.py generate-access-plan
npm --prefix ./frontend run build
npm --prefix ./frontend run visual:smoke
npm --prefix ./frontend run settings:toggle-smoke
```

## Visual Smoke

Use Playwright visual smoke whenever frontend layout, shell navigation, user-facing screens, or documentation screenshots change.

```bash
python -m power_web_os.demo generate-icp-radar
python -m power_web_os.demo generate-icp-radar-catalog
python -m power_web_os.demo generate-account-radar
npm --prefix ./frontend run visual:smoke
```

The script starts Vite through the Vite Node API, opens Chromium, captures key workspace screens at `1280x720` and `1366x768`, and writes screenshots to `docs/qa/screenshots/visual-smoke/`.

The screenshot set is smoke evidence, not pixel-perfect regression. It should still be refreshed when the documented UI changes.

Use the Settings toggle smoke when changing ICP Radar Settings, switches, local draft state, or editor block layout:

```bash
npm --prefix ./frontend run settings:toggle-smoke
```

The script starts Vite, opens the first ICP Radar in Russian locale, verifies the global-search switch through save and reload, injects a legacy partial localStorage override, enters every editable Settings block, clicks each visible switch twice, and fails on browser errors, an under-rendered workspace, or any viewport drift where `.app-shell` leaves the visible frame.

## GitHub Wiki Publishing

The GitHub Wiki is generated from repository docs and QA screenshots.

Build locally without pushing:

```bash
python scripts/publish_github_wiki.py --dry-run
```

Publish to GitHub Wiki:

```bash
python scripts/publish_github_wiki.py
```

The script builds:

- `Home.md`
- `_Sidebar.md`
- `User-Guide.md`
- `Developer-Guide.md`
- `Architecture.md`
- `Demo.md`
- `Roadmap.md`
- `QA-Visual-Smoke.md`
- `assets/screenshots/visual-smoke/*.png`

Wiki screenshot pages are curated through the screenshot walkthrough manifest in `scripts/publish_github_wiki.py`. Do not generate user-facing headings directly from screenshot filenames. When adding or replacing a documented screen:

- add or update the manifest item with a human title, short explanation, and both viewport image paths;
- add the same user-facing walkthrough context to `docs/user/USER_GUIDE.md`;
- keep `docs/qa/README.md` focused on reproducible QA assets and regeneration commands;
- run `python scripts/publish_github_wiki.py --dry-run` and inspect `.wiki-build/User-Guide.md`, `.wiki-build/Home.md`, and `.wiki-build/QA-Visual-Smoke.md` before publishing.

If GitHub has Wiki enabled but the wiki git repository does not exist yet, create one page in the GitHub Wiki web UI once, then rerun the publisher.

## Documentation Rules

Update `ROADMAP.md`, architecture docs, demo docs, and user docs in the same slice when behavior changes.
