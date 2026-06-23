from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from power_web_os.application.live_radar_definition import build_live_mini_radar_definition
from power_web_os.application.radar_preflight import (
    RadarExecutionPreflightService,
    RadarPreflightCheckResult,
    validate_provider_output_fixture,
)
from power_web_os.application.radar_records import RadarDefinitionRecord
from power_web_os.demo import build_icp_radar_catalog_from_workbook
from power_web_os.persistence import (
    Base,
    SqlAlchemyRadarDefinitionRepository,
    SqlAlchemyRadarRunOutputRepository,
    SqlAlchemyRadarRunRepository,
    create_database_engine,
    create_session_factory,
    session_scope,
)
from power_web_os.persistence.seed import seed_radar_catalog


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_current_toir_quick_live_preflight_reports_runtime_definition_mismatch() -> None:
    service = RadarExecutionPreflightService(
        definition_repository=_Repo(_toir_quick_live_definition()),
        runtime_definition_provider=build_live_mini_radar_definition,
        company_registry_provider_ids={"dadata"},
    )

    report = service.run(radar_id="toir-quick-live")

    assert not report.ready_for_live_run
    checks = _checks_by_code(report.checks)
    mismatch = checks["definition_runtime_mismatch"][0]
    assert mismatch.status == "failed"
    assert mismatch.severity == "error"
    assert "legacy hardcoded live mini definition" in mismatch.remediation
    assert report.summary["failed_codes"] == ["definition_runtime_mismatch"]


def test_preflight_requires_executable_company_registry_provider() -> None:
    service = RadarExecutionPreflightService(
        definition_repository=_Repo(_toir_quick_live_definition()),
        runtime_definition_provider=lambda: _toir_quick_live_definition().definition_payload,
        company_registry_provider_ids=set(),
    )

    report = service.run(radar_id="toir-quick-live", profile="static")

    assert not report.ready_for_live_run
    provider_check = _checks_by_code(report.checks)["company_registry_provider_available"][0]
    assert provider_check.status == "failed"
    assert provider_check.details["provider_id"] == "dadata"


def test_preflight_rejects_unknown_source_policy_references() -> None:
    definition = _toir_quick_live_definition()
    payload = json.loads(json.dumps(definition.definition_payload, ensure_ascii=False))
    payload["account_qualification"]["rule_group"]["rules"][0]["source_policy"]["source_ids"].append("missing_registry")
    service = RadarExecutionPreflightService(
        definition_repository=_Repo(definition.__class__(
            definition_id=definition.definition_id,
            radar_id=definition.radar_id,
            definition_payload=payload,
            definition_version=definition.definition_version,
        )),
        runtime_definition_provider=lambda: payload,
        company_registry_provider_ids={"dadata"},
    )

    report = service.run(radar_id="toir-quick-live", profile="static")

    assert not report.ready_for_live_run
    source_check = _checks_by_code(report.checks)["source_base_not_executable"][0]
    assert source_check.status == "failed"
    assert source_check.details["unknown_source_ids"] == ["missing_registry"]


def test_preflight_is_ready_when_definition_sources_and_runtime_match() -> None:
    definition = _toir_quick_live_definition()
    service = RadarExecutionPreflightService(
        definition_repository=_Repo(definition),
        runtime_definition_provider=lambda: definition.definition_payload,
        company_registry_provider_ids={"dadata"},
    )

    report = service.run(radar_id="toir-quick-live", profile="static")

    assert report.ready_for_live_run
    assert all(check.status in {"passed", "skipped"} for check in report.checks)


def test_provider_fixture_gate_detects_malformed_shapes_and_evidence_refs() -> None:
    malformed_payload = {
        "sources": [{"evidence_ref": "src_1", "title": "A", "url": "https://example.test", "snippet": "A"}],
        "candidates": {"legal_name": "Candidate A"},
        "source_outcomes": {"source_ref": "src_1"},
        "candidate_observations": [
            {
                "legal_name": "Candidate B",
                "evidence_refs": ["missing_src"],
                "signals": [
                    {
                        "signal_code": "S1",
                        "status": "not_observed",
                        "search_status": "not_searched_budget_limited",
                        "score": 0,
                    }
                ],
            }
        ],
    }

    issues = validate_provider_output_fixture(malformed_payload)
    codes = {issue.code for issue in issues}

    assert codes >= {
        "extraction_schema_invalid",
        "evidence_linking_failed",
        "invalid_zero_score_projection",
    }


def test_provider_fixture_gate_rejects_prose_first_output() -> None:
    issues = validate_provider_output_fixture('Result follows:\n{"sources": [], "candidates": []}')

    assert {issue.code for issue in issues} == {"extraction_schema_invalid"}
    assert issues[0].details["payload_excerpt"].startswith("Result follows")


def test_preflight_cli_returns_json_and_does_not_create_runs(tmp_path: Path) -> None:
    db_url = sqlite_url(tmp_path / "preflight.db")
    engine = create_database_engine(database_url=db_url)
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    catalog = build_icp_radar_catalog_from_workbook(Path("demo/fixtures/icp_radar/sibur_icp_pass1.xlsx"))
    with session_scope(session_factory) as session:
        seed_radar_catalog(session, catalog)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "power_web_os.demo",
            "preflight-radar",
            "--radar-id",
            "toir-quick-live",
            "--database-url",
            db_url,
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["artifact_type"] == "radar_execution_preflight_report"
    assert not payload["ready_for_live_run"]
    assert "definition_runtime_mismatch" in payload["summary"]["failed_codes"]
    with session_scope(session_factory) as session:
        assert SqlAlchemyRadarRunRepository(session).list_for_radar("toir-quick-live") == ()
        assert SqlAlchemyRadarRunOutputRepository(session).get("any-run") is None


class _Repo:
    def __init__(self, record: RadarDefinitionRecord | None) -> None:
        self._record = record

    def get_active(self, radar_id: str) -> RadarDefinitionRecord | None:
        if self._record is not None and self._record.radar_id == radar_id:
            return self._record
        return None


def _toir_quick_live_definition() -> RadarDefinitionRecord:
    catalog = build_icp_radar_catalog_from_workbook(Path("demo/fixtures/icp_radar/sibur_icp_pass1.xlsx"))
    for item in catalog["radars"]:
        if item["radar_id"] == "toir-quick-live":
            return RadarDefinitionRecord(
                definition_id=item["definition"]["definition_id"],
                radar_id=item["radar_id"],
                definition_payload=item["definition"],
                definition_version=catalog["artifact_version"],
            )
    raise AssertionError("toir-quick-live fixture is missing")


def _checks_by_code(checks: tuple[RadarPreflightCheckResult, ...]) -> dict[str, list[RadarPreflightCheckResult]]:
    result: dict[str, list[RadarPreflightCheckResult]] = {}
    for check in checks:
        result.setdefault(check.code, []).append(check)
    return result
