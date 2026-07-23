from __future__ import annotations

import json
from pathlib import Path

from power_web_os.power_web_people_search_validation import evaluate_artifact, validate, write_report
from test_power_web_people_search_pipeline import _artifact


def _benchmark() -> dict:
    return json.loads(Path("docs/radar/pipelines/power-web-discovery/benchmark/benchmark.user.json").read_text(encoding="utf-8"))


def test_people_search_planning_has_zero_blind_control_leakage() -> None:
    artifact, _ = _artifact()
    evaluation = evaluate_artifact(artifact, _benchmark())
    assert evaluation["controls_in_planning_count"] == 0
    assert all(item["found"] or item["path_reason"] for item in evaluation["profile_controls"])


def test_live_acceptance_requires_eight_roles_and_three_lanes() -> None:
    artifact, _ = _artifact()
    evaluation = evaluate_artifact(artifact, _benchmark())
    assert evaluation["role_demands"] == 8
    assert evaluation["roles_with_accepted_hypothesis"] == 8
    assert evaluation["mandatory_lane_decisions"] == 24
    assert evaluation["executed_mandatory_lanes"] == 24
    assert evaluation["unrecovered_mandatory_lane_errors"] == 0
    assert evaluation["budget_limited_mandatory_lanes"] == 0
    assert all(evaluation["leads_by_lane"][lane] >= 1 for lane in ("official_company", "hh_public_web", "generic_web"))
    assert evaluation["roles_with_relevant_leads"] >= 4
    assert evaluation["receipt_gaps"] == 0
    assert evaluation["orphan_decisions"] == 0


def test_full_validator_maps_all_manifest_requirements() -> None:
    artifact, _ = _artifact()
    report = validate(
        root=Path("."),
        artifact=artifact,
        tests_pass=True,
        remote_session_id="recorded-session",
        workspace_sha256="recorded-workspace-sha",
    )

    assert report["validation_status"] == "PASS"
    assert all(item["status"] == "PASS" for item in report["requirements"])


def test_validation_markdown_states_profile_recall_limit(tmp_path: Path) -> None:
    artifact, _ = _artifact()
    report = validate(
        root=Path("."),
        artifact=artifact,
        tests_pass=True,
        remote_session_id="recorded-session",
        workspace_sha256="recorded-workspace-sha",
    )

    write_report(tmp_path, report, artifact)

    markdown = (tmp_path / "VALIDATION_REPORT.md").read_text(encoding="utf-8")
    assert "profile-recall quality claim" in markdown
    assert "source verifications" in markdown
