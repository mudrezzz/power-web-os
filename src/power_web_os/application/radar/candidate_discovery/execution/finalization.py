"""Final result projection for candidate discovery staged execution."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.checkpoints import checkpoint_summary
from power_web_os.application.radar.candidate_discovery.extraction.diagnostics import (
    extraction_contract_state,
    extraction_repair_results,
    extraction_validation_event,
    extraction_validation_issues,
)
from power_web_os.application.radar.candidate_discovery.universe import candidate_name, candidate_name_set, candidate_universe_entries, dedupe_gap_payloads, dict_list, first_task_id, gap_payloads
from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarPipelineEvent,
    WebSearchProviderResult,
)
from power_web_os.application.radar.candidate_discovery.execution.context import CandidateDiscoveryExecutionContext
from power_web_os.application.radar.candidate_discovery.execution.expansion_diagnostics import (
    _results_by_target,
    _results_by_target_type,
    _search_expansion_execution_summary,
    _search_expansion_target_coverage,
    _target_probe_guarantees,
)
from power_web_os.application.radar.candidate_discovery.execution.finalization_universe import _append_benchmark_present_universe_entities, _append_review_needed_universe_entities, _linked_branch_or_site_count, _review_needed_universe_count, _upstream_disambiguation_events
from power_web_os.application.radar.candidate_discovery.execution.finalization_metadata import (
    _apply_smoke_candidate_promotion_cap,
    _benchmark_recall_target_summary,
    _budget_metadata,
    _external_budget_events,
    _legal_subsidiary_completion_summary,
)
from power_web_os.application.radar.candidate_discovery.execution.finalization_signals import (
    _signal_projection_observations,
    _signal_projection_candidates,
    _signal_handoff_status,
    _signal_monitoring_pending_count,
)
from power_web_os.application.radar.candidate_discovery.execution.reconciliation import (
    CandidateDiscoveryOutcomeReconciler,
)
from power_web_os.application.radar.candidate_discovery.execution.state import CandidateDiscoveryExecutionState
from power_web_os.application.radar.candidate_discovery.execution.task_runner import TaskExecutionService
from power_web_os.application.radar_source_obligations import obligation_decisions_from_plan, source_obligation_summary


class FinalizationProjector:
    """Projects execution state into provider result, events, and run metadata.

    Owns:
    - Final provider result, product-safe metadata, candidate universe, source
      obligations, budget/cache metadata, and execution events projection.

    Does not own:
    - Running provider tasks, changing checkpoint decisions, or selecting
      expansion targets.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#finalizationprojector
    """

    def __init__(
        self,
        task_service: TaskExecutionService | None = None,
        outcome_reconciler: CandidateDiscoveryOutcomeReconciler | None = None,
    ) -> None:
        self._task_service = task_service or TaskExecutionService()
        self._outcome_reconciler = outcome_reconciler or CandidateDiscoveryOutcomeReconciler()

    def project(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> tuple[WebSearchProviderResult, list[LiveRadarPipelineEvent], dict[str, Any]]:
        self._record_warnings(context, state)
        extraction_issues, repair_results = self._record_extraction_issues(state)
        signal_projected_observations = _signal_projection_observations(context, state, state.observations)
        normalized_candidates = self._task_service.normalized_candidates(
            radar=context.radar,
            sources=state.sources,
            observations=signal_projected_observations,
        )
        normalized_candidates, observations, smoke_gaps, smoke_metadata = _apply_smoke_candidate_promotion_cap(
            candidates=normalized_candidates,
            observations=signal_projected_observations,
            smoke_candidate_limit=context.external_budget.settings.smoke_max_candidates,
        )
        normalized_candidates = _signal_projection_candidates(context, state, normalized_candidates)
        unresolved_gaps = self._unresolved_gaps(state, smoke_gaps)
        self._record_smoke_cap_event(state, smoke_gaps, smoke_metadata)
        universe_payload = self._candidate_universe_payload(
            context,
            state,
            normalized_candidates,
            observations,
            unresolved_gaps,
        )
        reconciliation = self._outcome_reconciler.reconcile(
            public_candidates=normalized_candidates,
            candidate_universe=universe_payload,
            unresolved_gaps=unresolved_gaps,
        )
        universe_payload = reconciliation.candidate_universe
        source_obligation_decisions = self._source_obligation_decisions(context, state, observations)
        self._record_final_events(context, state, source_obligation_decisions)
        target_probe_payload = _target_probe_guarantees(provider_metadata=state.provider_metadata, radar=context.radar)
        result = self._provider_result(state, observations)
        metadata = self._metadata(
            context=context,
            state=state,
            observations=observations,
            normalized_candidates=normalized_candidates,
            unresolved_gaps=unresolved_gaps,
            universe_payload=universe_payload,
            source_obligation_decisions=source_obligation_decisions,
            smoke_metadata=smoke_metadata,
            extraction_issues=extraction_issues,
            repair_results=repair_results,
            target_probe_payload=target_probe_payload,
            outcome_reconciliation=reconciliation.summary,
            user_visible_candidates=reconciliation.user_visible_candidates,
            product_acceptance_ledger=reconciliation.product_acceptance_ledger,
        )
        return result, state.events, metadata

    def _record_warnings(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> None:
        for warnings in (state.signal_budget_warnings, context.task_budget.warnings):
            if warnings:
                state.coverage_warnings.extend(warnings)
                state.events.append(self._task_service.events.budget_warning_event(warnings))
        if state.useful_result_warnings:
            state.coverage_warnings.extend(state.useful_result_warnings)
            state.events.append(self._task_service.events.useful_result_warning_event(state.useful_result_warnings))

    def _record_extraction_issues(
        self,
        state: CandidateDiscoveryExecutionState,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        extraction_issues = extraction_validation_issues(state.provider_metadata)
        repair_results = extraction_repair_results(state.provider_metadata)
        if not extraction_issues:
            return extraction_issues, repair_results
        issue_codes = sorted({
            str(issue.get("code"))
            for issue in extraction_issues
            if str(issue.get("code", "")).strip()
        })
        state.coverage_warnings.extend([f"Extraction contract issue: {code}" for code in issue_codes])
        state.events.append(extraction_validation_event(extraction_issues, repair_results))
        return extraction_issues, repair_results

    def _candidate_universe_payload(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        normalized_candidates: list[Any],
        observations: list[dict[str, Any]],
        unresolved_gaps: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        candidate_universe = candidate_universe_entries(
            candidates=normalized_candidates,
            completed_qualification_ids=state.completed_qualification_ids,
            origin_task_id=first_task_id(context.execution_plan.tasks),
            gap_names={candidate_name(item) for item in unresolved_gaps if candidate_name(item)},
        )
        with_signal_statuses = self._task_service.projection.candidate_universe_with_signal_statuses(
            candidate_universe,
            state.signal_search_statuses,
        )
        with_entity_metadata = self._task_service.merger.candidate_universe_with_entity_metadata(
            with_signal_statuses,
            observations,
        )
        with_review_needed = _append_review_needed_universe_entities(
            with_entity_metadata,
            provider_metadata=state.provider_metadata,
        )
        return _append_benchmark_present_universe_entities(
            with_review_needed,
            radar=context.radar,
            provider_metadata=state.provider_metadata,
            sources=state.sources,
        )

    def _source_obligation_decisions(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        observations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return obligation_decisions_from_plan(
            global_policy=dict(context.radar.get("global_search_policy") or {}),
            steps=context.execution_plan.tasks,
            source_policy_decisions=context.source_policy_decisions or [],
            source_provider_outcomes=state.provider_metadata.get("source_provider_outcomes", []),
            sources=state.sources,
            observations=observations,
        )

    def _record_final_events(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        source_obligation_decisions: list[dict[str, Any]],
    ) -> None:
        upstream_results = dict_list(state.provider_metadata.get("upstream_disambiguation_results"))
        cross_tasks = dict_list(state.provider_metadata.get("cross_source_disambiguation_tasks"))
        if upstream_results:
            state.events.extend(_upstream_disambiguation_events(upstream_results, cross_tasks))
        state.events.extend(self._task_service.events.source_obligation_events(source_obligation_decisions))
        state.events.extend(_external_budget_events(context.external_budget.exhaustion_events))

    def _provider_result(
        self,
        state: CandidateDiscoveryExecutionState,
        observations: list[dict[str, Any]],
    ) -> WebSearchProviderResult:
        return WebSearchProviderResult(
            sources=self._task_service.dedupe_sources(state.sources),
            candidate_observations=self._task_service.merger.merge_candidate_observations(observations),
            provider_metadata={
                **state.provider_metadata,
                "execution_mode": "qualification_first_iterative_coverage",
            },
        )

    def _unresolved_gaps(
        self,
        state: CandidateDiscoveryExecutionState,
        smoke_gaps: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            *state.unresolved_candidate_gaps,
            *smoke_gaps,
            *gap_payloads(
                dict_list(state.provider_metadata.get("candidate_universe_gaps")),
                origin_task_id="entity_resolution",
            ),
        ]

    def _record_smoke_cap_event(
        self,
        state: CandidateDiscoveryExecutionState,
        smoke_gaps: list[dict[str, Any]],
        smoke_metadata: dict[str, Any],
    ) -> None:
        if not smoke_gaps:
            return
        state.events.append(LiveRadarPipelineEvent(
            event_type="smoke_candidate_cap_applied",
            phase="validation",
            actor="application",
            node_name="smoke_candidate_cap",
            visibility="operator",
            summary=(
                f"Smoke profile promoted {smoke_metadata['promoted_candidate_count']} candidates "
                f"and kept {smoke_metadata['diagnostic_candidate_count']} as diagnostic gaps."
            ),
            payload=smoke_metadata,
            candidate_refs=[item["legal_name"] for item in smoke_gaps if item.get("legal_name")],
        ))

    def _metadata(
        self,
        *,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
        observations: list[dict[str, Any]],
        normalized_candidates: list[Any],
        unresolved_gaps: list[dict[str, Any]],
        universe_payload: list[dict[str, Any]],
        source_obligation_decisions: list[dict[str, Any]],
        smoke_metadata: dict[str, Any],
        extraction_issues: list[dict[str, Any]],
        repair_results: list[dict[str, Any]],
        target_probe_payload: dict[str, Any],
        outcome_reconciliation: dict[str, Any],
        user_visible_candidates: list[dict[str, Any]],
        product_acceptance_ledger: list[dict[str, Any]],
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {"execution_mode": "qualification_first_iterative_coverage"}
        metadata.update(self._execution_metadata(context, state))
        metadata.update(_budget_metadata(context, state))
        metadata.update(self._retrieval_metadata(state))
        metadata.update(self._expansion_metadata(state, target_probe_payload))
        metadata.update(self._registry_metadata(state))
        metadata.update(self._source_obligation_metadata(source_obligation_decisions))
        metadata.update(self._checkpoint_metadata(context, state))
        metadata.update(self._extraction_metadata(state, extraction_issues, repair_results))
        metadata.update(self._universe_metadata(state, observations, universe_payload, unresolved_gaps))
        metadata.update(self._coverage_metadata(context, state))
        metadata.update(smoke_metadata)
        metadata["candidate_discovery_reconciliation"] = outcome_reconciliation
        metadata["user_visible_candidates"] = user_visible_candidates
        metadata["product_acceptance_ledger"] = product_acceptance_ledger
        metadata["rejected_candidates"] = self._task_service.projection.rejected_candidate_summaries(
            normalized_candidates
        )
        return metadata

    @staticmethod
    def _execution_metadata(
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> dict[str, Any]:
        task_context = context.radar.get("task_context") if isinstance(context.radar.get("task_context"), dict) else {}
        benchmark_target_hints = dict_list(task_context.get("benchmark_target_hints"))
        benchmark_hints_used = bool(benchmark_target_hints)
        benchmark_profile = str(task_context.get("benchmark_profile") or "")
        return {
            "retrieval_plan": context.retrieval_plan.model_dump(),
            "executed_task_count": len(state.executed_task_ids),
            "executed_task_ids": state.executed_task_ids,
            "benchmark_profile": benchmark_profile,
            "benchmark_mode": (
                str(task_context.get("benchmark_mode") or ("guided" if benchmark_hints_used else "blind"))
                if benchmark_profile
                else ""
            ),
            "benchmark_hints_used": bool(task_context.get("benchmark_hints_used", benchmark_hints_used)),
            "benchmark_target_hint_count": len(benchmark_target_hints),
            "gate_results": state.gate_results,
            "signal_task_count": state.signal_task_count,
            "signal_execution_mode": context.signal_execution_mode,
            "signal_monitoring_handoff_status": _signal_handoff_status(context, state),
            "signal_monitoring_pending_count": _signal_monitoring_pending_count(state),
            "candidate_scope": state.candidate_scope,
            "signal_candidate_scope": state.signal_candidate_scope,
            "signal_search_statuses": state.signal_search_statuses,
            "signal_budget_warnings": state.signal_budget_warnings,
            "max_signal_candidates": len(state.signal_candidate_scope),
            "max_signal_tasks": context.budget_settings.max_signal_tasks_per_candidate_signal,
            "max_web_tasks_per_subject": context.budget_settings.compatibility_max_web_tasks_per_subject,
        }

    @staticmethod
    def _retrieval_metadata(state: CandidateDiscoveryExecutionState) -> dict[str, Any]:
        return {
            "source_verification_results": state.provider_metadata.get("source_verification_results", []),
            "retrieval_provider": state.provider_metadata.get("retrieval_provider"),
            "retrieval_engine": state.provider_metadata.get("retrieval_engine"),
            "retrieved_sources": state.provider_metadata.get("retrieved_sources", []),
            "retrieval_source_outcomes": state.provider_metadata.get("retrieval_source_outcomes", []),
            "retrieved_source_count": state.provider_metadata.get("retrieved_source_count", 0),
            "source_outcomes": state.provider_metadata.get("source_outcomes", []),
            "source_provider_outcomes": state.provider_metadata.get("source_provider_outcomes", []),
            "source_capability_strategy_summary": state.provider_metadata.get("source_capability_strategy_summary", {}),
        }

    @staticmethod
    def _expansion_metadata(
        state: CandidateDiscoveryExecutionState,
        target_probe_payload: dict[str, Any],
    ) -> dict[str, Any]:
        provider_metadata = state.provider_metadata
        return {
            "expansion_target_queue": provider_metadata.get("expansion_target_queue", []),
            "search_expansion_tasks": provider_metadata.get("search_expansion_tasks", []),
            "search_expansion_query_variants": provider_metadata.get("search_expansion_query_variants", []),
            "search_expansion_query_variants_by_target": (
                provider_metadata.get("search_expansion_query_variants_by_target", {})
            ),
            "search_expansion_selection_summary": provider_metadata.get("search_expansion_selection_summary", {}),
            "search_expansion_selection_diagnostics": provider_metadata.get(
                "search_expansion_selection_diagnostics", []
            ),
            "search_expansion_results": provider_metadata.get("search_expansion_results", []),
            "search_expansion_results_by_target": _results_by_target(
                provider_metadata.get("search_expansion_results", [])
            ),
            "search_expansion_results_by_target_type": _results_by_target_type(
                provider_metadata.get("search_expansion_results", [])
            ),
            "search_expansion_execution_summary": _search_expansion_execution_summary(provider_metadata),
            "search_expansion_target_coverage": _search_expansion_target_coverage(provider_metadata),
            "target_probe_guarantees": target_probe_payload["summary"],
            "target_probe_guarantee_failures": target_probe_payload["failures"],
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
        }

    @staticmethod
    def _registry_metadata(state: CandidateDiscoveryExecutionState) -> dict[str, Any]:
        return {
            "registry_ambiguity_fanout_summary": state.provider_metadata.get("registry_ambiguity_fanout_summary", {}),
            "registry_lookup_terms": state.provider_metadata.get("registry_lookup_terms", []),
            "registry_lookup_attempts": state.provider_metadata.get("registry_lookup_attempts", []),
            "identity_obligation_review_records": state.provider_metadata.get("identity_obligation_review_records", []),
            "review_needed_upstream_entities": state.provider_metadata.get("review_needed_upstream_entities", []),
        }

    @staticmethod
    def _source_obligation_metadata(source_obligation_decisions: list[dict[str, Any]]) -> dict[str, Any]:
        return {
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
        }

    @staticmethod
    def _checkpoint_metadata(
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> dict[str, Any]:
        return {
            "checkpoint_summary": checkpoint_summary(state.checkpoint_decisions),
            "checkpoint_decisions": state.checkpoint_decisions,
            "adaptive_actions": state.adaptive_actions,
            "checkpoint_warnings": sorted(set(state.checkpoint_warnings)),
            "stopped_for_review_reason": state.stopped_for_review_reason,
            "max_checkpoint_revisions_per_run": context.checkpoint_service.policy.max_revisions_per_run,
            "max_checkpoint_retries_per_stage": context.checkpoint_service.policy.max_retries_per_stage,
        }

    @staticmethod
    def _extraction_metadata(
        state: CandidateDiscoveryExecutionState,
        extraction_issues: list[dict[str, Any]],
        repair_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "extraction_validation_results": state.provider_metadata.get("extraction_validation_results", []),
            "extraction_validation_issues": extraction_issues,
            "extraction_repair_results": repair_results,
            "extraction_recovery_records": state.provider_metadata.get("extraction_recovery_records", []),
            "extraction_repair_attempt_count": state.provider_metadata.get("extraction_repair_attempt_count", 0),
            "extraction_retry_attempt_count": state.provider_metadata.get("extraction_retry_attempt_count", 0),
            "extraction_recovery_outcome": state.provider_metadata.get("extraction_recovery_outcome", ""),
            "extraction_contract_state": extraction_contract_state(state.provider_metadata),
            "post_extraction_salvage_records": state.provider_metadata.get("post_extraction_salvage_records", []),
            "post_extraction_salvage_count": state.provider_metadata.get("post_extraction_salvage_count", 0),
            "post_extraction_salvage_outcome": state.provider_metadata.get("post_extraction_salvage_outcome", ""),
            "post_extraction_salvage_unrecovered_reason": state.provider_metadata.get(
                "post_extraction_salvage_unrecovered_reason", ""
            ),
        }

    @staticmethod
    def _universe_metadata(
        state: CandidateDiscoveryExecutionState,
        observations: list[dict[str, Any]],
        universe_payload: list[dict[str, Any]],
        unresolved_gaps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "candidate_universe": universe_payload,
            "upstream_disambiguation_results": dict_list(state.provider_metadata.get("upstream_disambiguation_results")),
            "cross_source_disambiguation_tasks": dict_list(state.provider_metadata.get("cross_source_disambiguation_tasks")),
            "cross_source_disambiguation_execution": (
                state.provider_metadata.get("cross_source_disambiguation_execution", [])
            ),
            "review_needed_universe_count": _review_needed_universe_count(universe_payload),
            "linked_branch_or_site_count": _linked_branch_or_site_count(
                state.provider_metadata.get("linked_entity_facts", [])
            ),
            "unresolved_candidate_gaps": dedupe_gap_payloads(
                unresolved_gaps,
                known_candidate_names=candidate_name_set(observations),
            ),
            "entity_resolution_results": state.provider_metadata.get("entity_resolution_results", []),
            "linked_entity_facts": state.provider_metadata.get("linked_entity_facts", []),
            "entity_resolution_warnings": state.provider_metadata.get("entity_resolution_warnings", []),
        }

    @staticmethod
    def _coverage_metadata(
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> dict[str, Any]:
        return {
            "coverage_checks": state.coverage_checks,
            "coverage_warnings": sorted(set(state.coverage_warnings)),
            "discovery_iteration_count": state.discovery_iteration_count,
            "max_discovery_iterations": context.max_discovery_iterations,
            "max_candidate_universe_size": context.max_candidate_universe_size,
        }
