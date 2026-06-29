"""Execute qualification-first Radar plans through the provider port."""

from __future__ import annotations

from typing import Any

from power_web_os.application.live_radar_contracts import (
    LiveRadarPipelineEvent,
    RadarCoverageCheckRecord,
    RadarExecutionPlan,
    RadarExecutionTask,
    RadarSourceEvidence,
    WebSearchProvider,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_checkpoint_actions import (
    RadarCheckpointActionExecutor,
    RadarCheckpointRecoveryContext,
    RadarCheckpointRecoveryState,
)
from power_web_os.application.live_radar_checkpoint_execution import record_execution_checkpoint
from power_web_os.application.live_radar_checkpoints import RadarExecutionCheckpointPolicy, RadarExecutionCheckpointService, checkpoint_summary
from power_web_os.application.live_radar_cross_disambiguation import execute_cross_source_disambiguation
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget, budget_settings_from_context
from power_web_os.application.live_radar_execution_plan import scoped_execution_task
from power_web_os.application.live_radar_external_budget import RadarExternalCallBudget
from power_web_os.application.live_radar_external_budget_context import (
    current_external_call_budget,
    external_budget_settings_from_context,
    external_call_budget_context,
)
from power_web_os.application.live_radar_extraction_diagnostics import (
    extraction_contract_state,
    extraction_repair_results,
    extraction_validation_event,
    extraction_validation_issues,
)
from power_web_os.application.live_radar_retrieval_plan import retrieval_plan_from_execution_plan
from power_web_os.application.live_radar_retrieved_candidates import candidates_from_retrieved_sources
from power_web_os.application.radar_source_obligations import (
    obligation_decisions_from_plan,
    source_obligation_summary,
)
from power_web_os.application.radar_search_expansion import RadarSearchExpansionService
from power_web_os.application.live_radar_search_expansion_payloads import benchmark_target_probe_minimums, merge_selection_summary
from power_web_os.application.radar_search_expansion_models import RadarSearchExpansionPlan
from power_web_os.application.radar_search_expansion_scheduler import schedule_guaranteed_expansion_variants
from power_web_os.application.radar_work_scheduler import RadarWorkScheduler
from power_web_os.application.radar_work_scheduler_metadata import merge_work_scheduler_metadata
from power_web_os.application.live_radar_staged_helpers import (
    candidate_names_matching as _candidate_names_matching,
    combine_task_results as _combine_task_results,
    dedupe_sources as _dedupe_sources,
    eligible_candidate_names as _eligible_candidate_names,
    normalized_candidates as _normalized_candidates,
    run_gate_pass as _run_gate_pass,
    run_task as _run_task,
    tasks_for_stage as _tasks_for_stage,
    useful_result_warning_event as _useful_result_warning_event,
)
from power_web_os.application.live_radar_staged_merge import (
    candidate_universe_with_entity_metadata as _candidate_universe_with_entity_metadata,
    merge_candidate_observations as _merge_candidate_observations,
    merge_result as _merge_result,
)
from power_web_os.application.live_radar_staged_support import (
    budget_warning_event as _budget_warning_event,
    budget_decision as _budget_decision,
    candidate_universe_with_signal_statuses as _candidate_universe_with_signal_statuses,
    rejected_candidate_summaries as _rejected_candidate_summaries,
    signal_planned_event as _signal_planned_event,
    signal_status_record as _signal_status_record,
    source_obligation_events as _source_obligation_events,
    not_searched_signal_observation as _not_searched_signal_observation,
    task_event as _task_event,
)
from power_web_os.application.live_radar_useful_budget import UsefulResultBudget, run_task_with_useful_retries
from power_web_os.application.live_radar_universe import (
    candidate_name,
    candidate_name_set,
    candidate_universe_entries,
    coverage_risk,
    coverage_warnings as coverage_warning_messages,
    dedupe_gap_payloads,
    dict_list,
    filter_signal_result,
    first_task_id,
    gap_items,
    gap_observations,
    gap_payloads,
    stable_id,
)
from power_web_os.integrations.live_radar_source_verification import (
    SourceVerificationCache,
    source_verification_cache_context,
)

MAX_DISCOVERY_ITERATIONS = 2
MAX_CANDIDATE_UNIVERSE_SIZE = 50
def run_staged_radar_execution(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
    task_context: dict[str, Any] | None = None,
    max_web_tasks_per_subject: int | None = None,
    max_discovery_tasks_per_rule: int | None = None,
    max_gate_tasks_per_candidate_rule: int | None = None,
    max_signal_tasks_per_candidate_signal: int | None = None,
    max_total_web_tasks_per_run: int | None = None,
    min_useful_sources_per_discovery_task: int | None = None,
    min_candidates_per_discovery_task: int | None = None,
    max_discovery_retries_per_task: int | None = None,
    max_checkpoint_revisions_per_run: int | None = None,
    max_checkpoint_retries_per_stage: int | None = None,
    run_profile: str | None = None,
    max_openrouter_calls_per_run: int | None = None,
    max_openrouter_planner_calls_per_run: int | None = None,
    max_openrouter_web_task_calls_per_run: int | None = None,
    max_recall_expansion_openrouter_calls_per_run: int | None = None,
    max_openrouter_server_tool_web_searches_per_run: int | None = None,
    max_dadata_lookups_per_run: int | None = None,
    max_source_verification_requests_per_run: int | None = None,
    max_provider_retries_per_task: int | None = None,
    openrouter_web_max_results_per_call: int | None = None,
    openrouter_web_max_total_results_per_call: int | None = None,
    smoke_max_candidates: int | None = None,
    smoke_max_signals: int | None = None,
    budget_reserve_limits: dict[str, int] | None = None,
    semantic_task_reserve_limits: dict[str, int] | None = None,
    source_policy_decisions: list[dict[str, Any]] | None = None,
) -> tuple[WebSearchProviderResult, list[LiveRadarPipelineEvent], dict[str, Any]]:
    if task_context:
        radar = {
            **radar,
            "task_context": {
                **(radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}),
                **task_context,
            },
        }
    sources: list[RadarSourceEvidence] = []
    observations: list[dict[str, Any]] = []
    provider_metadata: dict[str, Any] = _initial_provider_metadata(radar)
    events: list[LiveRadarPipelineEvent] = []
    executed_task_ids: list[str] = []
    completed_qualification_ids: list[str] = []
    gate_results: list[dict[str, Any]] = []
    candidate_scope: list[str] = []
    coverage_checks: list[dict[str, Any]] = []
    unresolved_candidate_gaps: list[dict[str, Any]] = []
    coverage_warnings: list[str] = []
    useful_result_warnings: list[str] = []
    useful_result_retry_records: list[dict[str, Any]] = []
    checkpoint_decisions: list[dict[str, Any]] = []
    adaptive_actions: list[dict[str, Any]] = []
    checkpoint_warnings: list[str] = []
    stopped_for_review_reason = ""
    discovery_iteration_count = 0
    budget_settings = budget_settings_from_context(
        max_web_tasks_per_subject=max_web_tasks_per_subject,
        max_discovery_tasks_per_rule=max_discovery_tasks_per_rule,
        max_gate_tasks_per_candidate_rule=max_gate_tasks_per_candidate_rule,
        max_signal_tasks_per_candidate_signal=max_signal_tasks_per_candidate_signal,
        max_total_web_tasks_per_run=max_total_web_tasks_per_run,
        semantic_task_reserve_limits=semantic_task_reserve_limits,
    )
    task_budget = RadarExecutionBudget(budget_settings)
    external_budget = current_external_call_budget() or RadarExternalCallBudget(external_budget_settings_from_context({
        "run_profile": run_profile,
        "max_openrouter_calls_per_run": max_openrouter_calls_per_run,
        "max_openrouter_planner_calls_per_run": max_openrouter_planner_calls_per_run,
        "max_openrouter_web_task_calls_per_run": max_openrouter_web_task_calls_per_run,
        "max_recall_expansion_openrouter_calls_per_run": max_recall_expansion_openrouter_calls_per_run,
        "max_openrouter_server_tool_web_searches_per_run": max_openrouter_server_tool_web_searches_per_run,
        "max_dadata_lookups_per_run": max_dadata_lookups_per_run,
        "max_source_verification_requests_per_run": max_source_verification_requests_per_run,
        "max_provider_retries_per_task": max_provider_retries_per_task,
        "openrouter_web_max_results_per_call": openrouter_web_max_results_per_call,
        "openrouter_web_max_total_results_per_call": openrouter_web_max_total_results_per_call,
        "smoke_max_candidates": smoke_max_candidates,
        "smoke_max_signals": smoke_max_signals,
        "budget_reserve_limits": budget_reserve_limits,
    }))
    useful_budget = UsefulResultBudget(
        min_sources=min_useful_sources_per_discovery_task,
        min_candidates=min_candidates_per_discovery_task,
        max_retries=max_discovery_retries_per_task,
    )
    checkpoint_service = RadarExecutionCheckpointService(
        RadarExecutionCheckpointPolicy(
            max_revisions_per_run=2 if max_checkpoint_revisions_per_run is None else max_checkpoint_revisions_per_run,
            max_retries_per_stage=1 if max_checkpoint_retries_per_stage is None else max_checkpoint_retries_per_stage,
        )
    )
    checkpoint_executor = RadarCheckpointActionExecutor()
    search_expansion_service = RadarSearchExpansionService(
        max_variants=_search_expansion_variant_cap(run_profile=run_profile, radar=radar)
    )
    work_scheduler = RadarWorkScheduler()
    provider_metadata = {**provider_metadata, **work_scheduler.configure_run_admission(radar=radar, external_budget=external_budget)}
    retrieval_plan = retrieval_plan_from_execution_plan(execution_plan)
    verification_cache = SourceVerificationCache(results_by_url={})

    discovery_tasks = _tasks_for_stage(execution_plan, "qualification_discovery")
    with external_call_budget_context(external_budget), source_verification_cache_context(verification_cache):
        for task in discovery_tasks:
            result, run_ids, retry_records, retry_warnings = run_task_with_useful_retries(
                task=task,
                useful_budget=useful_budget,
                execution_id=task.task_id,
                run_task=lambda current_task: _run_task(
                    provider=provider,
                    radar=radar,
                    task=current_task,
                    radar_id=execution_plan.radar_id,
                    budget=task_budget,
                    external_budget=external_budget,
                ),
                combine_results=_combine_task_results,
            )
            sources, observations, provider_metadata = _merge_result(sources, observations, provider_metadata, result)
            executed_task_ids.extend(run_ids)
            useful_result_retry_records.extend(retry_records)
            useful_result_warnings.extend(retry_warnings)
            completed_qualification_ids.append(task.subject_id)
            candidate_scope = _eligible_candidate_names(
                radar=radar,
                sources=sources,
                observations=observations,
                completed_qualification_ids=completed_qualification_ids,
            )
            events.append(_task_event(task, result, "qualification_discovery_planned"))

        sources, observations, provider_metadata, candidate_scope = _extract_retrieved_candidates(
            radar=radar,
            sources=sources,
            observations=observations,
            provider_metadata=provider_metadata,
            candidate_scope=candidate_scope,
            completed_qualification_ids=completed_qualification_ids,
            events=events,
            smoke_candidate_limit=external_budget.settings.smoke_max_candidates,
        )
        sources, observations, provider_metadata = execute_cross_source_disambiguation(
            radar=radar,
            execution_plan=execution_plan,
            provider=provider,
            sources=sources,
            observations=observations,
            provider_metadata=provider_metadata,
            budget=task_budget,
            external_budget=external_budget,
            events=events,
            executed_task_ids=executed_task_ids,
        )
        candidate_scope = _eligible_candidate_names(
            radar=radar,
            sources=sources,
            observations=observations,
            completed_qualification_ids=completed_qualification_ids,
        )
        candidate_scope = _limit_smoke_candidates(candidate_scope, external_budget.settings.smoke_max_candidates)

        recovery_state, _ = checkpoint_executor.recover(
            checkpoint_id="after-discovery",
            phase="after_discovery",
            tasks=discovery_tasks,
            state=RadarCheckpointRecoveryState(sources, observations, provider_metadata, candidate_scope),
            context=RadarCheckpointRecoveryContext(
                radar=radar, execution_plan=execution_plan, provider=provider, service=checkpoint_service,
                budget=task_budget, completed_qualification_ids=completed_qualification_ids,
                checkpoint_decisions=checkpoint_decisions, adaptive_actions=adaptive_actions,
                checkpoint_warnings=checkpoint_warnings, events=events, executed_task_ids=executed_task_ids,
                useful_result_retry_records=useful_result_retry_records,
                external_budget=external_budget,
                search_expansion_service=search_expansion_service,
                work_scheduler=work_scheduler,
                smoke_candidate_limit=external_budget.settings.smoke_max_candidates,
            ),
        )
        sources, observations = recovery_state.sources, recovery_state.observations
        provider_metadata, candidate_scope = recovery_state.provider_metadata, recovery_state.candidate_scope
        candidate_scope = _limit_smoke_candidates(candidate_scope, external_budget.settings.smoke_max_candidates)
        stopped_for_review_reason = recovery_state.stopped_for_review_reason

        terminal_stop_after_discovery = bool(stopped_for_review_reason)
        gate_tasks = [] if terminal_stop_after_discovery else _tasks_for_stage(execution_plan, "qualification_gate")
        sources, observations, provider_metadata, candidate_scope = _run_gate_pass(
            radar=radar,
            execution_plan=execution_plan,
            provider=provider,
            tasks=gate_tasks,
            sources=sources,
            observations=observations,
            provider_metadata=provider_metadata,
            candidate_scope=candidate_scope,
            completed_qualification_ids=completed_qualification_ids,
            gate_results=gate_results,
            events=events,
            executed_task_ids=executed_task_ids,
            budget=task_budget,
            external_budget=external_budget,
        )
        candidate_scope = _limit_smoke_candidates(candidate_scope, external_budget.settings.smoke_max_candidates)

        record_execution_checkpoint(
            checkpoint_id="after-qualification-gates",
            phase="after_qualification_gates",
            service=checkpoint_service,
            candidate_count=len(_normalized_candidates(radar=radar, sources=sources, observations=observations)),
            sources=sources,
            observations=observations,
            provider_metadata=provider_metadata,
            candidate_scope=candidate_scope,
            coverage_checks=coverage_checks,
            coverage_warnings=coverage_warnings,
            unresolved_candidate_gaps=unresolved_candidate_gaps,
            budget=task_budget,
            useful_result_retry_records=useful_result_retry_records,
            source_obligation_decisions=[],
            checkpoint_decisions=checkpoint_decisions,
            adaptive_actions=adaptive_actions,
            checkpoint_warnings=checkpoint_warnings,
            events=events,
        )

        coverage_tasks = [] if terminal_stop_after_discovery else _tasks_for_stage(execution_plan, "coverage_check")
        for iteration in range(1, MAX_DISCOVERY_ITERATIONS + 1):
            if not coverage_tasks:
                break
            if len(_normalized_candidates(radar=radar, sources=sources, observations=observations)) >= MAX_CANDIDATE_UNIVERSE_SIZE:
                coverage_warnings.append(f"Candidate universe reached max size {MAX_CANDIDATE_UNIVERSE_SIZE}.")
                break
            discovery_iteration_count = iteration
            names_before = candidate_name_set(observations)
            iteration_new_names: set[str] = set()
            for task in coverage_tasks:
                scoped_task = scoped_execution_task(task, candidate_scope=candidate_scope)
                result, run_ids, retry_records, retry_warnings = run_task_with_useful_retries(
                    task=scoped_task,
                    useful_budget=useful_budget,
                    execution_id=f"{task.task_id}:iteration-{iteration}",
                    run_task=lambda current_task: _run_task(
                        provider=provider,
                        radar=radar,
                        task=current_task,
                        radar_id=execution_plan.radar_id,
                        budget=task_budget,
                        external_budget=external_budget,
                    ),
                    combine_results=_combine_task_results,
                )
                gaps = gap_items(result)
                result = result.model_copy(update={
                    "candidate_observations": [
                        *result.candidate_observations,
                        *gap_observations(gaps, origin_task_id=task.task_id),
                    ],
                })
                sources, observations, provider_metadata = _merge_result(sources, observations, provider_metadata, result)
                executed_task_ids.extend(run_ids)
                useful_result_retry_records.extend(retry_records)
                useful_result_warnings.extend(retry_warnings)
                names_after = candidate_name_set(observations)
                new_names = names_after - names_before
                iteration_new_names.update(new_names)
                unresolved_candidate_gaps.extend(gap_payloads(gaps, origin_task_id=task.task_id))
                warnings = coverage_warning_messages(result)
                coverage_warnings.extend(warnings)
                coverage_record = RadarCoverageCheckRecord(
                    task_id=task.task_id,
                    iteration=iteration,
                    source_count=len(result.sources),
                    candidate_observation_count=len(result.candidate_observations),
                    new_candidate_count=len(new_names),
                    gap_count=len(gaps),
                    completeness_risk=coverage_risk(result),  # type: ignore[arg-type]
                    warnings=warnings,
                ).model_dump()
                coverage_checks.append(coverage_record)
                events.append(_task_event(scoped_task, result, "coverage_warning" if warnings else "candidate_universe_discovered", payload=coverage_record))
                names_before = names_after

            if not iteration_new_names:
                break
            new_candidate_scope = _candidate_names_matching(observations, iteration_new_names)
            sources, observations, provider_metadata, _ = _run_gate_pass(
                radar=radar,
                execution_plan=execution_plan,
                provider=provider,
                tasks=[*discovery_tasks, *gate_tasks],
                sources=sources,
                observations=observations,
                provider_metadata=provider_metadata,
                candidate_scope=new_candidate_scope,
                completed_qualification_ids=completed_qualification_ids,
                gate_results=gate_results,
                events=events,
                executed_task_ids=executed_task_ids,
                budget=task_budget,
                external_budget=external_budget,
            )
            candidate_scope = _eligible_candidate_names(
                radar=radar,
                sources=sources,
                observations=observations,
                completed_qualification_ids=completed_qualification_ids,
            )
            candidate_scope = _limit_smoke_candidates(candidate_scope, external_budget.settings.smoke_max_candidates)

        if not stopped_for_review_reason:
            sources, observations, provider_metadata, candidate_scope = _run_search_expansion(
                radar=radar,
                execution_plan=execution_plan,
                provider=provider,
                service=search_expansion_service,
                base_tasks=coverage_tasks or discovery_tasks,
                sources=sources,
                observations=observations,
                provider_metadata=provider_metadata,
                candidate_scope=candidate_scope,
                completed_qualification_ids=completed_qualification_ids,
                coverage_checks=coverage_checks,
                unresolved_candidate_gaps=unresolved_candidate_gaps,
                events=events,
                executed_task_ids=executed_task_ids,
                budget=task_budget,
                external_budget=external_budget,
                work_scheduler=work_scheduler,
                smoke_candidate_limit=external_budget.settings.smoke_max_candidates,
            )

        if not stopped_for_review_reason:
            recovery_state, _ = checkpoint_executor.recover(
                checkpoint_id="after-coverage",
                phase="after_coverage",
                tasks=coverage_tasks,
                state=RadarCheckpointRecoveryState(sources, observations, provider_metadata, candidate_scope),
                context=RadarCheckpointRecoveryContext(
                    radar=radar, execution_plan=execution_plan, provider=provider, service=checkpoint_service,
                    budget=task_budget, completed_qualification_ids=completed_qualification_ids,
                    checkpoint_decisions=checkpoint_decisions, adaptive_actions=adaptive_actions,
                    checkpoint_warnings=checkpoint_warnings, events=events, executed_task_ids=executed_task_ids,
                    coverage_checks=coverage_checks, coverage_warnings=coverage_warnings,
                    unresolved_candidate_gaps=unresolved_candidate_gaps,
                    useful_result_retry_records=useful_result_retry_records,
                    external_budget=external_budget,
                    search_expansion_service=search_expansion_service,
                    work_scheduler=work_scheduler,
                    smoke_candidate_limit=external_budget.settings.smoke_max_candidates,
                ),
            )
            sources, observations = recovery_state.sources, recovery_state.observations
            provider_metadata, candidate_scope = recovery_state.provider_metadata, recovery_state.candidate_scope
            candidate_scope = _limit_smoke_candidates(candidate_scope, external_budget.settings.smoke_max_candidates)
            stopped_for_review_reason = stopped_for_review_reason or recovery_state.stopped_for_review_reason

        sources, observations, provider_metadata, candidate_scope = _extract_retrieved_candidates(
            radar=radar,
            sources=sources,
            observations=observations,
            provider_metadata=provider_metadata,
            candidate_scope=candidate_scope,
            completed_qualification_ids=completed_qualification_ids,
            events=events,
            smoke_candidate_limit=external_budget.settings.smoke_max_candidates,
        )
        if not stopped_for_review_reason:
            sources, observations, provider_metadata = execute_cross_source_disambiguation(
                radar=radar,
                execution_plan=execution_plan,
                provider=provider,
                sources=sources,
                observations=observations,
                provider_metadata=provider_metadata,
                budget=task_budget,
                external_budget=external_budget,
                events=events,
                executed_task_ids=executed_task_ids,
            )
        candidate_scope = _eligible_candidate_names(
            radar=radar,
            sources=sources,
            observations=observations,
            completed_qualification_ids=completed_qualification_ids,
        )
        candidate_scope = _limit_smoke_candidates(candidate_scope, external_budget.settings.smoke_max_candidates)

        pre_signal_source_obligations = obligation_decisions_from_plan(
            global_policy=dict(radar.get("global_search_policy") or {}),
            steps=execution_plan.tasks,
            source_policy_decisions=source_policy_decisions or [],
            source_provider_outcomes=provider_metadata.get("source_provider_outcomes", []),
            sources=sources,
            observations=observations,
        )
        pre_signal_decision = record_execution_checkpoint(
            checkpoint_id="before-signal-search",
            phase="before_signal_search",
            service=checkpoint_service,
            candidate_count=len(_normalized_candidates(radar=radar, sources=sources, observations=observations)),
            sources=sources,
            observations=observations,
            provider_metadata=provider_metadata,
            candidate_scope=candidate_scope,
            coverage_checks=coverage_checks,
            coverage_warnings=coverage_warnings,
            unresolved_candidate_gaps=unresolved_candidate_gaps,
            budget=task_budget,
            useful_result_retry_records=useful_result_retry_records,
            source_obligation_decisions=pre_signal_source_obligations,
            checkpoint_decisions=checkpoint_decisions,
            adaptive_actions=adaptive_actions,
            checkpoint_warnings=checkpoint_warnings,
            events=events,
        )
        can_run_signal_search = (
            not stopped_for_review_reason
            and pre_signal_decision.action == "continue"
            and pre_signal_decision.should_continue
            and pre_signal_decision.should_run_signal_search
        )
        if not can_run_signal_search:
            stopped_for_review_reason = stopped_for_review_reason or pre_signal_decision.message

        signal_task_count = 0
        signal_budget_warnings: list[str] = []
        signal_candidate_scope = list(candidate_scope)
        signal_search_statuses: list[dict[str, Any]] = []
        signal_tasks = _limit_smoke_signal_tasks(_tasks_for_stage(execution_plan, "signal_search"), external_budget.settings.smoke_max_signals)
        if can_run_signal_search:
            for task in signal_tasks:
                for scoped_candidate_name in signal_candidate_scope:
                    scoped_task = scoped_execution_task(task, candidate_scope=[scoped_candidate_name])
                    events.append(_signal_planned_event(scoped_task))
                    result = _run_task(provider=provider, radar=radar, task=scoped_task, radar_id=execution_plan.radar_id, budget=task_budget, external_budget=external_budget)
                    budget_decision = _budget_decision(result)
                    if budget_decision:
                        observations.append(_not_searched_signal_observation(scoped_candidate_name, task, budget_decision))
                        signal_search_statuses.append(_signal_status_record(scoped_candidate_name, task, budget_decision))
                        continue
                    result = filter_signal_result(result, allowed_candidate_names={scoped_candidate_name})
                    unresolved_candidate_gaps.extend(gap_payloads(gap_items(result), origin_task_id=task.task_id))
                    sources, observations, provider_metadata = _merge_result(sources, observations, provider_metadata, result)
                    executed_task_ids.append(f"{task.task_id}:{scoped_candidate_name}")
                    signal_search_statuses.append({
                        "candidate_name": scoped_candidate_name,
                        "signal_id": task.subject_id,
                        "task_id": task.task_id,
                        "search_status": "searched",
                        "not_searched_reason": "",
                    })
                    signal_task_count += 1
        else:
            for task in signal_tasks:
                for scoped_candidate_name in signal_candidate_scope:
                    decision = {
                        "state": "not_searched_policy_limited",
                        "reason": pre_signal_decision.reason_code if not stopped_for_review_reason else "stopped_for_review",
                        "message": pre_signal_decision.message if not stopped_for_review_reason else stopped_for_review_reason,
                        "key": f"checkpoint:{pre_signal_decision.checkpoint_id}",
                    }
                    observations.append(_not_searched_signal_observation(scoped_candidate_name, task, decision))
                    signal_search_statuses.append(_signal_status_record(scoped_candidate_name, task, decision))
    for warnings in (signal_budget_warnings, task_budget.warnings):
        if warnings:
            coverage_warnings.extend(warnings)
            events.append(_budget_warning_event(warnings))
    if useful_result_warnings:
        coverage_warnings.extend(useful_result_warnings)
        events.append(_useful_result_warning_event(useful_result_warnings))
    extraction_issues = extraction_validation_issues(provider_metadata)
    repair_results = extraction_repair_results(provider_metadata)
    if extraction_issues:
        issue_codes = sorted({str(issue.get("code")) for issue in extraction_issues if str(issue.get("code", "")).strip()})
        coverage_warnings.extend([f"Extraction contract issue: {code}" for code in issue_codes])
        events.append(extraction_validation_event(extraction_issues, repair_results))

    normalized_candidates = _normalized_candidates(radar=radar, sources=sources, observations=observations)
    (
        normalized_candidates,
        observations,
        smoke_overflow_gaps,
        smoke_cap_metadata,
    ) = _apply_smoke_candidate_promotion_cap(
        candidates=normalized_candidates,
        observations=observations,
        smoke_candidate_limit=external_budget.settings.smoke_max_candidates,
    )
    if smoke_overflow_gaps:
        unresolved_candidate_gaps.extend(smoke_overflow_gaps)
        events.append(LiveRadarPipelineEvent(
            event_type="smoke_candidate_cap_applied",
            phase="validation",
            actor="application",
            node_name="smoke_candidate_cap",
            visibility="operator",
            summary=(
                f"Smoke profile promoted {smoke_cap_metadata['promoted_candidate_count']} candidates "
                f"and kept {smoke_cap_metadata['diagnostic_candidate_count']} as diagnostic gaps."
            ),
            payload=smoke_cap_metadata,
            candidate_refs=[item["legal_name"] for item in smoke_overflow_gaps if item.get("legal_name")],
        ))
    unresolved_candidate_gaps.extend(gap_payloads(dict_list(provider_metadata.get("candidate_universe_gaps")), origin_task_id="entity_resolution"))
    candidate_universe = candidate_universe_entries(
        candidates=normalized_candidates, completed_qualification_ids=completed_qualification_ids,
        origin_task_id=first_task_id(execution_plan.tasks), gap_names={candidate_name(item) for item in unresolved_candidate_gaps if candidate_name(item)},
    )
    candidate_universe_payload = _candidate_universe_with_entity_metadata(
        _candidate_universe_with_signal_statuses(candidate_universe, signal_search_statuses),
        observations,
    )
    candidate_universe_payload = _append_review_needed_universe_entities(
        candidate_universe_payload,
        provider_metadata=provider_metadata,
    )
    upstream_disambiguation_results = dict_list(provider_metadata.get("upstream_disambiguation_results"))
    cross_source_disambiguation_tasks = dict_list(provider_metadata.get("cross_source_disambiguation_tasks"))
    if upstream_disambiguation_results:
        events.extend(_upstream_disambiguation_events(upstream_disambiguation_results, cross_source_disambiguation_tasks))
    source_obligation_decisions = obligation_decisions_from_plan(
        global_policy=dict(radar.get("global_search_policy") or {}),
        steps=execution_plan.tasks,
        source_policy_decisions=source_policy_decisions or [],
        source_provider_outcomes=provider_metadata.get("source_provider_outcomes", []),
        sources=sources,
        observations=observations,
    )
    events.extend(_source_obligation_events(source_obligation_decisions))
    events.extend(_external_budget_events(external_budget.exhaustion_events))
    target_probe_guarantee_payload = _target_probe_guarantees(provider_metadata=provider_metadata, radar=radar)
    return (
        WebSearchProviderResult(
            sources=_dedupe_sources(sources), candidate_observations=_merge_candidate_observations(observations),
            provider_metadata={**provider_metadata, "execution_mode": "qualification_first_iterative_coverage"},
        ),
        events,
        {
            "execution_mode": "qualification_first_iterative_coverage",
            "retrieval_plan": retrieval_plan.model_dump(),
            "executed_task_count": len(executed_task_ids),
            "executed_task_ids": executed_task_ids,
            "gate_results": gate_results,
            "signal_task_count": signal_task_count,
            "candidate_scope": candidate_scope,
            "signal_candidate_scope": signal_candidate_scope,
            "signal_search_statuses": signal_search_statuses,
            "signal_budget_warnings": signal_budget_warnings,
            "max_signal_candidates": len(signal_candidate_scope),
            "max_signal_tasks": budget_settings.max_signal_tasks_per_candidate_signal,
            "max_web_tasks_per_subject": budget_settings.compatibility_max_web_tasks_per_subject,
            "budget_settings": {
                "max_total_web_tasks_per_run": budget_settings.max_total_tasks_per_run, "max_discovery_tasks_per_rule": budget_settings.max_discovery_tasks_per_rule,
                "max_gate_tasks_per_candidate_rule": budget_settings.max_gate_tasks_per_candidate_rule,
                "max_signal_tasks_per_candidate_signal": budget_settings.max_signal_tasks_per_candidate_signal,
                "compatibility_max_web_tasks_per_subject": budget_settings.compatibility_max_web_tasks_per_subject,
            },
            "budget_counters": {
                "total": task_budget.total_count,
                "by_key": dict(task_budget.counts),
                "semantic_reserves": dict(task_budget.semantic_reserve_counts),
            },
            "budget_exhaustion_events": list(task_budget.exhaustion_events),
            **task_budget.to_metadata(),
            "source_verification_cache_stats": verification_cache.to_metadata(),
            **verification_cache.to_metadata(),
            "web_task_counts_by_subject": task_budget.counts,
            "web_task_budget_warnings": task_budget.warnings,
            "useful_result_retry_records": useful_result_retry_records,
            "useful_result_warnings": useful_result_warnings,
            "min_useful_sources_per_discovery_task": useful_budget.min_sources,
            "min_candidates_per_discovery_task": useful_budget.min_candidates,
            "max_discovery_retries_per_task": useful_budget.max_retries,
            "source_verification_results": provider_metadata.get("source_verification_results", []),
            **external_budget.to_metadata(),
            "retrieval_provider": provider_metadata.get("retrieval_provider"),
            "retrieval_engine": provider_metadata.get("retrieval_engine"),
            "retrieved_sources": provider_metadata.get("retrieved_sources", []),
            "retrieval_source_outcomes": provider_metadata.get("retrieval_source_outcomes", []),
            "retrieved_source_count": provider_metadata.get("retrieved_source_count", 0),
            "source_outcomes": provider_metadata.get("source_outcomes", []),
            "source_provider_outcomes": provider_metadata.get("source_provider_outcomes", []),
            "source_capability_strategy_summary": provider_metadata.get("source_capability_strategy_summary", {}),
            "expansion_target_queue": provider_metadata.get("expansion_target_queue", []),
            "search_expansion_tasks": provider_metadata.get("search_expansion_tasks", []),
            "search_expansion_query_variants": provider_metadata.get("search_expansion_query_variants", []),
            "search_expansion_query_variants_by_target": provider_metadata.get("search_expansion_query_variants_by_target", {}),
            "search_expansion_selection_summary": provider_metadata.get("search_expansion_selection_summary", {}),
            "search_expansion_selection_diagnostics": provider_metadata.get("search_expansion_selection_diagnostics", []),
            "search_expansion_results": provider_metadata.get("search_expansion_results", []),
            "search_expansion_results_by_target": _results_by_target(provider_metadata.get("search_expansion_results", [])),
            "search_expansion_results_by_target_type": _results_by_target_type(provider_metadata.get("search_expansion_results", [])),
            "search_expansion_execution_summary": _search_expansion_execution_summary(provider_metadata),
            "target_probe_guarantees": target_probe_guarantee_payload["summary"],
            "target_probe_guarantee_failures": target_probe_guarantee_payload["failures"],
            "work_scheduler_plan": provider_metadata.get("work_scheduler_plan", {}),
            "work_scheduler_ledger": provider_metadata.get("work_scheduler_ledger", {}),
            "work_admission_decisions": provider_metadata.get("work_admission_decisions", []),
            "work_lane_summary": provider_metadata.get("work_lane_summary", {}),
            "work_guarantee_failures": provider_metadata.get("work_guarantee_failures", []),
            "work_execution_order": provider_metadata.get("work_execution_order", []),
            "deferred_work_items": provider_metadata.get("deferred_work_items", []),
            "rejected_work_items": provider_metadata.get("rejected_work_items", []),
            "expansion_target_summary_by_type": provider_metadata.get("expansion_target_summary_by_type", {}),
            "targets_not_searched": provider_metadata.get("targets_not_searched", []),
            "benchmark_recall_target_summary": _benchmark_recall_target_summary(provider_metadata),
            "registry_ambiguity_fanout_summary": provider_metadata.get("registry_ambiguity_fanout_summary", {}),
            "registry_lookup_terms": provider_metadata.get("registry_lookup_terms", []),
            "registry_lookup_attempts": provider_metadata.get("registry_lookup_attempts", []),
            "identity_obligation_review_records": provider_metadata.get("identity_obligation_review_records", []),
            "review_needed_upstream_entities": provider_metadata.get("review_needed_upstream_entities", []),
            "source_obligations": [
                {
                    "source_id": item.get("source_id"),
                    "source_label": item.get("source_label"),
                    "source_type": item.get("source_type"),
                    "trust_level": item.get("trust_level"),
                    "usage_obligation": item.get("usage_obligation"),
                    "required": item.get("required"),
                }
                for item in source_obligation_decisions
            ],
            "source_obligation_decisions": source_obligation_decisions,
            "source_obligation_summary": source_obligation_summary(source_obligation_decisions),
            "checkpoint_summary": checkpoint_summary(checkpoint_decisions),
            "checkpoint_decisions": checkpoint_decisions,
            "adaptive_actions": adaptive_actions,
            "checkpoint_warnings": sorted(set(checkpoint_warnings)),
            "stopped_for_review_reason": stopped_for_review_reason,
            "max_checkpoint_revisions_per_run": checkpoint_service.policy.max_revisions_per_run,
            "max_checkpoint_retries_per_stage": checkpoint_service.policy.max_retries_per_stage,
            "extraction_validation_results": provider_metadata.get("extraction_validation_results", []),
            "extraction_validation_issues": extraction_issues,
            "extraction_repair_results": repair_results,
            "extraction_recovery_records": provider_metadata.get("extraction_recovery_records", []),
            "extraction_repair_attempt_count": provider_metadata.get("extraction_repair_attempt_count", 0),
            "extraction_retry_attempt_count": provider_metadata.get("extraction_retry_attempt_count", 0),
            "extraction_recovery_outcome": provider_metadata.get("extraction_recovery_outcome", ""),
            "extraction_contract_state": extraction_contract_state(provider_metadata),
            "candidate_universe": candidate_universe_payload,
            "upstream_disambiguation_results": upstream_disambiguation_results,
            "cross_source_disambiguation_tasks": cross_source_disambiguation_tasks,
            "cross_source_disambiguation_execution": provider_metadata.get("cross_source_disambiguation_execution", []),
            "review_needed_universe_count": _review_needed_universe_count(candidate_universe_payload),
            "linked_branch_or_site_count": _linked_branch_or_site_count(provider_metadata.get("linked_entity_facts", [])),
            **smoke_cap_metadata,
            "coverage_checks": coverage_checks,
            "coverage_warnings": sorted(set(coverage_warnings)),
            "unresolved_candidate_gaps": dedupe_gap_payloads(unresolved_candidate_gaps, known_candidate_names=candidate_name_set(observations)),
            "entity_resolution_results": provider_metadata.get("entity_resolution_results", []),
            "linked_entity_facts": provider_metadata.get("linked_entity_facts", []),
            "entity_resolution_warnings": provider_metadata.get("entity_resolution_warnings", []),
            "discovery_iteration_count": discovery_iteration_count,
            "max_discovery_iterations": MAX_DISCOVERY_ITERATIONS,
            "max_candidate_universe_size": MAX_CANDIDATE_UNIVERSE_SIZE,
            "rejected_candidates": _rejected_candidate_summaries(normalized_candidates),
        },
    )


