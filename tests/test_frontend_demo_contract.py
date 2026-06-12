import re
from pathlib import Path


def test_frontend_imports_design_system_tokens() -> None:
    entrypoint = Path("frontend/src/main.tsx").read_text(encoding="utf-8")

    assert "ui-design-system/colors_and_type.css" in entrypoint
    assert "import './i18n'" in entrypoint


def test_frontend_i18n_resources_cover_supported_locales() -> None:
    i18n = Path("frontend/src/i18n.ts").read_text(encoding="utf-8")

    assert "supportedLocales = ['en', 'ru']" in i18n
    assert "defaultLocale: SupportedLocale = 'en'" in i18n
    assert "localeStorageKey" in i18n
    assert "i18next" in Path("frontend/package.json").read_text(encoding="utf-8")
    assert "react-i18next" in Path("frontend/package.json").read_text(encoding="utf-8")


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
    css = Path("frontend/src/styles.css").read_text(encoding="utf-8")

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
    i18n = Path("frontend/src/i18n.ts").read_text(encoding="utf-8")

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
    css = Path("frontend/src/styles.css").read_text(encoding="utf-8")

    for selector in ["html,", "body,", "#root", ".app-shell", ".sidebar", ".workspace", ".workspace-body"]:
        assert selector in css

    assert "height: 100dvh" in css
    assert "overflow: hidden" in css
    assert "overflow: auto" in css
    assert "overflow-y: auto" in css


def test_accounts_screen_contains_overflow_safe_table_rules() -> None:
    css = Path("frontend/src/styles.css").read_text(encoding="utf-8")

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


def test_icp_radar_screen_is_default_and_loads_fixture_artifact() -> None:
    app = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    shell = Path("frontend/src/layout/AppShell.tsx").read_text(encoding="utf-8")
    screen = Path("frontend/src/screens/ICPRadarScreen.tsx").read_text(encoding="utf-8")
    types = Path("frontend/src/types.ts").read_text(encoding="utf-8")
    i18n = Path("frontend/src/i18n.ts").read_text(encoding="utf-8")
    css = Path("frontend/src/styles.css").read_text(encoding="utf-8")

    assert "useState<ScreenId>('icp_radar')" in app
    assert "/demo/icp_radars.json" in app
    assert "/demo/icp_radar.json" in app
    assert "activeScreen === 'icp_radar'" in app
    assert "nav.icpRadar" in shell
    assert "topbar.icpRadar" in shell
    assert "ICPRadarArtifact" in types
    assert "ICPRadarCatalogArtifact" in types
    assert "ICPRadarCatalogItem" in types
    assert "RadarDefinition" in types
    assert "CriterionEvidenceExplanation" in types
    assert "criteria_evidence" in types
    assert "definition: RadarDefinition" in types

    for contract_value in [
        "criteria_scores",
        "criteria_evidence",
        "evidence_refs",
        "artifact.radar.criteria",
        "candidate.score.fit_score",
        "candidate.score.intent_score",
        "candidate.score.trigger_score",
        "candidate.score.total_score",
        "selectedRadarId",
        "RadarCatalogScreen",
        "RadarSettings",
        "EmptyShortlist",
        "shortlistTab",
        "settingsTab",
        "readOnly",
        "definition.criteria",
        "definition.scoring_formula",
    ]:
        assert contract_value in screen

    assert "onSave" not in screen
    assert "Save" not in screen

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
        "icpRadar.evidence",
        "icpRadar.criteria",
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
        "icpRadar.localReview",
        "icpRadar.acceptCriterion",
        "icpRadar.rejectCriterion",
        "icpRadar.editCriterionScore",
        "icpRadar.catalogTitle",
        "icpRadar.openRadar",
        "icpRadar.backToCatalog",
        "icpRadar.settingsTab",
        "icpRadar.settings.criteria",
        "icpRadar.editingPlanned",
    ]:
        assert label_key in screen or label_key in i18n

    assert "takeIntoWorkPlanned" in i18n
    assert "CriterionReviewState" in screen
    assert "expandedCriterionCode" in screen
    assert "matchesCriterionFilter" in screen
    assert "compareCriterionRows" in screen
    assert "CriterionEvidenceDetail" in screen
    assert "criterionReviews" in screen
    assert "onReview({ status: 'accepted'" in screen
    assert "onReview({ status: 'rejected'" in screen
    assert "onReview({ status: 'edited'" in screen
    assert ".criteria-review-table" in css
    assert ".criteria-review-head" in css
    assert ".criteria-review-row" in css
    assert ".criterion-evidence-detail" in css
    assert ".criterion-review-panel" in css
    assert ".icp-radar-catalog-grid" in css
    assert ".icp-radar-card" in css
    assert ".icp-settings-grid" in css
    assert ".icp-radar-tabs" in css
    assert ".icp-detail-sticky-header" in css
    assert "icp-detail-screen" in screen
    assert ".icp-detail-screen" in css
    assert "top: 0" in css
    assert "criteria-action-head" in screen

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


def test_frontend_public_artifact_is_available_for_vite() -> None:
    radar_path = Path("frontend/public/demo/account_radar.json")
    icp_radar_path = Path("frontend/public/demo/icp_radar.json")
    icp_radars_path = Path("frontend/public/demo/icp_radars.json")

    assert radar_path.exists()
    assert icp_radar_path.exists()
    assert icp_radars_path.exists()
    assert Path("frontend/public/demo/access_plans").exists()
