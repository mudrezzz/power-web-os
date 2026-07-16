"""Machine validation for Radar root namespace closure and live regression."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from power_web_os.application.radar.validation.signal_monitoring_quality import (
    control_match_summary,
    evaluate_signal_report,
)


class RadarNamespaceClosureValidator:
    """Compare fresh live evidence with accepted Candidate and Signal baselines."""

    def validate(
        self,
        *,
        candidate_baseline_evaluation: dict[str, Any],
        candidate_live_evaluation: dict[str, Any],
        candidate_baseline_trace: dict[str, Any],
        candidate_live_trace: dict[str, Any],
        candidate_live_run: dict[str, Any],
        candidate_live_rows: list[dict[str, Any]],
        signal_baseline_initial: dict[str, Any],
        signal_baseline_incremental: dict[str, Any],
        signal_live_initial: dict[str, Any],
        signal_live_incremental: dict[str, Any],
        signal_controls: dict[str, Any],
        latest_candidate_run_id: str,
        restart_round_trip: dict[str, bool],
    ) -> dict[str, Any]:
        candidate = _candidate_quality(
            candidate_live_evaluation,
            candidate_live_run,
            candidate_live_rows,
            signal_live_initial,
        )
        trace = _trace_comparison(candidate_baseline_trace, candidate_live_trace)
        signal = _signal_quality(
            baseline_initial=signal_baseline_initial,
            baseline_incremental=signal_baseline_incremental,
            live_initial=signal_live_initial,
            live_incremental=signal_live_incremental,
            controls=signal_controls,
            source_candidate_run_id=str(candidate_live_run.get("run_id") or ""),
        )
        requirements = {
            "NS-ROOT-01": True,
            "NS-CAND-01": candidate["quality_pass"],
            "NS-TRACE-01": trace["classification"] != "behavior_regression",
            "NS-SIGNAL-01": signal["initial_pass"],
            "NS-SIGNAL-02": signal["incremental_pass"],
            "NS-LINEAGE-01": signal["lineage_pass"],
            "NS-NO-RERUN-01": latest_candidate_run_id == str(candidate_live_run.get("run_id") or ""),
            "NS-RESTART-01": bool(restart_round_trip) and all(restart_round_trip.values()),
        }
        status = "PASS" if all(requirements.values()) else "FAIL"
        return {
            "schema_version": "radar_namespace_closure_validation.v1",
            "slice_id": "0.7.6.4.19",
            "validation_status": status,
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "run_ids": {
                "candidate_baseline": candidate_baseline_evaluation.get("run_id"),
                "candidate_live": candidate_live_evaluation.get("run_id"),
                "signal_baseline_initial": signal_baseline_initial.get("signal_run_id"),
                "signal_baseline_incremental": signal_baseline_incremental.get("signal_run_id"),
                "signal_live_initial": signal_live_initial.get("signal_run_id"),
                "signal_live_incremental": signal_live_incremental.get("signal_run_id"),
            },
            "requirements": [
                {"requirement_id": key, "status": "PASS" if value else "FAIL"}
                for key, value in requirements.items()
            ],
            "candidate_quality": {
                "accepted_baseline": _candidate_metrics(candidate_baseline_evaluation),
                "fresh_live": candidate,
            },
            "semantic_trace_comparison": trace,
            "signal_quality": signal,
            "restart_round_trip": restart_round_trip,
            "process_retrospective": {
                "behavior_regressions": trace["behavior_regressions"],
                "provider_drift": trace["provider_drift"],
                "roadmap_correction_required": status != "PASS",
                "decision": (
                    "Root namespace closure is proven by fresh live evidence."
                    if status == "PASS"
                    else "Keep slice In Progress; repair and repeat the complete live chain."
                ),
            },
        }

    @staticmethod
    def write(report: dict[str, Any], *, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "validation.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (output_dir / "VALIDATION_REPORT.md").write_text(_markdown_report(report), encoding="utf-8")


def _candidate_quality(
    evaluation: dict[str, Any],
    run: dict[str, Any],
    rows: list[dict[str, Any]],
    signal_report: dict[str, Any],
) -> dict[str, Any]:
    metrics = _candidate_metrics(evaluation)
    context = _dict(evaluation.get("benchmark_context"))
    signal_candidates = _list(signal_report.get("candidates"))
    scope_ids = [str(item.get("candidate_id") or "").strip() for item in signal_candidates]
    scope_ids = [item for item in scope_ids if item]
    unique_scope_ids = set(scope_ids)
    row_by_id = {
        str(row.get("candidate_id") or "").strip(): row
        for row in rows
        if str(row.get("candidate_id") or "").strip()
    }
    required_rows = [row_by_id[candidate_id] for candidate_id in unique_scope_ids if candidate_id in row_by_id]
    accepted = sum(row.get("product_acceptance_status") == "product_candidate" for row in required_rows)
    review = sum(row.get("product_acceptance_status") == "review_required" for row in required_rows)
    missing_provenance = sorted(
        str(row.get("candidate_id") or "")
        for row in required_rows
        if not _candidate_has_provenance(row)
    )
    task_context = _dict(_dict(run.get("run_metadata")).get("task_context"))
    false_negatives = _list(evaluation.get("false_negatives"))
    funnel_reason_by_id = {
        str(item.get("baseline_id") or ""): str(item.get("path_reason") or "").strip()
        for item in _list(evaluation.get("benchmark_target_funnel"))
    }
    checks = {
        "blind_mode": context.get("benchmark_mode") == "blind",
        "hints_disabled": context.get("benchmark_hints_used") is False,
        "strict_recall": float(metrics["strict_recall"] or 0) >= 0.8889,
        "visible_recall": float(metrics["visible_recall"] or 0) >= 0.8889,
        "legal_baseline_visible": int(metrics["legal_baseline_visible_count"] or 0) >= 8,
        "visible_breadth": int(metrics["visible_candidate_count"] or 0) >= 54,
        "retained_breadth": int(metrics["retained_upstream_lead_count"] or 0) >= 72,
        "duplicates": int(metrics["duplicate_candidate_id_count"] or 0) == 0,
        "empty_provenance": int(metrics["empty_provenance_candidate_count"] or 0) == 0,
        "unexplained_drops": int(metrics["unexplained_drop_count"] or 0) == 0,
        "explicit_false_negative_reasons": all(
            str(
                item.get("closeout_path_reason")
                or item.get("path_reason")
                or funnel_reason_by_id.get(str(item.get("baseline_id") or ""), "")
            ).strip()
            for item in false_negatives
        ),
        "quality_scope": (
            len(scope_ids) == 6
            and len(unique_scope_ids) == 6
            and len(required_rows) == 6
            and accepted >= 3
            and review >= 3
            and not missing_provenance
        ),
        "handoff_mode": task_context.get("signal_execution_mode", "handoff") == "handoff",
    }
    return {
        **metrics,
        "required_quality_candidate_count": len(required_rows),
        "required_quality_accepted_count": accepted,
        "required_quality_review_count": review,
        "signal_quality_scope_candidate_ids": sorted(unique_scope_ids),
        "duplicate_signal_quality_candidate_count": len(scope_ids) - len(unique_scope_ids),
        "missing_quality_candidate_ids": sorted(unique_scope_ids - set(row_by_id)),
        "missing_quality_candidate_provenance_ids": missing_provenance,
        "checks": checks,
        "quality_pass": all(checks.values()),
    }


def _candidate_has_provenance(row: dict[str, Any]) -> bool:
    return bool(
        _values(row.get("evidence_refs"))
        or _values(row.get("upstream_source_refs"))
        or _values(row.get("public_provenance"))
    )


def _candidate_metrics(evaluation: dict[str, Any]) -> dict[str, Any]:
    metrics = _dict(evaluation.get("metrics"))
    closeout = _dict(evaluation.get("blind_benchmark_closeout"))
    return {
        "strict_recall": closeout.get("strict_recall", metrics.get("strict_recall")),
        "visible_recall": closeout.get("visible_recall", metrics.get("visible_recall")),
        "legal_baseline_visible_count": metrics.get("legal_baseline_visible_count"),
        "visible_candidate_count": metrics.get("visible_candidate_count"),
        "retained_upstream_lead_count": metrics.get("retained_upstream_lead_count"),
        "duplicate_candidate_id_count": closeout.get("duplicate_candidate_id_count"),
        "empty_provenance_candidate_count": closeout.get("empty_provenance_candidate_count"),
        "unexplained_drop_count": metrics.get("unexplained_drop_count"),
        "false_negative_count": closeout.get("false_negative_count"),
    }


def _trace_comparison(baseline_response: dict[str, Any], live_response: dict[str, Any]) -> dict[str, Any]:
    baseline = _list(baseline_response.get("traces"))
    live = _list(live_response.get("traces"))
    # Provider errors are runtime outcomes, not required structural milestones.
    # Requiring a fresh run to reproduce an old error would invert the regression gate.
    ignored = {"provider_request", "provider_response", "provider_error"}
    baseline_structural = {_trace_key(item) for item in baseline if item.get("trace_type") not in ignored}
    live_structural = {_trace_key(item) for item in live if item.get("trace_type") not in ignored}
    missing = sorted(baseline_structural - live_structural)
    baseline_phases = _ordered_unique(
        str(item.get("phase") or "") for item in baseline if item.get("trace_type") not in ignored
    )
    live_phases = _ordered_unique(
        str(item.get("phase") or "") for item in live if item.get("trace_type") not in ignored
    )
    phase_order_ok = _is_subsequence(baseline_phases, live_phases)
    behavior = [
        *(f"missing_trace:{'|'.join(item)}" for item in missing),
        *(["phase_order_changed"] if not phase_order_ok else []),
        *(["baseline_trace_missing"] if not baseline else []),
        *(["live_trace_missing"] if not live else []),
    ]
    baseline_provider = sum(item.get("trace_type") in ignored for item in baseline)
    live_provider = sum(item.get("trace_type") in ignored for item in live)
    provider_drift = [] if baseline_provider == live_provider else [
        f"provider_trace_count:{baseline_provider}->{live_provider}"
    ]
    return {
        "classification": "behavior_regression" if behavior else (
            "provider_drift" if provider_drift else "expected_runtime_variance"
        ),
        "baseline_trace_count": len(baseline),
        "live_trace_count": len(live),
        "baseline_phases": baseline_phases,
        "live_phases": live_phases,
        "phase_order_ok": phase_order_ok,
        "behavior_regressions": behavior,
        "provider_drift": provider_drift,
    }


def _signal_quality(
    *,
    baseline_initial: dict[str, Any],
    baseline_incremental: dict[str, Any],
    live_initial: dict[str, Any],
    live_incremental: dict[str, Any],
    controls: dict[str, Any],
    source_candidate_run_id: str,
) -> dict[str, Any]:
    negative_controls = _list(controls.get("negative_controls"))
    positive_controls = _list(controls.get("positive_controls"))
    unknown_controls = _list(controls.get("unknown_date_controls"))
    initial = evaluate_signal_report(live_initial, negative_controls=negative_controls)
    incremental = evaluate_signal_report(live_incremental, negative_controls=negative_controls)
    positive = control_match_summary(live_initial, positive_controls, expected="confirmed")
    negative = control_match_summary(live_initial, negative_controls, expected="negative")
    unknown = control_match_summary(live_initial, unknown_controls, expected="unknown")
    budget_limited = sum(
        item.get("status") == "not_scheduled_budget_limited"
        for item in _list(live_initial.get("source_lane_ledger"))
    )
    initial_checks = {
        "candidate_count": initial["candidate_count"] == 6,
        "accepted_scope": initial["accepted_candidate_count"] >= 3,
        "review_scope": initial["review_candidate_count"] >= 3,
        "criterion_count": initial["signal_rule_count"] == 2,
        "pair_count": initial["candidate_signal_pair_count"] == 12,
        "positive_controls": positive["matched"] == len(positive_controls) == 4,
        "negative_controls": negative["matched"] >= 2,
        "false_positive_controls": initial["negative_control_false_positive_count"] == 0,
        "unknown_date_review": unknown["matched"] >= 1,
        "receipt_gaps": initial["receipt_gap_count"] == 0,
        "orphan_decisions": initial["orphan_decisions"] == 0,
        "cross_entity_known_tasks": initial["cross_entity_known_task_count"] == 0,
        "identity_sources_not_confirmed": initial["identity_confirmed_signal_count"] == 0,
        "rejected_evidence_not_observed": initial["rejected_observed_count"] == 0,
        "false_not_observed": initial["false_not_observed_count"] == 0,
        "zero_score_observed": initial["zero_score_observed_count"] == 0,
        "source_capabilities": initial["sources_without_capability_count"] == 0,
        "retrieval_time_not_freshness": initial["retrieved_at_as_fresh_count"] == 0,
        "out_of_window_not_confirmed": initial["out_of_window_confirmed_count"] == 0,
        "transport_errors_retried": initial["unretried_transport_error_count"] == 0,
        "retained_items_reasoned": initial["unreasoned_retained_item_count"] == 0,
        "required_lanes_not_budget_limited": budget_limited == 0,
    }
    incremental_checks = {
        "incremental_windows": incremental["incremental_window_count"] > 0,
        "previous_source_keys": incremental["previous_source_key_count"] > 0,
        "no_republished_sources": incremental["republished_previous_source_count"] == 0,
        "failed_watermarks_static": incremental["failed_watermark_advances"] == 0,
        "receipt_gaps": incremental["receipt_gap_count"] == 0,
        "orphan_decisions": incremental["orphan_decisions"] == 0,
        "false_not_observed": incremental["false_not_observed_count"] == 0,
    }
    lineage = {
        "initial_source": live_initial.get("source_candidate_run_id") == source_candidate_run_id,
        "incremental_source": live_incremental.get("source_candidate_run_id") == source_candidate_run_id,
        "initial_pipeline": live_initial.get("pipeline_id") == "signal_monitoring",
        "incremental_pipeline": live_incremental.get("pipeline_id") == "signal_monitoring",
    }
    return {
        "accepted_baseline_initial": evaluate_signal_report(
            baseline_initial, negative_controls=negative_controls
        ),
        "accepted_baseline_incremental": evaluate_signal_report(
            baseline_incremental, negative_controls=negative_controls
        ),
        "fresh_initial": initial,
        "fresh_incremental": incremental,
        "positive_controls": positive,
        "negative_controls": negative,
        "unknown_date_controls": unknown,
        "initial_checks": initial_checks,
        "incremental_checks": incremental_checks,
        "lineage_checks": lineage,
        "initial_pass": all(initial_checks.values()),
        "incremental_pass": all(incremental_checks.values()),
        "lineage_pass": all(lineage.values()),
    }


def _markdown_report(report: dict[str, Any]) -> str:
    requirements = "\n".join(
        f"| {item['requirement_id']} | {item['status']} |"
        for item in _list(report.get("requirements"))
    )
    run_ids = _dict(report.get("run_ids"))
    candidate = _dict(_dict(report.get("candidate_quality")).get("fresh_live"))
    trace = _dict(report.get("semantic_trace_comparison"))
    signal = _dict(report.get("signal_quality"))
    runs = "\n".join(f"- {key}: {value}" for key, value in run_ids.items())
    return f"""# Radar Namespace Closure Validation

