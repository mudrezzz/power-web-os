"""Blind benchmark context, closeout, and public-surface quality helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from power_web_os.radar_evaluation_matching import normalize_name


def benchmark_context(*, run: dict[str, Any], dossier: dict[str, Any]) -> dict[str, Any]:
    run_metadata = _dict(run.get("run_metadata"))
    task_context = _dict(run_metadata.get("task_context"))
    profile = str(dossier.get("benchmark_profile") or task_context.get("benchmark_profile") or run.get("benchmark_profile") or "")
    mode = str(dossier.get("benchmark_mode") or task_context.get("benchmark_mode") or run.get("benchmark_mode") or "")
    if not mode and profile:
        mode = "blind" if profile == "blind_benchmark" else "guided"
    task_hints = _list(task_context.get("benchmark_target_hints"))
    hint_count = _int(dossier.get("benchmark_target_hint_count")) or len(task_hints)
    hints_used = dossier.get("benchmark_hints_used")
    if not isinstance(hints_used, bool):
        context_flag = task_context.get("benchmark_hints_used")
        hints_used = bool(context_flag) if isinstance(context_flag, bool) else hint_count > 0
    return {
        "benchmark_profile": profile,
        "benchmark_mode": mode,
        "benchmark_hints_used": hints_used,
        "benchmark_target_hint_count": hint_count,
    }


def blind_benchmark_closeout_summary(
    *,
    benchmark_context: dict[str, Any],
    benchmark_target_funnel: list[dict[str, Any]],
    metrics: dict[str, Any],
    false_negatives: list[dict[str, Any]],
) -> dict[str, Any]:
    target_results = [{**item, "closeout_path_reason": _closeout_path_reason(item)} for item in benchmark_target_funnel]
    missing_targets = [item for item in target_results if not item.get("projected")]
    top_miss_reasons = _count_by(str(item.get("closeout_path_reason") or "unknown") for item in missing_targets)
    strict_recall = metrics.get("strict_recall")
    return {
        "run_mode": benchmark_context.get("benchmark_mode"),
        "hints_used": benchmark_context.get("benchmark_hints_used"),
        "baseline_target_count": len(target_results),
        "strict_recall": strict_recall,
        "visible_recall": metrics.get("visible_recall"),
        "accepted_product_candidate_count": metrics.get("accepted_product_candidate_count"),
        "review_needed_candidate_count": metrics.get("review_needed_candidate_count"),
        "duplicate_candidate_id_count": metrics.get("duplicate_candidate_id_count"),
        "empty_provenance_candidate_count": metrics.get("empty_provenance_candidate_count"),
        "false_negative_count": len(false_negatives),
        "false_negative_ids": [str(item.get("baseline_id") or "") for item in false_negatives],
        "top_miss_reasons": top_miss_reasons,
        "requires_followup_rca": strict_recall == 0 or any(
            str(item.get("closeout_path_reason") or "") in {"unknown", ""} for item in missing_targets
        ),
        "baseline_target_results": target_results,
    }


def public_surface_quality(rows: list[dict[str, Any]]) -> dict[str, int]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    empty_provenance_count = 0
    for item in rows:
        key = str(item.get("candidate_id") or "").strip() or normalize_name(str(item.get("legal_name") or ""))
        if key:
            if key in seen:
                duplicates.add(key)
            seen.add(key)
        if not _has_public_provenance(item):
            empty_provenance_count += 1
    return {
        "duplicate_candidate_id_count": len(duplicates),
        "empty_provenance_candidate_count": empty_provenance_count,
    }


def _closeout_path_reason(item: dict[str, Any]) -> str:
    if item.get("projected"):
        return "projected"
    reason = str(item.get("path_reason") or "")
    if reason in {"not_generated", "no_executable_query", "not_selected", "not_admitted", "not_executed", "source_not_found", "present_not_projected", "explicitly_rejected"}:
        return reason
    if reason in {"selection_cap_exhausted_for_protected_legal_target", "completion_cap_exhausted", "completion_lane_quota_exhausted", "selector_priority_lost", "completion_not_selected", "expansion_not_selected"}:
        return "not_selected"
    if reason in {"source_found_not_projected", "expansion_source_found_not_projected", "present_not_matched", "projection_type_lost"}:
        return "present_not_projected"
    if reason in {"expansion_searched_no_support", "expansion_searched_not_projected"}:
        return "source_not_found"
    if reason in {"expansion_not_executed", "expansion_global_budget_limited", "external_budget_limited", "expansion_budget_limited", "expansion_reserve_limited", "scheduler_rejected"}:
        return "not_executed"
    if reason == "expansion_source_policy_limited":
        return "not_admitted"
    return "not_generated" if not reason else "not_executed"


def _has_public_provenance(item: dict[str, Any]) -> bool:
    if item.get("source_refs") or item.get("evidence_refs") or item.get("upstream_source_refs"):
        return True
    reason_keys = ("candidate_surface_reason", "public_projection_reason", "upstream_reason", "product_acceptance_reason", "not_candidate_reason")
    return any(str(item.get(key) or "").strip() for key in reason_keys) or bool(item.get("review_flags"))


def _count_by(values: Iterable[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return result


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _int(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0
