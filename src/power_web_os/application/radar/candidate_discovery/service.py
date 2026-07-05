"""Application service for one live Radar execution pass.

The service owns provider-neutral orchestration: build a plan, call a provider
port, normalize observations, validate contracts, and shape the live run artifact.
"""

from __future__ import annotations

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveRadarCollectionResult,
    LiveICPRadarRunState,
    LiveRadarPipelineEvent,
    RadarDiscoveryPlanner,
    RadarExecutionPlan,
    WebSearchProvider,
)
from power_web_os.application.live_radar_definition import build_live_mini_radar_definition
from power_web_os.application.radar.shared.budgets import RadarExternalCallBudget
from power_web_os.application.radar.shared.budgets.external_context import (
    current_external_call_budget,
    external_budget_settings_from_context,
    external_call_budget_context,
)
from power_web_os.application.live_radar_pipeline_support import (
    trace_pipeline_step as _trace,
)
from power_web_os.application.radar.candidate_discovery.execution.orchestrator import run_staged_radar_execution
from power_web_os.application.radar.candidate_discovery.service_context import (
    LiveRadarTaskContextReader,
)
from power_web_os.application.radar.candidate_discovery.service_factory import (
    LiveRadarRunComposition,
    LiveRadarRunServiceFactory,
    TaskContextReaderFactory,
)
from power_web_os.application.radar.candidate_discovery.planning.execution_plan import (
    compile_radar_execution_plan,
    execution_plan_to_search_plan,
)
from power_web_os.application.radar.candidate_discovery.planning.planning_pipeline import build_planned_state
from power_web_os.application.radar_source_providers import RadarSourceRegistry