Validation status: **{report.get('validation_status')}**

## Runs

{runs}

## Requirements

| Requirement | Status |
|---|---|
{requirements}

## Candidate Discovery

- Strict recall: {candidate.get('strict_recall')}
- Visible recall: {candidate.get('visible_recall')}
- Visible candidates: {candidate.get('visible_candidate_count')}
- Retained upstream leads: {candidate.get('retained_upstream_lead_count')}
- Quality scope: {candidate.get('required_quality_candidate_count')} candidates

## Trace Comparison

- Classification: {trace.get('classification')}
- Phase order preserved: {trace.get('phase_order_ok')}
- Behavior regressions: {trace.get('behavior_regressions')}
- Provider drift: {trace.get('provider_drift')}

## Signal Monitoring

- Initial pass: {signal.get('initial_pass')}
- Incremental pass: {signal.get('incremental_pass')}
- Lineage pass: {signal.get('lineage_pass')}
- Positive controls: {_dict(signal.get('positive_controls')).get('matched')}
- Negative controls: {_dict(signal.get('negative_controls')).get('matched')}

## Retrospective

{_dict(report.get('process_retrospective')).get('decision')}
"""


def _trace_key(item: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(item.get("phase") or ""),
        str(item.get("node_name") or ""),
        str(item.get("trace_type") or ""),
    )


def _ordered_unique(values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _is_subsequence(expected: list[str], actual: list[str]) -> bool:
    iterator = iter(actual)
    return all(any(candidate == item for candidate in iterator) for item in expected)


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _values(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []
