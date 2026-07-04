"""Search expansion diagnostic projections for candidate discovery."""

from __future__ import annotations

from typing import Any

from power_web_os.application.live_radar_universe import dict_list


def _results_by_target(value: object) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for item in dict_list(value):
        target_id = str(item.get("target_id") or "unclassified")
        result.setdefault(target_id, []).append(item)
    return result

def _results_by_target_type(value: object) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for item in dict_list(value):
        target_type = str(item.get("target_type") or "unknown")
        result.setdefault(target_type, []).append(item)
    return result

def _search_expansion_execution_summary(provider_metadata: dict[str, Any]) -> dict[str, Any]:
    targets = dict_list(provider_metadata.get("expansion_target_queue"))
    variants = dict_list(provider_metadata.get("search_expansion_query_variants"))
    results = dict_list(provider_metadata.get("search_expansion_results"))
    not_searched = dict_list(provider_metadata.get("targets_not_searched"))
    selection_diagnostics = dict_list(provider_metadata.get("search_expansion_selection_diagnostics"))
    executed = [item for item in results if _is_executed_expansion_result(item)]
    source_found = [item for item in executed if int(item.get("source_count") or 0) > 0]
    projected = [item for item in source_found if int(item.get("candidate_observation_count") or 0) > 0]
    selected_ids = {str(item.get("target_id") or "") for item in variants if str(item.get("target_id") or "")}
    attempted_ids = {str(item.get("target_id") or "") for item in results if str(item.get("target_id") or "")}
    executed_ids = {str(item.get("target_id") or "") for item in executed if str(item.get("target_id") or "")}
    source_found_ids = {str(item.get("target_id") or "") for item in source_found if str(item.get("target_id") or "")}
    projected_ids = {str(item.get("target_id") or "") for item in projected if str(item.get("target_id") or "")}
    return {
        "generated_count": len(targets),
        "selected_count": len(selected_ids),
        "attempted_count": len(attempted_ids),
        "executed_count": len(executed_ids),
        "source_found_count": len(source_found_ids),
        "projected_count": len(projected_ids),
        "not_searched_count": len(not_searched),
        "not_executed_global_budget_limited_count": sum(
            1 for item in not_searched if str(item.get("not_searched_reason") or "") == "not_executed_global_budget_limited"
        ),
        "not_executed_reserve_limited_count": sum(
            1 for item in not_searched if str(item.get("not_searched_reason") or "") == "not_executed_reserve_limited"
        ),
        "by_target_type": _expansion_funnel_by_target_type(targets, variants, results, not_searched),
    }

def _search_expansion_target_coverage(provider_metadata: dict[str, Any]) -> list[dict[str, Any]]:
    targets = dict_list(provider_metadata.get("expansion_target_queue"))
    variants = dict_list(provider_metadata.get("search_expansion_query_variants"))
    results = dict_list(provider_metadata.get("search_expansion_results"))
    not_searched = dict_list(provider_metadata.get("targets_not_searched"))
    selected_ids = {str(item.get("target_id") or "") for item in variants if str(item.get("target_id") or "")}
    result_by_target: dict[str, list[dict[str, Any]]] = {}
    for item in results:
        target_id = str(item.get("target_id") or "")
        if target_id:
            result_by_target.setdefault(target_id, []).append(item)
    not_searched_by_target: dict[str, list[dict[str, Any]]] = {}
    for item in not_searched:
        target_id = str(item.get("target_id") or "")
        if target_id:
            not_searched_by_target.setdefault(target_id, []).append(item)
    coverage: list[dict[str, Any]] = []
    seen: set[str] = set()
    for target in targets:
        target_id = str(target.get("target_id") or "")
        if not target_id or target_id in seen:
            continue
        seen.add(target_id)
        target_results = result_by_target.get(target_id, [])
        executed = [item for item in target_results if _is_executed_expansion_result(item)]
        source_found = [item for item in executed if int(item.get("source_count") or 0) > 0]
        projected = [item for item in executed if int(item.get("candidate_observation_count") or 0) > 0]
        skipped = not_searched_by_target.get(target_id, [])
        state = "generated"
        reason = ""
        if projected:
            state = "projected"
        elif source_found:
            state = "source_found"
        elif executed:
            state = "executed_no_support"
        elif target_results:
            state = "not_executed"
            reason = str(target_results[-1].get("not_searched_reason") or "")
        elif skipped:
            state = "not_selected" if target_id not in selected_ids else "not_admitted"
            reason = str(skipped[-1].get("not_searched_reason") or skipped[-1].get("reason") or "")
        elif target_id in selected_ids:
            state = "selected"
        coverage.append({
            "target_id": target_id,
            "target_label": target.get("target_label"),
            "target_type": target.get("target_type"),
            "target_origin": target.get("target_origin"),
            "completion_rank_reason": target.get("completion_rank_reason"),
            "deprioritized_reason": target.get("deprioritized_reason"),
            "uncovered_baseline_target": bool(target.get("uncovered_baseline_target")),
            "coverage_state": state,
            "not_searched_reason": reason,
            "selected": target_id in selected_ids,
            "executed": bool(executed),
            "source_found": bool(source_found),
            "projected": bool(projected),
        })
    return coverage

