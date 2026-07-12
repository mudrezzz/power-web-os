from __future__ import annotations

import json
from pathlib import Path

from power_web_os.application.radar.validation import RadarPipelineSliceValidator


def test_pipeline_validator_fails_without_required_live_evidence(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)

    report = RadarPipelineSliceValidator(root=tmp_path).validate(
        manifest_path=manifest,
        run_tests=False,
    )

    assert report.validation_status == "FAIL"
    assert report.requirements[0].requirement_id == "SM-PLAN-01"
    assert report.requirements[0].status == "FAIL"


def test_pipeline_validator_writes_pass_report_for_complete_signal_evidence(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)
    first = _report("signal-run-first", incremental=False, duplicate=False)
    second = _report("signal-run-second", incremental=True, duplicate=True)

    report = RadarPipelineSliceValidator(root=tmp_path).validate(
        manifest_path=manifest,
        first_live_report=first,
        second_live_report=second,
        run_tests=False,
    )

    assert report.validation_status == "PASS"
    persisted = json.loads((tmp_path / "validation/validation.json").read_text(encoding="utf-8"))
    assert persisted["validation_status"] == "PASS"
    assert "SM-PLAN-01" in (tmp_path / "validation/VALIDATION_REPORT.md").read_text(encoding="utf-8")


def test_pipeline_validator_checks_signal_quality_controls(tmp_path: Path) -> None:
    manifest = _write_quality_manifest(tmp_path)
    first = _quality_report("signal-run-quality-1", incremental=False)
    second = _quality_report("signal-run-quality-2", incremental=True)

    report = RadarPipelineSliceValidator(root=tmp_path).validate(
        manifest_path=manifest,
        first_live_report=first,
        second_live_report=second,
        run_tests=False,
    )

    assert report.validation_status == "PASS"
    results = {item.requirement_id: item.status for item in report.requirements}
    assert results["SM-BENCH-02"] == "PASS"
    assert results["SM-BENCH-03"] == "PASS"
    assert results["SM-DED-02"] == "PASS"


def _write_manifest(root: Path) -> Path:
    (root / "to-be.md").write_text("Status: Implemented\nSM-PLAN-01\n", encoding="utf-8")
    (root / "to-be.pdf").write_bytes(b"pdf")
    (root / "as-is.md").write_text("AS IS finalized after slice test-slice\nSM-PLAN-01\n", encoding="utf-8")
    (root / "as-is.pdf").write_bytes(b"pdf")
    (root / "baseline.md").write_text("baseline", encoding="utf-8")
    manifest = root / "to-be.acceptance.json"
    manifest.write_text(json.dumps({
        "slice_id": "test-slice",
        "pipeline_id": "signal-monitoring",
        "to_be_markdown": "to-be.md",
        "to_be_pdf": "to-be.pdf",
        "as_is_markdown": "as-is.md",
        "as_is_pdf": "as-is.pdf",
        "baseline_diagnostic": "baseline.md",
        "validation_json": "validation/validation.json",
        "validation_markdown": "validation/VALIDATION_REPORT.md",
        "requirements": [{
            "id": "SM-PLAN-01",
            "description": "selected decisions are accounted for",
        }],
        "live_acceptance": {"initial_lookback_days": 365},
    }), encoding="utf-8")
    return manifest


