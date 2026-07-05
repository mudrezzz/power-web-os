"""Execute qualification-first Radar plans through the provider port."""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarPipelineEvent,
    RadarExecutionPlan,
    WebSearchProvider,
    WebSearchProviderResult,
)
from power_web_os.application.radar.candidate_discovery.checkpoints.recovery import RadarCheckpointActionExecutor
from power_web_os.application.radar.candidate_discovery.checkpoints import RadarExecutionCheckpointPolicy, RadarExecutionCheckpointService
from power_web_os.application.live_radar_cross_disambiguation import execute_cross_source_disambiguation
from power_web_os.application.radar.candidate_discovery.execution.task_budget import RadarExecutionBudget
from power_web_os.application.radar.shared.budgets import RadarExternalCallBudget
from power_web_os.application.radar.shared.budgets.external_context import (
    current_external_call_budget,
    external_call_budget_context,
)
from power_web_os.application.radar.candidate_discovery.planning.retrieval_plan import retrieval_plan_from_execution_plan
from power_web_os.application.radar.candidate_discovery.search_expansion.service import RadarSearchExpansionService
from power_web_os.application.radar.candidate_discovery.search_expansion.work_scheduler import RadarWorkScheduler
from power_web_os.application.radar.candidate_discovery.execution.context import CandidateDiscoveryExecutionContext
from power_web_os.application.radar.candidate_discovery.execution.coverage import CoveragePhaseExecutor
from power_web_os.application.radar.candidate_discovery.execution.discovery import DiscoveryPhaseExecutor
from power_web_os.application.radar.candidate_discovery.execution.expansion import ExpansionPhaseExecutor
from power_web_os.application.radar.candidate_discovery.execution.expansion_diagnostics import _search_expansion_variant_cap
from power_web_os.application.radar.candidate_discovery.execution.finalization import FinalizationProjector
from power_web_os.application.radar.candidate_discovery.execution.options import CandidateDiscoveryExecutionOptions
from power_web_os.application.radar.candidate_discovery.execution.signals import SignalCompatibilityPhaseExecutor
from power_web_os.application.radar.candidate_discovery.execution.state import (
    CandidateDiscoveryExecutionState,
    ExecutionMetadataFactory,
    SmokeLimitPolicy,
)
from power_web_os.application.radar.candidate_discovery.execution.task_runner import TaskExecutionService
from power_web_os.integrations.live_radar_source_verification import (
    SourceVerificationCache,
    source_verification_cache_context,
)

MAX_DISCOVERY_ITERATIONS = 2
MAX_CANDIDATE_UNIVERSE_SIZE = 50


class CandidateDiscoveryOrchestrator:
    """Coordinates candidate-discovery phase services without owning phase logic.

    Owns:
    - Phase order, compatibility run flow, and final handoff to projection.

    Does not own:
    - Discovery, coverage, expansion, signal, finalization, provider, or budget
      internals.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidatediscoveryorchestrator
    """

    def __init__(
        self,
        *,
        task_service: TaskExecutionService | None = None,
        smoke_policy: SmokeLimitPolicy | None = None,
        discovery: DiscoveryPhaseExecutor | None = None,
        coverage: CoveragePhaseExecutor | None = None,
        expansion: ExpansionPhaseExecutor | None = None,
        signals: SignalCompatibilityPhaseExecutor | None = None,
        finalization: FinalizationProjector | None = None,
    ) -> None:
        self._task_service = task_service or TaskExecutionService()
        self._smoke_policy = smoke_policy or SmokeLimitPolicy()
        self._discovery = discovery or DiscoveryPhaseExecutor(
            task_service=self._task_service,
            smoke_policy=self._smoke_policy,
        )
        self._coverage = coverage or CoveragePhaseExecutor(
            task_service=self._task_service,
            smoke_policy=self._smoke_policy,
        )
        self._expansion = expansion or ExpansionPhaseExecutor(
            task_service=self._task_service,
            smoke_policy=self._smoke_policy,
        )
        self._signals = signals or SignalCompatibilityPhaseExecutor(self._task_service)
        self._finalization = finalization or FinalizationProjector(self._task_service)

    def run(
        self,
        context: CandidateDiscoveryExecutionContext,
        state: CandidateDiscoveryExecutionState,
    ) -> tuple[WebSearchProviderResult, list[LiveRadarPipelineEvent], dict[str, Any]]:
        discovery_tasks = self._task_service.tasks_for_stage(context.execution_plan, "qualification_discovery")
        gate_tasks, _ = self._discovery.run(context, state, discovery_tasks)
        terminal_stop_after_discovery = bool(state.stopped_for_review_reason)

        coverage_tasks = (
            []
            if terminal_stop_after_discovery
            else self._task_service.tasks_for_stage(context.execution_plan, "coverage_check")
        )
        self._coverage.run(
            context,
            state,
            discovery_tasks=discovery_tasks,
            gate_tasks=gate_tasks,
            coverage_tasks=coverage_tasks,
        )

        if not state.stopped_for_review_reason:
            self._expansion.run(context, state, coverage_tasks or discovery_tasks)

        if not state.stopped_for_review_reason:
            self._coverage.recover_after_coverage(context, state, coverage_tasks)

        self._discovery.extract_retrieved_candidates(context, state)
        if not state.stopped_for_review_reason:
            state.sources, state.observations, state.provider_metadata = execute_cross_source_disambiguation(
                radar=context.radar,
                execution_plan=context.execution_plan,
                provider=context.provider,
                sources=state.sources,
                observations=state.observations,
                provider_metadata=state.provider_metadata,
                budget=context.task_budget,
                external_budget=context.external_budget,
                events=state.events,
                executed_task_ids=state.executed_task_ids,
            )
        state.candidate_scope = self._task_service.eligible_candidate_names(
            radar=context.radar,
            sources=state.sources,
            observations=state.observations,
            completed_qualification_ids=state.completed_qualification_ids,
        )
        state.candidate_scope = self._smoke_policy.limit_candidates(
            state.candidate_scope,
            context.external_budget.settings.smoke_max_candidates,
        )

        pre_signal_decision, can_run_signal_search, _ = self._signals.review_before_search(context, state)
        signal_tasks = self._smoke_policy.limit_signal_tasks(
            self._task_service.tasks_for_stage(context.execution_plan, "signal_search"),
            context.external_budget.settings.smoke_max_signals,
        )
        self._signals.run(
            context,
            state,
            tasks=signal_tasks,
            can_run_signal_search=can_run_signal_search,
            pre_signal_decision=pre_signal_decision,
        )
        return self._finalization.project(context, state)
