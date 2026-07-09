from pathlib import Path


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_icp_radar_screen_is_feature_backed_thin_wrapper() -> None:
    wrapper = Path("frontend/src/screens/ICPRadarScreen.tsx")
    wrapper_text = wrapper.read_text(encoding="utf-8")

    assert line_count(wrapper) <= 10
    assert "features/icp-radar/ICPRadarScreen" in wrapper_text


def test_icp_radar_feature_is_decomposed_by_responsibility() -> None:
    feature_dir = Path("frontend/src/features/icp-radar")
    expected_directories = {"adapters", "application", "components", "domain"}
    expected_tsx_modules = {
        "ICPRadarScreen.tsx",
        "candidateViews.tsx",
        "criteriaBreakdown.tsx",
        "detailPrimitives.tsx",
        "fixtureDetail.tsx",
        "fixturePreview.tsx",
        "fixtureShortlist.tsx",
        "liveDetail.tsx",
        "liveOperations.tsx",
        "livePipelineControls.tsx",
        "livePreflightPanel.tsx",
        "liveRunDiagnostics.tsx",
        "liveTrace.tsx",
        "liveCandidateViews.tsx",
        "liveShortlist.tsx",
        "settings.tsx",
        "settingsBlocks.tsx",
        "settingsFields.tsx",
        "settingsHeader.tsx",
        "settingsMonitoring.tsx",
        "settingsQualification.tsx",
        "settingsScoring.tsx",
        "settingsSearch.tsx",
        "settingsSignals.tsx",
        "settingsValidation.tsx",
    }
    expected_model_modules = {
        "liveModel.ts",
        "liveTraceModel.ts",
        "model.tsx",
        "modelTypes.ts",
        "radarMetaModel.ts",
        "settingsModel.ts",
        "validationModel.ts",
    }

    module_names = {path.name for path in feature_dir.glob("*.ts*")}
    directory_names = {path.name for path in feature_dir.iterdir() if path.is_dir()}
    assert expected_directories.issubset(directory_names)
    assert expected_tsx_modules.issubset(module_names)
    assert expected_model_modules.issubset(module_names)
    assert line_count(feature_dir / "ICPRadarScreen.tsx") <= 250
    assert line_count(feature_dir / "candidateViews.tsx") <= 10
    assert line_count(feature_dir / "liveCandidateViews.tsx") <= 10
    assert line_count(feature_dir / "settings.tsx") <= 250
    assert line_count(feature_dir / "fixtureDetail.tsx") <= 400
    assert line_count(feature_dir / "fixturePreview.tsx") <= 160
    assert line_count(feature_dir / "fixtureShortlist.tsx") <= 180
    assert line_count(feature_dir / "liveDetail.tsx") <= 600
    assert line_count(feature_dir / "liveOperations.tsx") <= 180
    assert line_count(feature_dir / "livePipelineControls.tsx") <= 320
    assert line_count(feature_dir / "livePreflightPanel.tsx") <= 320
    assert line_count(feature_dir / "liveRunDiagnostics.tsx") <= 400
    assert line_count(feature_dir / "liveShortlist.tsx") <= 290
    assert line_count(feature_dir / "model.tsx") <= 10
    assert line_count(feature_dir / "settingsModel.ts") <= 700
    assert line_count(feature_dir / "validationModel.ts") <= 300
    assert line_count(feature_dir / "liveModel.ts") <= 250
    assert line_count(feature_dir / "liveTraceModel.ts") <= 300

    entrypoint = read("frontend/src/features/icp-radar/ICPRadarScreen.tsx")
    for component_name in [
        "function RadarSettings",
        "function CriteriaBreakdown",
        "function LiveRadarCandidateDetailView",
        "function FixtureRadarCandidateDetailView",
    ]:
        assert component_name not in entrypoint
    for forbidden_boundary in [
        "window.localStorage",
        "toir-quick-live",
        "selectedLiveRunArtifact",
        "selectedRadarArtifact",
        "buildValidatedCandidateScore",
        "validationForCandidate",
    ]:
        assert forbidden_boundary not in entrypoint


def test_icp_radar_has_application_and_adapter_boundaries() -> None:
    feature_dir = Path("frontend/src/features/icp-radar")
    adapters = {
        "catalogAdapter.ts": [
            "radarToViewModel",
            "mergeCatalogWithOverrides",
        ],
        "fixtureRadarAdapter.ts": [
            "fixtureRadarToViewModel",
            "fixtureCandidateToViewModel",
        ],
        "liveRadarAdapter.ts": [
            "liveRadarToViewModel",
            "liveCandidateToViewModel",
        ],
        "apiRadarAdapter.ts": [
            "apiDetailsToCatalogArtifact",
            "apiRunToLiveArtifact",
            "catalogWithLiveRunArtifacts",
        ],
        "viewModels.ts": [
            "RadarViewModel",
            "RadarCandidateViewModel",
        ],
    }
    hooks = {
        "useRadarWorkspace.ts": [
            "useRadarNavigation",
            "useRadarConfigOverrides",
            "useSignalValidationOverlay",
            "useQualificationReviewOverlay",
        ],
        "useRadarConfigOverrides.ts": ["radarConfigStorageKey", "window.localStorage"],
        "useSignalValidationOverlay.ts": ["signalValidationStorageKey", "window.localStorage"],
        "useQualificationReviewOverlay.ts": ["qualificationReviewStorageKey", "window.localStorage"],
        "useRadarBackend.ts": ["RadarApiClient", "queueCandidateDiscoveryRun", "getRunCandidates", "getRunDossier", "getRunTechnicalTrace", "getRadarPreflight", "updateRadarDefinition"],
    }

    for file_name, expected_symbols in adapters.items():
        text = read(str(feature_dir / "adapters" / file_name))
        for symbol in expected_symbols:
            assert symbol in text

    for file_name, expected_symbols in hooks.items():
        text = read(str(feature_dir / "application" / file_name))
        for symbol in expected_symbols:
            assert symbol in text


def test_icp_radar_backend_live_artifact_viewer_is_not_hardcoded_to_quick_radar() -> None:
    backend = read("frontend/src/features/icp-radar/application/useRadarBackend.ts")
    workspace = read("frontend/src/features/icp-radar/application/useRadarWorkspace.ts")
    adapter = read("frontend/src/features/icp-radar/adapters/catalogAdapter.ts")

    assert "const liveRadarId" not in backend
    assert "liveRunArtifacts" in backend
    assert "backend.liveRunArtifacts[selectedRadar.radar_id]" in workspace
    assert "radar.radar_id === 'toir-quick-live'" not in adapter


def test_icp_radar_benchmark_radars_are_protected_from_silent_local_delete() -> None:
    settings_model = read("frontend/src/features/icp-radar/settingsModel.ts")
    catalog_screen = read("frontend/src/features/icp-radar/components/RadarCatalogScreen.tsx")

    assert "isProtectedBackendRadar" in settings_model
    assert "run_mode === 'benchmark'" in settings_model
    assert "protected_from_delete" in settings_model
    assert "localOverrideProtected" in catalog_screen


def test_icp_radar_catalog_does_not_silently_fallback_while_backend_is_loading() -> None:
    app = read("frontend/src/App.tsx")
    backend = read("frontend/src/features/icp-radar/application/useRadarBackend.ts")
    catalog_screen = read("frontend/src/features/icp-radar/components/RadarCatalogScreen.tsx")
    workspace = read("frontend/src/features/icp-radar/application/useRadarWorkspace.ts")

    assert "const activeIcpRadarCatalog = icpRadarBackend.catalog;" in app
    assert "apiCatalog ?? (runState.mode === 'fallback' ? fallbackCatalog : null)" in backend
    assert "Promise.allSettled(summaries.map((item) => api.getRadar(item.radar_id)))" in backend
    assert "loadCompletedRunArtifacts" not in backend
    assert "loadRadarRunArtifact" in backend
    assert "backend.loadRadarRunArtifact(selectedRadar.radar_id)" in workspace
    assert "backendMode={backend.runState.mode}" in read("frontend/src/features/icp-radar/ICPRadarScreen.tsx")
    assert "icpRadar.live.backendMode.${backendMode}" in catalog_screen


