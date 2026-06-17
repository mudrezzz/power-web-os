"""Application service for persisted Radar human review decisions.

The service validates review semantics and delegates storage to a repository
port. It keeps FastAPI DTOs and SQLAlchemy models out of the application layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from power_web_os.application.ports import RadarReviewDecisionRepository
from power_web_os.application.radar_records import RadarReviewDecisionRecord

QUALIFICATION_SUBJECT = "qualification"
SIGNAL_SUBJECT = "signal"

QUALIFICATION_STATUSES = {"approved", "rejected", "corrected"}
SIGNAL_STATUSES = {"confirmed", "rejected", "stale", "corrected"}
QUALIFICATION_ASSESSMENTS = {"matches", "partially_matches", "does_not_match", "unknown"}


class RadarReviewValidationError(ValueError):
    """Raised when a review decision violates the application contract."""


@dataclass(frozen=True, slots=True)
class RadarReviewDecisionCommand:
    run_id: str
    radar_id: str
    candidate_id: str
    subject_type: str
    subject_id: str
    status: str
    reviewer: str = "api"
    comment: str = ""
    decision_payload: dict[str, Any] = field(default_factory=dict)
    source_payload: dict[str, Any] = field(default_factory=dict)
    score_impact: dict[str, Any] = field(default_factory=dict)
    reviewed_at: datetime | None = None


class RadarReviewDecisionService:
    def __init__(self, *, repository: RadarReviewDecisionRepository) -> None:
        self._repository = repository

    def save(self, command: RadarReviewDecisionCommand) -> RadarReviewDecisionRecord:
        _validate(command)
        reviewed_at = command.reviewed_at or datetime.now(UTC).replace(microsecond=0)
        return self._repository.upsert(
            RadarReviewDecisionRecord(
                decision_id=_decision_id(command),
                run_id=command.run_id,
                radar_id=command.radar_id,
                candidate_id=command.candidate_id,
                subject_type=command.subject_type,
                subject_id=command.subject_id,
                status=command.status,
                reviewer=command.reviewer,
                comment=command.comment.strip(),
                decision_payload=dict(command.decision_payload),
                score_impact=dict(command.score_impact) or _score_impact(command),
                reviewed_at=reviewed_at,
            )
        )

    def list_for_run(self, run_id: str) -> tuple[RadarReviewDecisionRecord, ...]:
        return self._repository.list_for_run(run_id)

    def delete(self, *, run_id: str, candidate_id: str, subject_type: str, subject_id: str) -> bool:
        return self._repository.delete(
            run_id=run_id,
            candidate_id=candidate_id,
            subject_type=subject_type,
            subject_id=subject_id,
        )


def _validate(command: RadarReviewDecisionCommand) -> None:
    if command.subject_type == QUALIFICATION_SUBJECT:
        _validate_qualification(command)
        return
    if command.subject_type == SIGNAL_SUBJECT:
        _validate_signal(command)
        return
    raise RadarReviewValidationError(f"Unsupported review subject type: {command.subject_type}")


def _validate_qualification(command: RadarReviewDecisionCommand) -> None:
    if command.status not in QUALIFICATION_STATUSES:
        raise RadarReviewValidationError(f"Unsupported qualification review status: {command.status}")
    if command.status in {"rejected", "corrected"} and not command.comment.strip():
        raise RadarReviewValidationError("Qualification rejected/corrected decisions require a comment")
    corrected = command.decision_payload.get("corrected_assessment")
    if command.status == "corrected" and corrected not in QUALIFICATION_ASSESSMENTS:
        raise RadarReviewValidationError("Qualification corrected decisions require corrected_assessment")


def _validate_signal(command: RadarReviewDecisionCommand) -> None:
    if command.status not in SIGNAL_STATUSES:
        raise RadarReviewValidationError(f"Unsupported signal review status: {command.status}")
    if command.status in {"rejected", "stale", "corrected"} and not command.comment.strip():
        raise RadarReviewValidationError("Signal rejected/stale/corrected decisions require a comment")
    if command.status == "corrected":
        adjusted_score = command.decision_payload.get("adjusted_score")
        if not isinstance(adjusted_score, int) or adjusted_score < 0 or adjusted_score > 2:
            raise RadarReviewValidationError("Signal corrected decisions require adjusted_score between 0 and 2")


def _decision_id(command: RadarReviewDecisionCommand) -> str:
    return f"{command.run_id}:{command.candidate_id}:{command.subject_type}:{command.subject_id}"


def _score_impact(command: RadarReviewDecisionCommand) -> dict[str, Any]:
    if command.subject_type == QUALIFICATION_SUBJECT:
        return _qualification_score_impact(command)
    if command.subject_type == SIGNAL_SUBJECT:
        return _signal_score_impact(command)
    return {}


def _qualification_score_impact(command: RadarReviewDecisionCommand) -> dict[str, Any]:
    original = str(command.source_payload.get("final_assessment", "unknown"))
    effective = original
    if command.status == "rejected":
        effective = "does_not_match"
    if command.status == "corrected":
        effective = str(command.decision_payload.get("corrected_assessment", original))
    return {"original_assessment": original, "effective_assessment": effective}


def _signal_score_impact(command: RadarReviewDecisionCommand) -> dict[str, Any]:
    original = int(command.source_payload.get("score", 0) or 0)
    effective = original
    if command.status in {"rejected", "stale"}:
        effective = 0
    if command.status == "corrected":
        effective = int(command.decision_payload.get("adjusted_score", original))
    return {"original_score": original, "effective_score": effective, "delta": effective - original}