def _target_probe_guarantees(*, provider_metadata: dict[str, Any], radar: dict[str, Any]) -> dict[str, Any]:
    task_context = radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}
    minimums = task_context.get("benchmark_target_probe_minimums")
    if not isinstance(minimums, dict) or not task_context.get("benchmark_profile"):
        return {"summary": {}, "failures": []}
    targets = dict_list(provider_metadata.get("expansion_target_queue"))
    variants = dict_list(provider_metadata.get("search_expansion_query_variants"))
    results = dict_list(provider_metadata.get("search_expansion_results"))
    not_searched = dict_list(provider_metadata.get("targets_not_searched"))
    selection_diagnostics = dict_list(provider_metadata.get("search_expansion_selection_diagnostics"))
    executed = [item for item in results if _is_executed_expansion_result(item)]
    summary: dict[str, Any] = {
        "required_target_probe_minimums": _int_minimums(minimums),
        "by_target_type": {},
        "target_probe_minimums_satisfied": True,
    }
    failures: list[dict[str, Any]] = []
    for target_type, required in _int_minimums(minimums).items():
        generated = [item for item in targets if str(item.get("target_type") or "") == target_type]
        selected = [item for item in variants if str(item.get("target_type") or "") == target_type]
        executed_items = [item for item in executed if str(item.get("target_type") or "") == target_type]
        not_searched_items = [item for item in not_searched if str(item.get("target_type") or "") == target_type]
        satisfied = len(executed_items) >= required
        summary["by_target_type"][target_type] = {
            "required": required,
            "generated_count": len(generated),
            "selected_count": len(selected),
            "executed_count": len(executed_items),
            "not_searched_count": len(not_searched_items),
            "satisfied": satisfied,
            "not_searched_reasons": _count_by_reason(not_searched_items),
        }
        if not satisfied:
            summary["target_probe_minimums_satisfied"] = False
            failures.append({
                "target_type": target_type,
                "required": required,
                "executed_count": len(executed_items),
                "generated_count": len(generated),
                "selected_count": len(selected),
                "reason": _target_probe_failure_reason(
                    generated,
                    selected,
                    not_searched_items,
                    selection_diagnostics=[
                        item for item in selection_diagnostics if str(item.get("target_type") or "") == target_type
                    ],
                ),
                "not_searched_reasons": _count_by_reason(not_searched_items),
            })
    return {"summary": summary, "failures": failures}

def _search_expansion_variant_cap(*, run_profile: str, radar: dict[str, Any]) -> int:
    base_cap = 4 if run_profile == "smoke" else 6
    task_context = radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}
    minimums = task_context.get("benchmark_target_probe_minimums")
    if not isinstance(minimums, dict) or not task_context.get("benchmark_profile"):
        return base_cap
    required_total = 0
    for value in minimums.values():
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            required_total += parsed
    return max(base_cap, required_total)

def _int_minimums(value: dict[Any, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for key, raw in value.items():
        try:
            parsed = int(raw)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            result[str(key)] = parsed
    return result

def _count_by_reason(items: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in items:
        reason = str(item.get("not_searched_reason") or item.get("reason") or "unknown")
        result[reason] = result.get(reason, 0) + 1
    return result

def _target_probe_failure_reason(
    generated: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    not_searched: list[dict[str, Any]],
    *,
    selection_diagnostics: list[dict[str, Any]] | None = None,
) -> str:
    for item in selection_diagnostics or []:
        reason = str(item.get("reason") or "")
        if reason:
            return reason
    reasons = _count_by_reason(not_searched)
    if not generated:
        return "target_not_generated"
    if not selected:
        return "target_not_selected"
    if any("semantic_task_reserve" in reason for reason in reasons):
        return "semantic_task_budget_limited"
    if any(
        "external" in reason
        or "global_budget" in reason
        or "server_tool" in reason
        or "openrouter_recall_expansion" in reason
        for reason in reasons
    ):
        return "external_budget_limited"
    if any("scheduled" in reason for reason in reasons):
        return "scheduled_below_minimum"
    if any("policy" in reason for reason in reasons):
        return "source_policy_limited"
    if reasons:
        return next(iter(reasons))
    return "executed_below_minimum"

def _expansion_funnel_by_target_type(
    targets: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    results: list[dict[str, Any]],
    not_searched: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    target_types = sorted({
        str(item.get("target_type") or "unknown")
        for item in [*targets, *variants, *results, *not_searched]
    })
    summary: dict[str, dict[str, int]] = {}
    for target_type in target_types:
        type_targets = [item for item in targets if str(item.get("target_type") or "unknown") == target_type]
        type_variants = [item for item in variants if str(item.get("target_type") or "unknown") == target_type]
        type_results = [item for item in results if str(item.get("target_type") or "unknown") == target_type]
        type_not_searched = [item for item in not_searched if str(item.get("target_type") or "unknown") == target_type]
        type_executed = [item for item in type_results if _is_executed_expansion_result(item)]
        summary[target_type] = {
            "generated": len({str(item.get("target_id") or "") for item in type_targets if str(item.get("target_id") or "")}),
            "selected": len({str(item.get("target_id") or "") for item in type_variants if str(item.get("target_id") or "")}),
            "attempted": len({str(item.get("target_id") or "") for item in type_results if str(item.get("target_id") or "")}),
            "executed": len({str(item.get("target_id") or "") for item in type_executed if str(item.get("target_id") or "")}),
            "source_found": len({
                str(item.get("target_id") or "")
                for item in type_executed
                if str(item.get("target_id") or "") and int(item.get("source_count") or 0) > 0
            }),
            "projected": len({
                str(item.get("target_id") or "")
                for item in type_executed
                if str(item.get("target_id") or "") and int(item.get("candidate_observation_count") or 0) > 0
            }),
            "not_searched": len(type_not_searched),
        }
    return summary

def _is_executed_expansion_result(item: dict[str, Any]) -> bool:
    status = str(item.get("execution_status") or "executed_source_found")
    return status.startswith("executed")
