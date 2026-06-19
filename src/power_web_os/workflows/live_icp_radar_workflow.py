"""Workflow wrapper for live ICP Radar execution.

This module is the only live Radar layer that knows about langgraph-dai. The
actual run logic stays in the application service, and provider calls stay behind
`WebSearchProvider` adapters.
"""

from __future__ import annotations

import os
from typing import Any

from power_web_os.application.live_radar_contracts import LiveICPRadarRunState, RadarDiscoveryPlanner, WebSearchProvider
from power_web_os.application.live_radar_definition import build_live_mini_radar_definition
from power_web_os.application.live_radar_service import LiveRadarRunService
from power_web_os.application.radar_technical_trace import RadarRunTechnicalTracer, technical_trace_context
from power_web_os.integrations.live_radar_openrouter import RecordedWebSearchProvider

try:  # pragma: no cover - covered only when langgraph-dai is installed.
    from framework.workflows.base import BaseWorkflow, WorkflowExecutionContext, WorkflowNodeSpec

    FRAMEWORK_AVAILABLE = True
except Exception:  # pragma: no cover - normal path for base install.
    BaseWorkflow = object  # type: ignore[assignment,misc]
    WorkflowExecutionContext = Any  # type: ignore[misc,assignment]
    WorkflowNodeSpec = None  # type: ignore[assignment]
    FRAMEWORK_AVAILABLE = False


def build_live_mini_radar_artifact(
    *,
    provider: WebSearchProvider,
    discovery_planner: RadarDiscoveryPlanner | None = None,
    live: bool,
    task_context: dict[str, Any] | None = None,
    technical_tracer: RadarRunTechnicalTracer | None = None,
) -> dict[str, Any]:
    workflow = LiveICPRadarRunWorkflow(provider=provider, discovery_planner=discovery_planner)
    default_task_context = dict(task_context or {
            "task_id": "live-mini-icp-radar",
            "correlation_id": "demo-slice-0.6.3.1",
            "requester": "demo",
        })
    default_task_context.setdefault("max_web_tasks_per_subject", _positive_int(os.getenv("POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT"), 20))
    default_task_context.setdefault("source_verification_mode", _verification_mode(os.getenv("POWER_WEB_OS_RADAR_SOURCE_VERIFICATION_MODE"), "soft"))
    default_task_context.setdefault(
        "min_useful_sources_per_discovery_task",
        _non_negative_int(os.getenv("POWER_WEB_OS_RADAR_MIN_USEFUL_SOURCES_PER_DISCOVERY_TASK"), 3),
    )
    default_task_context.setdefault(
        "min_candidates_per_discovery_task",
        _non_negative_int(os.getenv("POWER_WEB_OS_RADAR_MIN_CANDIDATES_PER_DISCOVERY_TASK"), 5),
    )
    default_task_context.setdefault(
        "max_discovery_retries_per_task",
        _non_negative_int(os.getenv("POWER_WEB_OS_RADAR_MAX_DISCOVERY_RETRIES_PER_TASK"), 2),
    )
    state = LiveICPRadarRunState(
        task_context=default_task_context,
        radar=build_live_mini_radar_definition(),
        live=live,
    )
    with technical_trace_context(technical_tracer):
        result = workflow.invoke(state)
    if result.artifact is None:
        raise RuntimeError("LiveICPRadarRunWorkflow did not produce an artifact")
    return result.artifact


def _positive_int(raw: str | None, default: int) -> int:
    try:
        value = int(raw or "")
    except ValueError:
        return default
    return value if value > 0 else default


def _non_negative_int(raw: str | None, default: int) -> int:
    try:
        value = int(raw or "")
    except ValueError:
        return default
    return value if value >= 0 else default


def _verification_mode(raw: str | None, default: str) -> str:
    value = (raw or default).strip().lower()
    return value if value in {"strict", "soft", "off"} else default


