"""Service interface contracts for candidate-discovery execution components."""

from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from power_web_os.application.radar.candidate_discovery.contracts import (
        LiveRadarPipelineEvent,
        WebSearchProviderResult,
    )
    from power_web_os.application.radar.candidate_discovery.execution.context import (
        CandidateDiscoveryExecutionContext,
        PhaseResult,
    )
    from power_web_os.application.radar.candidate_discovery.execution.state import (
        CandidateDiscoveryExecutionState,
    )


class CandidateDiscoveryPhaseExecutor(Protocol):
    """Contract for stateful execution phases.

    Owns:
    - A single candidate-discovery execution phase with a stable `phase_name`.

    Does not own:
    - Provider adapters, persistence, API routes, or cross-phase orchestration.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidatediscoveryphaseexecutor
    """

    phase_name: str

    def run(
        self,
        context: "CandidateDiscoveryExecutionContext",
        state: "CandidateDiscoveryExecutionState",
        *args: Any,
        **kwargs: Any,
    ) -> "PhaseResult":
        """Execute the phase against shared context and mutable run state."""


class CandidateDiscoveryProjector(Protocol):
    """Contract for final projection from execution state to provider artifacts.

    Owns:
    - Product-safe result, event, and metadata projection.

    Does not own:
    - Running provider tasks or changing checkpoint decisions.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidatediscoveryprojector
    """

    def project(
        self,
        context: "CandidateDiscoveryExecutionContext",
        state: "CandidateDiscoveryExecutionState",
    ) -> tuple["WebSearchProviderResult", list["LiveRadarPipelineEvent"], dict[str, Any]]:
        """Project the completed run state into compatibility artifacts."""


class CandidateDiscoveryPolicy(Protocol):
    """Contract for deterministic execution policies.

    Owns:
    - A narrow policy decision over already available facts.

    Does not own:
    - Provider calls, state mutation, persistence, or orchestration.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidatediscoverypolicy
    """

    def decide(self, *args: Any, **kwargs: Any) -> Any:
        """Return a deterministic policy decision."""


class CandidateDiscoveryFactory(Protocol):
    """Contract for product-safe payload and metadata factories.

    Owns:
    - Creating DTO-like payloads from explicit inputs.

    Does not own:
    - Provider execution, budget admission, or checkpoint semantics.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidatediscoveryfactory
    """

    def build(self, *args: Any, **kwargs: Any) -> Any:
        """Build a payload or service object from explicit inputs."""
