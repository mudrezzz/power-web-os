from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from power_web_os.radar_signal_monitoring import generate_recorded_signal_monitoring_report


FIXTURE = Path("demo/fixtures/radar_signal_monitoring/toir_recorded_signal_monitoring.json")
QUALITY_FIXTURE = Path("demo/fixtures/radar_signal_monitoring/signal_monitoring_positive_controls.json")


def test_recorded_toir_signal_monitoring_loop_projects_required_states(tmp_path: Path) -> None:
    output = tmp_path / "radar_signal_monitoring_report.json"

    report = generate_recorded_signal_monitoring_report(fixture_path=FIXTURE, output_path=output)

    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == report
    assert report["artifact_type"] == "radar_signal_monitoring_report"
    assert report["artifact_version"] == "0.7.6.4.18.2.1"
    assert report["recorded_provider"] is True
    assert report["live_provider_calls"] == 0
    assert report["summary"]["candidate_count"] == 5
    assert report["summary"]["new_signal_count"] >= 1
    assert report["summary"]["repeated_signal_count"] >= 1
    assert report["summary"]["searched_negative_count"] >= 1
    assert report["summary"]["not_searched_budget_limited_count"] >= 1

    statuses = {item["search_status"] for item in report["observations"]}
    assert {"searched", "duplicate_existing_signal", "not_searched_budget_limited"} <= statuses
    assert any(item["observation_status"] == "not_observed" for item in report["observations"])
    assert report["budget_counters"]["signal_provider_calls"] == 6
    assert len(report["provider_attempts"]) == 6


def test_recorded_toir_signal_monitoring_observed_signals_have_resolved_evidence(tmp_path: Path) -> None:
    report = generate_recorded_signal_monitoring_report(
        fixture_path=FIXTURE,
        output_path=tmp_path / "report.json",
    )

    observed = [
        item
        for item in report["observations"]
        if item["observation_status"] == "observed" and item["search_status"] == "searched"
    ]
    assert observed
    for item in observed:
        assert item["source_refs"]
        assert item["evidence"]
        assert {evidence["source_ref"] for evidence in item["evidence"]} == set(item["source_refs"])


def test_recorded_toir_signal_monitoring_duplicate_uses_previous_fingerprint(tmp_path: Path) -> None:
    report = generate_recorded_signal_monitoring_report(fixture_path=FIXTURE, output_path=tmp_path / "report.json")

    duplicates = [item for item in report["observations"] if item["search_status"] == "duplicate_existing_signal"]

    assert len(duplicates) == 1
    duplicate = duplicates[0]
    assert duplicate["candidate_id"] == "nizhnekamskneftekhim"
    assert duplicate["signal_code"] == "toir_digitalization"
    assert duplicate["score"] == 0


def test_recorded_signal_monitoring_report_is_product_safe(tmp_path: Path) -> None:
    report = generate_recorded_signal_monitoring_report(fixture_path=FIXTURE, output_path=tmp_path / "report.json")
    serialized = json.dumps(report, ensure_ascii=False)

    for marker in [
        "OPENROUTER_API_KEY",
        "DADATA_API_KEY",
        "Authorization",
        "Bearer ",
        "sk-or-",
        "chain_of_thought",
        "hidden_reasoning",
        "internal_thoughts",
    ]:
        assert marker not in serialized


def test_demo_command_writes_recorded_signal_monitoring_report(tmp_path: Path) -> None:
    output = tmp_path / "signal_report.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "power_web_os.demo",
            "run-recorded-signal-monitoring",
            "--signal-monitoring-fixture",
            str(FIXTURE),
            "--signal-monitoring-output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert output.exists()
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["summary"]["not_searched_budget_limited_count"] >= 1
    assert '"artifact_type": "radar_signal_monitoring_report"' in completed.stdout


def test_recorded_positive_control_benchmark_meets_quality_dod(tmp_path: Path) -> None:
    report = generate_recorded_signal_monitoring_report(
        fixture_path=QUALITY_FIXTURE,
        output_path=tmp_path / "quality-report.json",
    )

    quality = report["quality_control_summary"]
    assert quality["expected_positive_count"] == 4
    assert quality["detected_positive_count"] == 4
    assert quality["positive_recall"] == 1.0
    assert quality["false_positive_control_count"] == 0
    assert {item["status"] for item in report["source_lane_ledger"]} == {"executed"}
    assert len(report["search_execution_receipts"]) == len(report["tasks"])
