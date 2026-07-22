"""Persistence adapter for Radar review decisions."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from power_web_os.application.radar.lifecycle.records import RadarReviewDecisionRecord
from power_web_os.persistence.models import RadarReviewDecisionModel, utc_now
from power_web_os.persistence.record_mappers import review_decision_record


class SqlAlchemyRadarReviewDecisionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, record: RadarReviewDecisionRecord) -> RadarReviewDecisionRecord:
        model = self._find_subject(
            run_id=record.run_id,
            candidate_id=record.candidate_id,
            subject_type=record.subject_type,
            subject_id=record.subject_id,
        )
        now = utc_now()
        if model is None:
            model = RadarReviewDecisionModel(decision_id=record.decision_id, created_at=record.created_at or now)
            self._session.add(model)
        model.run_id = record.run_id
        model.radar_id = record.radar_id
        model.candidate_id = record.candidate_id
        model.subject_type = record.subject_type
        model.subject_id = record.subject_id
        model.status = record.status
        model.reviewer = record.reviewer
        model.comment = record.comment
        model.decision_payload_json = dict(record.decision_payload)
        model.score_impact_json = dict(record.score_impact)
        model.reviewed_at = record.reviewed_at or now
        model.updated_at = record.updated_at or now
        self._session.flush()
        return review_decision_record(model)

    def get(
        self,
        *,
        run_id: str,
        candidate_id: str,
        subject_type: str,
        subject_id: str,
    ) -> RadarReviewDecisionRecord | None:
        model = self._find_subject(
            run_id=run_id,
            candidate_id=candidate_id,
            subject_type=subject_type,
            subject_id=subject_id,
        )
        return review_decision_record(model) if model is not None else None

    def list_for_run(self, run_id: str) -> tuple[RadarReviewDecisionRecord, ...]:
        stmt = (
            select(RadarReviewDecisionModel)
            .where(RadarReviewDecisionModel.run_id == run_id)
            .order_by(
                RadarReviewDecisionModel.candidate_id,
                RadarReviewDecisionModel.subject_type,
                RadarReviewDecisionModel.subject_id,
            )
        )
        return tuple(review_decision_record(model) for model in self._session.scalars(stmt).all())

    def delete(
        self,
        *,
        run_id: str,
        candidate_id: str,
        subject_type: str,
        subject_id: str,
    ) -> bool:
        model = self._find_subject(
            run_id=run_id,
            candidate_id=candidate_id,
            subject_type=subject_type,
            subject_id=subject_id,
        )
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    def _find_subject(
        self,
        *,
        run_id: str,
        candidate_id: str,
        subject_type: str,
        subject_id: str,
    ) -> RadarReviewDecisionModel | None:
        stmt = select(RadarReviewDecisionModel).where(
            RadarReviewDecisionModel.run_id == run_id,
            RadarReviewDecisionModel.candidate_id == candidate_id,
            RadarReviewDecisionModel.subject_type == subject_type,
            RadarReviewDecisionModel.subject_id == subject_id,
        )
        return self._session.scalars(stmt).first()