def run_staged_radar_execution(
    *,
    radar: dict[str, Any],
    execution_plan: RadarExecutionPlan,
    provider: WebSearchProvider,
    options: CandidateDiscoveryExecutionOptions | None = None,
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
    legacy_options = {
        "task_context": task_context,
        "max_web_tasks_per_subject": max_web_tasks_per_subject,
        "max_discovery_tasks_per_rule": max_discovery_tasks_per_rule,
        "max_gate_tasks_per_candidate_rule": max_gate_tasks_per_candidate_rule,
        "max_signal_tasks_per_candidate_signal": max_signal_tasks_per_candidate_signal,
        "max_total_web_tasks_per_run": max_total_web_tasks_per_run,
        "min_useful_sources_per_discovery_task": min_useful_sources_per_discovery_task,
        "min_candidates_per_discovery_task": min_candidates_per_discovery_task,
        "max_discovery_retries_per_task": max_discovery_retries_per_task,
        "max_checkpoint_revisions_per_run": max_checkpoint_revisions_per_run,
        "max_checkpoint_retries_per_stage": max_checkpoint_retries_per_stage,
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
        "semantic_task_reserve_limits": semantic_task_reserve_limits,
        "source_policy_decisions": source_policy_decisions,
    }
    if options is not None and any(value is not None for value in legacy_options.values()):
        raise ValueError("Pass staged execution options either as `options` or legacy keyword arguments, not both.")
    options = options or CandidateDiscoveryExecutionOptions.from_legacy_kwargs(**legacy_options)
    radar = options.apply_task_context(radar)
    budget_settings = options.to_task_budget_settings()
    task_budget = RadarExecutionBudget(budget_settings)
    external_budget = current_external_call_budget() or RadarExternalCallBudget(options.to_external_budget_settings())
    useful_budget = options.to_useful_budget()
    checkpoint_service = RadarExecutionCheckpointService(
        RadarExecutionCheckpointPolicy(**options.checkpoint_policy_kwargs())
    )
    checkpoint_executor = RadarCheckpointActionExecutor()
    search_expansion_service = RadarSearchExpansionService(
        max_variants=_search_expansion_variant_cap(run_profile=options.run_profile, radar=radar)
    )
    work_scheduler = RadarWorkScheduler()
    retrieval_plan = retrieval_plan_from_execution_plan(execution_plan)
    verification_cache = SourceVerificationCache(results_by_url={})
    state = CandidateDiscoveryExecutionState(
        provider_metadata={
            **ExecutionMetadataFactory().initial_provider_metadata(radar),
            **work_scheduler.configure_run_admission(radar=radar, external_budget=external_budget),
        }
    )
    context = CandidateDiscoveryExecutionContext(
        radar=radar,
        execution_plan=execution_plan,
        retrieval_plan=retrieval_plan,
        provider=provider,
        task_budget=task_budget,
        budget_settings=budget_settings,
        external_budget=external_budget,
        useful_budget=useful_budget,
        checkpoint_service=checkpoint_service,
        checkpoint_executor=checkpoint_executor,
        search_expansion_service=search_expansion_service,
        work_scheduler=work_scheduler,
        verification_cache=verification_cache,
        source_policy_decisions=options.source_policy_decisions,
        max_discovery_iterations=MAX_DISCOVERY_ITERATIONS,
        max_candidate_universe_size=MAX_CANDIDATE_UNIVERSE_SIZE,
    )

    with external_call_budget_context(external_budget), source_verification_cache_context(verification_cache):
        return CandidateDiscoveryOrchestrator().run(context, state)
