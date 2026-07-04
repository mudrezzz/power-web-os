"""Execution state records for candidate discovery staged execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from power_web_os.application.radar.candidate_discovery.contracts import LiveRadarPipelineEvent, RadarSourceEvidence
from power_web_os.application.live_radar_universe import dict_list


@dataclass
class CandidateDiscoveryExecutionState:
    """Mutable state passed from the orchestrator to phase/finalization services.

    Owns:
    - Cross-phase mutable sources, observations, metadata, events, checkpoints,
      candidate scope, coverage records, expansion diagnostics, and signal status.

    Does not own:
    - Provider dependencies, budgets, policy services, or immutable run limits.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#candidatediscoveryexecutionstate
    """

    sources: list[RadarSourceEvidence] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    events: list[LiveRadarPipelineEvent] = field(default_factory=list)
    executed_task_ids: list[str] = field(default_factory=list)
    completed_qualification_ids: list[str] = field(default_factory=list)
    gate_results: list[dict[str, Any]] = field(default_factory=list)
    candidate_scope: list[str] = field(default_factory=list)
    coverage_checks: list[dict[str, Any]] = field(default_factory=list)
    unresolved_candidate_gaps: list[dict[str, Any]] = field(default_factory=list)
    coverage_warnings: list[str] = field(default_factory=list)
    useful_result_warnings: list[str] = field(default_factory=list)
    useful_result_retry_records: list[dict[str, Any]] = field(default_factory=list)
    checkpoint_decisions: list[dict[str, Any]] = field(default_factory=list)
    adaptive_actions: list[dict[str, Any]] = field(default_factory=list)
    checkpoint_warnings: list[str] = field(default_factory=list)
    stopped_for_review_reason: str = ""
    discovery_iteration_count: int = 0
    signal_task_count: int = 0
    signal_budget_warnings: list[str] = field(default_factory=list)
    signal_candidate_scope: list[str] = field(default_factory=list)
    signal_search_statuses: list[dict[str, Any]] = field(default_factory=list)


class SmokeLimitPolicy:
    """Applies smoke-profile caps without owning candidate selection semantics.

    Owns:
    - Deterministic smoke-profile list truncation for candidate and signal scopes.

    Does not own:
    - Candidate scoring, source policy, or budget admission.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#smokelimitpolicy
    """

    def limit_candidates(self, candidate_scope: list[str], limit: int | None) -> list[str]:
        if limit is None or limit <= 0:
            return candidate_scope
        return candidate_scope[:limit]

    def limit_signal_tasks(self, tasks: list[Any], limit: int | None) -> list[Any]:
        if limit is None or limit <= 0:
            return tasks
        return tasks[:limit]


class ExecutionMetadataFactory:
    """Builds initial execution metadata from product-safe task context.

    Owns:
    - Initial product-safe provider metadata derived from explicit task context.

    Does not own:
    - Runtime provider results, checkpoint decisions, or final metadata projection.

    Architecture:
    docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md#executionmetadatafactory
    """

    def initial_provider_metadata(self, radar: dict[str, Any]) -> dict[str, Any]:
        task_context = radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}
        if not str(task_context.get("benchmark_profile") or "").startswith("benchmark_"):
            return {}
        targets = dict_list(task_context.get("benchmark_target_hints"))
        if not targets:
            return {}
        return {"benchmark_recall_targets": targets}
