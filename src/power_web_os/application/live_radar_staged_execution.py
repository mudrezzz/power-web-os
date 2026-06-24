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
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget, budget_settings_from_context
from power_web_os.application.live_radar_execution_plan import scoped_execution_task
from power_web_os.application.live_radar_extraction_diagnostics import (
    extraction_contract_state,
    extraction_repair_results,
    extraction_validation_event,
    extraction_validation_issues,
)
from power_web_os.application.live_radar_retrieval_plan import retrieval_plan_from_execution_plan
from power_web_os.application.radar_source_obligations import (
    obligation_decisions_from_plan,
    source_obligation_summary,
)
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
)

MAX_DISCOVERY_ITERATIONS = 2
MAX_CANDIDATE_UNIVERSE_SIZE = 50
def run_staged_radar_execution(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
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
    source_policy_decisions: list[dict[str, Any]] | None = None,
) -> tuple[WebSearchProviderResult, list[LiveRadarPipelineEvent], dict[str, Any]]:
    sources: list[RadarSourceEvidence] = []
    observations: list[dict[str, Any]] = []
    provider_metadata: dict[str, Any] = {}
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
    )
    task_budget = RadarExecutionBudget(budget_settings)
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
    retrieval_plan = retrieval_plan_from_execution_plan(execution_plan)

    discovery_tasks = _tasks_for_stage(execution_plan, "qualification_discovery")
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
        ),
    )
    sources, observations = recovery_state.sources, recovery_state.observations
    provider_metadata, candidate_scope = recovery_state.provider_metadata, recovery_state.candidate_scope
    stopped_for_review_reason = recovery_state.stopped_for_review_reason

    gate_tasks = _tasks_for_stage(execution_plan, "qualification_gate")
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
    )

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

    coverage_tasks = _tasks_for_stage(execution_plan, "coverage_check")
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
        )
        candidate_scope = _eligible_candidate_names(
            radar=radar,
            sources=sources,
            observations=observations,
            completed_qualification_ids=completed_qualification_ids,
        )

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
        ),
    )
    sources, observations = recovery_state.sources, recovery_state.observations
    provider_metadata, candidate_scope = recovery_state.provider_metadata, recovery_state.candidate_scope
    stopped_for_review_reason = stopped_for_review_reason or recovery_state.stopped_for_review_reason

    pre_signal_source_obligations = obligation_decisions_from_plan(
        global_policy=dict(radar.get("global_search_policy") or {}),
        steps=execution_plan.tasks,
        source_policy_decisions=source_policy_decisions or [],
        source_provider_outcomes=provider_metadata.get("source_provider_outcomes", []),
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
    can_run_signal_search = pre_signal_decision.action == "continue" and pre_signal_decision.should_continue and pre_signal_decision.should_run_signal_search
    if not can_run_signal_search:
        stopped_for_review_reason = stopped_for_review_reason or pre_signal_decision.message

    signal_task_count = 0
    signal_budget_warnings: list[str] = []
    signal_candidate_scope = list(candidate_scope)
    signal_search_statuses: list[dict[str, Any]] = []
    if can_run_signal_search:
        for task in _tasks_for_stage(execution_plan, "signal_search"):
            for scoped_candidate_name in signal_candidate_scope:
                scoped_task = scoped_execution_task(task, candidate_scope=[scoped_candidate_name])
                events.append(_signal_planned_event(scoped_task))
                result = _run_task(provider=provider, radar=radar, task=scoped_task, radar_id=execution_plan.radar_id, budget=task_budget)
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
        for task in _tasks_for_stage(execution_plan, "signal_search"):
            for scoped_candidate_name in signal_candidate_scope:
                decision = {
                    "state": "not_searched_policy_limited",
                    "reason": pre_signal_decision.reason_code,
                    "message": pre_signal_decision.message,
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
    candidate_universe = candidate_universe_entries(
        candidates=normalized_candidates, completed_qualification_ids=completed_qualification_ids,
        origin_task_id=first_task_id(execution_plan.tasks), gap_names={candidate_name(item) for item in unresolved_candidate_gaps if candidate_name(item)},
    )
    unresolved_candidate_gaps.extend(gap_payloads(dict_list(provider_metadata.get("candidate_universe_gaps")), origin_task_id="entity_resolution"))
    candidate_universe_payload = _candidate_universe_with_entity_metadata(
        _candidate_universe_with_signal_statuses(candidate_universe, signal_search_statuses),
        observations,
    )
    source_obligation_decisions = obligation_decisions_from_plan(
        global_policy=dict(radar.get("global_search_policy") or {}),
        steps=execution_plan.tasks,
        source_policy_decisions=source_policy_decisions or [],
        source_provider_outcomes=provider_metadata.get("source_provider_outcomes", []),
    )
    events.extend(_source_obligation_events(source_obligation_decisions))
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
            "budget_counters": {"total": task_budget.total_count, "by_key": dict(task_budget.counts)},
            "budget_exhaustion_events": list(task_budget.exhaustion_events),
            "web_task_counts_by_subject": task_budget.counts,
            "web_task_budget_warnings": task_budget.warnings,
            "useful_result_retry_records": useful_result_retry_records,
            "useful_result_warnings": useful_result_warnings,
            "min_useful_sources_per_discovery_task": useful_budget.min_sources,
            "min_candidates_per_discovery_task": useful_budget.min_candidates,
            "max_discovery_retries_per_task": useful_budget.max_retries,
            "source_verification_results": provider_metadata.get("source_verification_results", []),
            "retrieval_provider": provider_metadata.get("retrieval_provider"),
            "retrieval_engine": provider_metadata.get("retrieval_engine"),
            "retrieved_sources": provider_metadata.get("retrieved_sources", []),
            "retrieval_source_outcomes": provider_metadata.get("retrieval_source_outcomes", []),
            "retrieved_source_count": provider_metadata.get("retrieved_source_count", 0),
            "source_outcomes": provider_metadata.get("source_outcomes", []),
            "source_provider_outcomes": provider_metadata.get("source_provider_outcomes", []),
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
            "extraction_contract_state": extraction_contract_state(provider_metadata),
            "candidate_universe": candidate_universe_payload,
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
