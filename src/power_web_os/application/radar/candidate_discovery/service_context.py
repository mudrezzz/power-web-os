"""Typed task-context access for live Radar execution options."""

from __future__ import annotations

from typing import Any, Mapping

from power_web_os.application.radar.candidate_discovery.execution.options import CandidateDiscoveryExecutionOptions


class LiveRadarTaskContextReader:
    """Reads provider-neutral live Radar execution options from task context."""

    def __init__(self, context: Mapping[str, Any]) -> None:
        self._context = context

    def staged_execution_options(
        self,
        discovery_plan: Mapping[str, Any] | None,
    ) -> CandidateDiscoveryExecutionOptions:
        return CandidateDiscoveryExecutionOptions.from_task_context(self._context, discovery_plan)
