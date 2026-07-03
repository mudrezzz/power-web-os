import re
from pathlib import Path


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def i18n_text() -> str:
    i18n_files = [
        Path("frontend/src/i18n.ts"),
        Path("frontend/src/i18nResources.ts"),
        *sorted(Path("frontend/src/i18n").glob("*.ts")),
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in i18n_files)


def icp_radar_feature_text() -> str:
    feature_dir = Path("frontend/src/features/icp-radar")
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted(feature_dir.rglob("*.ts*")))


def css_text() -> str:
    css_files = [Path("frontend/src/styles.css"), *sorted(Path("frontend/src/features").glob("**/*.css"))]
    return "\n".join(path.read_text(encoding="utf-8") for path in css_files)


def test_frontend_imports_design_system_tokens() -> None:
    entrypoint = Path("frontend/src/main.tsx").read_text(encoding="utf-8")

    assert "ui-design-system/colors_and_type.css" in entrypoint
    assert "import './i18n'" in entrypoint


def test_frontend_i18n_resources_cover_supported_locales() -> None:
    i18n = i18n_text()
    package_json = Path("frontend/package.json").read_text(encoding="utf-8")

    assert "supportedLocales = ['en', 'ru']" in i18n
    assert "defaultLocale: SupportedLocale = 'en'" in i18n
    assert "localeStorageKey" in i18n
    assert "i18next" in package_json
    assert "react-i18next" in package_json
    assert "settings:toggle-smoke" in package_json


def test_frontend_localizes_visible_demo_artifact_data_for_ru() -> None:
    localizer = Path("frontend/src/demoLocalization.ts").read_text(encoding="utf-8")
    accounts_screen = Path("frontend/src/screens/AccountsScreen.tsx").read_text(encoding="utf-8")
    access_plans_screen = Path("frontend/src/screens/AccessPlansScreen.tsx").read_text(encoding="utf-8")
    playbook_screen = Path("frontend/src/screens/PlaybookScreen.tsx").read_text(encoding="utf-8")

    assert "useDemoLocalization" in accounts_screen
    assert "useDemoLocalization" in access_plans_screen
    assert "useDemoLocalization" in playbook_screen

    for english_value in [
        "Access",
        "Mapping",
        "partner_intro",
        "procurement_discovery",
        "Manufacturing analytics services purchase indicates an active buying process.",
        "Formal route can be slow and may expose the team too late.",
        "procurement_role: unknown -> identified",
        "procurement",
        "Account Executive",
        "Partner Manager",
        "economic_buyer",
        "procurement_role",
        "selected",
        "missing",
        "cold_telegram",
        "partner_case_data_platform",
        "Allowed by playbook and supported by account evidence.",
        "Partner motion disabled in this what-if playbook.",
        "Missing roles exist, but stronger allowed routes outrank this discovery move.",
        "Route conditions are not met.",
        "София Чернова can become a technical champion.",
        "Майя Коган can become a technical champion.",
        "Иван Петров can become a technical champion.",
        "Геликс Системы is connected to the account as partner.",
        "Икс-Софт is connected to the account as partner.",
    ]:
        assert english_value in localizer

    for screen_value in [
        "item.top_reason",
        "item.best_route_title",
        "item.owner",
        "route.reason",
        "route.expected_state_change",
        "route.risk",
        "item.summary",
        "signal.kind",
        "signal.summary",
        "decision.reason",
        "variant.assets",
        "variant.blocked_channels",
    ]:
        assert screen_value in accounts_screen or screen_value in access_plans_screen or screen_value in playbook_screen


def test_frontend_demo_contains_required_sections() -> None:
    shell = Path("frontend/src/layout/AppShell.tsx").read_text(encoding="utf-8")
    accounts_screen = Path("frontend/src/screens/AccountsScreen.tsx").read_text(encoding="utf-8")
    access_plans_screen = Path("frontend/src/screens/AccessPlansScreen.tsx").read_text(encoding="utf-8")
    planned_screen = Path("frontend/src/screens/PlannedScreen.tsx").read_text(encoding="utf-8")

    for label_key in [
        "nav.icpRadar",
        "nav.accounts",
        "nav.map",
        "nav.plans",
        "nav.signals",
        "nav.playbook",
        "nav.tasks",
        "nav.inbox",
    ]:
        assert label_key in shell

    for label_key in [
        "accounts.eyebrow",
        "accounts.columns.radarScore",
        "accounts.columns.signals",
        "accounts.columns.missing",
        "accounts.columns.bestRoute",
        "accounts.columns.owner",
        "accounts.columns.review",
    ]:
        assert label_key in accounts_screen

    for label_key in [
        "plans.objectiveEyebrow",
        "plans.boardCoverage",
        "plans.signalEvidence",
        "plans.reviewStatus",
    ]:
        assert label_key in access_plans_screen

    assert "planned.workspaceEyebrow" in planned_screen
    assert "planned.queueEyebrow" in planned_screen
    assert "Accounts portfolio" not in planned_screen


