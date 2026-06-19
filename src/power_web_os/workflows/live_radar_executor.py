"""Workflow-backed executor adapter for persisted live Radar runs.

Application services depend on `LiveRadarArtifactExecutor`; this adapter wires
that port to the current live Radar workflow without exposing workflow runtime
or provider details to the application layer.
"""

from __future__ import annotations

import os
from typing import Any

from power_web_os.application.ports import LiveRadarArtifactExecutor, RadarRunTechnicalTraceRepository
from power_web_os.application.live_radar_contracts import RadarDiscoveryPlanner, WebSearchProvider
from power_web_os.application.radar_technical_trace import RadarRunTechnicalTracer
from power_web_os.workflows.live_icp_radar_workflow import build_live_mini_radar_artifact


class WorkflowLiveRadarArtifactExecutor(LiveRadarArtifactExecutor):
    def __init__(
        self,
        provider: WebSearchProvider,
        *,
        discovery_planner: RadarDiscoveryPlanner | None = None,
        technical_trace_repository: RadarRunTechnicalTraceRepository | None = None,
    ) -> None:
        self._provider = provider
        self._discovery_planner = discovery_planner
        self._technical_trace_repository = technical_trace_repository

    def execute(self, *, live: bool, task_context: dict[str, object]) -> dict[str, Any]:
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
            task_context=_task_context_with_runtime_defaults(task_context),
            technical_tracer=technical_tracer,
        )


def _task_context_with_runtime_defaults(task_context: dict[str, object]) -> dict[str, object]:
    context = dict(task_context)
    context.setdefault("max_web_tasks_per_subject", _positive_int(os.getenv("POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT"), 20))
    context.setdefault("source_verification_mode", _verification_mode(os.getenv("POWER_WEB_OS_RADAR_SOURCE_VERIFICATION_MODE"), "soft"))
    context.setdefault(
        "min_useful_sources_per_discovery_task",
        _non_negative_int(os.getenv("POWER_WEB_OS_RADAR_MIN_USEFUL_SOURCES_PER_DISCOVERY_TASK"), 3),
    )
    context.setdefault(
        "min_candidates_per_discovery_task",
        _non_negative_int(os.getenv("POWER_WEB_OS_RADAR_MIN_CANDIDATES_PER_DISCOVERY_TASK"), 5),
    )
    context.setdefault(
        "max_discovery_retries_per_task",
        _non_negative_int(os.getenv("POWER_WEB_OS_RADAR_MAX_DISCOVERY_RETRIES_PER_TASK"), 2),
    )
    return context


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
