"""Final result projection for candidate discovery staged execution."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarPipelineEvent,
    RadarExecutionPlan,
    RadarSourceEvidence,
    WebSearchProviderResult,
)
from power_web_os.application.live_radar_checkpoints import RadarExecutionCheckpointService, checkpoint_summary
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget, RadarExecutionBudgetSettings
from power_web_os.application.live_radar_external_budget import RadarExternalCallBudget
from power_web_os.application.live_radar_extraction_diagnostics import (
    extraction_contract_state,
    extraction_repair_results,
    extraction_validation_event,
    extraction_validation_issues,
)
from power_web_os.application.live_radar_useful_budget import UsefulResultBudget
from power_web_os.application.radar_source_obligations import obligation_decisions_from_plan, source_obligation_summary
from power_web_os.application.radar.candidate_discovery.execution.context import CandidateDiscoveryExecutionContext
from power_web_os.application.radar.candidate_discovery.execution.expansion_diagnostics import (
    _is_executed_expansion_result,
    _results_by_target,
    _results_by_target_type,
    _search_expansion_execution_summary,
    _search_expansion_target_coverage,
    _target_probe_guarantees,
)
from power_web_os.application.radar.candidate_discovery.execution.finalization_universe import (
    _append_review_needed_universe_entities,
    _linked_branch_or_site_count,
    _review_needed_universe_count,
    _upstream_disambiguation_events,
)
from power_web_os.application.radar.candidate_discovery.execution.merge import (
    candidate_universe_with_entity_metadata as _candidate_universe_with_entity_metadata,
    merge_candidate_observations as _merge_candidate_observations,
)
from power_web_os.application.radar.candidate_discovery.execution.projection import (
    budget_warning_event as _budget_warning_event,
    candidate_universe_with_signal_statuses as _candidate_universe_with_signal_statuses,
    rejected_candidate_summaries as _rejected_candidate_summaries,
    source_obligation_events as _source_obligation_events,
)
from power_web_os.application.radar.candidate_discovery.execution.state import CandidateDiscoveryExecutionState
from power_web_os.application.radar.candidate_discovery.execution.task_runner import (
    dedupe_sources as _dedupe_sources,
    normalized_candidates as _normalized_candidates,
    useful_result_warning_event as _useful_result_warning_event,
)
from power_web_os.application.live_radar_universe import (
    candidate_name,
    candidate_name_set,
    candidate_universe_entries,
    dedupe_gap_payloads,
    dict_list,
    first_task_id,
    gap_payloads,
    stable_id,
)
from power_web_os.integrations.live_radar_source_verification import SourceVerificationCache


class FinalizationProjector:
    """Projects execution state into provider result, events, and run metadata."""

    def project(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> tuple[WebSearchProviderResult, list[LiveRadarPipelineEvent], dict[str, Any]]:
        return _finalize_staged_execution_result(
            radar=context.radar,
            execution_plan=context.execution_plan,
            retrieval_plan=context.retrieval_plan,
            sources=state.sources,
            observations=state.observations,
            provider_metadata=state.provider_metadata,
            events=state.events,
            executed_task_ids=state.executed_task_ids,
            completed_qualification_ids=state.completed_qualification_ids,
            gate_results=state.gate_results,
            candidate_scope=state.candidate_scope,
            coverage_checks=state.coverage_checks,
            unresolved_candidate_gaps=state.unresolved_candidate_gaps,
            coverage_warnings=state.coverage_warnings,
            useful_result_warnings=state.useful_result_warnings,
            useful_result_retry_records=state.useful_result_retry_records,
            checkpoint_decisions=state.checkpoint_decisions,
            adaptive_actions=state.adaptive_actions,
            checkpoint_warnings=state.checkpoint_warnings,
            stopped_for_review_reason=state.stopped_for_review_reason,
            discovery_iteration_count=state.discovery_iteration_count,
            signal_task_count=state.signal_task_count,
            signal_budget_warnings=state.signal_budget_warnings,
            signal_candidate_scope=state.signal_candidate_scope,
            signal_search_statuses=state.signal_search_statuses,
            task_budget=context.task_budget,
            budget_settings=context.budget_settings,
            external_budget=context.external_budget,
            useful_budget=context.useful_budget,
            checkpoint_service=context.checkpoint_service,
            verification_cache=context.verification_cache,
            source_policy_decisions=context.source_policy_decisions,
            max_discovery_iterations=context.max_discovery_iterations,
            max_candidate_universe_size=context.max_candidate_universe_size,
        )


def _finalize_staged_execution_result(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    retrieval_plan: Any,
    sources: list[RadarSourceEvidence],
    observations: list[dict[str, Any]],
    provider_metadata: dict[str, Any],
    events: list[LiveRadarPipelineEvent],
    executed_task_ids: list[str],
    completed_qualification_ids: list[str],
    gate_results: list[dict[str, Any]],
    candidate_scope: list[str],
    coverage_checks: list[dict[str, Any]],
    unresolved_candidate_gaps: list[dict[str, Any]],
    coverage_warnings: list[str],
    useful_result_warnings: list[str],
    useful_result_retry_records: list[dict[str, Any]],
    checkpoint_decisions: list[dict[str, Any]],
    adaptive_actions: list[dict[str, Any]],
    checkpoint_warnings: list[str],
    stopped_for_review_reason: str,
    discovery_iteration_count: int,
    signal_task_count: int,
    signal_budget_warnings: list[str],
    signal_candidate_scope: list[str],
    signal_search_statuses: list[dict[str, Any]],
    task_budget: RadarExecutionBudget,
    budget_settings: RadarExecutionBudgetSettings,
    external_budget: RadarExternalCallBudget,
    useful_budget: UsefulResultBudget,
    checkpoint_service: RadarExecutionCheckpointService,
    verification_cache: SourceVerificationCache,
    source_policy_decisions: list[dict[str, Any]] | None,
    max_discovery_iterations: int,
    max_candidate_universe_size: int,
) -> tuple[WebSearchProviderResult, list[LiveRadarPipelineEvent], dict[str, Any]]:
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
                "search_expansion_target_coverage": _search_expansion_target_coverage(provider_metadata),
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
                "legal_subsidiary_completion_summary": _legal_subsidiary_completion_summary(provider_metadata),
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
                "max_discovery_iterations": max_discovery_iterations,
                "max_candidate_universe_size": max_candidate_universe_size,
                "rejected_candidates": _rejected_candidate_summaries(normalized_candidates),
            },
        )




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

def _legal_subsidiary_completion_summary(provider_metadata: dict[str, Any]) -> dict[str, Any]:
    target_type = "known_subsidiary_or_legal_entity_target"
    targets = [
        item for item in dict_list(provider_metadata.get("expansion_target_queue"))
        if str(item.get("target_type") or "") == target_type
    ]
    variants = [
        item for item in dict_list(provider_metadata.get("search_expansion_query_variants"))
        if str(item.get("target_type") or "") == target_type
    ]
    results = [
        item for item in dict_list(provider_metadata.get("search_expansion_results"))
        if str(item.get("target_type") or "") == target_type
    ]
    not_searched = [
        item for item in dict_list(provider_metadata.get("targets_not_searched"))
        if str(item.get("target_type") or "") == target_type
    ]
    diagnostics = [
        item for item in dict_list(provider_metadata.get("search_expansion_selection_diagnostics"))
        if str(item.get("target_type") or "") == target_type
    ]
    if not (targets or variants or results or not_searched or diagnostics):
        return {}
    executed = [item for item in results if _is_executed_expansion_result(item)]
    return {
        "target_type": target_type,
        "generated_count": len(targets),
        "selected_variant_count": len({str(item.get("target_id") or "") for item in variants if str(item.get("target_id") or "")}),
        "executed_count": len({str(item.get("target_id") or "") for item in executed if str(item.get("target_id") or "")}),
        "not_searched_count": len({str(item.get("target_id") or "") for item in not_searched if str(item.get("target_id") or "")}),
        "selection_diagnostic_count": len(diagnostics),
        "not_searched_by_reason": _count_by_reason(not_searched),
        "selection_diagnostics_by_reason": _count_by_reason(diagnostics),
    }

def _count_by_reason(items: list[dict[str, Any]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in items:
        reason = str(item.get("not_searched_reason") or item.get("reason") or "unknown")
        result[reason] = result.get(reason, 0) + 1
    return result

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
