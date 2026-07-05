"""Workflow wrapper for live ICP Radar execution.

This module is the only live Radar layer that knows about langgraph-dai. The
actual run logic stays in the application service, and provider calls stay behind
`WebSearchProvider` adapters.
"""

from __future__ import annotations

from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import LiveICPRadarRunState, RadarDiscoveryPlanner, WebSearchProvider
from power_web_os.application.radar.candidate_discovery.retrieval.definition import build_live_mini_radar_definition
from power_web_os.application.radar.candidate_discovery.service_factory import LiveRadarRunServiceFactory
from power_web_os.application.radar_runtime_settings import effective_runtime_env
from power_web_os.application.radar_source_providers import RadarSourceRegistry
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
    source_registry: RadarSourceRegistry | None = None,
    task_context: dict[str, Any] | None = None,
    radar: dict[str, Any] | None = None,
    technical_tracer: RadarRunTechnicalTracer | None = None,
) -> dict[str, Any]:
    workflow = LiveICPRadarRunWorkflow(provider=provider, discovery_planner=discovery_planner, source_registry=source_registry)
    default_task_context = dict(task_context or {
            "task_id": "live-mini-icp-radar",
            "correlation_id": "demo-slice-0.6.3.1",
            "requester": "demo",
        })
    runtime_env = effective_runtime_env()
    default_task_context.setdefault("max_web_tasks_per_subject", _positive_int(runtime_env.get("POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT"), 20))
    _set_optional_positive(default_task_context, runtime_env, "max_discovery_tasks_per_rule", "POWER_WEB_OS_RADAR_MAX_DISCOVERY_TASKS_PER_RULE")
    _set_optional_positive(default_task_context, runtime_env, "max_gate_tasks_per_candidate_rule", "POWER_WEB_OS_RADAR_MAX_GATE_TASKS_PER_CANDIDATE_RULE")
    _set_optional_positive(default_task_context, runtime_env, "max_signal_tasks_per_candidate_signal", "POWER_WEB_OS_RADAR_MAX_SIGNAL_TASKS_PER_CANDIDATE_SIGNAL")
    _set_optional_positive(default_task_context, runtime_env, "max_total_web_tasks_per_run", "POWER_WEB_OS_RADAR_MAX_TOTAL_WEB_TASKS_PER_RUN")
    default_task_context.setdefault("run_profile", _run_profile(runtime_env.get("POWER_WEB_OS_RADAR_RUN_PROFILE"), "live"))
    _set_optional_non_negative(default_task_context, runtime_env, "max_openrouter_calls_per_run", "POWER_WEB_OS_RADAR_MAX_OPENROUTER_CALLS_PER_RUN")
    _set_optional_non_negative(default_task_context, runtime_env, "max_openrouter_planner_calls_per_run", "POWER_WEB_OS_RADAR_MAX_OPENROUTER_PLANNER_CALLS_PER_RUN")
    _set_optional_non_negative(default_task_context, runtime_env, "max_openrouter_web_task_calls_per_run", "POWER_WEB_OS_RADAR_MAX_OPENROUTER_WEB_TASK_CALLS_PER_RUN")
    _set_optional_non_negative(default_task_context, runtime_env, "max_openrouter_server_tool_web_searches_per_run", "POWER_WEB_OS_RADAR_MAX_OPENROUTER_SERVER_TOOL_WEB_SEARCHES_PER_RUN")
    _set_optional_non_negative(default_task_context, runtime_env, "max_dadata_lookups_per_run", "POWER_WEB_OS_RADAR_MAX_DADATA_LOOKUPS_PER_RUN")
    _set_optional_non_negative(default_task_context, runtime_env, "max_source_verification_requests_per_run", "POWER_WEB_OS_RADAR_MAX_SOURCE_VERIFICATION_REQUESTS_PER_RUN")
    _set_optional_non_negative(default_task_context, runtime_env, "max_provider_retries_per_task", "POWER_WEB_OS_RADAR_MAX_PROVIDER_RETRIES_PER_TASK")
    _set_optional_non_negative(default_task_context, runtime_env, "openrouter_web_max_results_per_call", "POWER_WEB_OS_RADAR_OPENROUTER_WEB_MAX_RESULTS_PER_CALL")
    _set_optional_non_negative(default_task_context, runtime_env, "openrouter_web_max_total_results_per_call", "POWER_WEB_OS_RADAR_OPENROUTER_WEB_MAX_TOTAL_RESULTS_PER_CALL")
    _set_optional_non_negative(default_task_context, runtime_env, "smoke_max_candidates", "POWER_WEB_OS_RADAR_SMOKE_MAX_CANDIDATES")
    _set_optional_non_negative(default_task_context, runtime_env, "smoke_max_signals", "POWER_WEB_OS_RADAR_SMOKE_MAX_SIGNALS")
    default_task_context.setdefault("source_verification_mode", _verification_mode(runtime_env.get("POWER_WEB_OS_RADAR_SOURCE_VERIFICATION_MODE"), "soft"))
    default_task_context.setdefault(
        "min_useful_sources_per_discovery_task",
        _non_negative_int(runtime_env.get("POWER_WEB_OS_RADAR_MIN_USEFUL_SOURCES_PER_DISCOVERY_TASK"), 3),
    )
    default_task_context.setdefault(
        "min_candidates_per_discovery_task",
        _non_negative_int(runtime_env.get("POWER_WEB_OS_RADAR_MIN_CANDIDATES_PER_DISCOVERY_TASK"), 5),
    )
    default_task_context.setdefault(
        "max_discovery_retries_per_task",
        _non_negative_int(runtime_env.get("POWER_WEB_OS_RADAR_MAX_DISCOVERY_RETRIES_PER_TASK"), 2),
    )
    default_task_context.setdefault(
        "max_checkpoint_revisions_per_run",
        _non_negative_int(runtime_env.get("POWER_WEB_OS_RADAR_MAX_CHECKPOINT_REVISIONS_PER_RUN"), 2),
    )
    default_task_context.setdefault(
        "max_checkpoint_retries_per_stage",
        _non_negative_int(runtime_env.get("POWER_WEB_OS_RADAR_MAX_CHECKPOINT_RETRIES_PER_STAGE"), 1),
    )
    state = LiveICPRadarRunState(
        task_context=default_task_context,
        radar=radar or build_live_mini_radar_definition(),
        live=live,
    )
    with technical_trace_context(technical_tracer):
        result = workflow.invoke(state)
    if result.artifact is None:
        raise RuntimeError("LiveICPRadarRunWorkflow did not produce an artifact")
    return result.artifact


