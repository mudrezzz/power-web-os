from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = Path("src/power_web_os")
ADR_PATH = Path("docs/adr/2026-06-16-backend-architecture-guardrails.md")
ARCHITECTURE_PATH = Path("docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md")
DEVELOPER_GUIDE_PATH = Path("docs/developer/DEVELOPER_GUIDE.md")

MAX_BACKEND_MODULE_LINES = 500

LEGACY_LARGE_MODULE_ALLOWLIST = {
    Path("src/power_web_os/live_icp_radar.py"),
    Path("src/power_web_os/icp_radar.py"),
    Path("src/power_web_os/icp_radar_catalog.py"),
    Path("src/power_web_os/icp_radar_xlsx.py"),
}

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
    "sqlalchemy",
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
}

JOB_FORBIDDEN_SNIPPETS = {
    "sqlalchemy",
    "session.execute",
    ".query(",
    "deterministicaccessplanner",
    "normalize_openrouter_response",
    "normalize_live_candidate",
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