def test_account_map_screen_replaces_planned_placeholder() -> None:
    app = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    planned_screen = Path("frontend/src/screens/PlannedScreen.tsx").read_text(encoding="utf-8")
    account_map_screen = Path("frontend/src/screens/AccountMapScreen.tsx").read_text(encoding="utf-8")
    types = Path("frontend/src/types.ts").read_text(encoding="utf-8")
    css = css_text()

    assert "AccountMapScreen" in app
    assert "activeScreen === 'map'" in app
    assert "planned.map" not in planned_screen
    assert "PowerWebBoard" in types

    for contract_value in ["power_web_board", "board.nodes", "board.edges", "board.route_path"]:
        assert contract_value in account_map_screen

    for css_rule in [
        ".account-map-screen",
        ".board-scene",
        ".board-edge-highlighted",
        ".board-node-route",
        ".map-inspector",
    ]:
        assert css_rule in css


def test_playbook_screen_replaces_planned_placeholder() -> None:
    app = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    planned_screen = Path("frontend/src/screens/PlannedScreen.tsx").read_text(encoding="utf-8")
    playbook_screen = Path("frontend/src/screens/PlaybookScreen.tsx").read_text(encoding="utf-8")
    types = Path("frontend/src/types.ts").read_text(encoding="utf-8")
    i18n = i18n_text()

    assert "PlaybookScreen" in app
    assert "activeScreen === 'playbook'" in app
    assert "planned.playbook" not in planned_screen
    assert "PlaybookAnalysis" in types

    for contract_value in [
        "playbook_analysis",
        "route_decisions",
        "route_preview",
        "variant-option",
    ]:
        assert contract_value in playbook_screen

    assert "no_partner_motion" in i18n

    for label_key in [
        "playbook.allowedRoutes",
        "playbook.blockedChannels",
        "playbook.assets",
        "playbook.reviewRules",
        "playbook.decisionStatus",
    ]:
        assert label_key in playbook_screen or label_key in i18n


def test_frontend_shell_uses_design_system_prototype_structure() -> None:
    shell = Path("frontend/src/layout/AppShell.tsx").read_text(encoding="utf-8")
    app = Path("frontend/src/App.tsx").read_text(encoding="utf-8")

    assert "AppShell" in app
    assert "Sidebar" in shell
    assert "TopBar" in shell
    assert "topbar.accessPlansFor" in shell
    assert "LanguageSwitch" in shell
    assert "localeStorageKey" in shell


def test_frontend_shell_uses_bounded_spa_frame_css() -> None:
    css = css_text()

    for selector in ["html,", "body,", "#root", ".app-shell", ".sidebar", ".workspace", ".workspace-body"]:
        assert selector in css

    assert "height: 100dvh" in css
    assert "overflow: hidden" in css
    assert "overflow: auto" in css
    assert "overflow-y: auto" in css


def test_accounts_screen_contains_overflow_safe_table_rules() -> None:
    css = css_text()

    assert ".accounts-screen .card" in css
    assert "overflow-x: auto" in css
    assert ".accounts-table-head > span" in css
    assert ".account-row > span" in css
    assert "min-width: 0" in css
    assert "text-overflow: ellipsis" in css


def test_app_loads_account_radar_and_selected_access_plan_artifacts() -> None:
    app = Path("frontend/src/App.tsx").read_text(encoding="utf-8")

    assert "/demo/account_radar.json" in app
    assert "access_plan_path" in app


def test_icp_radar_ui_separates_candidate_discovery_and_signal_monitoring() -> None:
    app = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    api = Path("frontend/src/api/radarApi.ts").read_text(encoding="utf-8")
    backend_hook = Path("frontend/src/features/icp-radar/application/useRadarBackend.ts").read_text(encoding="utf-8")
    controls = Path("frontend/src/features/icp-radar/livePipelineControls.tsx").read_text(encoding="utf-8")
    report_mapper = Path("frontend/src/features/icp-radar/signalMonitoringReport.ts").read_text(encoding="utf-8")
    report = Path("frontend/public/demo/radar_signal_monitoring_report.json").read_text(encoding="utf-8")
    i18n = i18n_text()

    assert "/demo/radar_signal_monitoring_report.json" in app
    assert "const defaultBaseUrl = 'http://127.0.0.1:8001'" in api
    assert "const requestTimeoutMs = 30000" in api
    assert "controller.abort()" in api
    assert "signalMonitoringReportFromJson" in app
    assert "queueCandidateDiscoveryRun" in api
    assert "pipeline_id: 'candidate-discovery'" in api
    assert "run_kind: 'candidate_discovery'" in api
    assert "signalMonitoringRunSupport" in api
    assert "queueCandidateDiscoveryRun" in backend_hook
    assert "queueRadarRun(radarId" not in backend_hook

    for expected in [
        "candidateDiscoveryLastRunLabel",
        "artifact?.dossier?.run_context.run_id",
        "artifact?.run_metadata.task_id",
        "summaryLastRun !== 'not_run'",
        "icpRadar.live.pipeline.candidate.run",
        "icpRadar.live.pipeline.signal.run",
        "disabled",
        "signalMonitoringReport",
        "onToggleSignalReport",
    ]:
        assert expected in controls

    for expected in [
        "Кого мониторить",
        "Что нового произошло",
        "Run candidate discovery",
        "Check signals",
        "Production execution will arrive after the backend API slice",
    ]:
        assert expected in i18n

    assert "blockedKeyPattern" in report_mapper
    assert "raw_prompt" not in report
    assert "headers" not in report
    assert "secret" not in report.lower()
    assert '"live_provider_calls": 0' in report


def test_icp_radar_screen_is_default_and_loads_fixture_artifact() -> None:
    app = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    shell = Path("frontend/src/layout/AppShell.tsx").read_text(encoding="utf-8")
    screen = icp_radar_feature_text()
    types = Path("frontend/src/types.ts").read_text(encoding="utf-8")
    i18n = i18n_text()
    css = css_text()

    assert "useState<ScreenId>('icp_radar')" in app
    assert "/demo/icp_radars.json" in app
    assert "/demo/icp_radar.json" in app
    assert "/demo/live_mini_icp_radar_run.json" in app
    assert "useRadarBackend" in app
    assert "liveRunArtifact={activeLiveMiniRadarArtifact}" in app
    assert "backend={icpRadarBackend}" in app
    assert "activeScreen === 'icp_radar'" in app
    assert "nav.icpRadar" in shell
    assert "topbar.icpRadar" in shell
    assert "ICPRadarArtifact" in types
    assert "ICPRadarCatalogArtifact" in types
    assert "ICPRadarCatalogItem" in types
    assert "LiveICPRadarRunArtifact" in types
    assert "LiveRadarCandidate" in types
    assert "LiveRadarSourceEvidence" in types
    assert "RadarDefinition" in types
    assert "EditableRadarDefinitionDraft" in types
    assert "RadarConfigOverride" in types
    assert "RadarEditorState" in types
    assert "RadarMetadata" in types
    assert "GlobalSearchPolicy" in types
    assert "RuleGroup" in types
    assert "AtomicRule" in types
    assert "SourceDefinition" in types
    assert "SourcePolicy" in types
    assert "IntentSignalDefinition" in types
    assert "SignalScoringRubric" in types
    assert "MonitoringPolicy" in types
    assert "RadarScoringModel" in types
    assert "RadarValidationReport" in types
    assert "CriterionEvidenceExplanation" in types
    assert "SignalValidationDecision" in types
    assert "SignalValidationOverlay" in types
    assert "ValidatedCandidateScore" in types
    assert "criteria_evidence" in types
    assert "definition: RadarDefinition" in types

    for contract_value in [
        "criteria_scores",
        "criteria_evidence",
        "evidence_refs",
        "artifact.radar.definition.intent_signals",
        "score.effective_score.fit_score",
        "score.effective_score.intent_score",
        "score.effective_score.trigger_score",
        "score.effective_score.total_score",
        "selectedRadarId",
        "RadarCatalogScreen",
        "RadarSettings",
        "SettingsBlockCard",
        "QualificationRulesEditor",
        "SimpleRuleEditor",
        "SourceListEditor",
        "sourceUsageObligationValue",
        "SimpleSourcePolicyEditor",
        "IntentSignalsEditor",
        "SignalRubricOverride",
        "SignalRubricTable",
        "DurationField",
        "ToggleField",
        "ValidationReportView",
        "EmptyShortlist",
        "shortlistTab",
        "operationsTab",
        "settingsTab",
        "radarOverrides",
        "power-web-os-icp-radar-config-overrides",
        "power-web-os-icp-radar-signal-validation",
        "localStorage",
        "createRadar",
        "saveDraft",
        "discardChanges",
        "duplicateRadar",
        "deleteRadar",
        "resetToArtifact",
        "resetDemoChanges",
        "definition.intent_signals",
        "definition.scoring_model",
        "draft.validation_report",
        "local_draft",
        "modified_locally",
        "LiveRadarShortlistTable",
        "LiveRadarRunDiagnosticsView",
        "LiveRadarPreflightPanel",
        "LiveRadarCandidatePreview",
        "LiveRadarCandidateDetailView",
        "CandidateDetailTabs",
        "FixtureRadarCandidateDetailView",
        "canonicalPreview",
        "canonicalDetail",
        "expandedLiveCandidateId",
        "detailLiveCandidateId",
        "CandidateDetailTab",
            "toir-quick-live",
            "icpRadar.live.emptyTitle",
            "icpRadar.live.qualification",
            "icpRadar.live.signals",
            "icpRadar.live.evidence",
    ]:
        assert contract_value in screen

    assert "/api/" not in Path("frontend/src/features/icp-radar/ICPRadarScreen.tsx").read_text(encoding="utf-8")
    assert "RadarApiClient" in screen
    assert "fetch(" not in screen

    for table_first_value in [
        "expandedCandidateId",
        "detailCandidateId",
        "icp-sticky-cell",
        "icp-candidate-preview",
        "icp-detail-breadcrumbs",
        "backToTable",
        "openDetails",
    ]:
        assert table_first_value in screen or table_first_value in i18n

    assert "icp-radar-detail" not in screen
    assert "t('icpRadar.readOnly')" not in screen
    assert "position: sticky" in css
    assert ".icp-sticky-cell" in css
    assert ".icp-candidate-preview" in css
    assert "max-height" in css
    assert ".icp-candidate-detail-grid" in css
    assert ".icp-radar-screen > .card" in css
    assert "overflow-x: hidden" in css
    assert ".icp-detail-sticky-header" in css
    assert "height: calc(var(--s-10) + var(--s-5))" in css
    assert ".account-meta span" in css
    assert ".icp-detail-section > .eyebrow" in css
    assert ".icp-definition-list div" in css
    assert "container-type: inline-size" in css
    assert "width: 100cqw" in css
    assert ".icp-settings-grid" in css
    assert ".icp-editor-field" in css
    assert ".criteria-editor-row" in css
    assert ".source-policy-editor" in css
    assert ".source-table" in css
    assert ".source-table-wrap" in css
    assert ".settings-table-row" in css
    assert ".signal-scale-editor" in css
    assert ".settings-table" in css
    assert ".qualification-table" in css
    assert ".intent-signal-table" in css
    assert ".policy-switch-strip" in css
    assert "icp-settings-action-row" not in screen
    assert "signal-scale-panel" not in screen
    assert ".toggle-field" in css
    assert "targetField" not in screen
    assert "icpRadar.settings.comparison" not in screen
    assert "SourcePicker" not in screen
    assert "RuleGroupEditor" not in screen
    assert "AtomicRuleEditor" not in screen
    assert "selectedGlobalSources" not in screen
    assert "setPrimaryRuleDescription" in screen
    assert "source_id: sourceIdFrom(label" not in screen
    assert "triggerFormula" not in screen
    assert "totalFormula" not in screen
    assert "sourceIdFrom(" in screen
    assert "generated_target_field" in types
    assert "formula_preset" in types

    for editable_key in [
        "createRadar",
        "editSettings",
        "viewSettings",
        "saveDraft",
        "discardChanges",
        "duplicateRadar",
        "resetToArtifact",
        "resetDemoChanges",
        "unsavedChanges",
        "localDraft",
        "validation",
        "qualificationRules",
        "intentSignals",
        "globalSearch",
        "scoringRubric",
        "useGlobalSearchPolicy",
        "globalSearchPolicyCopy",
        "generatedId",
        "generatedIdReadonly",
        "generatedCode",
        "signalScaleLocked",
        "aiSuggest",
        "crossValidation",
        "hitlAdditionalSources",
        "notRule",
        "sourceNumber",
        "operator",
        "crossValidationShort",
        "additionalSourcesShort",
        "globalSources",
        "globalAndLocalSources",
        "localSourceCount",
        "scaleOverrideShort",
        "signalScale",
        "durationUnits",
        "deduplicationPolicies",
        "trustPolicies",
        "sourceTypes",
        "formulaPresets",
        "validConfiguration",
        "usageObligation",
        "sourceUsageObligations",
    ]:
        assert editable_key in i18n
    assert "onEditHeader" in screen
    assert "SignalScaleSummary" in screen
    assert "SignalScaleEditor" in screen
    assert "BooleanPill" in screen
    assert "sourcePolicySummary" in screen
    assert "signalRuleText" in screen
    assert "definition.intent_signals.slice(0, 8)" not in screen
    header_segment = screen.split("function RadarDetailHeader", 1)[1].split("function CandidateTable", 1)[0]
    assert "headerDraft.metadata.description" in header_segment
    assert "icp-radar-header-meta-row" in header_segment
    assert "runModeKey(radar.summary.run_mode)" not in header_segment
    assert "TextField label={t('icpRadar.settings.signalName')" not in screen
    assert "TextAreaField label={t('icpRadar.settings.signalDescription')" not in screen
    assert "???" not in i18n
    assert ".icp-preview-heading" in css
    assert ".icp-preview-actions" in css
    assert "icp-preview-sticky-cell" not in screen
    assert "grid-column: 2 / -1" not in css
    assert "candidate.evidence_refs.slice(0, 5)" in screen
    assert "icp-preview-section" in screen

    preview_segment = screen.split("function CandidatePreview", 1)[1].split("function CandidateScoreGrid", 1)[0]
    assert "CandidateScoreGrid" not in preview_segment

    compact_criteria_block = re.search(r"\.criteria-list-compact\s*\{(?P<body>[^}]*)\}", css)
    assert compact_criteria_block is not None
    assert "overflow-y: auto" not in compact_criteria_block.group("body")

    for label_key in [
        "icpRadar.fit",
        "icpRadar.intent",
        "icpRadar.trigger",
        "icpRadar.total",
        "icpRadar.columns.tier",
        "icpRadar.criteria",
        "icpRadar.canonicalDetail.sources",
        "icpRadar.previewEyebrow",
        "icpRadar.openDetails",
        "icpRadar.backToTable",
        "icpRadar.takeIntoWorkPlanned",
        "icpRadar.criterionEvidence",
        "icpRadar.syntheticAnnotation",
        "icpRadar.workbookFallback",
        "icpRadar.supported",
        "icpRadar.inferred",
        "icpRadar.notObserved",
        "icpRadar.criteriaReviewToolbar",
        "icpRadar.criteriaFilters",
        "icpRadar.criteriaSort",
        "icpRadar.localValidation",
        "icpRadar.confirmSignal",
        "icpRadar.rejectSignal",
        "icpRadar.markSignalStale",
        "icpRadar.correctSignal",
        "icpRadar.resetLocalValidation",
        "icpRadar.correctedSummary",
        "icpRadar.selectedEvidenceRefs",
        "icpRadar.catalogTitle",
        "icpRadar.openRadar",
        "icpRadar.backToCatalog",
        "icpRadar.settingsTab",
        "icpRadar.settings.aiSuggest",
        "icpRadar.deleteRadar",
        "icpRadar.settings.intentSignals",
            "icpRadar.settings.qualificationRules",
            "icpRadar.settings.globalSearch",
            "icpRadar.live.emptyTitle",
            "icpRadar.live.runtimeOpenRouter",
            "icpRadar.live.assessment",
            "icpRadar.live.signalStatus",
            "criteria",
            "editingPlanned",
    ]:
        assert label_key in screen or label_key in i18n

    assert "takeIntoWorkPlanned" in i18n
    assert "SignalValidationDecision" in screen
    assert "SignalValidationOverlay" in screen
    assert "ValidatedCandidateScore" in screen
    assert "expandedCriterionCode" in screen
    assert "matchesCriterionFilter" in screen
    assert "compareCriterionRows" in screen
    assert "CriterionEvidenceDetail" in screen
    assert "signalValidation" in screen
    assert "loadSignalValidationOverlay" in screen
    assert "buildValidatedCandidateScore" in screen
    assert "validatedCandidatesForArtifact" in screen
    assert "resetCandidateSignalValidation" in screen
    assert "scoreDelta" in screen
    assert "submitDecision('confirmed')" in screen
    assert "submitDecision('rejected')" in screen
    assert "submitDecision('stale')" in screen
    assert "submitDecision('corrected')" in screen
    assert "criterionReviews" not in screen
    assert "CriterionReviewState" not in screen
    assert "onReview({ status: 'accepted'" not in screen
    assert "onReview({ status: 'edited'" not in screen
    assert ".criteria-review-table" in css
    assert ".criteria-review-head" in css
    assert ".criteria-review-row" in css
    assert ".criterion-evidence-detail" in css
    assert ".criterion-review-panel" in css
    assert ".icp-radar-catalog-list" in css
    assert ".icp-radar-list-row" in css
    assert ".icp-radar-list-status" in css
    assert ".icp-radar-run-mode" in css
    assert ".icp-radar-header-meta-row" in css
    assert ".icp-radar-table-live" in css
    assert ".icp-radar-table-live .icp-radar-table-head" not in css
    assert ".icp-radar-table-live .icp-candidate-row" not in css
    assert ".icp-candidate-preview .criterion-row" in css
    assert "grid-template-columns: var(--s-10) minmax(0, 1fr) minmax(var(--s-16), max-content)" in css
    assert ".icp-score-grid + .icp-detail-section" in css
    assert "--s-14" not in css
    assert ".icp-candidate-detail-tabs" in css
    assert ".icp-candidate-detail-panel" in css
    assert ".canonical-detail-table" in css
    assert ".canonical-journal-list" in css
    assert ".run-dossier" in css
    assert ".run-dossier-source-list" in css
    assert ".live-radar-source-list" in css
    assert ".live-radar-layout" not in css
    assert ".live-radar-grid" not in css
    assert ".live-radar-table" not in css
    assert ".live-radar-detail" not in css
    assert "live-radar-summary" not in screen
    assert "live-radar-metadata" not in screen
    assert "LiveMiniRadarShortlist" not in screen
    assert "LiveRadarCandidateDetail(" not in screen
    assert ".icp-radar-header-badges" not in css
    assert "html,\nbody,\n#root" in css
    assert ".app-shell {\n  position: fixed;\n  inset: 0;" in css
    assert "transform: translate(var(--s-4), -50%)" in css
    assert "transform: translate(calc(var(--s-4) + var(--s-1)), -50%)" not in css
    assert ".toggle-field {\n  position: relative;" in css
    assert ".toggle-field input {\n  position: absolute;\n  inset: 0;" in css
    assert ".icp-search-policy-grid .icp-detail-section" in css
    assert "if (!disabled)" in screen
    assert "normalizeRadarDefinition" in screen
    assert "normalizeRadarCatalogItem" in screen
    assert "normalizeSourcePolicy" in screen
    assert "normalizeRuleGroup" in screen
    assert "icp-radar-list-status" in screen
    assert "icp-radar-run-mode" in screen
    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" not in css
    assert ".icp-settings-grid" in css
    assert ".icp-radar-tabs" in css
    assert ".icp-detail-sticky-header" in css
    assert "icp-detail-screen" in screen
    assert ".icp-detail-screen" in css
    assert "top: 0" in css
    assert "criteria-action-head" in screen

    toggle_smoke = Path("frontend/scripts/settings-toggle-smoke.mjs").read_text(encoding="utf-8")
    assert "power-web-os-locale" in toggle_smoke
    assert "'ru'" in toggle_smoke
    assert "clickAllTogglesIn" in toggle_smoke
    assert "Settings toggle smoke passed" in toggle_smoke
    assert "clicked < 90" in toggle_smoke
    assert "toggleGlobalSearchAndPersist" in toggle_smoke
    assert "clickGlobalSearchSwitchWithLegacyOverride" in toggle_smoke
    assert "legacy override global search switch" in toggle_smoke
    assert "SPA shell left viewport" in toggle_smoke
    assert "window.scrollY" in toggle_smoke
    assert "shellTop" in toggle_smoke
    assert "shellBottom" in toggle_smoke

    visual_smoke = Path("frontend/scripts/visual-smoke.mjs").read_text(encoding="utf-8")
    assert "live_mini_icp_radar_run.json" in visual_smoke
    assert "captureFixtureRadarFlow" in visual_smoke
    assert "icp-radar-preview" in visual_smoke
    assert "icp-radar-detail" in visual_smoke
    assert "captureLiveRadarFlow" in visual_smoke
    assert "live-icp-radar-preview" in visual_smoke
    assert "live-icp-radar-detail" in visual_smoke
    assert "live-icp-radar-journal" in visual_smoke
    assert "Journal" in visual_smoke
    assert "assertNoSplitLiveLayout" in visual_smoke
    assert "assertNoPageHorizontalScroll" in visual_smoke

    for canonical_key in [
        "icpRadar.canonicalPreview.summary",
        "icpRadar.canonicalPreview.tier",
        "icpRadar.canonicalPreview.qualification",
        "icpRadar.canonicalPreview.signals",
        "icpRadar.radarStatus.draft",
        "icpRadar.radarStatus.active",
        "icpRadar.radarStatus.stopped",
    ]:
        assert canonical_key in screen or canonical_key in i18n
    assert "icpRadar.canonicalDetail.tabs.${tab}" in screen
    assert "showTrace" in screen
    assert "['overview', 'qualification', 'signals', 'sources', 'journal', 'trace']" in screen
    for tab_label in [
        "overview: 'Overview'",
        "qualification: 'Qualification'",
        "signals: 'Signals'",
        "sources: 'Sources'",
        "journal: 'Journal'",
        "trace: 'Trace'",
        "overview: 'Основная информация'",
        "qualification: 'Квалификация'",
        "signals: 'Сигналы'",
        "sources: 'Источники'",
        "journal: 'Журнал'",
        "trace: 'Trace'",
    ]:
        assert tab_label in i18n

    live_table_segment = screen.split("function LiveRadarShortlistTable", 1)[1].split("function LiveRadarCandidatePreview", 1)[0]
    for column_key in [
        "icpRadar.columns.company",
        "icpRadar.columns.total",
        "icpRadar.columns.fit",
        "icpRadar.columns.intent",
        "icpRadar.columns.trigger",
        "icpRadar.columns.tier",
        "icpRadar.columns.evidence",
        "icpRadar.columns.action",
    ]:
        assert column_key in live_table_segment
    assert "icpRadar.live.columns" not in live_table_segment

    live_preview_segment = screen.split("function LiveRadarCandidatePreview", 1)[1].split("function LiveRadarCandidateDetailView", 1)[0]
    assert "LiveEvidenceList" not in live_preview_segment
    assert "icpRadar.live.reviewRequired" not in live_preview_segment
    assert "candidate.qualification.slice(0, 5)" in live_preview_segment
    assert "candidate.signals.slice(0, 5)" in live_preview_segment

    live_detail_segment = screen.split("function LiveRadarCandidateDetailView", 1)[1].split("function LiveEvidenceList", 1)[0]
    assert "CandidateDetailTabs" in live_detail_segment
    assert "activeTab === 'journal'" in live_detail_segment
    assert "LiveRunDossierPanel" in live_detail_segment
    assert "LiveRunTechnicalTracePanel" in live_detail_segment
    assert "artifact.dossier" in live_detail_segment
    assert "artifact.technical_trace" in live_detail_segment
    assert "artifact.run_metadata.model" in live_detail_segment
    assert "artifact.run_metadata.query_count" in live_detail_segment
    assert "icpRadar.live.dossier.plan" in live_detail_segment
    assert "icpRadar.live.dossier.sourceLifecycle" in live_detail_segment
    assert "icpRadar.live.dossier.sourcesTitle" in live_detail_segment
    assert "source_lifecycle_summary" in live_detail_segment
    assert "source_lifecycle.map" in live_detail_segment

    live_run_diagnostics_segment = screen.split("function LiveRadarRunDiagnosticsView", 1)[1].split("function RunDiagnosticsStatus", 1)[0]
    live_operations_segment = read_text("frontend/src/features/icp-radar/liveOperations.tsx")
    assert "icpRadar.live.diagnostics.inspectRun" in screen
    assert "runDiagnosticsOpen" in screen
    assert "LiveRunDossierPanel artifact={artifact} dossier={artifact.dossier}" in screen
    assert "LiveRunTechnicalTracePanel trace={artifact?.technical_trace}" in screen
    assert "LiveRadarPreflightPanel" in live_operations_segment
    assert "LiveRadarRunDiagnosticsView" in live_operations_segment
    assert "RadarPipelineControlPanel" in live_operations_segment
    assert "live-radar-run-toolbar" not in screen
    assert "CandidateUniverseDiagnostics" in live_run_diagnostics_segment
    assert "SourceLifecycleDiagnostics" in live_run_diagnostics_segment
    assert "fetch(" not in live_run_diagnostics_segment

    for ru_label in [
        "Соответствие",
        "Интент",
        "Триггеры",
        "Уровень",
        "Доказательства",
        "Ссылки на источники",
        "Уверенность",
    ]:
        assert ru_label in i18n
    assert "shortlistTab: 'Found accounts'" in i18n
    assert "shortlistTab: 'Найденные аккаунты'" in i18n
    assert "operationsTab: 'Runs'" in i18n
    assert "operationsTab: 'Запуски'" in i18n
    assert "backToTable: 'Back to found accounts'" in i18n
    assert "backToTable: 'К найденным аккаунтам'" in i18n
    for lifecycle_label in [
        "sourceLifecycle: 'Source lifecycle'",
        "sourceLifecycle: 'Жизненный цикл источников'",
        "inspectRun: 'Диагностика запуска'",
        "used_in_product: 'Used in product'",
        "used_in_product: 'В зачете'",
        "not_used_by_candidate: 'Analyzed but not linked to candidate evidence.'",
        "not_used_by_candidate: 'Проанализирован, но не связан с evidence кандидата.'",
        "checkSetup: 'Check setup'",
        "checkSetup: 'Проверка'",
        "parity: 'API / worker parity'",
        "parity: 'Сверка API / worker'",
        "verification: 'Проверка источников'",
    ]:
        assert lifecycle_label in i18n