def _limit_smoke_candidates(candidate_scope: list[str], limit: int | None) -> list[str]:
    if limit is None or limit <= 0:
        return candidate_scope
    return candidate_scope[:limit]


def _limit_smoke_signal_tasks(tasks: list[RadarExecutionTask], limit: int | None) -> list[RadarExecutionTask]:
    if limit is None or limit <= 0:
        return tasks
    return tasks[:limit]


def _initial_provider_metadata(radar: dict[str, Any]) -> dict[str, Any]:
    task_context = radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}
    if not str(task_context.get("benchmark_profile") or "").startswith("benchmark_"):
        return {}
    targets = dict_list(task_context.get("benchmark_target_hints"))
    if not targets:
        return {}
    return {"benchmark_recall_targets": targets}


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


def _extract_retrieved_candidates(
    *,
    radar: dict[str, Any],
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    candidate_scope: list[str],
    completed_qualification_ids: list[str],
    events: list[LiveRadarPipelineEvent],
    smoke_candidate_limit: int | None,
) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any], list[str]]:
    retrieved_candidates = candidates_from_retrieved_sources(
        radar=radar,
        provider_metadata=provider_metadata,
        known_candidate_names=candidate_name_set(observations),
        known_source_refs={source.evidence_ref for source in sources if source.evidence_ref},
    )
    if not retrieved_candidates.candidate_observations:
        return sources, observations, provider_metadata, candidate_scope
    merged_sources, merged_observations, merged_metadata = _merge_result(sources, observations, provider_metadata, retrieved_candidates)
    merged_scope = _eligible_candidate_names(
        radar=radar,
        sources=merged_sources,
        observations=merged_observations,
        completed_qualification_ids=completed_qualification_ids,
    )
    merged_scope = _limit_smoke_candidates(merged_scope, smoke_candidate_limit)
    events.append(LiveRadarPipelineEvent(
        event_type="candidate_universe_extracted_from_retrieval",
        phase="collection",
        actor="application",
        node_name="retrieved_candidate_extraction",
        visibility="operator",
        summary=f"Extracted {len(retrieved_candidates.candidate_observations)} review-needed candidates from retrieved sources.",
        payload={
            "candidate_observation_count": len(retrieved_candidates.candidate_observations),
            "source_count": len(retrieved_candidates.sources),
            "extractions": retrieved_candidates.provider_metadata.get("retrieved_candidate_extractions", []),
        },
        source_refs=[source.evidence_ref for source in retrieved_candidates.sources if source.evidence_ref],
    ))
    return merged_sources, merged_observations, merged_metadata, merged_scope


