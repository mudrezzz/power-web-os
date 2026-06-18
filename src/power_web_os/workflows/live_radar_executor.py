"""Workflow-backed executor adapter for persisted live Radar runs.

Application services depend on `LiveRadarArtifactExecutor`; this adapter wires
that port to the current live Radar workflow without exposing workflow runtime
or provider details to the application layer.
"""

from __future__ import annotations

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
            task_context=dict(task_context),
            technical_tracer=technical_tracer,
        )
