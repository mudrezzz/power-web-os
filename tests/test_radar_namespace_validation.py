from __future__ import annotations

from pathlib import Path

from power_web_os.application.radar.validation import namespace_closure
from power_web_os.application.radar.validation.namespace_closure import RadarNamespaceClosureValidator


QUALITY_CANDIDATE_IDS = {f"candidate-{index}" for index in range(6)}


def test_namespace_closure_validator_requires_candidate_trace_and_signal_quality(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def signal_metrics(report, *, negative_controls):
        if report["kind"] == "incremental":
            return _signal_metrics(incremental=True)
        return _signal_metrics(incremental=False)

    monkeypatch.setattr(namespace_closure, "evaluate_signal_report", signal_metrics)
    monkeypatch.setattr(
        namespace_closure,
        "control_match_summary",
        lambda report, controls, *, expected: {
            "matched": 4 if expected == "confirmed" else (2 if expected == "negative" else 1),
            "matched_ids": [],
            "missing": [],
        },
    )
    candidate_run_id = "radar-run-live"
    report = RadarNamespaceClosureValidator().validate(
        candidate_baseline_evaluation=_candidate_evaluation("radar-run-baseline"),
        candidate_live_evaluation=_candidate_evaluation(candidate_run_id),
        candidate_baseline_trace=_trace("radar-run-baseline"),
        candidate_live_trace=_trace(candidate_run_id),
        candidate_live_run={
            "run_id": candidate_run_id,
            "run_metadata": {"task_context": {"signal_execution_mode": "handoff"}},
        },
        candidate_live_rows=_quality_rows(),
        signal_baseline_initial={"kind": "initial", "signal_run_id": "signal-baseline-1"},
        signal_baseline_incremental={"kind": "incremental", "signal_run_id": "signal-baseline-2"},
        signal_live_initial={
            "kind": "initial",
            "signal_run_id": "signal-live-1",
            "source_candidate_run_id": candidate_run_id,
            "pipeline_id": "signal_monitoring",
            "candidates": _signal_candidates(),
        },
        signal_live_incremental={
            "kind": "incremental",
            "signal_run_id": "signal-live-2",
            "source_candidate_run_id": candidate_run_id,
            "pipeline_id": "signal_monitoring",
        },
        signal_controls={
            "positive_controls": [{}, {}, {}, {}],
            "negative_controls": [{}, {}],
            "unknown_date_controls": [{}],
        },
        latest_candidate_run_id=candidate_run_id,
        restart_round_trip={"api": True, "candidate": True, "signal": True},
    )

    assert report["validation_status"] == "PASS"
    assert report["semantic_trace_comparison"]["behavior_regressions"] == []
    RadarNamespaceClosureValidator.write(report, output_dir=tmp_path)
    assert (tmp_path / "validation.json").exists()
    assert "Validation status: **PASS**" in (tmp_path / "VALIDATION_REPORT.md").read_text(encoding="utf-8")


def test_namespace_closure_validator_fails_on_live_trace_regression(monkeypatch) -> None:
    monkeypatch.setattr(
        namespace_closure,
        "evaluate_signal_report",
        lambda report, *, negative_controls: _signal_metrics(incremental=report["kind"] == "incremental"),
    )
    monkeypatch.setattr(
        namespace_closure,
        "control_match_summary",
        lambda report, controls, *, expected: {
            "matched": 4 if expected == "confirmed" else (2 if expected == "negative" else 1),
            "matched_ids": [],
            "missing": [],
        },
    )
    kwargs = _validation_kwargs()
    kwargs["candidate_live_trace"] = {"run_id": "radar-run-live", "traces": []}

    report = RadarNamespaceClosureValidator().validate(**kwargs)

    assert report["validation_status"] == "FAIL"
    assert report["semantic_trace_comparison"]["classification"] == "behavior_regression"


def test_trace_comparison_does_not_require_reproducing_baseline_provider_errors() -> None:
    baseline = _trace("radar-run-baseline")
    baseline["traces"].append(
        {
            "phase": "provider",
            "node_name": "openrouter_web_search",
            "trace_type": "provider_error",
        }
    )

    comparison = namespace_closure._trace_comparison(baseline, _trace("radar-run-live"))

    assert comparison["classification"] == "provider_drift"
    assert comparison["behavior_regressions"] == []


def _validation_kwargs():
    candidate_run_id = "radar-run-live"
    return {
        "candidate_baseline_evaluation": _candidate_evaluation("radar-run-baseline"),
        "candidate_live_evaluation": _candidate_evaluation(candidate_run_id),
        "candidate_baseline_trace": _trace("radar-run-baseline"),
        "candidate_live_trace": _trace(candidate_run_id),
        "candidate_live_run": {
            "run_id": candidate_run_id,
            "run_metadata": {"task_context": {"signal_execution_mode": "handoff"}},
        },
        "candidate_live_rows": _quality_rows(),
        "signal_baseline_initial": {"kind": "initial", "signal_run_id": "signal-baseline-1"},
        "signal_baseline_incremental": {"kind": "incremental", "signal_run_id": "signal-baseline-2"},
        "signal_live_initial": {
            "kind": "initial",
            "signal_run_id": "signal-live-1",
            "source_candidate_run_id": candidate_run_id,
            "pipeline_id": "signal_monitoring",
            "candidates": _signal_candidates(),
        },
        "signal_live_incremental": {
            "kind": "incremental",
            "signal_run_id": "signal-live-2",
            "source_candidate_run_id": candidate_run_id,
            "pipeline_id": "signal_monitoring",
        },
        "signal_controls": {
            "positive_controls": [{}, {}, {}, {}],
            "negative_controls": [{}, {}],
            "unknown_date_controls": [{}],
        },
        "latest_candidate_run_id": candidate_run_id,
        "restart_round_trip": {"api": True},
    }


def _candidate_evaluation(run_id: str):
    return {
        "run_id": run_id,
        "benchmark_context": {"benchmark_mode": "blind", "benchmark_hints_used": False},
        "blind_benchmark_closeout": {
            "strict_recall": 0.8889,
            "visible_recall": 0.8889,
            "duplicate_candidate_id_count": 0,
            "empty_provenance_candidate_count": 0,
            "false_negative_count": 1,
        },
        "metrics": {
            "legal_baseline_visible_count": 8,
            "visible_candidate_count": 77,
            "retained_upstream_lead_count": 102,
            "unexplained_drop_count": 0,
        },
        "false_negatives": [{"path_reason": "not_generated"}],
    }


def _quality_rows():
    rows = []
    for index, candidate_id in enumerate(sorted(QUALITY_CANDIDATE_IDS)):
        rows.append(
            {
                "candidate_id": candidate_id,
                "product_acceptance_status": "product_candidate" if index < 3 else "review_required",
                "evidence_refs": [f"source-{index}"],
            }
        )
    return rows


def _signal_candidates():
    return [{"candidate_id": candidate_id} for candidate_id in sorted(QUALITY_CANDIDATE_IDS)]


def _trace(run_id: str):
    return {
        "run_id": run_id,
        "traces": [
            {
                "phase": "planning",
                "node_name": "build_search_plan",
                "trace_type": "pipeline_input",
            },
            {
                "phase": "finalization",
                "node_name": "shape_artifact",
                "trace_type": "pipeline_output",
            },
        ],
    }


def _signal_metrics(*, incremental: bool):
    return {
        "candidate_count": 6,
        "accepted_candidate_count": 3,
        "review_candidate_count": 3,
        "signal_rule_count": 2,
        "candidate_signal_pair_count": 12,
        "negative_control_false_positive_count": 0,
        "receipt_gap_count": 0,
        "orphan_decisions": 0,
        "cross_entity_known_task_count": 0,
        "identity_confirmed_signal_count": 0,
        "rejected_observed_count": 0,
        "false_not_observed_count": 0,
        "zero_score_observed_count": 0,
        "sources_without_capability_count": 0,
        "retrieved_at_as_fresh_count": 0,
        "out_of_window_confirmed_count": 0,
        "unretried_transport_error_count": 0,
        "unreasoned_retained_item_count": 0,
        "incremental_window_count": 12 if incremental else 0,
        "previous_source_key_count": 24 if incremental else 0,
        "republished_previous_source_count": 0,
        "failed_watermark_advances": 0,
    }