def _run_search_expansion(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
    service: RadarSearchExpansionService,
    base_tasks: list[RadarExecutionTask],
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
    work_scheduler: RadarWorkScheduler,
    smoke_candidate_limit: int | None,
) -> tuple[list[RadarSourceEvidence], list[dict[str, Any]], dict[str, Any], list[str]]:
    expansion_plan = service.plan_expansion(
        radar=radar,
        candidate_scope=candidate_scope,
        provider_metadata=provider_metadata,
        coverage_checks=coverage_checks,
        unresolved_candidate_gaps=unresolved_candidate_gaps,
    )
    expansion_payload = expansion_plan.to_payload()
    provider_metadata = {
        **provider_metadata,
        "expansion_target_queue": [
            *dict_list(provider_metadata.get("expansion_target_queue")),
            *expansion_payload.get("targets", []),
        ],
        "expansion_target_summary_by_type": _merge_int_dicts(
            provider_metadata.get("expansion_target_summary_by_type"),
            expansion_payload.get("targets_by_type"),
        ),
        "search_expansion_query_variants_by_target": {
            **(
                provider_metadata.get("search_expansion_query_variants_by_target")
                if isinstance(provider_metadata.get("search_expansion_query_variants_by_target"), dict)
                else {}
            ),
            **expansion_payload.get("variants_by_target", {}),
        },
        "search_expansion_query_variants_by_target_type": {
            **(
                provider_metadata.get("search_expansion_query_variants_by_target_type")
                if isinstance(provider_metadata.get("search_expansion_query_variants_by_target_type"), dict)
                else {}
            ),
            **expansion_payload.get("variants_by_target_type", {}),
        },
        "targets_not_searched": _dedupe_target_records([
            *dict_list(provider_metadata.get("targets_not_searched")),
            *dict_list(expansion_payload.get("targets_not_selected")),
        ]),
        "search_expansion_selection_summary": merge_selection_summary(
            provider_metadata.get("search_expansion_selection_summary"),
            expansion_payload.get("selection_summary"),
        ),
        "search_expansion_selection_diagnostics": [
            *dict_list(provider_metadata.get("search_expansion_selection_diagnostics")),
            *dict_list(expansion_payload.get("selection_diagnostics")),
        ],
        "source_capability_strategy_summary": _source_capability_strategy_summary(
            radar=radar,
            expansion_plan=expansion_payload,
        ),
        "search_expansion_query_variants": [
            *dict_list(provider_metadata.get("search_expansion_query_variants")),
            *expansion_payload.get("variants", []),
        ],
    }
    if not expansion_plan.should_expand:
        return sources, observations, provider_metadata, candidate_scope
    schedule = schedule_guaranteed_expansion_variants(
        variants=list(expansion_plan.variants),
        targets=expansion_payload.get("targets", []),
        minimums=benchmark_target_probe_minimums(radar),
    )
    provider_metadata = {
        **provider_metadata,
        **schedule.to_metadata(),
        "targets_not_searched": _dedupe_target_records([
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
    tasks = service.tasks_from_plan(plan=scheduled_plan, base_task=base_tasks[0] if base_tasks else None)
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
                }
                for task in tasks
            ],
        ],
    }
    portfolio = work_scheduler.build_recall_expansion_portfolio(
        tasks=tasks,
        scheduled_variants=list(schedule.scheduled_variants),
        external_budget=external_budget,
    )
    provider_metadata = merge_work_scheduler_metadata(provider_metadata, portfolio.to_metadata())
    decisions_by_work_id = {decision.work_id: decision for decision in portfolio.ledger.decisions}
    for work_item in portfolio.work_items:
        task = work_item.task
        scheduled_variant = work_item.scheduled_variant
        if scheduled_variant is None:
            continue
        variant = scheduled_variant.variant
        admission_decision = decisions_by_work_id.get(work_item.work_id)
        if admission_decision is not None and not admission_decision.accepted:
            skipped = {
                "task_id": task.task_id,
                "query": task.query,
                "source_ids": list(task.source_ids),
                "target_id": variant.target_id,
                "target_type": variant.target_type,
                "budget_reserve_key": variant.budget_reserve_key,
                "execution_status": "work_admission_rejected",
                "not_searched_reason": admission_decision.reason,
                "budget_decision": admission_decision.budget_decision,
                "work_id": work_item.work_id,
                "lane": work_item.lane,
            }
            provider_metadata = {
                **provider_metadata,
                "targets_not_searched": [
                    *dict_list(provider_metadata.get("targets_not_searched")),
                    skipped,
                ],
            }
            events.append(LiveRadarPipelineEvent(
                event_type="search_expansion_skipped_budget_reserve",
                phase="collection",
                actor="application",
                node_name="search_expansion",
                visibility="operator",
                summary=f"Skipped recall expansion task {task.task_id}: {admission_decision.message}",
                payload=skipped,
            ))
            continue
        result = _run_task(
            provider=provider,
            radar=radar,
            task=task,
            radar_id=execution_plan.radar_id,
            budget=budget,
            external_budget=external_budget,
            semantic_reserve_key=variant.budget_reserve_key,
        )
        result_payload = _expansion_result_payload(
            task=task,
            variant=variant,
            result=result,
            budget_decision=result.provider_metadata.get("budget_decision", {}),
        )
        if result_payload["execution_status"] == "not_executed":
            not_executed = {
                **result_payload,
                "execution_status": "not_searched",
            }
            provider_metadata = {
                **provider_metadata,
                "targets_not_searched": [
                    *dict_list(provider_metadata.get("targets_not_searched")),
                    not_executed,
                ],
                "search_expansion_results": [
                    *dict_list(provider_metadata.get("search_expansion_results")),
                    result_payload,
                ],
            }
            events.append(LiveRadarPipelineEvent(
                event_type="search_expansion_skipped_external_budget",
                phase="collection",
                actor="application",
                node_name="search_expansion",
                visibility="operator",
                summary=f"Skipped recall expansion task {task.task_id}: external provider budget was exhausted.",
                payload=not_executed,
            ))
            continue
        gaps = gap_items(result)
        result = result.model_copy(update={
            "candidate_observations": [
                *result.candidate_observations,
                *gap_observations(gaps, origin_task_id=task.task_id),
            ],
        })
        sources, observations, provider_metadata = _merge_result(sources, observations, provider_metadata, result)
        executed_task_ids.append(f"{task.task_id}:search_expansion")
        unresolved_candidate_gaps.extend(gap_payloads(gaps, origin_task_id=task.task_id))
        provider_metadata = {
            **provider_metadata,
            "search_expansion_results": [
                *dict_list(provider_metadata.get("search_expansion_results")),
                {
                    **result_payload,
                },
            ],
        }
        events.append(LiveRadarPipelineEvent(
            event_type="search_expansion_executed",
            phase="collection",
            actor="application",
            node_name="search_expansion",
            visibility="operator",
            summary=f"Executed recall-first search expansion task {task.task_id}.",
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
        ))
    candidate_scope = _eligible_candidate_names(
        radar=radar,
        sources=sources,
        observations=observations,
        completed_qualification_ids=completed_qualification_ids,
    )
    return sources, observations, provider_metadata, _limit_smoke_candidates(candidate_scope, smoke_candidate_limit)


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


