"""Small metadata helpers for candidate-discovery finalization."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.universe import candidate_name, dict_list
from power_web_os.application.radar.candidate_discovery.contracts import LiveRadarPipelineEvent
from power_web_os.application.radar.candidate_discovery.execution.expansion_diagnostics import _is_executed_expansion_result


def _apply_smoke_candidate_promotion_cap(
    *,
    candidates: list[Any],
    observations: list[dict[str, Any]],
    smoke_candidate_limit: int | None,
) -> tuple[list[Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if smoke_candidate_limit is None or smoke_candidate_limit <= 0 or len(candidates) <= smoke_candidate_limit:
        return candidates, observations, [], {
            "smoke_candidate_cap": smoke_candidate_limit,
            "promoted_candidate_count": len(candidates),
            "diagnostic_candidate_count": 0,
        }

    promoted = candidates[:smoke_candidate_limit]
    overflow = candidates[smoke_candidate_limit:]
    promoted_names = {candidate.legal_name.lower() for candidate in promoted if getattr(candidate, "legal_name", "")}
    filtered_observations = [
        observation
        for observation in observations
        if not candidate_name(observation) or candidate_name(observation).lower() in promoted_names
    ]
    overflow_gaps = [
        {
            "legal_name": candidate.legal_name,
            "origin_task_id": "smoke_candidate_cap",
            "status": "gap",
            "reason": "smoke_candidate_cap_exceeded",
            "review_flags": ["smoke_candidate_cap_exceeded"],
            "entity_type": "legal_entity",
        }
        for candidate in overflow
        if getattr(candidate, "legal_name", "")
    ]
    return promoted, filtered_observations, overflow_gaps, {
        "smoke_candidate_cap": smoke_candidate_limit,
        "promoted_candidate_count": len(promoted),
        "diagnostic_candidate_count": len(overflow_gaps),
    }


def _budget_metadata(context: Any, state: Any) -> dict[str, Any]:
    metadata = {
        "budget_settings": {
            "max_total_web_tasks_per_run": context.budget_settings.max_total_tasks_per_run,
            "max_discovery_tasks_per_rule": context.budget_settings.max_discovery_tasks_per_rule,
            "max_gate_tasks_per_candidate_rule": context.budget_settings.max_gate_tasks_per_candidate_rule,
            "max_signal_tasks_per_candidate_signal": context.budget_settings.max_signal_tasks_per_candidate_signal,
            "compatibility_max_web_tasks_per_subject": (
                context.budget_settings.compatibility_max_web_tasks_per_subject
            ),
        },
        "budget_counters": {
            "total": context.task_budget.total_count,
            "by_key": dict(context.task_budget.counts),
            "semantic_reserves": dict(context.task_budget.semantic_reserve_counts),
        },
        "budget_exhaustion_events": list(context.task_budget.exhaustion_events),
        "source_verification_cache_stats": context.verification_cache.to_metadata(),
        "web_task_counts_by_subject": context.task_budget.counts,
        "web_task_budget_warnings": context.task_budget.warnings,
        "useful_result_retry_records": state.useful_result_retry_records,
        "useful_result_warnings": state.useful_result_warnings,
        "min_useful_sources_per_discovery_task": context.useful_budget.min_sources,
        "min_candidates_per_discovery_task": context.useful_budget.min_candidates,
        "max_discovery_retries_per_task": context.useful_budget.max_retries,
    }
    metadata.update(context.task_budget.to_metadata())
    metadata.update(context.verification_cache.to_metadata())
    metadata.update(context.external_budget.to_metadata())
    return metadata


def _benchmark_recall_target_summary(provider_metadata: dict[str, Any]) -> dict[str, Any]:
    targets = dict_list(provider_metadata.get("expansion_target_queue"))
    if not targets:
        return {}
    searched_ids = {
        str(item.get("target_id") or "")
        for item in dict_list(provider_metadata.get("search_expansion_results"))
        if _is_executed_expansion_result(item)
    }
    not_searched = dict_list(provider_metadata.get("targets_not_searched"))
    return {
        "target_count": len(targets),
        "searched_target_count": len([target for target in targets if str(target.get("target_id") or "") in searched_ids]),
        "not_searched_target_count": len(not_searched),
        "by_target_type": _target_count_by_type(targets),
        "searched_by_target_type": _searched_targets_by_type(targets, searched_ids),
        "not_searched_by_target_type": _target_count_by_type(not_searched),
    }


def _legal_subsidiary_completion_summary(provider_metadata: dict[str, Any]) -> dict[str, Any]:
    target_type = "known_subsidiary_or_legal_entity_target"
    targets = _typed_items(provider_metadata, "expansion_target_queue", target_type)
    variants = _typed_items(provider_metadata, "search_expansion_query_variants", target_type)
    results = _typed_items(provider_metadata, "search_expansion_results", target_type)
    not_searched = _typed_items(provider_metadata, "targets_not_searched", target_type)
    diagnostics = _typed_items(provider_metadata, "search_expansion_selection_diagnostics", target_type)
    if not (targets or variants or results or not_searched or diagnostics):
        return {}
    executed = [item for item in results if _is_executed_expansion_result(item)]
    return {
        "target_type": target_type,
        "generated_count": len(targets),
        "selected_variant_count": len(_target_ids(variants)),
        "executed_count": len(_target_ids(executed)),
        "not_searched_count": len(_target_ids(not_searched)),
        "selection_diagnostic_count": len(diagnostics),
        "not_searched_by_reason": _count_by_reason(not_searched),
        "selection_diagnostics_by_reason": _count_by_reason(diagnostics),
    }


def _external_budget_events(exhaustion_events: object) -> list[LiveRadarPipelineEvent]:
    return [
        LiveRadarPipelineEvent(
            event_type="external_budget_exhausted",
            phase="validation",
            actor="application",
            node_name="external_call_budget",
            visibility="operator",
            summary=str(item.get("message") or "External call budget exhausted."),
            payload=dict(item),
        )
        for item in dict_list(exhaustion_events)
    ]


def _typed_items(provider_metadata: dict[str, Any], key: str, target_type: str) -> list[dict[str, Any]]:
    return [
        item for item in dict_list(provider_metadata.get(key))
        if str(item.get("target_type") or "") == target_type
    ]


def _target_ids(items: list[dict[str, Any]]) -> set[str]:
    return {str(item.get("target_id") or "") for item in items if str(item.get("target_id") or "")}


def _target_count_by_type(targets: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for target in targets:
        target_type = str(target.get("target_type") or "unknown")
        result[target_type] = result.get(target_type, 0) + 1
    return result


def _searched_targets_by_type(targets: list[dict[str, Any]], searched_ids: set[str]) -> dict[str, int]:
    searched: dict[str, int] = {}
    for target in targets:
        target_id = str(target.get("target_id") or "")
        if not target_id or target_id not in searched_ids:
            continue
        target_type = str(target.get("target_type") or "unknown")
        searched[target_type] = searched.get(target_type, 0) + 1
    return searched


def _count_by_reason(items: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in items:
        reason = str(item.get("not_searched_reason") or item.get("reason") or "unknown")
        result[reason] = result.get(reason, 0) + 1
    return result
