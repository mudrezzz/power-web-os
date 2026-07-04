"""Execution context contracts for candidate-discovery phase services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import (
    RadarExecutionPlan,
    WebSearchProvider,
)
from power_web_os.application.live_radar_checkpoint_actions import RadarCheckpointActionExecutor
from power_web_os.application.live_radar_checkpoints import RadarExecutionCheckpointService
from power_web_os.application.live_radar_execution_budget import RadarExecutionBudget, RadarExecutionBudgetSettings
from power_web_os.application.live_radar_external_budget import RadarExternalCallBudget
from power_web_os.application.live_radar_useful_budget import UsefulResultBudget
from power_web_os.application.radar_search_expansion import RadarSearchExpansionService
from power_web_os.application.radar_work_scheduler import RadarWorkScheduler
from power_web_os.integrations.live_radar_source_verification import SourceVerificationCache


@dataclass(slots=True)
class CandidateDiscoveryExecutionContext:
    """Shared dependencies and immutable-ish limits for one candidate-discovery run.

    Owns:
    - Provider port, budgets, checkpoint services, scheduler, expansion service,
      retrieval plan, source policy decisions, and execution limits for one run.

    Does not own:
    - Mutable sources, observations, events, or provider metadata; those belong to
      `CandidateDiscoveryExecutionState`.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidatediscoveryexecutioncontext
    """

    radar: dict[str, Any]
    execution_plan: RadarExecutionPlan
    retrieval_plan: Any
    provider: WebSearchProvider
    task_budget: RadarExecutionBudget
    budget_settings: RadarExecutionBudgetSettings
    external_budget: RadarExternalCallBudget
    useful_budget: UsefulResultBudget
    checkpoint_service: RadarExecutionCheckpointService
    checkpoint_executor: RadarCheckpointActionExecutor
    search_expansion_service: RadarSearchExpansionService
    work_scheduler: RadarWorkScheduler
    verification_cache: SourceVerificationCache
    source_policy_decisions: list[dict[str, Any]] | None
    max_discovery_iterations: int
    max_candidate_universe_size: int


@dataclass(frozen=True, slots=True)
class PhaseResult:
    """Small phase status record; phase services mutate state explicitly.

    Owns:
    - Compact phase status, reason, and phase name for orchestration decisions.

    Does not own:
    - Full state transfer, provider results, events, or dossier metadata.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#phaseresult
    """

    phase_name: str
    status: str = "completed"
    reason: str = ""
