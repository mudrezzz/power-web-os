"""Payload helpers for targeted Radar search expansion execution."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import LiveRadarPipelineEvent, RadarExecutionTask
from power_web_os.application.radar.candidate_discovery.universe import dict_list


def expansion_action_payload(
    checkpoint_id: str,
    phase: str,
    attempt: int,
    base_task: RadarExecutionTask,
    tasks: list[RadarExecutionTask],
    executed_count: int,
    skipped_count: int,
    expansion_plan: Any,
    attempted_count: int = 0,
) -> dict[str, Any]:
    return {
        "checkpoint_id": checkpoint_id,
        "phase": phase,
        "action": "expand_sources",
        "attempt": attempt,
        "task_id": base_task.task_id,
        "source_scope": "targeted_expansion",
        "source_ids": sorted({source_id for task in tasks for source_id in task.source_ids}),
        "outcome": "executed" if executed_count else "not_executed",
        "message": f"Executed {executed_count} targeted expansion tasks; skipped {skipped_count}.",
        "budget_key": "budget_reserve",
        "target_count": len(expansion_plan.targets),
        "variant_count": len(expansion_plan.variants),
        "executed_task_count": executed_count,
        "skipped_task_count": skipped_count,
        "attempted_task_count": attempted_count,
    }


def with_expansion_plan_metadata(metadata: dict[str, Any], *, radar: dict[str, Any], expansion_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        **metadata,
        "expansion_target_queue": [*dict_list(metadata.get("expansion_target_queue")), *expansion_plan.get("targets", [])],
        "expansion_target_summary_by_type": merge_int_dicts(
            metadata.get("expansion_target_summary_by_type"),
            expansion_plan.get("targets_by_type"),
        ),
        "search_expansion_query_variants_by_target": {
            **(metadata.get("search_expansion_query_variants_by_target") if isinstance(metadata.get("search_expansion_query_variants_by_target"), dict) else {}),
            **expansion_plan.get("variants_by_target", {}),
        },
        "search_expansion_query_variants_by_target_type": {
            **(metadata.get("search_expansion_query_variants_by_target_type") if isinstance(metadata.get("search_expansion_query_variants_by_target_type"), dict) else {}),
            **expansion_plan.get("variants_by_target_type", {}),
        },
        "targets_not_searched": dedupe_target_records([
            *dict_list(metadata.get("targets_not_searched")),
            *dict_list(expansion_plan.get("targets_not_selected")),
        ]),
        "search_expansion_selection_summary": merge_selection_summary(
            metadata.get("search_expansion_selection_summary"),
            expansion_plan.get("selection_summary"),
        ),
        "search_expansion_selection_diagnostics": [
            *dict_list(metadata.get("search_expansion_selection_diagnostics")),
            *dict_list(expansion_plan.get("selection_diagnostics")),
        ],
        "source_capability_strategy_summary": source_capability_strategy_summary(radar=radar, expansion_plan=expansion_plan),
        "search_expansion_query_variants": [
            *dict_list(metadata.get("search_expansion_query_variants")),
            *expansion_plan.get("variants", []),
        ],
    }


def source_capability_strategy_summary(*, radar: dict[str, Any], expansion_plan: dict[str, Any]) -> dict[str, Any]:
    policy = radar.get("global_search_policy") if isinstance(radar.get("global_search_policy"), dict) else {}
    configured_sources = [
        str(item.get("source_id") or item.get("reference") or "")
        for item in dict_list(policy.get("sources"))
        if str(item.get("source_id") or item.get("reference") or "").strip()
    ]
    variants = dict_list(expansion_plan.get("variants"))
    return {
        "configured_source_count": len(configured_sources),
        "target_count": len(dict_list(expansion_plan.get("targets"))),
        "variant_count": len(variants),
        "official_probe_count": sum(1 for item in variants if item.get("budget_reserve_key") == "official_coverage_probe"),
        "open_web_probe_count": sum(1 for item in variants if item.get("budget_reserve_key") == "open_web_coverage_probe"),
        "production_site_probe_count": sum(1 for item in variants if item.get("budget_reserve_key") == "production_site_coverage_probe"),
        "target_count_by_type": dict(expansion_plan.get("targets_by_type") or {}),
        "variant_count_by_target_type": {
            key: len(value)
            for key, value in (
                expansion_plan.get("variants_by_target_type")
                if isinstance(expansion_plan.get("variants_by_target_type"), dict)
                else {}
            ).items()
            if isinstance(value, list)
        },
        "uses_profile_driven_sources": bool(configured_sources and variants),
    }


def merge_int_dicts(left: object, right: object) -> dict[str, int]:
    result: dict[str, int] = {}
    for source in (left, right):
        if not isinstance(source, dict):
            continue
        for key, value in source.items():
            try:
                result[str(key)] = result.get(str(key), 0) + int(value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
    return result


def merge_selection_summary(left: object, right: object) -> dict[str, Any]:
    result: dict[str, Any] = dict(left) if isinstance(left, dict) else {}
    if not isinstance(right, dict):
        return result
    for key in ("selected_guaranteed_count", "selected_completion_count", "selected_optional_count", "diagnostic_count"):
        try:
            result[key] = int(result.get(key) or 0) + int(right.get(key) or 0)
        except (TypeError, ValueError):
            continue
    try:
        result["completion_target_limit"] = max(
            int(result.get("completion_target_limit") or 0),
            int(right.get("completion_target_limit") or 0),
        )
    except (TypeError, ValueError):
        pass
    effective = right.get("effective_max_variants")
    if effective is not None:
        result["effective_max_variants"] = max(int(result.get("effective_max_variants") or 0), int(effective))
    result["missing_minimums"] = [
        *dict_list(result.get("missing_minimums")),
        *dict_list(right.get("missing_minimums")),
    ]
    return result


def dedupe_target_records(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        key = (str(item.get("target_id") or ""), str(item.get("task_id") or ""), str(item.get("not_searched_reason") or ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def skipped_payload(
    task: RadarExecutionTask,
    variant: Any,
    budget_decision: dict[str, Any],
    checkpoint_id: str,
    *,
    schedule_role: str = "",
    execution_status: str = "not_searched",
    not_searched_reason: str = "",
) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "query": task.query,
        "source_ids": list(task.source_ids),
        "target_id": variant.target_id,
        "target_type": variant.target_type,
        "budget_reserve_key": variant.budget_reserve_key,
        "schedule_role": schedule_role,
        "execution_status": execution_status,
        "not_searched_reason": not_searched_reason or budget_decision.get("reason") or "budget_reserve_exhausted",
        "budget_decision": budget_decision,
        "checkpoint_id": checkpoint_id,
    }


def executed_payload(
    task: RadarExecutionTask,
    variant: Any,
    budget_decision: dict[str, Any],
    checkpoint_id: str,
    result: Any,
    *,
    schedule_role: str = "",
) -> dict[str, Any]:
    status, reason = execution_status(result=result, budget_decision=budget_decision)
    return {
        "task_id": task.task_id,
        "query": task.query,
        "source_ids": list(task.source_ids),
        "target_id": variant.target_id,
        "target_type": variant.target_type,
        "budget_reserve_key": variant.budget_reserve_key,
        "schedule_role": schedule_role,
        "execution_status": status,
        "not_searched_reason": reason if status == "not_executed" else "",
        "source_count": len(result.sources),
        "candidate_observation_count": len(result.candidate_observations),
        "budget_decision": budget_decision,
        "checkpoint_id": checkpoint_id,
    }


def not_executed_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "execution_status": "not_searched",
        "not_searched_reason": payload.get("not_searched_reason") or "not_executed_global_budget_limited",
    }


def execution_status(*, result: Any, budget_decision: dict[str, Any]) -> tuple[str, str]:
    if isinstance(budget_decision, dict) and budget_decision.get("accepted") is False:
        return "not_executed", budget_limited_reason(budget_decision)
    if len(result.sources) > 0:
        return "executed_source_found", ""
    return "executed_no_support", ""


def budget_limited_reason(budget_decision: dict[str, Any]) -> str:
    reason = str(budget_decision.get("reason") or "")
    if str(budget_decision.get("kind") or "") == "budget_reserve":
        return "not_executed_reserve_limited"
    if reason == "semantic_task_reserve_exhausted":
        return "semantic_task_budget_limited"
    if bool(budget_decision.get("used_semantic_reserve")):
        return ""
    return "not_executed_global_budget_limited"


def preflight_budget_limited_reason(budget_decision: dict[str, Any]) -> str:
    kind = str(budget_decision.get("kind") or "")
    if kind == "openrouter":
        return "external_total_budget_limited"
    if kind == "openrouter_recall_expansion":
        return "openrouter_recall_expansion_budget_limited"
    if kind == "openrouter_server_tool_web_search":
        return "server_tool_budget_limited"
    return "scheduled_but_budget_not_reserved"


def benchmark_target_probe_minimums(radar: dict[str, Any]) -> dict[str, int]:
    task_context = radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}
    raw = task_context.get("benchmark_target_probe_minimums")
    if not isinstance(raw, dict) or not task_context.get("benchmark_profile"):
        return {}
    result: dict[str, int] = {}
    for key, value in raw.items():
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            result[str(key)] = parsed
    return result


def skipped_event(task: RadarExecutionTask, message: str, payload: dict[str, Any]) -> LiveRadarPipelineEvent:
    return LiveRadarPipelineEvent(
        event_type="search_expansion_skipped_budget_reserve",
        phase="collection",
        actor="application",
        node_name="checkpoint_search_expansion",
        visibility="operator",
        summary=f"Skipped recall expansion task {task.task_id}: {message}",
        payload=payload,
    )


def executed_event(task: RadarExecutionTask, variant: Any, result: Any) -> LiveRadarPipelineEvent:
    return LiveRadarPipelineEvent(
        event_type="search_expansion_executed",
        phase="collection",
        actor="application",
        node_name="checkpoint_search_expansion",
        visibility="operator",
        summary=f"Executed checkpoint recall expansion task {task.task_id}.",
        payload={
            "task_id": task.task_id,
            "query": task.query,
            "source_ids": list(task.source_ids),
            "target_id": variant.target_id,
            "target_type": variant.target_type,
            "budget_reserve_key": variant.budget_reserve_key,
            "source_count": len(result.sources),
            "candidate_observation_count": len(result.candidate_observations),
        },
        source_refs=[source.evidence_ref for source in result.sources if source.evidence_ref],
    )


def has_extraction_issues(metadata: dict[str, Any]) -> bool:
    for result in metadata.get("extraction_validation_results", []):
        if isinstance(result, dict) and str(result.get("state")) in {"extraction_schema_invalid", "evidence_linking_failed"}:
            return True
    for issue in metadata.get("extraction_validation_issues", []):
        if isinstance(issue, dict) and str(issue.get("severity")) == "error":
            return True
    return False


def without_extraction_issues(metadata: dict[str, Any]) -> dict[str, Any]:
    return {**metadata, "extraction_validation_results": [], "extraction_validation_issues": [], "extraction_repair_results": []}
