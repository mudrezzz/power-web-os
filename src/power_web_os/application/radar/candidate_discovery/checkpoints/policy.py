"""Checkpoint policy and deterministic review decisions."""

from __future__ import annotations

from collections import Counter
from typing import Any, Literal

from .models import (
    RadarCheckpointAction,
    RadarCheckpointReasonCode,
    RadarExecutionCheckpointDecision,
    RadarExecutionCheckpointInput,
    RadarExecutionCheckpointPolicy,
)


class RadarExecutionCheckpointService:
    """Review staged execution quality before moving to the next phase.

    Owns:
        Deterministic checkpoint action selection from provider-neutral execution facts.
    Does not own:
        Provider calls, persistence, API projection, or phase execution loops.
    Architecture:
        See docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md.
    """

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
                action="repair_extraction",
                reason_code="extraction_schema_failed",
                severity="error",
                message="Provider extraction schema failed; extraction repair or retry is required before continuing.",
                should_continue=False,
                details={"extraction_issue_codes": sorted(set(checkpoint.extraction_issue_codes))},
            )

        if checkpoint.evidence_linking_issue_count or "evidence_linking_failed" in checkpoint.extraction_issue_codes:
            if _should_expand_before_revision(checkpoint, self._policy):
                return _decision(
                    checkpoint,
                    action="expand_sources",
                    reason_code="weak_candidate_coverage",
                    severity="warning",
                    message="Evidence linking is weak because recall coverage is incomplete; run bounded source expansion before plan revision.",
                    details={
                        "evidence_linking_issue_count": checkpoint.evidence_linking_issue_count,
                        "extraction_issue_codes": sorted(set(checkpoint.extraction_issue_codes)),
                        "search_expansion_target_count": checkpoint.search_expansion_target_count,
                        "uncovered_target_hint_count": checkpoint.uncovered_target_hint_count,
                    },
                )
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
                action = "expand_sources" if _recall_expansion_is_available(checkpoint) else "retry_same_source"
                return _decision(
                    checkpoint,
                    action=action,
                    reason_code="weak_candidate_coverage",
                    severity="warning",
                    message="Candidate discovery is too weak; retry or source expansion is required before continuing.",
                    details={
                        "candidate_scope_count": checkpoint.candidate_scope_count,
                        "search_expansion_target_count": checkpoint.search_expansion_target_count,
                        "uncovered_target_hint_count": checkpoint.uncovered_target_hint_count,
                    },
                )
            if checkpoint.linked_source_count < self._policy.min_linked_sources_before_signals:
                action = "expand_sources" if _recall_expansion_is_available(checkpoint) else "retry_same_source"
                return _decision(
                    checkpoint,
                    action=action,
                    reason_code="weak_candidate_coverage",
                    severity="warning",
                    message="Discovery candidates do not have enough linked source evidence.",
                    details={
                        "linked_source_count": checkpoint.linked_source_count,
                        "min_linked_sources": self._policy.min_linked_sources_before_signals,
                        "search_expansion_target_count": checkpoint.search_expansion_target_count,
                        "uncovered_target_hint_count": checkpoint.uncovered_target_hint_count,
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

        return _continue(checkpoint)

    def _before_signal_search(self, checkpoint: RadarExecutionCheckpointInput) -> RadarExecutionCheckpointDecision:
        if checkpoint.candidate_scope_count < self._policy.min_candidates_before_signals:
            return _decision(
                checkpoint,
                action="stop_review_needed",
                reason_code="no_candidate_scope",
                severity="warning",
                message="No qualified candidate scope is available for signal-monitoring handoff.",
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
                message="Qualified candidates do not have enough linked source evidence for signal-monitoring handoff.",
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
                message="Coverage risk is high before signal-monitoring handoff.",
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
                message="Execution budget was exhausted before signal-monitoring handoff.",
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
    should_run_signal_search: bool | None = None,
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
        should_run_signal_search=should_continue if should_run_signal_search is None else should_run_signal_search,
        details={
            "candidate_count": checkpoint.candidate_count,
            "candidate_scope_count": checkpoint.candidate_scope_count,
            "source_count": checkpoint.source_count,
            "retrieved_source_count": checkpoint.retrieved_source_count,
            "linked_source_count": checkpoint.linked_source_count,
            "diagnostic_source_count": checkpoint.diagnostic_source_count,
            "unresolved_gap_count": checkpoint.unresolved_gap_count,
            "search_expansion_target_count": checkpoint.search_expansion_target_count,
            "search_expansion_result_count": checkpoint.search_expansion_result_count,
            "targets_not_searched_count": checkpoint.targets_not_searched_count,
            "uncovered_target_hint_count": checkpoint.uncovered_target_hint_count,
            **(details or {}),
        },
    )


def _blocking_source_obligations(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocking_statuses = {
        "blocked",
        "violated",
        "unavailable",
        "empty",
        "attempted_empty",
        "attempted_insufficient",
        "attempted_unlinked",
    }
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


def _recall_expansion_is_available(checkpoint: RadarExecutionCheckpointInput) -> bool:
    if checkpoint.budget_exhaustion_events:
        return False
    if checkpoint.search_expansion_result_count or checkpoint.targets_not_searched_count:
        return False
    return bool(
        checkpoint.search_expansion_target_count
        or checkpoint.uncovered_target_hint_count
        or _high_coverage_risk(checkpoint)
        or checkpoint.unresolved_gap_count
    )


def _should_expand_before_revision(
    checkpoint: RadarExecutionCheckpointInput,
    policy: RadarExecutionCheckpointPolicy,
) -> bool:
    if checkpoint.phase not in {"after_discovery", "after_coverage"}:
        return False
    if not _recall_expansion_is_available(checkpoint):
        return False
    if checkpoint.search_expansion_result_count or checkpoint.targets_not_searched_count:
        return False
    weak_scope = checkpoint.candidate_scope_count < policy.min_candidates_before_signals
    weak_linkage = checkpoint.linked_source_count < policy.min_linked_sources_before_signals
    target_gap = bool(checkpoint.search_expansion_target_count or checkpoint.uncovered_target_hint_count)
    return weak_scope or weak_linkage or target_gap or _high_coverage_risk(checkpoint)
