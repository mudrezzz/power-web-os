"""Workflow-backed executor adapter for persisted live Radar runs.

Application services depend on `LiveRadarArtifactExecutor`; this adapter wires
that port to the current live Radar workflow without exposing workflow runtime
or provider details to the application layer.
"""

from __future__ import annotations

from typing import Any

from power_web_os.application.ports import LiveRadarArtifactExecutor
from power_web_os.application.live_radar_contracts import WebSearchProvider
from power_web_os.workflows.live_icp_radar_workflow import build_live_mini_radar_artifact


class WorkflowLiveRadarArtifactExecutor(LiveRadarArtifactExecutor):
    def __init__(self, provider: WebSearchProvider) -> None:
        self._provider = provider

    def execute(self, *, live: bool, task_context: dict[str, object]) -> dict[str, Any]:
        return build_live_mini_radar_artifact(
            provider=self._provider,
            live=live,
            task_context=dict(task_context),
        )
