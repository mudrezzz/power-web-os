from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = Path("src/power_web_os")
ADR_PATH = Path("docs/adr/2026-06-16-backend-architecture-guardrails.md")
ARCHITECTURE_PATH = Path("docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md")
RADAR_BACKEND_ARCHITECTURE_PATH = Path("docs/architecture/RADAR_BACKEND_ARCHITECTURE.md")
DEVELOPER_GUIDE_PATH = Path("docs/developer/DEVELOPER_GUIDE.md")
APPLICATION_README_PATH = Path("src/power_web_os/application/README.md")
PERSISTENCE_README_PATH = Path("src/power_web_os/persistence/README.md")
INTEGRATIONS_README_PATH = Path("src/power_web_os/integrations/README.md")
WORKFLOWS_README_PATH = Path("src/power_web_os/workflows/README.md")
JOBS_README_PATH = Path("src/power_web_os/jobs/README.md")
RADAR_PACKAGE_ROOT = Path("src/power_web_os/application/radar")

MAX_BACKEND_MODULE_LINES = 500
MAX_APPLICATION_IMPORT_FANOUT = 10

LEGACY_LARGE_MODULE_ALLOWLIST = {
    Path("src/power_web_os/icp_radar.py"),
    Path("src/power_web_os/icp_radar_catalog.py"),
    Path("src/power_web_os/icp_radar_xlsx.py"),
    Path("src/power_web_os/application/live_radar_service.py"),
    Path("src/power_web_os/application/live_radar_staged_execution.py"),
    Path("src/power_web_os/integrations/live_radar_openrouter.py"),
}

LEGACY_ROOT_LIVE_RADAR_MODULES = {
    Path("src/power_web_os/application/live_radar_candidate_refs.py"),
    Path("src/power_web_os/application/live_radar_checkpoints.py"),
    Path("src/power_web_os/application/live_radar_checkpoint_actions.py"),
    Path("src/power_web_os/application/live_radar_checkpoint_execution.py"),
    Path("src/power_web_os/application/live_radar_collection_utils.py"),
    Path("src/power_web_os/application/live_radar_contracts.py"),
    Path("src/power_web_os/application/live_radar_cross_disambiguation.py"),
    Path("src/power_web_os/application/live_radar_definition.py"),
    Path("src/power_web_os/application/live_radar_definition_runtime.py"),
    Path("src/power_web_os/application/live_radar_discovery_planning.py"),
    Path("src/power_web_os/application/live_radar_entity_resolution.py"),
    Path("src/power_web_os/application/live_radar_execution_budget.py"),
    Path("src/power_web_os/application/live_radar_execution_plan.py"),
    Path("src/power_web_os/application/live_radar_external_budget.py"),
    Path("src/power_web_os/application/live_radar_external_budget_context.py"),
    Path("src/power_web_os/application/live_radar_external_budget_reservations.py"),
    Path("src/power_web_os/application/live_radar_external_budget_settings.py"),
    Path("src/power_web_os/application/live_radar_extraction_contract.py"),
    Path("src/power_web_os/application/live_radar_extraction_diagnostics.py"),
    Path("src/power_web_os/application/live_radar_normalization.py"),
    Path("src/power_web_os/application/live_radar_pipeline_support.py"),
    Path("src/power_web_os/application/live_radar_planning_pipeline.py"),
    Path("src/power_web_os/application/live_radar_plan_acceptance.py"),
    Path("src/power_web_os/application/live_radar_product_sources.py"),
    Path("src/power_web_os/application/live_radar_retrieval_plan.py"),
    Path("src/power_web_os/application/live_radar_retrieved_candidates.py"),
    Path("src/power_web_os/application/live_radar_search_expansion_execution.py"),
    Path("src/power_web_os/application/live_radar_search_expansion_payloads.py"),
    Path("src/power_web_os/application/live_radar_service.py"),
    Path("src/power_web_os/application/live_radar_source_cards.py"),
    Path("src/power_web_os/application/live_radar_source_risk.py"),
    Path("src/power_web_os/application/live_radar_staged_execution.py"),
    Path("src/power_web_os/application/live_radar_staged_helpers.py"),
    Path("src/power_web_os/application/live_radar_staged_merge.py"),
    Path("src/power_web_os/application/live_radar_staged_support.py"),
    Path("src/power_web_os/application/live_radar_universe.py"),
    Path("src/power_web_os/application/live_radar_useful_budget.py"),
    Path("src/power_web_os/application/live_radar_web_retrieval.py"),
}

