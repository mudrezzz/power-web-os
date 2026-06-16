"""Workflow wrapper for live ICP Radar execution.

This module is the only live Radar layer that knows about langgraph-dai. The
actual run logic stays in the application service, and provider calls stay behind
`WebSearchProvider` adapters.
"""

from __future__ import annotations

from typing import Any

from power_web_os.application.live_radar_contracts import LiveICPRadarRunState, WebSearchProvider
from power_web_os.application.live_radar_definition import build_live_mini_radar_definition
from power_web_os.application.live_radar_service import LiveRadarRunService
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
    live: bool,
    task_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    workflow = LiveICPRadarRunWorkflow(provider=provider)
    state = LiveICPRadarRunState(
        task_context=task_context or {
            "task_id": "live-mini-icp-radar",
            "correlation_id": "demo-slice-0.6.3.1",
            "requester": "demo",
        },
        radar=build_live_mini_radar_definition(),
        live=live,
    )
    result = workflow.invoke(state)
    if result.artifact is None:
        raise RuntimeError("LiveICPRadarRunWorkflow did not produce an artifact")
    return result.artifact


class _FallbackLiveICPRadarRunWorkflow:
    def __init__(self, provider: WebSearchProvider | None = None, **_: Any) -> None:
        self._provider = provider or RecordedWebSearchProvider({"sources": [], "candidate_observations": []})
        self._runtime_mode = "local_fallback"
        self._service = LiveRadarRunService(self._provider)

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


if FRAMEWORK_AVAILABLE:

    class LiveICPRadarRunWorkflow(BaseWorkflow):  # type: ignore[misc,valid-type]
        def __init__(
            self,
            provider: WebSearchProvider | None = None,
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
            self._fallback = _FallbackLiveICPRadarRunWorkflow(provider=provider)
            self.compile()

        def state_schema(self) -> type[LiveICPRadarRunState]:
            return LiveICPRadarRunState

        def workflow_nodes(self, *, is_resume: bool) -> list[Any]:
            _ = is_resume
            return [
                WorkflowNodeSpec(name="build_search_plan", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="run_web_search", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="normalize_sources", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="extract_candidates", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="evaluate_qualification", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="extract_signals", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="rank_candidates", handler=self._run_node),  # type: ignore[misc,operator]
                WorkflowNodeSpec(name="shape_artifact", handler=self._run_node),  # type: ignore[misc,operator]
            ]

        def execute(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
            return self._run_with_langgraph_metadata(state)

        def execute_resume(self, state: LiveICPRadarRunState) -> LiveICPRadarRunState:
            return self.execute(state)

        def _run_node(self, state: LiveICPRadarRunState, context: WorkflowExecutionContext) -> LiveICPRadarRunState:
            _ = context
            if state.artifact is not None:
                return state
            return self._run_with_langgraph_metadata(state)

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
