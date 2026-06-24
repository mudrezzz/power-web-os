"""Adaptive review checkpoints for staged Radar execution.

The checkpoint service owns product-safe execution decisions between expensive
pipeline phases. It does not call providers or persistence adapters; staged
execution applies the returned decision.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Literal

from pydantic import BaseModel, Field


RadarCheckpointAction = Literal[
    "continue",
    "retry_same_source",
    "expand_sources",
    "revise_plan",
    "stop_review_needed",
    "fail_hard",
]
RadarCheckpointReasonCode = Literal[
    "quality_sufficient",
    "weak_candidate_coverage",
    "source_obligation_unmet",
    "extraction_schema_failed",
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
    linked_source_count: int = 0
    analyzed_source_count: int = 0
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


class RadarExecutionCheckpointService:
    """Review staged execution quality before moving to the next phase."""

    def __init__(self, policy: RadarExecutionCheckpointPolicy | None = None) -> None:
        self._policy = policy or RadarExecutionCheckpointPolicy()

    @property
    def policy(self) -> RadarExecutionCheckpointPolicy:
        return self._policy

    def review(self, checkpoint: RadarExecutionCheckpointInput) -> RadarExecutionCheckpointDecision:
        hard_obligation = _blocking_source_obligations(checkpoint.source_obligation_decisions)
        if hard_obligation:
            return _decision(
                checkpoint,
                action="fail_hard",
                reason_code="source_obligation_unmet",
                severity="error",
                message="A required source obligation was not satisfied.",
                should_continue=False,
                details={"source_obligations": hard_obligation},
            )

        if "extraction_schema_invalid" in checkpoint.extraction_issue_codes:
            return _decision(
                checkpoint,
                action="revise_plan",
                reason_code="extraction_schema_failed",
                severity="error",
                message="Provider extraction schema failed; execution should not continue blindly.",
                should_continue=False,
                details={"extraction_issue_codes": sorted(set(checkpoint.extraction_issue_codes))},
            )

        if checkpoint.evidence_linking_issue_count or "evidence_linking_failed" in checkpoint.extraction_issue_codes:
            return _decision(
                checkpoint,
                action="revise_plan",
                reason_code="evidence_linking_failed",
                severity="error",
                message="Evidence references did not resolve to normalized sources.",
                should_continue=False,
                details={
                    "evidence_linking_issue_count": checkpoint.evidence_linking_issue_count,
                    "extraction_issue_codes": sorted(set(checkpoint.extraction_issue_codes)),
                },
            )

        if checkpoint.phase == "before_signal_search":
            return self._before_signal_search(checkpoint)

        if checkpoint.phase in {"after_discovery", "after_coverage"}:
            if checkpoint.candidate_scope_count < self._policy.min_candidates_before_signals:
                return _decision(
                    checkpoint,
                    action="retry_same_source",
                    reason_code="weak_candidate_coverage",
                    severity="warning",
                    message="Candidate discovery is too weak; retry or source expansion is required before continuing.",
                    details={"candidate_scope_count": checkpoint.candidate_scope_count},
                )
            if checkpoint.linked_source_count < self._policy.min_linked_sources_before_signals:
                return _decision(
                    checkpoint,
                    action="retry_same_source",
                    reason_code="weak_candidate_coverage",
                    severity="warning",
                    message="Discovery candidates do not have enough linked source evidence.",
                    details={
                        "linked_source_count": checkpoint.linked_source_count,
                        "min_linked_sources": self._policy.min_linked_sources_before_signals,
                    },
                )

        if checkpoint.budget_exhaustion_events:
            return _decision(
                checkpoint,
                action="stop_review_needed",
                reason_code="budget_exhausted",
                severity="warning",
                message="Execution budget was exhausted before this checkpoint completed.",
                should_continue=False,
                details={"budget_exhaustion_events": checkpoint.budget_exhaustion_events},
            )

        if checkpoint.useful_result_retry_count:
            return _decision(
                checkpoint,
                action="retry_same_source",
                reason_code="weak_candidate_coverage",
                severity="warning",
                message="A bounded retry was used because an earlier result was weak.",
                details={"useful_result_retry_count": checkpoint.useful_result_retry_count},
            )

        return _continue(checkpoint)

    def _before_signal_search(self, checkpoint: RadarExecutionCheckpointInput) -> RadarExecutionCheckpointDecision:
        if checkpoint.candidate_scope_count < self._policy.min_candidates_before_signals:
            return _decision(
                checkpoint,
                action="stop_review_needed",
                reason_code="no_candidate_scope",
                severity="warning",
                message="No qualified candidate scope is available for signal search.",
                should_continue=False,
                should_run_signal_search=False,
                details={"candidate_scope_count": checkpoint.candidate_scope_count},
            )
        if checkpoint.linked_source_count < self._policy.min_linked_sources_before_signals:
            return _decision(
                checkpoint,
                action="stop_review_needed",
                reason_code="weak_candidate_coverage",
                severity="warning",
                message="Qualified candidates do not have enough linked source evidence for signal search.",
                should_continue=False,
                should_run_signal_search=False,
                details={
                    "linked_source_count": checkpoint.linked_source_count,
                    "min_linked_sources": self._policy.min_linked_sources_before_signals,
                },
            )
        if _high_coverage_risk(checkpoint):
            return _decision(
                checkpoint,
                action="stop_review_needed",
                reason_code="coverage_risk_high",
                severity="warning",
                message="Coverage risk is high before signal search.",
                should_continue=False,
                should_run_signal_search=False,
                details={"coverage_warnings": checkpoint.coverage_warnings, "coverage_checks": checkpoint.coverage_checks},
            )
        if checkpoint.budget_exhaustion_events:
            return _decision(
                checkpoint,
                action="stop_review_needed",
                reason_code="budget_exhausted",
                severity="warning",
                message="Execution budget was exhausted before signal search.",
                should_continue=False,
                should_run_signal_search=False,
                details={"budget_exhaustion_events": checkpoint.budget_exhaustion_events},
            )
        return _continue(checkpoint)


def checkpoint_summary(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    by_action = Counter(str(item.get("action") or "unknown") for item in decisions)
    by_reason = Counter(str(item.get("reason_code") or "unknown") for item in decisions)
    blocking = [
        item for item in decisions
        if str(item.get("action")) in {"stop_review_needed", "fail_hard", "revise_plan"}
    ]
    return {
        "decision_count": len(decisions),
        "by_action": dict(by_action),
        "by_reason": dict(by_reason),
        "blocking_count": len(blocking),
        "stopped_for_review": any(str(item.get("action")) == "stop_review_needed" for item in decisions),
        "hard_failure_recommended": any(str(item.get("action")) == "fail_hard" for item in decisions),
    }


def _continue(checkpoint: RadarExecutionCheckpointInput) -> RadarExecutionCheckpointDecision:
    return _decision(
        checkpoint,
        action="continue",
        reason_code="quality_sufficient",
        message="Checkpoint quality gates passed.",
    )


def _decision(
    checkpoint: RadarExecutionCheckpointInput,
    *,
    action: RadarCheckpointAction,
    reason_code: RadarCheckpointReasonCode,
    message: str,
    severity: Literal["info", "warning", "error"] = "info",
    should_continue: bool = True,
    should_run_signal_search: bool = True,
    details: dict[str, Any] | None = None,
) -> RadarExecutionCheckpointDecision:
    return RadarExecutionCheckpointDecision(
        checkpoint_id=checkpoint.checkpoint_id,
        phase=checkpoint.phase,
        action=action,
        reason_code=reason_code,
        severity=severity,
        message=message,
        should_continue=should_continue,
        should_run_signal_search=should_run_signal_search,
        details={
            "candidate_count": checkpoint.candidate_count,
            "candidate_scope_count": checkpoint.candidate_scope_count,
            "source_count": checkpoint.source_count,
            "linked_source_count": checkpoint.linked_source_count,
            "unresolved_gap_count": checkpoint.unresolved_gap_count,
            **(details or {}),
        },
    )


def _blocking_source_obligations(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocking_statuses = {"blocked", "violated", "unavailable", "empty"}
    return [
        dict(item)
        for item in decisions
        if bool(item.get("required")) and str(item.get("status") or "") in blocking_statuses
    ]


def _high_coverage_risk(checkpoint: RadarExecutionCheckpointInput) -> bool:
    if any("high" in warning.lower() and "coverage" in warning.lower() for warning in checkpoint.coverage_warnings):
        return True
    for item in checkpoint.coverage_checks:
        if str(item.get("completeness_risk") or "").lower() == "high":
            return True
    return False