def _expansion_result_payload(
    *,
    task: RadarExecutionTask,
    variant: Any,
    result: WebSearchProviderResult,
    budget_decision: dict[str, Any],
) -> dict[str, Any]:
    status, reason = _expansion_execution_status(result=result, budget_decision=budget_decision)
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
    }


def _expansion_execution_status(*, result: WebSearchProviderResult, budget_decision: dict[str, Any]) -> tuple[str, str]:
    if isinstance(budget_decision, dict) and budget_decision.get("accepted") is False:
        kind = str(budget_decision.get("kind") or "")
        reason = str(budget_decision.get("reason") or "")
        if kind == "budget_reserve":
            return "not_executed", "not_executed_reserve_limited"
        if reason == "semantic_task_reserve_exhausted":
            return "not_executed", "semantic_task_budget_limited"
        return "not_executed", "not_executed_global_budget_limited"
    if result.sources:
        return "executed_source_found", ""
    return "executed_no_support", ""


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
    by_type: dict[str, int] = {}
    for target in targets:
        target_type = str(target.get("target_type") or "unknown")
        by_type[target_type] = by_type.get(target_type, 0) + 1
    searched_by_type: dict[str, int] = {}
    for target in targets:
        target_id = str(target.get("target_id") or "")
        if not target_id or target_id not in searched_ids:
            continue
        target_type = str(target.get("target_type") or "unknown")
        searched_by_type[target_type] = searched_by_type.get(target_type, 0) + 1
    not_searched_by_type: dict[str, int] = {}
    for item in not_searched:
        target_type = str(item.get("target_type") or "unknown")
        not_searched_by_type[target_type] = not_searched_by_type.get(target_type, 0) + 1
    return {
        "target_count": len(targets),
        "searched_target_count": len([target for target in targets if str(target.get("target_id") or "") in searched_ids]),
        "not_searched_target_count": len(not_searched),
        "by_target_type": by_type,
        "searched_by_target_type": searched_by_type,
        "not_searched_by_target_type": not_searched_by_type,
    }


