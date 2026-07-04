"""Execution state records for candidate discovery staged execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeVar

from power_web_os.application.radar.candidate_discovery.contracts import LiveRadarPipelineEvent, RadarSourceEvidence
from power_web_os.application.live_radar_universe import dict_list

T = TypeVar("T")


@dataclass
class CandidateDiscoveryExecutionState:
    """Mutable state passed from the orchestrator to phase/finalization services."""

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


def limit_smoke_candidates(candidate_scope: list[str], limit: int | None) -> list[str]:
    if limit is None or limit <= 0:
        return candidate_scope
    return candidate_scope[:limit]


def limit_smoke_signal_tasks(tasks: list[T], limit: int | None) -> list[T]:
    if limit is None or limit <= 0:
        return tasks
    return tasks[:limit]


def initial_provider_metadata(radar: dict[str, Any]) -> dict[str, Any]:
    task_context = radar.get("task_context") if isinstance(radar.get("task_context"), dict) else {}
    if not str(task_context.get("benchmark_profile") or "").startswith("benchmark_"):
        return {}
    targets = dict_list(task_context.get("benchmark_target_hints"))
    if not targets:
        return {}
    return {"benchmark_recall_targets": targets}
