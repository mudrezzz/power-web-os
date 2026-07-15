"""Composition root for the standalone signal-monitoring application runtime."""

from __future__ import annotations

from dataclasses import dataclass
from power_web_os.application.radar.signal_monitoring.artifact import SignalMonitoringArtifactProjector
from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalMonitoringEvidenceProvider,
    SignalSourceMetadataProvider,
)
from power_web_os.application.radar.signal_monitoring.evidence import SignalEvidenceValidationService
from power_web_os.application.radar.signal_monitoring.executor import SignalMonitoringExecutor
from power_web_os.application.radar.signal_monitoring.input_assembler import SignalMonitoringInputAssembler
from power_web_os.application.radar.signal_monitoring.temporal import SignalTemporalEvidenceService
from power_web_os.application.radar.configuration.model_profiles import (
    RadarModelProfileRegistry,
    default_model_profile_registry,
)


@dataclass(frozen=True, slots=True)
class SignalMonitoringRunComposition:
    """Ready collaborators for one signal-monitoring runtime."""

    executor: SignalMonitoringExecutor
    input_assembler: SignalMonitoringInputAssembler
    artifact_projector: SignalMonitoringArtifactProjector
    primary_provider: SignalMonitoringEvidenceProvider
    backup_provider: SignalMonitoringEvidenceProvider | None


class SignalMonitoringRunServiceFactory:
    """Own provider/model composition without owning execution behavior."""

    def build_composition(
        self,
        *,
        primary_provider: SignalMonitoringEvidenceProvider,
        backup_provider: SignalMonitoringEvidenceProvider | None = None,
        source_metadata_provider: SignalSourceMetadataProvider | None = None,
        model_profile_registry: RadarModelProfileRegistry | None = None,
    ) -> SignalMonitoringRunComposition:
        registry = model_profile_registry or default_model_profile_registry()
        registry.require("signal_monitoring_default")
        return SignalMonitoringRunComposition(
            executor=SignalMonitoringExecutor(
                primary_provider,
                backup_provider=backup_provider,
                evidence_validator=SignalEvidenceValidationService(
                    SignalTemporalEvidenceService(source_metadata_provider)
                ),
                model_profile_registry=registry,
            ),
            input_assembler=SignalMonitoringInputAssembler(),
            artifact_projector=SignalMonitoringArtifactProjector(),
            primary_provider=primary_provider,
            backup_provider=backup_provider,
        )