class LiveRadarRunService:
    """Provider-neutral planner/executor/evaluator pipeline for live Radar."""

    def __init__(
        self,
        provider: WebSearchProvider | LiveRadarRunComposition,
        *,
        discovery_planner: RadarDiscoveryPlanner | None = None,
        source_registry: RadarSourceRegistry | None = None,
        task_context_reader_factory: TaskContextReaderFactory = LiveRadarTaskContextReader,
    ) -> None:
        composition = (
            provider
            if isinstance(provider, LiveRadarRunComposition)
            else LiveRadarRunServiceFactory().build_composition(
                provider,
                discovery_planner=discovery_planner,
                source_registry=source_registry,
                task_context_reader_factory=task_context_reader_factory,
            )
        )
        self._provider = composition.provider
        self._discovery_planner = composition.discovery_planner
        self._connector_profile_registry = composition.connector_profile_registry
        self._artifact_projector = composition.artifact_projector
        self._budget_metadata_merger = composition.budget_metadata_merger
        self._event_state_projector = composition.event_state_projector
        self._task_context_reader_factory = composition.task_context_reader_factory

    def run(
        self,
        *,
        state: LiveICPRadarRunState,
        node_name: str,
        runtime_mode: str,
        framework_available: bool,
    ) -> LiveICPRadarRunState:
        external_budget = RadarExternalCallBudget(external_budget_settings_from_context(state.task_context))
        with external_call_budget_context(external_budget):
            for step in [
                self.build_search_plan,
                self.run_web_search,
                self._artifact_projector.normalize_sources,
                self._artifact_projector.extract_candidates,
                self._artifact_projector.evaluate_candidates,
                self._artifact_projector.validate_artifact,
            ]:
                state = step(state)
        return self._artifact_projector.shape_artifact(
            state=state,
            node_name=node_name,
            runtime_mode=runtime_mode,
            framework_available=framework_available,
        )

    def build_search_plan(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        if current_external_call_budget() is not None:
            return build_planned_state(
                state=state,
                planner=self._discovery_planner,
                connector_profile_registry=self._connector_profile_registry,
            )

        # LangGraph executes workflow nodes independently, so the service-level
        # budget context is not available when `build_search_plan` runs as a
        # node. Preserve planner-call accounting in state and merge it with the
        # staged execution budget in `run_web_search`.
        external_budget = RadarExternalCallBudget(external_budget_settings_from_context(state.task_context))
        with external_call_budget_context(external_budget):
            planned_state = build_planned_state(
                state=state,
                planner=self._discovery_planner,
                connector_profile_registry=self._connector_profile_registry,
            )
        return planned_state.model_copy(update={
            "execution_results": self._budget_metadata_merger.merge(
                planned_state.execution_results,
                external_budget.to_metadata(),
            ),
        })

    def run_web_search(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        radar = state.radar or build_live_mini_radar_definition()
        execution_plan = RadarExecutionPlan.model_validate(state.execution_plan or compile_radar_execution_plan(radar))
        plan = execution_plan_to_search_plan(execution_plan)
        _trace(
            state, "collection", "run_web_search", "pipeline_input", "Web search input",
            payload={"radar_id": plan.radar_id, "execution_plan": execution_plan.model_dump()},
        )
        provider_result, task_events, execution_results = run_staged_radar_execution(
            radar=radar,
            execution_plan=execution_plan,
            provider=self._provider,
            options=self._task_context_reader_factory(state.task_context).staged_execution_options(
                state.discovery_plan
            ),
        )
        execution_results = self._budget_metadata_merger.merge(state.execution_results, execution_results)
        result = LiveRadarCollectionResult(
            sources=provider_result.sources,
            candidate_observations=provider_result.candidate_observations,
            provider_metadata=provider_result.provider_metadata,
            events=[
                *task_events,
                LiveRadarPipelineEvent(
                    event_type="source_collected",
                    phase="collection",
                    actor="provider",
                    node_name="run_web_search",
                    visibility="operator",
                    summary=f"Provider returned {len(provider_result.sources)} sources across {execution_results['executed_task_count']} staged tasks.",
                    payload={
                        "source_count": len(provider_result.sources),
                        "candidate_observation_count": len(provider_result.candidate_observations),
                        "executed_task_count": execution_results["executed_task_count"],
                        "provider": str(provider_result.provider_metadata.get("provider", "")),
                        "model": str(provider_result.provider_metadata.get("model", "")),
                        "web_mode": str(provider_result.provider_metadata.get("web_mode", "")),
                    },
                    source_refs=[source.evidence_ref for source in provider_result.sources if source.evidence_ref],
                )
            ],
        )
        next_state = state.model_copy(update={
            "sources": [item.model_dump() for item in result.sources],
            "candidate_observations": [dict(item) for item in result.candidate_observations],
            "provider_metadata": dict(result.provider_metadata),
            "execution_results": execution_results,
            "pipeline_events": self._event_state_projector.append(state, result.events),
        })
        _trace(
            next_state, "collection", "run_web_search", "pipeline_output", "Web search output",
            summary=f"Provider returned {len(result.sources)} sources from qualification-first execution.",
            payload={
                "provider_metadata": dict(result.provider_metadata),
                "source_count": len(result.sources),
                "candidate_observation_count": len(result.candidate_observations),
                "execution_results": execution_results,
                "source_refs": [source.evidence_ref for source in result.sources],
            },
        )
        return next_state

    def normalize_sources(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        return self._artifact_projector.normalize_sources(state)

    def extract_candidates(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        return self._artifact_projector.extract_candidates(state)

    def evaluate_candidates(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        return self._artifact_projector.evaluate_candidates(state)

    def validate_artifact(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        return self._artifact_projector.validate_artifact(state)

    def shape_artifact(
        self,
        *,
        state: LiveICPRadarRunState,
        node_name: str,
        runtime_mode: str,
        framework_available: bool,
    ) -> LiveICPRadarRunState:
        return self._artifact_projector.shape_artifact(
            state=state,
            node_name=node_name,
            runtime_mode=runtime_mode,
            framework_available=framework_available,
        )