def _set_optional_positive(context: dict[str, Any], runtime_env: dict[str, str], key: str, env_name: str) -> None:
    if key in context and context[key] is not None:
        return
    value = _optional_positive_int(runtime_env.get(env_name))
    if value is not None:
        context[key] = value


def _set_optional_non_negative(context: dict[str, Any], runtime_env: dict[str, str], key: str, env_name: str) -> None:
    if key in context and context[key] is not None:
        return
    value = _optional_non_negative_int(runtime_env.get(env_name))
    if value is not None:
        context[key] = value


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


def _optional_positive_int(raw: str | None) -> int | None:
    try:
        value = int(raw or "")
    except ValueError:
        return None
    return value if value > 0 else None


def _optional_non_negative_int(raw: str | None) -> int | None:
    try:
        value = int(raw or "")
    except ValueError:
        return None
    return value if value >= 0 else None


def _run_profile(raw: str | None, default: str) -> str:
    value = (raw or default).strip().lower()
    return value if value in {"live", "smoke"} else default


def _verification_mode(raw: str | None, default: str) -> str:
    value = (raw or default).strip().lower()
    return value if value in {"strict", "soft", "off"} else default


class _FallbackLiveICPRadarRunWorkflow:
    def __init__(
        self,
        provider: WebSearchProvider | None = None,
        discovery_planner: RadarDiscoveryPlanner | None = None,
        source_registry: RadarSourceRegistry | None = None,
        **_: Any,
    ) -> None:
        self._provider = provider or RecordedWebSearchProvider({"sources": [], "candidate_observations": []})
        self._runtime_mode = "local_fallback"
        self._service = LiveRadarRunServiceFactory().create(
            self._provider,
            discovery_planner=discovery_planner,
            source_registry=source_registry,
        )

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
            source_registry: RadarSourceRegistry | None = None,
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
            self._fallback = _FallbackLiveICPRadarRunWorkflow(
                provider=provider,
                discovery_planner=discovery_planner,
                source_registry=source_registry,
            )
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