RADAR_APPLICATION_FANOUT_ALLOWLIST = {
    Path("src/power_web_os/application/live_radar_service.py"),
    Path("src/power_web_os/application/live_radar_staged_execution.py"),
    Path("src/power_web_os/application/live_radar_search_expansion_execution.py"),
}

RADAR_TARGET_PACKAGES = [
    RADAR_PACKAGE_ROOT,
    RADAR_PACKAGE_ROOT / "shared",
    RADAR_PACKAGE_ROOT / "candidate_discovery",
    RADAR_PACKAGE_ROOT / "candidate_discovery" / "planning",
    RADAR_PACKAGE_ROOT / "candidate_discovery" / "retrieval",
    RADAR_PACKAGE_ROOT / "candidate_discovery" / "extraction",
    RADAR_PACKAGE_ROOT / "candidate_discovery" / "sources",
    RADAR_PACKAGE_ROOT / "candidate_discovery" / "universe",
    RADAR_PACKAGE_ROOT / "candidate_discovery" / "checkpoints",
    RADAR_PACKAGE_ROOT / "candidate_discovery" / "execution",
    RADAR_PACKAGE_ROOT / "candidate_discovery" / "diagnostics",
    RADAR_PACKAGE_ROOT / "signal_monitoring",
    RADAR_PACKAGE_ROOT / "power_web_discovery",
]

RADAR_PACKAGE_READMES = [path / "README.md" for path in RADAR_TARGET_PACKAGES]

PURE_DOMAIN_MODULES = {
    Path("src/power_web_os/domain.py"),
    Path("src/power_web_os/planner.py"),
    Path("src/power_web_os/radar.py"),
    Path("src/power_web_os/board.py"),
    Path("src/power_web_os/playbook_analysis.py"),
    Path("src/power_web_os/icp_radar.py"),
    Path("src/power_web_os/icp_radar_evidence.py"),
}

FORBIDDEN_DOMAIN_IMPORT_PREFIXES = {
    "fastapi",
    "sqlalchemy",
    "celery",
    "redis",
    "httpx",
    "dotenv",
    "uvicorn",
    "openai",
    "anthropic",
}

API_FORBIDDEN_SNIPPETS = {
    "from sqlalchemy",
    "import sqlalchemy",
    "session.execute",
    ".query(",
    "select(",
    "deterministicaccessplanner",
    "accountradar",
}

APPLICATION_FORBIDDEN_IMPORT_PREFIXES = {
    "alembic",
    "sqlalchemy",
    "fastapi",
    "uvicorn",
    "httpx",
    "dotenv",
}

RADAR_PACKAGE_FORBIDDEN_IMPORT_PREFIXES = APPLICATION_FORBIDDEN_IMPORT_PREFIXES | {
    "celery",
    "redis",
    "openai",
    "anthropic",
}

INTEGRATION_FORBIDDEN_IMPORT_PREFIXES = {
    "alembic",
    "fastapi",
    "sqlalchemy",
    "uvicorn",
}

WORKFLOW_FORBIDDEN_SNIPPETS = {
    "sqlalchemy",
    "session.execute",
    ".query(",
    "httpx.",
    "normalize_openrouter_response",
}

JOB_FORBIDDEN_SNIPPETS = {
    "from sqlalchemy",
    "import sqlalchemy",
    "session.execute",
    ".query(",
    "deterministicaccessplanner",
    "normalize_openrouter_response",
    "normalize_live_candidate",
}

