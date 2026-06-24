from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from power_web_os.application.live_radar_definition import build_live_mini_radar_definition
from power_web_os.application.live_radar_definition_runtime import active_definition_to_live_radar_payload
from power_web_os.application.connector_profiles import ConnectorProfile, ConnectorProfileRegistry
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


def test_toir_quick_live_preflight_uses_active_runtime_definition() -> None:
    definition = _toir_quick_live_definition()
    service = RadarExecutionPreflightService(
        definition_repository=_Repo(definition),
        runtime_definition_provider=lambda: active_definition_to_live_radar_payload(definition),
        company_registry_provider_ids={"dadata"},
    )

    report = service.run(radar_id="toir-quick-live", profile="static")

    assert report.ready_for_live_run
    checks = _checks_by_code(report.checks)
    mismatch = checks["definition_runtime_mismatch"][0]
    assert mismatch.status == "passed"
    assert mismatch.severity == "info"
    assert report.summary["failed_codes"] == []


def test_preflight_still_detects_legacy_hardcoded_runtime_definition() -> None:
    service = RadarExecutionPreflightService(
        definition_repository=_Repo(_toir_quick_live_definition()),
        runtime_definition_provider=build_live_mini_radar_definition,
        company_registry_provider_ids={"dadata"},
    )

    report = service.run(radar_id="toir-quick-live", profile="static")

    assert not report.ready_for_live_run
    checks = _checks_by_code(report.checks)
    mismatch = checks["definition_runtime_mismatch"][0]
    assert mismatch.status == "failed"
    assert mismatch.severity == "error"
    assert "legacy hardcoded live mini definition" in mismatch.remediation
    assert "definition_runtime_mismatch" in report.summary["failed_codes"]


def test_preflight_requires_executable_company_registry_provider() -> None:
    service = RadarExecutionPreflightService(
        definition_repository=_Repo(_toir_quick_live_definition()),
        runtime_definition_provider=lambda: active_definition_to_live_radar_payload(_toir_quick_live_definition()),
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
        runtime_definition_provider=lambda: active_definition_to_live_radar_payload(definition.__class__(
            definition_id=definition.definition_id,
            radar_id=definition.radar_id,
            definition_payload=payload,
            definition_version=definition.definition_version,
        )),
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
        runtime_definition_provider=lambda: active_definition_to_live_radar_payload(definition),
        company_registry_provider_ids={"dadata"},
    )

    report = service.run(radar_id="toir-quick-live", profile="static")

    assert report.ready_for_live_run
    assert all(check.status in {"passed", "skipped"} for check in report.checks)


def test_preflight_resolves_active_definition_sources_to_connector_profiles() -> None:
    definition = _toir_quick_live_definition()
    service = RadarExecutionPreflightService(
        definition_repository=_Repo(definition),
        runtime_definition_provider=lambda: active_definition_to_live_radar_payload(definition),
        company_registry_provider_ids={"dadata"},
    )

    report = service.run(radar_id="toir-quick-live", profile="static")

    checks = _checks_by_code(report.checks)
    resolved = checks["source_connector_profile_resolved"]
    assert {check.details["connector_profile_id"] for check in resolved} == {
        "dadata_registry",
        "openrouter_web",
        "sibur_site",
    }
    compiled = checks["source_connector_capability_compiled"]
    assert any(check.details["capability"]["requires_concrete_input"] for check in compiled)


def test_preflight_rejects_unknown_connector_profile() -> None:
    definition = _toir_quick_live_definition()
    payload = json.loads(json.dumps(definition.definition_payload, ensure_ascii=False))
    payload["global_search_policy"]["sources"][0]["connector_profile_id"] = "missing_profile"
    invalid_definition = RadarDefinitionRecord(
        definition_id=definition.definition_id,
        radar_id=definition.radar_id,
        definition_payload=payload,
        definition_version=definition.definition_version,
    )
    registry = ConnectorProfileRegistry.from_profiles([
        ConnectorProfile(
            id="openrouter_web",
            display_name="OpenRouter web",
            description="Open web search for broad discovery and signal evidence.",
            source_type="search_engine",
            runtime_provider_id="openrouter_web",
            good_inputs=("free text web search",),
            bad_inputs=("secrets",),
            expected_facts=("url", "snippet", "signal evidence"),
            limitations=("requires extraction",),
        )
    ])
    service = RadarExecutionPreflightService(
        definition_repository=_Repo(invalid_definition),
        runtime_definition_provider=lambda: active_definition_to_live_radar_payload(invalid_definition),
        company_registry_provider_ids={"dadata"},
        connector_profile_registry=registry,
    )

    report = service.run(radar_id="toir-quick-live", profile="static")

    assert not report.ready_for_live_run
    check = _checks_by_code(report.checks)["source_connector_profile_resolved"][0]
    assert check.status == "failed"
    assert check.details["connector_profile_id"] == "missing_profile"