def _write_quality_manifest(root: Path) -> Path:
    (root / "to-be.md").write_text(
        "Status: Implemented\nSM-BENCH-01\nSM-BENCH-02\nSM-BENCH-03\nSM-DED-02\nSM-TIME-01\n"
        "SM-TIME-02\nSM-TIME-03\nSM-CAP-01\nSM-BIND-01\nSM-BIND-02\nSM-QUERY-01\nSM-RETRY-01\n"
        "SM-SCORE-01\nSM-AUD-02\nSM-PROC-02\n",
        encoding="utf-8",
    )
    (root / "to-be.pdf").write_bytes(b"pdf")
    (root / "as-is.md").write_text(
        "Status: AS IS\n0.7.6.4.18.2.2\nSM-BENCH-01\nSM-BENCH-02\nSM-BENCH-03\nSM-DED-02\n"
        "SM-TIME-01\nSM-TIME-02\nSM-TIME-03\nSM-CAP-01\nSM-BIND-01\nSM-BIND-02\nSM-QUERY-01\n"
        "SM-RETRY-01\nSM-SCORE-01\nSM-AUD-02\nSM-PROC-02\n",
        encoding="utf-8",
    )
    (root / "as-is.pdf").write_bytes(b"pdf")
    (root / "baseline.md").write_text("baseline", encoding="utf-8")
    requirements = [
        "SM-BENCH-01", "SM-BENCH-02", "SM-BENCH-03", "SM-DED-02",
        "SM-TIME-01", "SM-TIME-02", "SM-TIME-03", "SM-CAP-01",
        "SM-BIND-01", "SM-BIND-02", "SM-QUERY-01", "SM-RETRY-01",
        "SM-SCORE-01", "SM-AUD-02", "SM-PROC-02",
    ]
    manifest = root / "to-be.acceptance.json"
    manifest.write_text(json.dumps({
        "slice_id": "0.7.6.4.18.2.2",
        "pipeline_id": "signal-monitoring",
        "to_be_markdown": "to-be.md",
        "to_be_pdf": "to-be.pdf",
        "as_is_markdown": "as-is.md",
        "as_is_pdf": "as-is.pdf",
        "baseline_diagnostic": "baseline.md",
        "validation_json": "validation/quality.json",
        "validation_markdown": "validation/quality.md",
        "requirements": [{"id": requirement, "description": requirement} for requirement in requirements],
        "live_acceptance": {
            "accepted_candidate_count": 3,
            "review_candidate_count": 3,
            "signal_codes": ["S1", "S2"],
            "initial_lookback_days": 365,
            "positive_controls": [{
                "id": "positive-a",
                "candidate_id": "candidate-a",
                "signal_code": "S1",
                "url": "https://source.test/a",
                "date_start": "2026-06-01",
                "date_end": "2026-06-30",
            }],
            "negative_controls": [{
                "id": "negative-old",
                "candidate_id": "candidate-b",
                "signal_code": "S1",
                "url": "https://source.test/old",
                "expected_reason": "rejected_out_of_window",
            }],
            "unknown_date_controls": [{
                "id": "unknown-a",
                "candidate_id": "candidate-c",
                "signal_code": "S2",
                "url": "https://source.test/unknown",
            }],
        },
    }), encoding="utf-8")
    return manifest


def _report(run_id: str, *, incremental: bool, duplicate: bool) -> dict[str, object]:
    task = {
        "task_id": "task-open",
        "candidate_id": "candidate-a",
        "signal_code": "S1",
        "source_lane": "open_web",
        "source_contracts": [],
        "domain_restrictions": [],
        "window_basis": "incremental_watermark" if incremental else "explicit_override",
    }
    search_status = "duplicate_existing_signal" if duplicate else "searched"
    return {
        "run_id": run_id,
        "candidates": [{"candidate_id": "candidate-a"}, {"candidate_id": "candidate-b"}],
        "signal_rules": [{"signal_code": "S1"}, {"signal_code": "S2"}],
        "tasks": [task],
        "source_strategy_decisions": [{"decision_id": "decision-open", "status": "selected"}],
        "source_lane_ledger": [{
            "task_id": "task-open",
            "status": "executed",
            "source_decision_ids": ["decision-open"],
        }],
        "search_execution_receipts": [{"task_id": "task-open"}],
        "checkpoint_decisions": [{
            "action": "observed",
            "required_task_count": 1,
            "completed_required_task_count": 1,
        }],
        "window_policy": {"initial_lookback_days": 365},
        "task_observations": [{
            "task_id": "task-open",
            "candidate_id": "candidate-a",
            "signal_code": "S1",
            "observation_status": "observed" if not duplicate else "unclear",
            "search_status": search_status,
            "source_refs": ["source-1"],
        }],
        "sources": [{"source_ref": "source-1", "url": "https://example.com/event"}],
        "input_snapshot": {
            "previous_signal_source_keys": (
                ["candidate-a|S1|https://example.com/event"] if incremental else []
            ),
        },
        "observations": [{"observation_status": "observed"}, {"observation_status": "observed"}],
        "watermarks_before": ([{
            "candidate_id": "candidate-a", "signal_code": "S1", "source_lane": "open_web",
            "searched_through_at": "2026-07-08T00:00:00Z",
        }] if incremental else []),
        "watermarks_after": [{
            "candidate_id": "candidate-a", "signal_code": "S1", "source_lane": "open_web",
            "searched_through_at": "2026-07-10T00:00:00Z",
        }],
        "evidence_validation_summary": {"records": [{"task_id": "task-open", "accepted": True}]},
    }