BACKEND_DOCSTRING_REQUIRED_MODULES = {
    Path("src/power_web_os/application/live_radar_contracts.py"),
    Path("src/power_web_os/application/live_radar_definition.py"),
    Path("src/power_web_os/application/live_radar_normalization.py"),
    Path("src/power_web_os/application/live_radar_service.py"),
    Path("src/power_web_os/application/persisted_live_radar.py"),
    Path("src/power_web_os/integrations/live_radar_openrouter.py"),
    Path("src/power_web_os/workflows/live_icp_radar_workflow.py"),
    Path("src/power_web_os/workflows/live_radar_executor.py"),
    Path("src/power_web_os/live_icp_radar.py"),
    Path("src/power_web_os/application/radar_records.py"),
    Path("src/power_web_os/application/ports.py"),
    Path("src/power_web_os/application/radar_catalog_seed.py"),
    Path("src/power_web_os/application/radar_review.py"),
    Path("src/power_web_os/application/radar_run_journal.py"),
    Path("src/power_web_os/persistence/engine.py"),
    Path("src/power_web_os/persistence/models.py"),
    Path("src/power_web_os/persistence/repositories.py"),
    Path("src/power_web_os/persistence/seed.py"),
    Path("src/power_web_os/jobs/radar_jobs.py"),
}


def python_files(root: Path = BACKEND_ROOT) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def application_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("power_web_os.application"):
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("power_web_os.application"):
                    imports.add(alias.name)
    return imports


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
    return imports


def test_backend_architecture_docs_define_required_boundaries() -> None:
    docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [ADR_PATH, ARCHITECTURE_PATH, DEVELOPER_GUIDE_PATH]
    )

    for boundary in ["api", "application", "domain", "persistence", "integrations", "workflows", "jobs"]:
        assert f"`{boundary}`" in docs
    for expected in [
        "Application services own use cases",
        "Postgres remains the source of truth",
        "Celery/Redis",
        "FastAPI `BackgroundTasks` is not the production execution model",
    ]:
        assert expected in docs


def test_backend_onboarding_docs_explain_extension_rules() -> None:
    application_readme = APPLICATION_README_PATH.read_text(encoding="utf-8")
    persistence_readme = PERSISTENCE_README_PATH.read_text(encoding="utf-8")
    integrations_readme = INTEGRATIONS_README_PATH.read_text(encoding="utf-8")
    workflows_readme = WORKFLOWS_README_PATH.read_text(encoding="utf-8")
    jobs_readme = JOBS_README_PATH.read_text(encoding="utf-8")
    developer_guide = DEVELOPER_GUIDE_PATH.read_text(encoding="utf-8")

    for text in [application_readme, persistence_readme, integrations_readme, workflows_readme, jobs_readme]:
        assert "Dependency Rules" in text
        assert "How To Extend" in text
    assert "Forbidden imports" in application_readme
    assert "Transaction Boundary" in persistence_readme
    assert "OpenRouter" in integrations_readme
    assert "langgraph-document-ai-platform" in workflows_readme
    assert "Celery" in jobs_readme
    assert "How To Extend Backend Persistence" in developer_guide


def test_key_backend_modules_have_onboarding_docstrings() -> None:
    missing = [
        path.as_posix()
        for path in sorted(BACKEND_DOCSTRING_REQUIRED_MODULES)
        if not ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    ]

    assert missing == []


def test_legacy_large_backend_modules_are_documented_as_temporary_allowlist() -> None:
    docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [ADR_PATH, ARCHITECTURE_PATH, DEVELOPER_GUIDE_PATH]
    )

    for path in LEGACY_LARGE_MODULE_ALLOWLIST:
        assert path.name in docs
    assert "not examples for new backend work" in docs or "not examples to copy" in docs


def test_new_backend_modules_stay_below_file_size_threshold() -> None:
    oversized = [
        f"{path.as_posix()} has {line_count(path)} lines"
        for path in python_files()
        if line_count(path) > MAX_BACKEND_MODULE_LINES and path not in LEGACY_LARGE_MODULE_ALLOWLIST
    ]

    assert oversized == []


def test_domain_modules_do_not_import_transport_persistence_or_provider_infrastructure() -> None:
    domain_files = sorted(
        path
        for path in set(PURE_DOMAIN_MODULES) | set((BACKEND_ROOT / "domain").rglob("*.py"))
        if path.exists() and path.name != "__init__.py"
    )

    violations = {
        path.as_posix(): sorted(imported_roots(path) & FORBIDDEN_DOMAIN_IMPORT_PREFIXES)
        for path in domain_files
        if imported_roots(path) & FORBIDDEN_DOMAIN_IMPORT_PREFIXES
    }

    assert violations == {}


def test_no_new_root_live_radar_modules_are_added() -> None:
    root_live_radar_modules = set((BACKEND_ROOT / "application").glob("live_radar_*.py"))
    unexpected = sorted(path.as_posix() for path in root_live_radar_modules - LEGACY_ROOT_LIVE_RADAR_MODULES)
    missing = sorted(path.as_posix() for path in LEGACY_ROOT_LIVE_RADAR_MODULES - root_live_radar_modules)

    assert unexpected == [], (
        "New root-level application/live_radar_*.py modules are not allowed. "
        "Use src/power_web_os/application/radar/... package ownership instead."
    )
    assert missing == []


def test_radar_backend_architecture_doc_exists_and_defines_target_packages() -> None:
    text = RADAR_BACKEND_ARCHITECTURE_PATH.read_text(encoding="utf-8")

    for expected in [
        "candidate_discovery",
        "signal_monitoring",
        "power_web_discovery",
        "shared",
        "planning",
        "retrieval",
        "extraction",
        "sources",
        "universe",
        "checkpoints",
        "execution",
        "diagnostics",
    ]:
        assert expected in text


def test_radar_root_legacy_hotspots_are_documented_as_migration_debt() -> None:
    text = RADAR_BACKEND_ARCHITECTURE_PATH.read_text(encoding="utf-8")

    for expected in ["live_radar_staged_execution.py", "live_radar_service.py", "migration debt"]:
        assert expected in text


def test_radar_application_import_fanout_requires_allowlist() -> None:
    docs = RADAR_BACKEND_ARCHITECTURE_PATH.read_text(encoding="utf-8")
    violations: dict[str, int] = {}
    for path in sorted((BACKEND_ROOT / "application").glob("*.py")):
        if path.name == "__init__.py":
            continue
        fanout = len(application_imports(path))
        if fanout > MAX_APPLICATION_IMPORT_FANOUT and path not in RADAR_APPLICATION_FANOUT_ALLOWLIST:
            violations[path.as_posix()] = fanout
        if path in RADAR_APPLICATION_FANOUT_ALLOWLIST:
            assert path.name in docs

    assert violations == {}


def test_radar_component_contract_is_documented() -> None:
    text = RADAR_BACKEND_ARCHITECTURE_PATH.read_text(encoding="utf-8")

    for expected in ["Input", "Result", "Decision", "Issue", "Event", "Service"]:
        assert expected in text


def test_radar_target_packages_exist_with_package_markers() -> None:
    missing = [
        path.as_posix()
        for path in RADAR_TARGET_PACKAGES
        if not path.is_dir() or not (path / "__init__.py").exists()
    ]

    assert missing == []


def test_radar_package_readmes_define_local_extension_rules() -> None:
    missing_or_incomplete: dict[str, list[str]] = {}
    for path in RADAR_PACKAGE_READMES:
        if not path.exists():
            missing_or_incomplete[path.as_posix()] = ["missing"]
            continue
        text = path.read_text(encoding="utf-8")
        missing_sections = [
            section
            for section in ["Ownership", "Allowed imports", "Forbidden imports", "How to extend"]
            if section not in text
        ]
        if missing_sections:
            missing_or_incomplete[path.as_posix()] = missing_sections

    assert missing_or_incomplete == {}


def test_radar_package_modules_do_not_import_infrastructure_or_legacy_runtime() -> None:
    violations: dict[str, list[str]] = {}
    for path in sorted(RADAR_PACKAGE_ROOT.rglob("*.py")):
        roots = imported_roots(path) & RADAR_PACKAGE_FORBIDDEN_IMPORT_PREFIXES
        modules = imported_modules(path)
        found = sorted(roots)
        found.extend(sorted(module for module in modules if module.startswith("power_web_os.application.live_radar")))
        if found:
            violations[path.as_posix()] = found

    assert violations == {}