def test_preflight_rejects_source_connector_profile_type_mismatch() -> None:
    definition = _toir_quick_live_definition()
    payload = json.loads(json.dumps(definition.definition_payload, ensure_ascii=False))
    payload["global_search_policy"]["sources"][0]["connector_profile_id"] = "openrouter_web"
    invalid_definition = RadarDefinitionRecord(
        definition_id=definition.definition_id,
        radar_id=definition.radar_id,
        definition_payload=payload,
        definition_version=definition.definition_version,
    )
    service = RadarExecutionPreflightService(
        definition_repository=_Repo(invalid_definition),
        runtime_definition_provider=lambda: active_definition_to_live_radar_payload(invalid_definition),
        company_registry_provider_ids={"dadata"},
    )

    report = service.run(radar_id="toir-quick-live", profile="static")

    assert not report.ready_for_live_run
    check = _checks_by_code(report.checks)["source_connector_profile_mismatch"][0]
    assert check.status == "failed"
    assert check.details["source_type"] == "company_registry"
    assert check.details["profile_source_type"] == "search_engine"


def test_preflight_strict_credentials_blocks_required_live_connector() -> None:
    definition = _toir_quick_live_definition()
    service = RadarExecutionPreflightService(
        definition_repository=_Repo(definition),
        runtime_definition_provider=lambda: active_definition_to_live_radar_payload(definition),
        company_registry_provider_ids={"dadata"},
        environment={},
        require_connector_credentials=True,
    )

    report = service.run(radar_id="toir-quick-live", profile="static")

    assert not report.ready_for_live_run
    failed_credentials = [
        check
        for check in _checks_by_code(report.checks)["connector_credentials_present"]
        if check.status == "failed"
    ]
    assert failed_credentials
    assert failed_credentials[0].details["missing_credential_count"] > 0


def test_preflight_rejects_invalid_source_usage_obligation() -> None:
    definition = _toir_quick_live_definition()
    payload = json.loads(json.dumps(definition.definition_payload, ensure_ascii=False))
    payload["global_search_policy"]["sources"][0]["usage_obligation"] = "must_use_somehow"
    invalid_definition = RadarDefinitionRecord(
        definition_id=definition.definition_id,
        radar_id=definition.radar_id,
        definition_payload=payload,
        definition_version=definition.definition_version,
    )
    service = RadarExecutionPreflightService(
        definition_repository=_Repo(invalid_definition),
        runtime_definition_provider=lambda: active_definition_to_live_radar_payload(invalid_definition),
        company_registry_provider_ids={"dadata"},
    )

    report = service.run(radar_id="toir-quick-live", profile="static")

    assert not report.ready_for_live_run
    check = _checks_by_code(report.checks)["source_usage_obligation_invalid"][0]
    assert check.status == "failed"
    assert check.details["usage_obligation"] == "must_use_somehow"


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
        "extraction_repair_needed",
        "evidence_linking_failed",
        "invalid_zero_score_projection",
    }


def test_provider_fixture_gate_rejects_prose_first_output() -> None:
    issues = validate_provider_output_fixture('Result follows:\n{"sources": [], "candidates": []}')

    assert {issue.code for issue in issues} == {"extraction_repair_needed"}
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
            "--show-runtime-config",
            "--probe",
            "dadata",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(Path.cwd() / "src")},
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert payload["artifact_type"] == "radar_execution_preflight_report"
    assert payload["ready_for_live_run"]
    assert payload["runtime_config"]["artifact_type"] == "radar_runtime_config_report"
    assert payload["runtime_config"]["component"] == "cli"
    assert payload["live_probes"][0]["code"] == "dadata_probe"
    assert payload["live_probes"][0]["status"] == "skipped"
    assert "definition_runtime_mismatch" not in payload["summary"]["failed_codes"]
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