def test_icp_radar_feature_has_local_onboarding_readme() -> None:
    readme = read("frontend/src/features/icp-radar/README.md")

    for expected in [
        "RadarViewModel",
        "RadarCandidateViewModel",
        "How To Add A New Radar Type",
        "flowchart TD",
        "No `window.localStorage` in presentation components.",
        "No ICP Radar selectors in global `frontend/src/styles.css`.",
    ]:
        assert expected in readme


def test_icp_radar_boundary_modules_have_ownership_comments() -> None:
    comment_expectations = {
        "adapters/viewModels.ts": "Canonical view models are the boundary",
        "adapters/catalogAdapter.ts": "raw artifact adapter owns a radar",
        "adapters/fixtureRadarAdapter.ts": "Fixture artifacts are normalized here",
        "adapters/liveRadarAdapter.ts": "provider metadata goes to journal rows",
        "adapters/apiRadarAdapter.ts": "API DTOs are normalized here",
        "application/useRadarWorkspace.ts": "composes adapters, navigation, and local overlays",
        "application/useRadarBackend.ts": "backend mode",
        "application/useRadarConfigOverrides.ts": "demo persistence boundary",
        "application/useSignalValidationOverlay.ts": "never mutate generated demo artifacts",
        "application/useQualificationReviewOverlay.ts": "mirror signal validation",
    }

    for relative_path, expected_comment in comment_expectations.items():
        assert expected_comment in read(f"frontend/src/features/icp-radar/{relative_path}")


def test_icp_radar_presentation_components_do_not_own_storage() -> None:
    component_dir = Path("frontend/src/features/icp-radar/components")
    for component in component_dir.glob("*.tsx"):
        text = component.read_text(encoding="utf-8")
        assert "window.localStorage" not in text
        assert "StorageKey" not in text


def test_icp_radar_presentation_does_not_own_api_transport() -> None:
    feature_dir = Path("frontend/src/features/icp-radar")
    presentation_files = [
        feature_dir / "ICPRadarScreen.tsx",
        feature_dir / "liveShortlist.tsx",
        feature_dir / "liveOperations.tsx",
        feature_dir / "liveDetail.tsx",
        feature_dir / "livePreflightPanel.tsx",
        feature_dir / "liveRunDiagnostics.tsx",
        feature_dir / "liveTrace.tsx",
        *list((feature_dir / "components").glob("*.tsx")),
    ]

    for component in presentation_files:
        text = component.read_text(encoding="utf-8")
        assert "fetch(" not in text
        assert "RadarApiClient" not in text


def test_icp_radar_component_barrels_stay_small() -> None:
    candidate_barrel = read("frontend/src/features/icp-radar/candidateViews.tsx")
    live_barrel = read("frontend/src/features/icp-radar/liveCandidateViews.tsx")

    assert "export { CandidateTable, EmptyShortlist } from './fixtureShortlist';" in candidate_barrel
    assert "export { FixtureRadarCandidateDetailView } from './fixtureDetail';" in candidate_barrel
    assert "export { LiveRadarCandidatePreview, LiveRadarShortlistTable } from './liveShortlist';" in live_barrel
    assert "export { LiveRadarCandidateDetailView } from './liveDetail';" in live_barrel


def test_icp_radar_feature_modules_document_non_obvious_boundaries() -> None:
    comment_expectations = {
        "fixtureShortlist.tsx": "Fixture shortlist is optimized for scanning",
        "fixturePreview.tsx": "Preview stays intentionally bounded",
        "fixtureDetail.tsx": "Fixture detail hosts signal validation",
        "liveShortlist.tsx": "Live shortlist deliberately mirrors fixture shortlist",
        "liveOperations.tsx": "Operations owns run controls and diagnostics",
        "livePipelineControls.tsx": "Radar pipeline controls make candidate discovery",
        "liveDetail.tsx": "Detail tabs keep runtime/provider evidence separate",
        "livePreflightPanel.tsx": "Preflight stays run-scoped",
        "liveRunDiagnostics.tsx": "Run diagnostics is intentionally run-scoped",
        "settings.tsx": "Settings is block-editable by design",
    }

    for file_name, expected_comment in comment_expectations.items():
        assert expected_comment in read(f"frontend/src/features/icp-radar/{file_name}")