class _FallbackLiveICPRadarRunWorkflow:
    def __init__(self, provider: WebSearchProvider | None = None, discovery_planner: RadarDiscoveryPlanner | None = None, **_: Any) -> None:
        self._provider = provider or RecordedWebSearchProvider({"sources": [], "candidate_observations": []})
        self._runtime_mode = "local_fallback"
        self._service = LiveRadarRunService(self._provider, discovery_planner=discovery_planner)

    def compile(self) -> dict[str, Any]:
        return {
            "workflow": self.__class__.__name__,
            "runtime_mode": self._runtime_mode,
            "invoke_graph_ready": True,
            "resume_graph_ready": True,
            "invoke_node_count": 7,
            "resume_node_count": 7,
        }

    def invoke(self, payload: LiveICPRadarRunState | dict[str, Any]) -> LiveICPRadarRunState:
        state = LiveICPRadarRunState.model_validate(payload)
        return self._run(state=state, node_name="shape_artifact")

    def resume(self, payload: LiveICPRadarRunState | dict[str, Any]) -> LiveICPRadarRunState:
        return self.invoke(payload)

    def _run(self, *, state: LiveICPRadarRunState, node_name: str) -> LiveICPRadarRunState:
        return self._service.run(
            state=state,
            node_name=node_name,
            runtime_mode=self._runtime_mode,
            framework_available=False,
        )

    def build_search_plan(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        return self._service.build_search_plan(state)

    def run_web_search(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        return self._service.run_web_search(state)

    def normalize_sources(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        return self._service.normalize_sources(state)

    def extract_candidates(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        return self._service.extract_candidates(state)

    def evaluate_candidates(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        return self._service.evaluate_candidates(state)

    def validate_artifact(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
        return self._service.validate_artifact(state)

    def shape_artifact(
        self,
        state: LiveICPRadarRunState,
        *,
        node_name: str,
        runtime_mode: str | None = None,
        framework_available: bool = False,
    ) -> LiveICPRadarRunState:
        return self._service.shape_artifact(
            state=state,
            node_name=node_name,
            runtime_mode=runtime_mode or self._runtime_mode,
            framework_available=framework_available,
        )


if FRAMEWORK_AVAILABLE:

    class LiveICPRadarRunWorkflow(BaseWorkflow):  # type: ignore[misc,valid-type]
        def __init__(
            self,
            provider: WebSearchProvider | None = None,
            discovery_planner: RadarDiscoveryPlanner | None = None,
            *,
            use_langgraph_runtime: bool = True,
            checkpointer: object | None = None,
            node_event_sink: object | None = None,
        ) -> None:
            super().__init__(
                use_langgraph_runtime=use_langgraph_runtime,
                checkpointer=checkpointer,
                node_event_sink=node_event_sink,
            )
            self._fallback = _FallbackLiveICPRadarRunWorkflow(provider=provider, discovery_planner=discovery_planner)
            self.compile()

        def state_schema(self) -> type[LiveICPRadarRunState]:
            return LiveICPRadarRunState

        def workflow_nodes(self, *, is_resume: bool) -> list[Any]:
            _ = is_resume
            return [
                WorkflowNodeSpec(name="build_search_plan", handler=self._build_search_plan_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="run_web_search", handler=self._run_web_search_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="normalize_sources", handler=self._normalize_sources_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="extract_candidates", handler=self._extract_candidates_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="evaluate_candidates", handler=self._evaluate_candidates_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="validate_artifact", handler=self._validate_artifact_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="shape_artifact", handler=self._shape_artifact_node),  # type: ignore[misc,operator]
            ]

        def execute(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
            return self._run_with_langgraph_metadata(state)

        def execute_resume(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
            return self.execute(state)

        def _build_search_plan_node(self, state: LiveICPRadarRunState, context: WorkflowExecutionContext) -> LiveICPRadarRunState:
            _ = context
            if state.artifact is not None:
                return state
            return self._fallback.build_search_plan(state)

        def _run_web_search_node(self, state: LiveICPRadarRunState, context: WorkflowExecutionContext) -> LiveICPRadarRunState:
            _ = context
            if state.artifact is not None:
                return state
            return self._fallback.run_web_search(state)

        def _normalize_sources_node(self, state: LiveICPRadarRunState, context: WorkflowExecutionContext) -> LiveICPRadarRunState:
            _ = context
            if state.artifact is not None:
                return state
            return self._fallback.normalize_sources(state)

        def _extract_candidates_node(self, state: LiveICPRadarRunState, context: WorkflowExecutionContext) -> LiveICPRadarRunState:
            _ = context
            if state.artifact is not None:
                return state
            return self._fallback.extract_candidates(state)

        def _evaluate_candidates_node(self, state: LiveICPRadarRunState, context: WorkflowExecutionContext) -> LiveICPRadarRunState:
            _ = context
            if state.artifact is not None:
                return state
            return self._fallback.evaluate_candidates(state)

        def _validate_artifact_node(self, state: LiveICPRadarRunState, context: WorkflowExecutionContext) -> LiveICPRadarRunState:
            _ = context
            if state.artifact is not None:
                return state
            return self._fallback.validate_artifact(state)

        def _shape_artifact_node(self, state: LiveICPRadarRunState, context: WorkflowExecutionContext) -> LiveICPRadarRunState:
            _ = context
            if state.artifact is not None:
                return state
            return self._fallback.shape_artifact(
                state,
                node_name="shape_artifact",
                runtime_mode="langgraph_dai",
                framework_available=True,
            )

        def _run_with_langgraph_metadata(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
            result = self._fallback.invoke(state)
            metadata = {
                **result.workflow_metadata,
                "runtime_mode": "langgraph_dai",
                "framework_available": True,
            }
            artifact = {**(result.artifact or {}), "run_metadata": metadata}
            return result.model_copy(update={"workflow_metadata": metadata, "artifact": artifact})

else:
    LiveICPRadarRunWorkflow = _FallbackLiveICPRadarRunWorkflow
