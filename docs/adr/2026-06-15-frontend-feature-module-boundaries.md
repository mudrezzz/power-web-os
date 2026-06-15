# ADR: Frontend Feature Module Boundaries

- Status: Accepted
- Date: 2026-06-15

## Context

`ICPRadarScreen.tsx` grew into a multi-thousand-line file that mixed catalog state, artifact adapters, scoring helpers, localStorage overlays, settings editors, candidate previews, detail views, and review controls. That made the screen difficult to review and made future UX changes likely to reintroduce inconsistent radar-specific layouts.

## Decision

Complex frontend product areas must live as feature modules under `frontend/src/features/<feature>/`.

For ICP Radar, the public screen in `frontend/src/screens/ICPRadarScreen.tsx` is a thin compatibility wrapper. The implementation lives in `frontend/src/features/icp-radar/` and is split by responsibility:

- `ICPRadarScreen.tsx`: thin feature coordinator, data loading state, and current surface selection.
- `domain/`: pure score, validation, qualification review, status, and metadata helper modules.
- `adapters/`: fixture/live/empty radar adapters that map raw artifacts into canonical radar and candidate view models.
- `application/`: hooks that own screen navigation, browser-local overlays, settings draft actions, and review actions.
- `components/`: presentation-only catalog and selected-radar header components.
- `model.tsx`: a barrel that keeps the public feature import stable while focused model modules own artifact normalization, local overlay loading, scoring helpers, generated IDs, and status mapping.
- `modelTypes.ts`: feature-local view-state types, storage keys, and signal-code constants.
- `validationModel.ts`: signal validation overlay loading, effective score calculation, and validation status helpers.
- `radarMetaModel.ts`: radar status and catalog metadata labels.
- `liveModel.ts`: live radar score, qualification, source, and signal view-model helpers.
- `settingsModel.ts`: settings draft factories, normalization, generated IDs, and settings validation.
- `candidateViews.tsx`: a stable barrel for fixture-backed candidate views.
- `fixtureShortlist.tsx`: fixture-backed candidate table and empty shortlist state.
- `fixturePreview.tsx`: bounded fixture candidate preview and top-criteria selection helpers.
- `fixtureDetail.tsx`: fixture candidate detail tabs and signal validation summary.
- `liveCandidateViews.tsx`: a stable barrel for live-radar candidate views.
- `liveShortlist.tsx`: live candidate table and bounded live preview using the canonical radar UX.
- `liveDetail.tsx`: live candidate detail tabs, qualification review, sources, and journal.
- `criteriaBreakdown.tsx`: C1-C20 signal validation and evidence review table.
- `settings.tsx`: block-editable settings shell.
- `settingsBlocks.tsx`: settings cards, metrics, and planned AI suggestion affordance.
- `settingsSearch.tsx`: global search policy, source table, and source editor.
- `settingsQualification.tsx`: account qualification summary and editor.
- `settingsMonitoring.tsx`: monitoring policy summary and editor.
- `settingsSignals.tsx`: intent signals and signal scale editor.
- `settingsScoring.tsx`: scoring model summary and editor.
- `settingsValidation.tsx`: validation report summary.
- `settingsFields.tsx`: reusable settings field primitives.
- `settingsHeader.tsx`: lightweight radar header editor that can load without the full settings editor.
- `detailPrimitives.tsx`: shared detail tab and metric primitives.

Heavy settings UI is lazy-loaded from the feature entrypoint so the default shortlist/catalog path does not pull the whole editor into the first application bundle.

ICP Radar CSS is owned by the feature module in `icpRadar.css`. Global `styles.css` remains responsible for the app shell and shared primitives. Runtime i18n initialization stays in `frontend/src/i18n.ts`; large EN/RU resources live in dedicated resource modules.

React remains functional-component based. The target architecture applies OOP principles through explicit module ownership, typed contracts, adapters, hooks, and pure services. Class components and inheritance-heavy UI hierarchies are not the preferred style.

## Rules

- Screen files in `frontend/src/screens/` should be thin wrappers once a feature becomes large.
- Feature entrypoints should remain thin coordinators; they should not own localStorage, scoring rules, or provider-specific artifact branching.
- New data-source variants should enter through adapters and canonical view models, not through new visual paradigms or screen branches.
- Application hooks own browser-local workflow state and mutations.
- Presentation components must not read or write `window.localStorage`.
- A feature entrypoint must not define the feature's large table/detail/settings subcomponents inline.
- Domain/view-model helpers should not import React UI primitives unless they are explicitly presentation helpers.
- Model barrels are acceptable as stable import boundaries, but implementation logic should live in responsibility-specific modules.
- Feature-specific selectors should live with the feature CSS, not in the global stylesheet.
- Runtime initialization files should stay small; resource dictionaries should be isolated and directly testable.
- Add comments at module boundaries and before non-obvious data-shaping logic; avoid comments that restate JSX.
- Contract tests must guard the decomposition so future changes do not collapse the module back into one screen file.
- Resource files may be large, but runtime init files should remain small and focused.

## Consequences

New radar UX work should modify the relevant feature module instead of adding more code to the screen wrapper. Future cleanup should continue by reducing large feature component files, but without changing user-visible behavior or breaking the table-preview-detail UX contract.
