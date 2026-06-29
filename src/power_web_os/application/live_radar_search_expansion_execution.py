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
)
from power_web_os.application.live_radar_staged_helpers import eligible_candidate_names, run_task
from power_web_os.application.live_radar_staged_merge import merge_result
from power_web_os.application.live_radar_universe import gap_items, gap_observations, gap_payloads, dict_list
from power_web_os.application.radar_search_expansion import RadarSearchExpansionService
from power_web_os.application.radar_search_expansion_models import RadarSearchExpansionPlan
from power_web_os.application.live_radar_search_expansion_payloads import (
    benchmark_target_probe_minimums,
    dedupe_target_records,
    executed_event,
    executed_payload,
    expansion_action_payload,
    has_extraction_issues,
    not_executed_payload,
    skipped_event,
    skipped_payload,
    with_expansion_plan_metadata,
    without_extraction_issues,
)
from power_web_os.application.radar_search_expansion_scheduler import schedule_guaranteed_expansion_variants
from power_web_os.application.radar_work_scheduler import RadarWorkScheduler
from power_web_os.application.radar_work_scheduler_metadata import merge_work_scheduler_metadata


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
    work_scheduler: RadarWorkScheduler | None = None,
    smoke_candidate_limit: int | None = None,
) -> TargetedSearchExpansionExecutionResult:
    expansion_plan = service.plan_expansion(
        radar=radar,
        candidate_scope=candidate_scope,
        provider_metadata=provider_metadata,
        coverage_checks=coverage_checks,
        unresolved_candidate_gaps=unresolved_candidate_gaps,
    )
    plan_payload = expansion_plan.to_payload()
    provider_metadata = with_expansion_plan_metadata(provider_metadata, radar=radar, expansion_plan=plan_payload)
    if not expansion_plan.should_expand:
        message = f"Checkpoint selected expansion, but no executable expansion task was available: {expansion_plan.reason}."
        return TargetedSearchExpansionExecutionResult(
            sources=sources,
            observations=observations,
            provider_metadata=provider_metadata,
            candidate_scope=candidate_scope,
            adaptive_action=expansion_action_payload(checkpoint_id, phase, attempt, base_task, [], 0, 0, expansion_plan),
            stopped_for_review_reason=message,
            stop_reason_code="weak_candidate_coverage",
            stop_details={"expansion_reason": expansion_plan.reason},
        )

    schedule = schedule_guaranteed_expansion_variants(
        variants=list(expansion_plan.variants),
        targets=plan_payload.get("targets", []),
        minimums=benchmark_target_probe_minimums(radar),
    )
    provider_metadata = {
        **provider_metadata,
        **schedule.to_metadata(),
        "targets_not_searched": dedupe_target_records([
            *dict_list(provider_metadata.get("targets_not_searched")),
            *schedule.unscheduled_targets,
        ]),
    }
    scheduled_plan = RadarSearchExpansionPlan(
        should_expand=expansion_plan.should_expand,
        variants=schedule.variants,
        targets=expansion_plan.targets,
        reason=expansion_plan.reason,
    )
    tasks = service.tasks_from_plan(plan=scheduled_plan, base_task=base_task)
    if not tasks:
        message = "Checkpoint selected expansion, but expansion produced no executable task."
        return TargetedSearchExpansionExecutionResult(
            sources=sources,
            observations=observations,
            provider_metadata=provider_metadata,
            candidate_scope=candidate_scope,
            adaptive_action=expansion_action_payload(checkpoint_id, phase, attempt, base_task, [], 0, 0, expansion_plan),
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
    scheduler = work_scheduler or RadarWorkScheduler()
    portfolio = scheduler.build_recall_expansion_portfolio(
        tasks=tasks,
        scheduled_variants=list(schedule.scheduled_variants),
        external_budget=external_budget,
    )
    provider_metadata = merge_work_scheduler_metadata(provider_metadata, portfolio.to_metadata())
    executed_count = 0
    skipped_count = 0
    attempted_count = 0
    decisions_by_work_id = {decision.work_id: decision for decision in portfolio.ledger.decisions}
    for work_item in portfolio.work_items:
        task = work_item.task
        scheduled_variant = work_item.scheduled_variant
        if scheduled_variant is None:
            continue
        variant = scheduled_variant.variant
        admission_decision = decisions_by_work_id.get(work_item.work_id)
        if admission_decision is not None and not admission_decision.accepted:
            skipped_count += 1
            skipped = skipped_payload(
                task,
                variant,
                admission_decision.budget_decision,
                checkpoint_id,
                schedule_role=scheduled_variant.schedule_role,
                execution_status="work_admission_rejected",
                not_searched_reason=admission_decision.reason,
            )
            provider_metadata = {
                **provider_metadata,
                "targets_not_searched": [*dict_list(provider_metadata.get("targets_not_searched")), skipped],
                "search_expansion_results": [*dict_list(provider_metadata.get("search_expansion_results")), skipped],
            }
            events.append(skipped_event(task, admission_decision.message, skipped))
            continue

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
        expansion_result_payload = executed_payload(
            task,
            variant,
            result.provider_metadata.get("budget_decision", {}),
            checkpoint_id,
            result,
            schedule_role=scheduled_variant.schedule_role,
        )
        if expansion_result_payload["execution_status"] == "not_executed":
            skipped_count += 1
            provider_metadata = {
                **provider_metadata,
                "targets_not_searched": [
                    *dict_list(provider_metadata.get("targets_not_searched")),
                    not_executed_payload(expansion_result_payload),
                ],
                "search_expansion_results": [
                    *dict_list(provider_metadata.get("search_expansion_results")),
                    expansion_result_payload,
                ],
            }
            events.append(skipped_event(task, str(expansion_result_payload.get("not_searched_reason") or ""), expansion_result_payload))
            continue
        gaps = gap_items(result)
        result = result.model_copy(update={
            "candidate_observations": [
                *result.candidate_observations,
                *gap_observations(gaps, origin_task_id=task.task_id),
            ],
        })
        sources, observations, provider_metadata = merge_result(sources, observations, provider_metadata, result)
        if not has_extraction_issues(result.provider_metadata):
            provider_metadata = without_extraction_issues(provider_metadata)
        unresolved_candidate_gaps.extend(gap_payloads(gaps, origin_task_id=task.task_id))
        executed_task_ids.append(f"{task.task_id}:checkpoint-search-expansion")
        executed_count += 1
        provider_metadata = {
            **provider_metadata,
            "search_expansion_results": [
                *dict_list(provider_metadata.get("search_expansion_results")),
                expansion_result_payload,
            ],
        }
        events.append(executed_event(task, variant, result))

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
        adaptive_action=expansion_action_payload(
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