def test_frontend_public_artifact_is_available_for_vite() -> None:
    radar_path = Path("frontend/public/demo/account_radar.json")
    icp_radar_path = Path("frontend/public/demo/icp_radar.json")
    icp_radars_path = Path("frontend/public/demo/icp_radars.json")

    assert radar_path.exists()
    assert icp_radar_path.exists()
    assert icp_radars_path.exists()
    assert Path("frontend/public/demo/access_plans").exists()


def test_live_mini_icp_radar_catalog_and_frontend_contract() -> None:
    catalog = Path("frontend/public/demo/icp_radars.json").read_text(encoding="utf-8")
    app = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    screen = icp_radar_feature_text()
    api_client = Path("frontend/src/api/radarApi.ts").read_text(encoding="utf-8")
    api_adapter = Path("frontend/src/features/icp-radar/adapters/apiRadarAdapter.ts").read_text(encoding="utf-8")
    types = Path("frontend/src/types.ts").read_text(encoding="utf-8")
    i18n = i18n_text()

    assert "toir-quick-live" in catalog
    assert "/demo/live_mini_icp_radar_run.json" in catalog
    assert "fetch(liveMiniRadarArtifactUrl)" in app
    assert "getRunDossier" in api_client
    assert "getRunTechnicalTrace" in api_client
    assert "getRadarPreflight" in api_client
    assert "updateRadarDefinition" in api_client
    assert "RadarPreflightDto" in api_client
    assert "RadarRunDossierDto" in api_client
    assert "RadarRunTechnicalTraceDto" in api_client
    assert "normalizedDossier?.search_plan.map" in api_adapter
    assert "queries: []" not in api_adapter
    assert "return null" in app
    assert "LiveRadarShortlistTable" in screen
    assert "LiveRadarCandidatePreview" in screen
    assert "LiveRadarCandidateDetailView" in screen
    assert "expandedLiveCandidateId" in screen
    assert "detailLiveCandidateId" in screen
    assert "document.querySelector('.workspace-body')?.scrollTo({ top: 0 })" in screen
    assert "icp-radar-table-live" in screen
    assert "icp-candidate-preview" in screen
    assert "icp-detail-sticky-header" in screen
    assert "LiveMiniRadarShortlist" not in screen
    assert "live-radar-grid" not in screen
    assert "live-radar-table" not in screen
    assert "live-radar-detail" not in screen
    assert "fetch(" not in screen
    assert "LiveICPRadarRunArtifact" in types
    for type_name in [
        "QualificationSourceUsage",
        "QualificationEvidenceFinding",
        "QualificationCrossValidation",
        "QualificationRequirementEvaluation",
        "QualificationReviewDecision",
        "SignalEvidenceFinding",
        "SignalScoreEvaluation",
        "LiveRadarRunDossier",
        "LiveRadarTechnicalTrace",
    ]:
        assert type_name in types
    for screen_token in [
        "qualificationReviewStorageKey",
        "LiveQualificationReviewTable",
        "qualification-review-table",
        "source_usages",
        "evidence_findings",
        "cross_validation",
        "requirement_evaluation",
        "onQualificationReviewChange",
        "icpRadar.live.qualificationColumns.operator",
        "icpRadar.live.crossValidationCopy",
        "icpRadar.live.requirementEvaluationFields.crossValidation",
        "icpRadar.live.evidenceCard.noExcerpt",
        "icpRadar.live.excerptType.${card.excerptType}",
        "qualificationEvidenceCardViews",
        "qualificationRequirementEvaluationView",
        "qualification-evaluation-list",
        "qualification-finding-source",
        "qualification-finding-body",
        "qualification-review-choice",
        "requiresComment = reviewAction !== 'approved'",
        "disabled={!canSaveReview}",
        "icpRadar.live.review.actions.${status}",
        "icpRadar.live.review.save",
        "icpRadar.live.review.commentRequired",
        "LiveSignalReviewTable",
        "signal-review-table",
        "signalScoreEvaluationView",
        "signalEvidenceCardViews",
        "icpRadar.live.signalScoreEvaluation",
        "icpRadar.live.signalColumns.originalScore",
        "icpRadar.live.signalEvaluationFields.crossValidation",
        "icpRadar.live.signalEvidenceCard.whyScore",
        "icpRadar.live.signalReview.actions.${status}",
        "requiresComment = reviewAction !== 'confirmed'",
        "reviewAction === 'corrected'",
        "onSignalDecisionChange",
        "onSignalDecisionReset",
        "LiveRunTechnicalTracePanel",
        "technical-trace-viewer",
        "technical-trace-step",
        "technical-trace-section",
        "filterReadableTraceGroups",
        "readableTraceGroups",
        "showRaw",
        "icpRadar.live.trace.policy",
        "icpRadar.live.trace.searchPlaceholder",
        "LiveRadarPreflightPanel",
        "preflightOpen",
        "preflightState",
        "onCheckSetup",
        "icpRadar.live.preflight.checkSetup",
        "icpRadar.live.preflight.runtimeCards.${card.key}",
        "icpRadar.live.preflight.checkStatus.${check.status}",
    ]:
        assert screen_token in screen
    qualification_header = screen.split('<div className="qualification-review-head">', 1)[1].split("</div>", 1)[0]
    assert "qualificationColumns.requirement" not in qualification_header
    assert "icpRadar.settings.requirement." not in screen
    assert "qualification-source-table" not in screen
    assert "icpRadar.live.sourcesUsed" not in screen
    assert "item.cross_validation?.notes" not in screen
    assert screen.index('className="qualification-review-evaluation"') < screen.index("qualification-finding-list")
    assert "LiveEvidenceList refs={item.evidence_refs}" not in screen
    assert screen.index('className="signal-review-evaluation"') < screen.index("signal-finding-list")
    assert "excerpt?: string" in types
    assert "excerpt_type?: 'quote' | 'paraphrase' | 'not_available'" in types
    assert "why_it_matches_signal" in types
    assert "why_score_applies" in types
    for i18n_key in [
        "qualificationColumns",
        "signalColumns",
        "signalScoreEvaluation",
        "signalEvaluationFields",
        "signalEvidenceCard",
        "signalReview",
        "sourceOrigin",
        "trustPolicy",
        "crossValidationStatus",
        "crossValidationCopy",
        "evidenceCard",
        "excerptType",
        "requirementLevel",
        "requirementEvaluationFields",
        "crossValidation",
        "requirementAction",
        "reviewStatus",
        "actions",
        "approved",
        "rejected",
        "corrected",
        "correctedAssessment",
        "commentRequired",
        "provider_request",
        "viewerTitle",
        "filters",
        "section",
        "technical trace",
    ]:
        assert i18n_key in i18n
