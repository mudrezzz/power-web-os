"""Execute target-aware recall expansion tasks under checkpoint control."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from power_web_os.application.live_radar_contracts import (
    LiveRadarPipelineEvent,
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
    WebSearchProvider,
)
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget
from power_web_os.application.live_radar_external_budget import (
    RadarExternalCallBudget,
    protect_recall_expansion_openrouter_task,
    reserve_budget_slice,
)
from power_web_os.application.live_radar_staged_helpers import eligible_candidate_names, run_task
from power_web_os.application.live_radar_staged_merge import merge_result
from power_web_os.application.live_radar_universe import gap_items, gap_observations, gap_payloads, dict_list
from power_web_os.application.radar_search_expansion import RadarSearchExpansionService


@dataclass(slots=True)
class TargetedSearchExpansionExecutionResult:
    sources: list[RadarSourceEvidence]
    observations: list[dict[str, Any]]
    provider_metadata: dict[str, Any]
    candidate_scope: list[str]
    adaptive_action: dict[str, Any]
    stopped_for_review_reason: str = ""
    stop_reason_code: str = ""
    stop_details: dict[str, Any] | None = None


def execute_targeted_search_expansion(
    *,
    base_task: RadarExecutionTask,
    checkpoint_id: str,
    phase: str,
    attempt: int,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
    service: RadarSearchExpansionService,
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    candidate_scope: list[str],
    completed_qualification_ids: list[str],
    coverage_checks: list[dict[str, Any]],
    unresolved_candidate_gaps: list[dict[str, Any]],
    events: list[LiveRadarPipelineEvent],
    executed_task_ids: list[str],
    budget: RadarExecutionBudget,
    external_budget: RadarExternalCallBudget | None,
    smoke_candidate_limit: int | None,
) -> TargetedSearchExpansionExecutionResult:
    expansion_plan = service.plan_expansion(
        radar=radar,
        candidate_scope=candidate_scope,
        provider_metadata=provider_metadata,
        coverage_checks=coverage_checks,
        unresolved_candidate_gaps=unresolved_candidate_gaps,
    )
    plan_payload = expansion_plan.to_payload()
    provider_metadata = _with_expansion_plan_metadata(provider_metadata, radar=radar, expansion_plan=plan_payload)
    if not expansion_plan.should_expand:
        message = f"Checkpoint selected expansion, but no executable expansion task was available: {expansion_plan.reason}."
        return TargetedSearchExpansionExecutionResult(
            sources=sources,
            observations=observations,
            provider_metadata=provider_metadata,
            candidate_scope=candidate_scope,
            adaptive_action=_action_payload(checkpoint_id, phase, attempt, base_task, [], 0, 0, expansion_plan),
            stopped_for_review_reason=message,
            stop_reason_code="weak_candidate_coverage",
            stop_details={"expansion_reason": expansion_plan.reason},
        )

    tasks = service.tasks_from_plan(plan=expansion_plan, base_task=base_task)
    if not tasks:
        message = "Checkpoint selected expansion, but expansion produced no executable task."
        return TargetedSearchExpansionExecutionResult(
            sources=sources,
            observations=observations,
            provider_metadata=provider_metadata,
            candidate_scope=candidate_scope,
            adaptive_action=_action_payload(checkpoint_id, phase, attempt, base_task, [], 0, 0, expansion_plan),
            stopped_for_review_reason=message,
            stop_reason_code="weak_candidate_coverage",
        )

    provider_metadata = {
        **provider_metadata,
        "search_expansion_tasks": [
            *dict_list(provider_metadata.get("search_expansion_tasks")),
            *[
                {
                    "task_id": task.task_id,
                    "query": task.query,
                    "source_ids": list(task.source_ids),
                    "source_scope": task.source_scope,
                    "reason": expansion_plan.reason,
                    "checkpoint_id": checkpoint_id,
                }
                for task in tasks
            ],
        ],
    }
    executed_count = 0
    skipped_count = 0
    attempted_count = 0
    for task, variant in zip(tasks, list(expansion_plan.variants)):
        reserve_decision = reserve_budget_slice(
            variant.budget_reserve_key,
            task_id=task.task_id,
            reason=variant.reason,
        )
        if not reserve_decision.accepted:
            skipped_count += 1
            skipped = _skipped_payload(task, variant, reserve_decision.to_payload(), checkpoint_id)
            provider_metadata = {
                **provider_metadata,
                "targets_not_searched": [*dict_list(provider_metadata.get("targets_not_searched")), skipped],
            }
            events.append(_skipped_event(task, reserve_decision.message, skipped))
            continue

        protect_recall_expansion_openrouter_task(task_id=task.task_id, reserve_key=variant.budget_reserve_key)
        attempted_count += 1
        result = run_task(
            provider=provider,
            radar=radar,
            task=task,
            radar_id=execution_plan.radar_id,
            budget=budget,
            external_budget=external_budget,
            semantic_reserve_key=variant.budget_reserve_key,
        )
        executed_payload = _executed_payload(
            task,
            variant,
            result.provider_metadata.get("budget_decision", {}),
            checkpoint_id,
            result,
        )
        if executed_payload["execution_status"] == "not_executed":
            skipped_count += 1
            provider_metadata = {
                **provider_metadata,
                "targets_not_searched": [
                    *dict_list(provider_metadata.get("targets_not_searched")),
                    _not_executed_payload(executed_payload),
                ],
                "search_expansion_results": [
                    *dict_list(provider_metadata.get("search_expansion_results")),
                    executed_payload,
                ],
            }
            events.append(_skipped_event(task, str(executed_payload.get("not_searched_reason") or ""), executed_payload))
            continue
        gaps = gap_items(result)
        result = result.model_copy(update={
            "candidate_observations": [
                *result.candidate_observations,
                *gap_observations(gaps, origin_task_id=task.task_id),
            ],
        })
        sources, observations, provider_metadata = merge_result(sources, observations, provider_metadata, result)
        if not _has_extraction_issues(result.provider_metadata):
            provider_metadata = _without_extraction_issues(provider_metadata)
        unresolved_candidate_gaps.extend(gap_payloads(gaps, origin_task_id=task.task_id))
        executed_task_ids.append(f"{task.task_id}:checkpoint-search-expansion")
        executed_count += 1
        provider_metadata = {
            **provider_metadata,
            "search_expansion_results": [
                *dict_list(provider_metadata.get("search_expansion_results")),
                executed_payload,
            ],
        }
        events.append(_executed_event(task, variant, result))

    candidate_scope = eligible_candidate_names(
        radar=radar,
        sources=sources,
        observations=observations,
        completed_qualification_ids=completed_qualification_ids,
    )
    if smoke_candidate_limit and smoke_candidate_limit > 0:
        candidate_scope = candidate_scope[:smoke_candidate_limit]
    stopped_reason = ""
    stop_code = ""
    if not executed_count and skipped_count:
        stopped_reason = "Recall expansion targets were selected but no external search call was executed."
        stop_code = "budget_exhausted"
    return TargetedSearchExpansionExecutionResult(
        sources=sources,
        observations=observations,
        provider_metadata=provider_metadata,
        candidate_scope=candidate_scope,
        adaptive_action=_action_payload(
            checkpoint_id,
            phase,
            attempt,
            base_task,
            tasks,
            executed_count,
            skipped_count,
            expansion_plan,
            attempted_count=attempted_count,
        ),
        stopped_for_review_reason=stopped_reason,
        stop_reason_code=stop_code,
    )


def _action_payload(
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


def _with_expansion_plan_metadata(
    metadata: dict[str, Any],
    *,
    radar: dict[str, Any],
    expansion_plan: dict[str, Any],
) -> dict[str, Any]:
    return {
        **metadata,
        "expansion_target_queue": [*dict_list(metadata.get("expansion_target_queue")), *expansion_plan.get("targets", [])],
        "expansion_target_summary_by_type": _merge_int_dicts(
            metadata.get("expansion_target_summary_by_type"),
            expansion_plan.get("targets_by_type"),
        ),
        "search_expansion_query_variants_by_target": {
            **(
                metadata.get("search_expansion_query_variants_by_target")
                if isinstance(metadata.get("search_expansion_query_variants_by_target"), dict)
                else {}
            ),
            **expansion_plan.get("variants_by_target", {}),
        },
        "search_expansion_query_variants_by_target_type": {
            **(
                metadata.get("search_expansion_query_variants_by_target_type")
                if isinstance(metadata.get("search_expansion_query_variants_by_target_type"), dict)
                else {}
            ),
            **expansion_plan.get("variants_by_target_type", {}),
        },
        "targets_not_searched": _dedupe_target_records([
            *dict_list(metadata.get("targets_not_searched")),
            *dict_list(expansion_plan.get("targets_not_selected")),
        ]),
        "source_capability_strategy_summary": _source_capability_strategy_summary(radar=radar, expansion_plan=expansion_plan),
        "search_expansion_query_variants": [
            *dict_list(metadata.get("search_expansion_query_variants")),
            *expansion_plan.get("variants", []),
        ],
    }


def _source_capability_strategy_summary(*, radar: dict[str, Any], expansion_plan: dict[str, Any]) -> dict[str, Any]:
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


def _merge_int_dicts(left: object, right: object) -> dict[str, int]:
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


def _dedupe_target_records(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        key = (
            str(item.get("target_id") or ""),
            str(item.get("task_id") or ""),
            str(item.get("not_searched_reason") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _skipped_payload(task: RadarExecutionTask, variant: Any, budget_decision: dict[str, Any], checkpoint_id: str) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "query": task.query,
        "source_ids": list(task.source_ids),
        "target_id": variant.target_id,
        "target_type": variant.target_type,
        "budget_reserve_key": variant.budget_reserve_key,
        "execution_status": "not_searched",
        "not_searched_reason": budget_decision.get("reason") or "budget_reserve_exhausted",
        "budget_decision": budget_decision,
        "checkpoint_id": checkpoint_id,
    }


def _executed_payload(task: RadarExecutionTask, variant: Any, budget_decision: dict[str, Any], checkpoint_id: str, result: Any) -> dict[str, Any]:
    status, reason = _execution_status(result=result, budget_decision=budget_decision)
    return {
        "task_id": task.task_id,
        "query": task.query,
        "source_ids": list(task.source_ids),
        "target_id": variant.target_id,
        "target_type": variant.target_type,
        "budget_reserve_key": variant.budget_reserve_key,
        "execution_status": status,
        "not_searched_reason": reason if status == "not_executed" else "",
        "source_count": len(result.sources),
        "candidate_observation_count": len(result.candidate_observations),
        "budget_decision": budget_decision,
        "checkpoint_id": checkpoint_id,
    }


def _not_executed_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "execution_status": "not_searched",
        "not_searched_reason": payload.get("not_searched_reason") or "not_executed_global_budget_limited",
    }


def _execution_status(*, result: Any, budget_decision: dict[str, Any]) -> tuple[str, str]:
    if isinstance(budget_decision, dict) and budget_decision.get("accepted") is False:
        return "not_executed", _budget_limited_reason(budget_decision)
    if len(result.sources) > 0:
        return "executed_source_found", ""
    return "executed_no_support", ""


def _budget_limited_reason(budget_decision: dict[str, Any]) -> str:
    kind = str(budget_decision.get("kind") or "")
    reason = str(budget_decision.get("reason") or "")
    if kind == "budget_reserve":
        return "not_executed_reserve_limited"
    if reason == "semantic_task_reserve_exhausted":
        return "semantic_task_budget_limited"
    if bool(budget_decision.get("used_semantic_reserve")):
        return ""
    return "not_executed_global_budget_limited"


def _skipped_event(task: RadarExecutionTask, message: str, payload: dict[str, Any]) -> LiveRadarPipelineEvent:
    return LiveRadarPipelineEvent(
        event_type="search_expansion_skipped_budget_reserve",
        phase="collection",
        actor="application",
        node_name="checkpoint_search_expansion",
        visibility="operator",
        summary=f"Skipped recall expansion task {task.task_id}: {message}",
        payload=payload,
    )


def _executed_event(task: RadarExecutionTask, variant: Any, result: Any) -> LiveRadarPipelineEvent:
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


def _has_extraction_issues(metadata: dict[str, Any]) -> bool:
    for result in metadata.get("extraction_validation_results", []):
        if isinstance(result, dict) and str(result.get("state")) in {"extraction_schema_invalid", "evidence_linking_failed"}:
            return True
    for issue in metadata.get("extraction_validation_issues", []):
        if isinstance(issue, dict) and str(issue.get("severity")) == "error":
            return True
    return False


def _without_extraction_issues(metadata: dict[str, Any]) -> dict[str, Any]:
    return {**metadata, "extraction_validation_results": [], "extraction_validation_issues": [], "extraction_repair_results": []}
