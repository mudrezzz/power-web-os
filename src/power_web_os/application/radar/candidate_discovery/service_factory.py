"""Composition helpers for the live Radar run service.

This module wires service collaborators. Pipeline order and candidate-discovery
decisions remain in `LiveRadarRunService` and execution phase services.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from power_web_os.application.connector_profiles import ConnectorProfileRegistry
from power_web_os.application.radar.candidate_discovery.contracts import (
    RadarDiscoveryPlanner,
    WebSearchProvider,
)
from power_web_os.application.radar.candidate_discovery.diagnostics.live_run_artifact import (
    LiveRadarRunArtifactProjector,
)
from power_web_os.application.radar.candidate_discovery.planning.discovery_planning import (
    DeterministicRadarDiscoveryPlanner,
)
from power_web_os.application.radar.candidate_discovery.service_budget import ExternalBudgetMetadataMerger
from power_web_os.application.radar.candidate_discovery.service_context import LiveRadarTaskContextReader
from power_web_os.application.radar.candidate_discovery.service_events import LiveRadarEventStateProjector
from power_web_os.application.radar.candidate_discovery.sources.providers import (
    RadarSourceRegistry,
    SourceRegistryWebSearchProvider,
)

if TYPE_CHECKING:  # pragma: no cover - typing-only import avoids a runtime cycle.
    from power_web_os.application.radar.candidate_discovery.service import LiveRadarRunService

TaskContextReaderFactory = Callable[[Mapping[str, Any]], LiveRadarTaskContextReader]


@dataclass(frozen=True, slots=True)
class LiveRadarRunComposition:
    """Ready collaborators for `LiveRadarRunService`.

    The composition object keeps assembly decisions out of the use-case facade.
    """

    provider: WebSearchProvider
    discovery_planner: RadarDiscoveryPlanner
    connector_profile_registry: ConnectorProfileRegistry | None
    artifact_projector: LiveRadarRunArtifactProjector
    budget_metadata_merger: ExternalBudgetMetadataMerger
    event_state_projector: LiveRadarEventStateProjector
    task_context_reader_factory: TaskContextReaderFactory


class LiveRadarRunServiceFactory:
    """Build `LiveRadarRunService` and its package-owned collaborators."""

    def build_composition(
        self,
        provider: WebSearchProvider,
        *,
        discovery_planner: RadarDiscoveryPlanner | None = None,
        source_registry: RadarSourceRegistry | None = None,
        artifact_projector: LiveRadarRunArtifactProjector | None = None,
        budget_metadata_merger: ExternalBudgetMetadataMerger | None = None,
        event_state_projector: LiveRadarEventStateProjector | None = None,
        task_context_reader_factory: TaskContextReaderFactory = LiveRadarTaskContextReader,
    ) -> LiveRadarRunComposition:
        """Return default or explicitly injected live-run collaborators."""

        resolved_provider = (
            SourceRegistryWebSearchProvider(provider, source_registry)
            if source_registry is not None
            else provider
        )
        return LiveRadarRunComposition(
            provider=resolved_provider,
            discovery_planner=discovery_planner or DeterministicRadarDiscoveryPlanner(),
            connector_profile_registry=(
                source_registry.connector_profile_registry if source_registry is not None else None
            ),
            artifact_projector=artifact_projector or LiveRadarRunArtifactProjector(resolved_provider),
            budget_metadata_merger=budget_metadata_merger or ExternalBudgetMetadataMerger(),
            event_state_projector=event_state_projector or LiveRadarEventStateProjector(),
            task_context_reader_factory=task_context_reader_factory,
        )

    def create(
        self,
        provider: WebSearchProvider,
        *,
        discovery_planner: RadarDiscoveryPlanner | None = None,
        source_registry: RadarSourceRegistry | None = None,
        artifact_projector: LiveRadarRunArtifactProjector | None = None,
        budget_metadata_merger: ExternalBudgetMetadataMerger | None = None,
        event_state_projector: LiveRadarEventStateProjector | None = None,
        task_context_reader_factory: TaskContextReaderFactory = LiveRadarTaskContextReader,
    ) -> LiveRadarRunService:
        """Create the live-run facade from an assembled composition."""

        from power_web_os.application.radar.candidate_discovery.service import LiveRadarRunService

        return LiveRadarRunService(
            self.build_composition(
                provider,
                discovery_planner=discovery_planner,
                source_registry=source_registry,
                artifact_projector=artifact_projector,
                budget_metadata_merger=budget_metadata_merger,
                event_state_projector=event_state_projector,
                task_context_reader_factory=task_context_reader_factory,
            )
        )


__all__ = [
    "LiveRadarRunComposition",
    "LiveRadarRunServiceFactory",
    "TaskContextReaderFactory",
]
