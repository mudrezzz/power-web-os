"""Checkpoint value models for candidate-discovery execution."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RadarCheckpointAction = Literal[
    "continue",
    "retry_same_source",
    "expand_sources",
    "repair_extraction",
    "retry_extraction",
    "revise_plan",
    "stop_review_needed",
    "fail_hard",
]
RadarCheckpointReasonCode = Literal[
    "quality_sufficient",
    "weak_candidate_coverage",
    "source_obligation_unmet",
    "extraction_schema_failed",
    "extraction_repair_exhausted",
    "evidence_linking_failed",
    "budget_exhausted",
    "coverage_risk_high",
    "no_candidate_scope",
]
RadarCheckpointPhase = Literal[
    "after_discovery",
    "after_qualification_gates",
    "after_coverage",
    "before_signal_search",
]


class RadarExecutionCheckpointPolicy(BaseModel):
    min_candidates_before_signals: int = 1
    min_linked_sources_before_signals: int = 1
    max_revisions_per_run: int = 2
    max_retries_per_stage: int = 1


class RadarExecutionCheckpointInput(BaseModel):
    checkpoint_id: str
    phase: RadarCheckpointPhase
    candidate_count: int = 0
    candidate_scope_count: int = 0
    source_count: int = 0
    retrieved_source_count: int = 0
    linked_source_count: int = 0
    diagnostic_source_count: int = 0
    analyzed_source_count: int = 0
    search_expansion_target_count: int = 0
    search_expansion_result_count: int = 0
    targets_not_searched_count: int = 0
    uncovered_target_hint_count: int = 0
    source_obligation_decisions: list[dict[str, Any]] = Field(default_factory=list)
    extraction_issue_codes: list[str] = Field(default_factory=list)
    evidence_linking_issue_count: int = 0
    coverage_warnings: list[str] = Field(default_factory=list)
    coverage_checks: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_gap_count: int = 0
    budget_exhaustion_events: list[dict[str, Any]] = Field(default_factory=list)
    useful_result_retry_count: int = 0
    remaining_signal_task_count: int = 0


class RadarExecutionCheckpointDecision(BaseModel):
    checkpoint_id: str
    phase: RadarCheckpointPhase
    action: RadarCheckpointAction
    reason_code: RadarCheckpointReasonCode
    severity: Literal["info", "warning", "error"] = "info"
    message: str
    should_continue: bool = True
    should_run_signal_search: bool = True
    details: dict[str, Any] = Field(default_factory=dict)