def test_icp_radar_model_barrel_has_responsibility_boundaries() -> None:
    model = read("frontend/src/features/icp-radar/model.tsx")

    for boundary in [
        "modelTypes",
        "validationModel",
        "radarMetaModel",
        "liveModel",
        "liveTraceModel",
        "settingsModel",
    ]:
        assert f"export * from './{boundary}';" in model


def test_icp_radar_settings_are_lazy_loaded() -> None:
    entrypoint = read("frontend/src/features/icp-radar/ICPRadarScreen.tsx")

    assert "lazy(() => import('./settings')" in entrypoint
    assert "<Suspense" in entrypoint
    assert "icpRadar.settings.loading" in entrypoint


def test_i18n_runtime_is_separate_from_large_resource_dictionary() -> None:
    runtime = read("frontend/src/i18n.ts")
    resources = read("frontend/src/i18nResources.ts")
    en = read("frontend/src/i18n/en.ts")
    ru = read("frontend/src/i18n/ru.ts")

    assert line_count(Path("frontend/src/i18n.ts")) <= 40
    assert line_count(Path("frontend/src/i18nResources.ts")) <= 10
    assert "initReactI18next" in runtime
    assert "resources" in runtime
    assert "export const resources" in resources
    assert "import { en }" in resources
    assert "import { ru }" in resources
    assert "icpRadar" in en
    assert "icpRadar" in ru


def test_icp_radar_css_is_owned_by_feature_module() -> None:
    global_css_path = Path("frontend/src/styles.css")
    feature_css_path = Path("frontend/src/features/icp-radar/icpRadar.css")
    feature_styles_dir = Path("frontend/src/features/icp-radar/styles")
    entrypoint = read("frontend/src/features/icp-radar/ICPRadarScreen.tsx")
    global_css = global_css_path.read_text(encoding="utf-8")
    feature_css = feature_css_path.read_text(encoding="utf-8").lstrip("\ufeff")
    expected_style_modules = [
        "base.css",
        "catalog.css",
        "shortlist.css",
        "preview.css",
        "detail.css",
        "trace.css",
        "diagnostics.css",
        "settings.css",
        "settings-editors.css",
        "criteria.css",
        "responsive.css",
    ]

    assert feature_css_path.exists()
    assert feature_styles_dir.exists()
    assert line_count(global_css_path) <= 1700
    assert line_count(feature_css_path) <= 20
    assert "import './icpRadar.css';" in entrypoint
    assert feature_css.splitlines() == [
        f"@import './styles/{module_name}';" for module_name in expected_style_modules
    ]
    for module_name in expected_style_modules:
        module_path = feature_styles_dir / module_name
        assert module_path.exists()
        assert line_count(module_path) <= 650

    assert ".icp-radar-screen" in read(str(feature_styles_dir / "base.css"))
    assert ".icp-radar-list-row" in read(str(feature_styles_dir / "catalog.css"))
    assert "@media" not in read(str(feature_styles_dir / "settings.css"))
    assert "@media" in read(str(feature_styles_dir / "responsive.css"))
    assert ".icp-radar-list-row" not in global_css
    assert ".icp-settings-grid" not in global_css


def test_icp_radar_operations_tab_owns_run_level_controls() -> None:
    feature_dir = Path("frontend/src/features/icp-radar")
    shortlist = read(str(feature_dir / "liveShortlist.tsx"))
    operations = read(str(feature_dir / "liveOperations.tsx"))
    header = read(str(feature_dir / "components" / "RadarDetailHeader.tsx"))
    css = "\n".join(path.read_text(encoding="utf-8") for path in sorted((feature_dir / "styles").glob("*.css")))

    assert "onClick={() => onTabChange('operations')}" in header
    assert "LiveRadarPreflightPanel" in operations
    assert "LiveRadarRunDiagnosticsView" in operations
    assert "RadarPipelineControlPanel" in operations
    assert "LiveRadarPreflightPanel" not in shortlist
    assert "LiveRadarRunDiagnosticsView" not in shortlist
    assert "RadarPipelineControlPanel" not in shortlist
    assert "live-radar-run-toolbar" not in shortlist
    assert ".live-radar-run-toolbar" not in css
    assert ".radar-operations-stack" in css
