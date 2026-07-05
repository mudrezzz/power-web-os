"""Workflow-backed executor adapter for persisted live Radar runs.

Application services depend on `LiveRadarArtifactExecutor`; this adapter wires
that port to the current live Radar workflow without exposing workflow runtime
or provider details to the application layer.
"""

from __future__ import annotations

from typing import Any

from power_web_os.application.ports import LiveRadarArtifactExecutor, RadarRunTechnicalTraceRepository
from power_web_os.application.radar.candidate_discovery.contracts import RadarDiscoveryPlanner, WebSearchProvider
from power_web_os.application.radar_runtime_settings import effective_runtime_env
from power_web_os.application.radar_source_providers import RadarSourceRegistry
from power_web_os.application.radar_technical_trace import RadarRunTechnicalTracer
from power_web_os.workflows.live_icp_radar_workflow import build_live_mini_radar_artifact


class WorkflowLiveRadarArtifactExecutor(LiveRadarArtifactExecutor):
    def __init__(
        self,
        provider: WebSearchProvider,
        *,
        discovery_planner: RadarDiscoveryPlanner | None = None,
        source_registry: RadarSourceRegistry | None = None,
        technical_trace_repository: RadarRunTechnicalTraceRepository | None = None,
    ) -> None:
        self._provider = provider
        self._discovery_planner = discovery_planner
        self._source_registry = source_registry
        self._technical_trace_repository = technical_trace_repository

    def execute(
        self,
        *,
        live: bool,
        task_context: dict[str, object],
        radar_payload: dict[str, object] | None = None,
    ) -> dict[str, Any]:
        technical_tracer = None
        run_id = task_context.get("run_id")
        if self._technical_trace_repository is not None and run_id:
            technical_tracer = RadarRunTechnicalTracer(
                repository=self._technical_trace_repository,
                default_run_id=str(run_id),
            )
        return build_live_mini_radar_artifact(
            provider=self._provider,
            discovery_planner=self._discovery_planner,
            live=live,
            source_registry=self._source_registry,
            task_context=_task_context_with_runtime_defaults(task_context),
            radar=dict(radar_payload) if radar_payload is not None else None,
            technical_tracer=technical_tracer,
        )


def _task_context_with_runtime_defaults(task_context: dict[str, object]) -> dict[str, object]:
    context = dict(task_context)
    runtime_env = effective_runtime_env()
    context.setdefault("max_web_tasks_per_subject", _positive_int(runtime_env.get("POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT"), 20))
    _set_optional_positive(context, runtime_env, "max_discovery_tasks_per_rule", "POWER_WEB_OS_RADAR_MAX_DISCOVERY_TASKS_PER_RULE")
    _set_optional_positive(context, runtime_env, "max_gate_tasks_per_candidate_rule", "POWER_WEB_OS_RADAR_MAX_GATE_TASKS_PER_CANDIDATE_RULE")
    _set_optional_positive(context, runtime_env, "max_signal_tasks_per_candidate_signal", "POWER_WEB_OS_RADAR_MAX_SIGNAL_TASKS_PER_CANDIDATE_SIGNAL")
    _set_optional_positive(context, runtime_env, "max_total_web_tasks_per_run", "POWER_WEB_OS_RADAR_MAX_TOTAL_WEB_TASKS_PER_RUN")
    context.setdefault("run_profile", _run_profile(runtime_env.get("POWER_WEB_OS_RADAR_RUN_PROFILE"), "live"))
    _set_optional_non_negative(context, runtime_env, "max_openrouter_calls_per_run", "POWER_WEB_OS_RADAR_MAX_OPENROUTER_CALLS_PER_RUN")
    _set_optional_non_negative(context, runtime_env, "max_openrouter_planner_calls_per_run", "POWER_WEB_OS_RADAR_MAX_OPENROUTER_PLANNER_CALLS_PER_RUN")
    _set_optional_non_negative(context, runtime_env, "max_openrouter_web_task_calls_per_run", "POWER_WEB_OS_RADAR_MAX_OPENROUTER_WEB_TASK_CALLS_PER_RUN")
    _set_optional_non_negative(context, runtime_env, "max_openrouter_server_tool_web_searches_per_run", "POWER_WEB_OS_RADAR_MAX_OPENROUTER_SERVER_TOOL_WEB_SEARCHES_PER_RUN")
    _set_optional_non_negative(context, runtime_env, "max_dadata_lookups_per_run", "POWER_WEB_OS_RADAR_MAX_DADATA_LOOKUPS_PER_RUN")
    _set_optional_non_negative(context, runtime_env, "max_source_verification_requests_per_run", "POWER_WEB_OS_RADAR_MAX_SOURCE_VERIFICATION_REQUESTS_PER_RUN")
    _set_optional_non_negative(context, runtime_env, "max_provider_retries_per_task", "POWER_WEB_OS_RADAR_MAX_PROVIDER_RETRIES_PER_TASK")
    _set_optional_non_negative(context, runtime_env, "openrouter_web_max_results_per_call", "POWER_WEB_OS_RADAR_OPENROUTER_WEB_MAX_RESULTS_PER_CALL")
    _set_optional_non_negative(context, runtime_env, "openrouter_web_max_total_results_per_call", "POWER_WEB_OS_RADAR_OPENROUTER_WEB_MAX_TOTAL_RESULTS_PER_CALL")
    _set_optional_non_negative(context, runtime_env, "smoke_max_candidates", "POWER_WEB_OS_RADAR_SMOKE_MAX_CANDIDATES")
    _set_optional_non_negative(context, runtime_env, "smoke_max_signals", "POWER_WEB_OS_RADAR_SMOKE_MAX_SIGNALS")
    context.setdefault("source_verification_mode", _verification_mode(runtime_env.get("POWER_WEB_OS_RADAR_SOURCE_VERIFICATION_MODE"), "soft"))
    context.setdefault(
        "min_useful_sources_per_discovery_task",
        _non_negative_int(runtime_env.get("POWER_WEB_OS_RADAR_MIN_USEFUL_SOURCES_PER_DISCOVERY_TASK"), 3),
    )
    context.setdefault(
        "min_candidates_per_discovery_task",
        _non_negative_int(runtime_env.get("POWER_WEB_OS_RADAR_MIN_CANDIDATES_PER_DISCOVERY_TASK"), 5),
    )
    context.setdefault(
        "max_discovery_retries_per_task",
        _non_negative_int(runtime_env.get("POWER_WEB_OS_RADAR_MAX_DISCOVERY_RETRIES_PER_TASK"), 2),
    )
    context.setdefault(
        "max_checkpoint_revisions_per_run",
        _non_negative_int(runtime_env.get("POWER_WEB_OS_RADAR_MAX_CHECKPOINT_REVISIONS_PER_RUN"), 2),
    )
    context.setdefault(
        "max_checkpoint_retries_per_stage",
        _non_negative_int(runtime_env.get("POWER_WEB_OS_RADAR_MAX_CHECKPOINT_RETRIES_PER_STAGE"), 1),
    )
    return context


def _set_optional_positive(context: dict[str, object], runtime_env: dict[str, str], key: str, env_name: str) -> None:
    if key in context and context[key] is not None:
        return
    value = _optional_positive_int(runtime_env.get(env_name))
    if value is not None:
        context[key] = value


def _set_optional_non_negative(context: dict[str, object], runtime_env: dict[str, str], key: str, env_name: str) -> None:
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