def _external_budget_events(exhaustion_events: list[dict[str, object]]) -> list[LiveRadarPipelineEvent]:
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
        for item in exhaustion_events
    ]


def _append_review_needed_universe_entities(
    candidate_universe: list[dict[str, Any]],
    *,
    provider_metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    known = {str(item.get("legal_name") or "").casefold() for item in candidate_universe}
    result = list(candidate_universe)
    review_sources = [
        *dict_list(provider_metadata.get("upstream_disambiguation_results")),
        *[
            item
            for item in dict_list(provider_metadata.get("candidate_universe_gaps"))
            if _string_list(item.get("source_refs")) or str(item.get("entity_type") or "") in {"branch", "production_site", "asset", "project"}
        ],
        *dict_list(provider_metadata.get("review_needed_upstream_entities")),
    ]
    for item in review_sources:
        name = str(item.get("legal_name") or item.get("entity_name") or "").strip()
        if not name or name.casefold() in known:
            continue
        known.add(name.casefold())
        entity_type = str(item.get("entity_type") or "unknown_entity")
        result.append({
            "candidate_id": stable_id(name),
            "legal_name": name,
            "status": "unknown_review_needed",
            "origin_task_id": str(item.get("origin_task_id") or item.get("lookup_query") or "upstream_disambiguation"),
            "source_refs": list(item.get("source_refs", [])) if isinstance(item.get("source_refs"), list) else [],
            "gate_results": [],
            "rejection_reasons": [],
            "coverage_flags": [flag for flag in _string_list(item.get("review_flags")) if "candidate_universe" in flag or "coverage" in flag],
            "entity_type": entity_type,
            "resolution_status": str(item.get("resolution_status") or "review_needed"),
            "not_candidate_reason": str(item.get("not_candidate_reason") or ("not_standalone_legal_entity" if entity_type != "legal_entity" else "")),
            "review_flags": _string_list(item.get("review_flags")),
            "linked_fact_count": 0,
            "signal_searches": [],
        })
    return result


def _review_needed_universe_count(candidate_universe: list[dict[str, Any]]) -> int:
    return sum(1 for item in candidate_universe if str(item.get("status") or "") == "unknown_review_needed")


def _linked_branch_or_site_count(linked_facts: object) -> int:
    return sum(
        1
        for item in dict_list(linked_facts)
        if str(item.get("entity_type") or "") in {"branch", "production_site", "asset", "project"}
    )


def _upstream_disambiguation_events(
    results: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
) -> list[LiveRadarPipelineEvent]:
    events: list[LiveRadarPipelineEvent] = []
    tasks_by_entity = {str(item.get("entity_name") or ""): item for item in tasks}
    for item in results:
        name = str(item.get("legal_name") or item.get("entity_name") or "")
        task = tasks_by_entity.get(name)
        events.append(LiveRadarPipelineEvent(
            event_type="upstream_entity_retained_for_review",
            phase="collection",
            actor="application",
            node_name="upstream_disambiguation",
            visibility="operator",
            summary=f"Retained upstream entity {name} for human review.",
            payload=dict(item),
            source_refs=list(item.get("source_refs", [])) if isinstance(item.get("source_refs"), list) else [],
            candidate_refs=[name] if name else [],
        ))
        if task:
            events.append(LiveRadarPipelineEvent(
                event_type="cross_source_disambiguation_requested",
                phase="planning",
                actor="application",
                node_name="upstream_disambiguation",
                visibility="operator",
                summary=f"Planned cross-source disambiguation for {name}.",
                payload=dict(task),
                candidate_refs=[name] if name else [],
            ))
    return events


def _string_list(value: object) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []
