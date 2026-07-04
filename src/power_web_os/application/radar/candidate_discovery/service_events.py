"""Pipeline event state projection for live Radar runs."""

from __future__ import annotations

from typing import Any, Sequence

from power_web_os.application.radar.candidate_discovery.contracts import (
    LiveICPRadarRunState,
    LiveRadarPipelineEvent,
)


class LiveRadarEventStateProjector:
    """Appends product-safe pipeline events to the live Radar run state shape."""

    def append(
        self,
        state: LiveICPRadarRunState,
        events: Sequence[LiveRadarPipelineEvent],
    ) -> list[dict[str, Any]]:
        return [*state.pipeline_events, *[event.model_dump() for event in events]]
