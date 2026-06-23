"""Demo CLI helpers for Radar execution preflight."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from power_web_os.application.live_radar_definition import build_live_mini_radar_definition
from power_web_os.application.live_radar_definition_runtime import active_definition_to_live_radar_payload
from power_web_os.application.radar_preflight import RadarExecutionPreflightService
from power_web_os.persistence import (
    SqlAlchemyRadarDefinitionRepository,
    create_database_engine,
    create_session_factory,
    session_scope,
)


def build_radar_preflight_report(
    *,
    radar_id: str,
    database_url: str | None = None,
    profile: str = "recorded",
) -> dict[str, Any]:
    engine = create_database_engine(database_url=database_url)
    session_factory = create_session_factory(engine)
    with session_scope(session_factory) as session:
        definition_repository = SqlAlchemyRadarDefinitionRepository(session)
        service = RadarExecutionPreflightService(
            definition_repository=definition_repository,
            runtime_definition_provider=lambda: _active_runtime_definition_payload(
                definition_repository,
                radar_id=radar_id,
            ),
            company_registry_provider_ids=_available_company_registry_provider_ids(),
        )
        report = service.run(radar_id=radar_id, profile="recorded" if profile == "recorded" else "static")
    return report.to_payload()


def print_preflight_report(report: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    status = "READY" if report.get("ready_for_live_run") else "NOT READY"
    summary = report.get("summary", {})
    print(f"Radar preflight: {status}")
    print(f"Radar: {report.get('radar_id')}")
    print(f"Definition: {report.get('definition_id') or 'missing'}")
    print(
        "Checks: "
        f"{summary.get('passed_count', 0)} passed, "
        f"{summary.get('error_count', 0)} errors, "
        f"{summary.get('warning_count', 0)} warnings"
    )
    for check in report.get("checks", []):
        if check.get("status") == "passed":
            continue
        print(f"- {check.get('code')}: {check.get('message')}")
        if check.get("remediation"):
            print(f"  remediation: {check['remediation']}")


def _active_runtime_definition_payload(
    definition_repository: Any,
    *,
    radar_id: str,
) -> dict[str, Any]:
    definition = definition_repository.get_active(radar_id)
    if definition is None:
        return build_live_mini_radar_definition()
    return active_definition_to_live_radar_payload(definition)


def _available_company_registry_provider_ids() -> set[str]:
    env = _load_env_file(Path.cwd() / ".env")
    mode = (env.get("POWER_WEB_OS_DADATA_MODE") or "recorded").strip().lower()
    if mode == "recorded":
        return {"dadata"}
    return {"dadata"} if mode == "live" and env.get("DADATA_API_KEY") and env.get("DADATA_SECRET_KEY") else set()


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