def test_radar_shared_package_does_not_import_pipeline_packages() -> None:
    shared_root = RADAR_PACKAGE_ROOT / "shared"
    forbidden = {
        "power_web_os.application.radar.candidate_discovery",
        "power_web_os.application.radar.signal_monitoring",
        "power_web_os.application.radar.power_web_discovery",
    }
    violations: dict[str, list[str]] = {}
    for path in sorted(shared_root.rglob("*.py")):
        imports = imported_modules(path)
        found = sorted(module for module in imports for prefix in forbidden if module.startswith(prefix))
        if found:
            violations[path.as_posix()] = found

    assert violations == {}


def test_radar_candidate_discovery_does_not_import_other_pipeline_packages() -> None:
    candidate_root = RADAR_PACKAGE_ROOT / "candidate_discovery"
    forbidden = {
        "power_web_os.application.radar.signal_monitoring",
        "power_web_os.application.radar.power_web_discovery",
    }
    violations: dict[str, list[str]] = {}
    for path in sorted(candidate_root.rglob("*.py")):
        imports = imported_modules(path)
        found = sorted(module for module in imports for prefix in forbidden if module.startswith(prefix))
        if found:
            violations[path.as_posix()] = found

    assert violations == {}


def test_api_modules_do_not_own_persistence_queries_or_domain_scoring() -> None:
    api_dir = BACKEND_ROOT / "api"
    violations: dict[str, list[str]] = {}
    for path in sorted(api_dir.rglob("*.py")):
        text = path.read_text(encoding="utf-8").lower()
        found = sorted(snippet for snippet in API_FORBIDDEN_SNIPPETS if snippet in text)
        if found:
            violations[path.as_posix()] = found

    assert violations == {}


def test_application_modules_depend_on_ports_not_persistence_adapters() -> None:
    application_dir = BACKEND_ROOT / "application"
    if not application_dir.exists():
        return

    violations: dict[str, list[str]] = {}
    for path in sorted(application_dir.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        found = sorted(imported_roots(path) & APPLICATION_FORBIDDEN_IMPORT_PREFIXES)
        if "power_web_os.persistence" in text:
            found.append("power_web_os.persistence")
        if found:
            violations[path.as_posix()] = found

    assert violations == {}


def test_integration_modules_do_not_own_api_persistence_or_domain_scoring() -> None:
    integrations_dir = BACKEND_ROOT / "integrations"
    if not integrations_dir.exists():
        return

    violations: dict[str, list[str]] = {}
    for path in sorted(integrations_dir.rglob("*.py")):
        text = path.read_text(encoding="utf-8").lower()
        found = sorted(imported_roots(path) & INTEGRATION_FORBIDDEN_IMPORT_PREFIXES)
        for forbidden in ["session.execute", ".query(", "radarrunmodel", "radarmodel"]:
            if forbidden in text:
                found.append(forbidden)
        if found:
            violations[path.as_posix()] = found

    assert violations == {}


def test_workflow_modules_delegate_to_application_services_without_provider_logic() -> None:
    workflows_dir = BACKEND_ROOT / "workflows"
    if not workflows_dir.exists():
        return

    violations: dict[str, list[str]] = {}
    for path in sorted(workflows_dir.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8").lower()
        found = sorted(snippet for snippet in WORKFLOW_FORBIDDEN_SNIPPETS if snippet in text)
        if "power_web_os.application" not in text:
            found.append("missing application service import")
        if found:
            violations[path.as_posix()] = found

    assert violations == {}


def test_persistence_modules_do_not_import_fastapi() -> None:
    persistence_dir = BACKEND_ROOT / "persistence"
    if not persistence_dir.exists():
        return

    violations = [
        path.as_posix()
        for path in sorted(persistence_dir.rglob("*.py"))
        if "fastapi" in imported_roots(path)
    ]

    assert violations == []


def test_job_modules_are_thin_application_entrypoints() -> None:
    jobs_dir = BACKEND_ROOT / "jobs"
    if not jobs_dir.exists():
        return

    violations: dict[str, list[str]] = {}
    for path in sorted(jobs_dir.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8").lower()
        found = sorted(snippet for snippet in JOB_FORBIDDEN_SNIPPETS if snippet in text)
        if "power_web_os.application" not in text:
            found.append("missing application service import")
        if found:
            violations[path.as_posix()] = found

    assert violations == {}