def _quality_report(run_id: str, *, incremental: bool) -> dict[str, object]:
    candidates = [
        {"candidate_id": f"candidate-{value}", "product_acceptance_status": "product_candidate" if value in "abc" else "review_required"}
        for value in "abcdef"
    ]
    tasks = [
        {
            "task_id": f"task-{candidate['candidate_id']}-{signal}",
            "candidate_id": candidate["candidate_id"],
            "signal_code": signal,
            "source_lane": "open_web",
            "alternate_query": f"{candidate['candidate_id']} {signal} alias",
            "window_basis": "incremental" if incremental else "explicit_override",
        }
        for candidate in candidates
        for signal in ("S1", "S2")
    ]
    task_observations = [
        {
            "task_id": "task-candidate-a-S1",
            "candidate_id": "candidate-a",
            "signal_code": "S1",
            "observation_status": "observed" if not incremental else "unclear",
            "search_status": "searched" if not incremental else "duplicate_existing_signal",
            "score": 2 if not incremental else 0,
            "source_refs": ["positive-a"],
            "evidence": [{"source_ref": "positive-a", "event_at": "2026-06-10", "temporal_status": "confirmed_in_window"}],
        },
        {
            "task_id": "task-candidate-b-S1",
            "candidate_id": "candidate-b",
            "signal_code": "S1",
            "observation_status": "unclear",
            "search_status": "rejected_out_of_window",
            "source_refs": ["negative-old"],
            "evidence": [{"source_ref": "negative-old", "event_at": "2024-01-10", "temporal_status": "rejected_out_of_window"}],
        },
        {
            "task_id": "task-candidate-c-S2",
            "candidate_id": "candidate-c",
            "signal_code": "S2",
            "observation_status": "unclear",
            "search_status": "review_needed_date_unknown" if not incremental else "duplicate_existing_review",
            "source_refs": ["unknown-a"],
            "evidence": [{"source_ref": "unknown-a", "temporal_status": "review_needed_date_unknown"}],
        },
    ]
    return {
        "run_id": run_id,
        "candidates": candidates,
        "signal_rules": [{"signal_code": "S1"}, {"signal_code": "S2"}],
        "tasks": tasks,
        "source_strategy_decisions": [{"decision_id": "open", "status": "selected"}],
        "source_lane_ledger": [{"task_id": task["task_id"], "status": "executed", "source_decision_ids": ["open"]} for task in tasks],
        "search_execution_receipts": [{"task_id": task["task_id"], "outcome": "retrieved"} for task in tasks],
        "checkpoint_decisions": [{"action": "observed", "required_task_count": 1, "completed_required_task_count": 1}],
        "window_policy": {"initial_lookback_days": 365},
        "task_observations": task_observations,
        "observations": task_observations,
        "sources": [
            {"source_ref": "positive-a", "url": "https://source.test/a", "published_at": "2026-06-10", "capability": "official_press", "capability_basis": "test"},
            {"source_ref": "negative-old", "url": "https://source.test/old", "published_at": "2024-01-10", "capability": "official_press", "capability_basis": "test"},
            {"source_ref": "unknown-a", "url": "https://source.test/unknown", "capability": "official_press", "capability_basis": "test"},
        ],
        "provider_attempts": [{"task_id": "task-candidate-a-S1", "attempt_role": "primary", "outcome": "provider_error"}, {"task_id": "task-candidate-a-S1", "attempt_role": "primary_retry", "outcome": "accepted"}],
        "watermarks_before": ([{"candidate_id": "candidate-a", "signal_code": "S1", "source_lane": "open_web", "searched_through_at": "2026-07-01T00:00:00Z"}] if incremental else []),
        "watermarks_after": [{"candidate_id": "candidate-a", "signal_code": "S1", "source_lane": "open_web", "searched_through_at": "2026-07-10T00:00:00Z"}],
        "input_snapshot": {"previous_signal_source_keys": (["candidate-a|S1|https://source.test/a"] if incremental else [])},
        "evidence_validation_summary": {"records": [{"task_id": "task-candidate-a-S1", "accepted": not incremental}]},
    }
