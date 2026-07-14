"""SQLAlchemy implementations of application Radar repository ports.

This module is the adapter boundary: it translates between ORM models and
application records, while callers own transactions and use only ports.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from power_web_os.application.radar.candidate_discovery.execution.stored_public_surface import (
    StoredCandidatePublicSurfaceProjector,
)
from power_web_os.application.radar_records import (
    RadarDefinitionRecord,
    RadarRecord,
    RadarRunEventRecord,
    RadarRunOutputRecord,
    RadarRunOutputSummaryRecord,
    RadarRunRecord,
    RadarRunStatus,
    RadarReviewDecisionRecord,
    RadarRunTechnicalTraceRecord,
)
from power_web_os.persistence.models import (
    RadarDefinitionModel,
    RadarModel,
    RadarRunEventModel,
    RadarRunModel,
    RadarRunOutputModel,
    RadarReviewDecisionModel,
    RadarRunTechnicalTraceModel,
    utc_now,
)
from power_web_os.persistence.record_mappers import (
    definition_record as _definition_record,
    radar_record as _radar_record,
    review_decision_record as _review_decision_record,
    run_event_record as _run_event_record,
    run_output_record as _run_output_record,
    run_record as _run_record,
    technical_trace_record as _technical_trace_record,
)


class SqlAlchemyRadarRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, record: RadarRecord) -> RadarRecord:
        model = self._session.get(RadarModel, record.radar_id)
        now = utc_now()
        if model is None:
            model = RadarModel(radar_id=record.radar_id, created_at=record.created_at or now)
            self._session.add(model)
        model.name = record.name
        model.status = record.status
        model.owner = record.owner
        model.profile_json = dict(record.profile)
        model.summary_json = dict(record.summary)
        model.artifact_path = record.artifact_path
        model.updated_at = record.updated_at or now
        self._session.flush()
        return _radar_record(model)

    def get(self, radar_id: str) -> RadarRecord | None:
        model = self._session.get(RadarModel, radar_id)
        return _radar_record(model) if model is not None else None

    def list(self) -> tuple[RadarRecord, ...]:
        models = self._session.scalars(select(RadarModel).order_by(RadarModel.radar_id)).all()
        return tuple(_radar_record(model) for model in models)


class SqlAlchemyRadarDefinitionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, record: RadarDefinitionRecord) -> RadarDefinitionRecord:
        model = self._session.get(RadarDefinitionModel, record.definition_id)
        now = utc_now()
        if model is None:
            model = RadarDefinitionModel(definition_id=record.definition_id, created_at=record.created_at or now)
            self._session.add(model)
        model.radar_id = record.radar_id
        model.definition_version = record.definition_version
        model.definition_json = dict(record.definition_payload)
        model.is_active = record.is_active
        model.updated_at = record.updated_at or now
        self._session.flush()
        return _definition_record(model)

    def get_active(self, radar_id: str) -> RadarDefinitionRecord | None:
        stmt = (
            select(RadarDefinitionModel)
            .where(RadarDefinitionModel.radar_id == radar_id, RadarDefinitionModel.is_active.is_(True))
            .order_by(RadarDefinitionModel.updated_at.desc(), RadarDefinitionModel.definition_id)
        )
        model = self._session.scalars(stmt).first()
        return _definition_record(model) if model is not None else None

    def list_for_radar(self, radar_id: str) -> tuple[RadarDefinitionRecord, ...]:
        stmt = (
            select(RadarDefinitionModel)
            .where(RadarDefinitionModel.radar_id == radar_id)
            .order_by(RadarDefinitionModel.definition_id)
        )
        return tuple(_definition_record(model) for model in self._session.scalars(stmt).all())


class SqlAlchemyRadarRunRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, record: RadarRunRecord) -> RadarRunRecord:
        now = utc_now()
        model = RadarRunModel(
            run_id=record.run_id,
            radar_id=record.radar_id,
            pipeline_id=record.pipeline_id,
            source_run_id=record.source_run_id,
            status=record.status.value,
            queued_at=record.queued_at or now,
            started_at=record.started_at,
            completed_at=record.completed_at,
            idempotency_key=record.idempotency_key,
            correlation_id=record.correlation_id,
            error_message=record.error_message,
            error_metadata_json=dict(record.error_metadata),
            run_metadata_json=dict(record.run_metadata),
            created_at=record.created_at or now,
            updated_at=record.updated_at or now,
        )
        self._session.add(model)
        self._session.flush()
        return _run_record(model)

    def get(self, run_id: str) -> RadarRunRecord | None:
        model = self._session.get(RadarRunModel, run_id)
        return _run_record(model) if model is not None else None

    def find_by_idempotency_key(self, idempotency_key: str) -> RadarRunRecord | None:
        model = self._session.scalars(
            select(RadarRunModel).where(RadarRunModel.idempotency_key == idempotency_key)
        ).first()
        return _run_record(model) if model is not None else None

    def list_for_radar(
        self,
        radar_id: str,
        *,
        pipeline_id: str = "candidate_discovery",
    ) -> tuple[RadarRunRecord, ...]:
        stmt = (
            select(RadarRunModel)
            .where(RadarRunModel.radar_id == radar_id, RadarRunModel.pipeline_id == pipeline_id)
            .order_by(RadarRunModel.queued_at)
        )
        return tuple(_run_record(model) for model in self._session.scalars(stmt).all())

    def latest_for_radar(self, radar_id: str, *, pipeline_id: str = "candidate_discovery") -> RadarRunRecord | None:
        stmt = (
            select(RadarRunModel)
            .where(RadarRunModel.radar_id == radar_id, RadarRunModel.pipeline_id == pipeline_id)
            .order_by(RadarRunModel.queued_at.desc())
            .limit(1)
        )
        model = self._session.scalars(stmt).first()
        return _run_record(model) if model is not None else None

    def latest_summary_for_radar(
        self,
        radar_id: str,
        *,
        pipeline_id: str = "candidate_discovery",
    ) -> RadarRunRecord | None:
        stmt = (
            select(
                RadarRunModel.run_id,
                RadarRunModel.radar_id,
                RadarRunModel.pipeline_id,
                RadarRunModel.source_run_id,
                RadarRunModel.status,
                RadarRunModel.queued_at,
                RadarRunModel.started_at,
                RadarRunModel.completed_at,
                RadarRunModel.idempotency_key,
                RadarRunModel.correlation_id,
                RadarRunModel.error_message,
                RadarRunModel.created_at,
                RadarRunModel.updated_at,
            )
            .where(
                RadarRunModel.radar_id == radar_id,
                RadarRunModel.pipeline_id == pipeline_id,
                RadarRunModel.status == RadarRunStatus.COMPLETED.value,
            )
            .order_by(RadarRunModel.queued_at.desc())
            .limit(1)
        )
        row = self._session.execute(stmt).first()
        if row is None:
            return None
        return RadarRunRecord(
            run_id=row.run_id,
            radar_id=row.radar_id,
            pipeline_id=row.pipeline_id,
            source_run_id=row.source_run_id,
            status=RadarRunStatus(row.status),
            queued_at=row.queued_at,
            started_at=row.started_at,
            completed_at=row.completed_at,
            idempotency_key=row.idempotency_key,
            correlation_id=row.correlation_id,
            error_message=row.error_message,
            error_metadata={},
            run_metadata={},
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def count_for_radar(self, radar_id: str, *, pipeline_id: str = "candidate_discovery") -> int:
        stmt = select(func.count()).select_from(RadarRunModel).where(
            RadarRunModel.radar_id == radar_id,
            RadarRunModel.pipeline_id == pipeline_id,
        )
        return int(self._session.scalar(stmt) or 0)

    def update_status(
        self,
        run_id: str,
        status: RadarRunStatus,
        *,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        error_message: str | None = None,
        error_metadata: dict[str, object] | None = None,
        run_metadata: dict[str, object] | None = None,
    ) -> RadarRunRecord:
        model = self._session.get(RadarRunModel, run_id)
        if model is None:
            raise KeyError(f"Radar run not found: {run_id}")

        now = utc_now()
        model.status = status.value
        if status is RadarRunStatus.RUNNING:
            model.started_at = started_at or model.started_at or now
        if status.is_terminal:
            model.completed_at = completed_at or model.completed_at or now
        if error_message is not None:
            model.error_message = error_message
        if error_metadata is not None:
            model.error_metadata_json = dict(error_metadata)
        if run_metadata is not None:
            model.run_metadata_json = dict(run_metadata)
        model.updated_at = now
        self._session.flush()
        return _run_record(model)


class SqlAlchemyRadarRunOutputRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, record: RadarRunOutputRecord) -> RadarRunOutputRecord:
        public_surface = StoredCandidatePublicSurfaceProjector().project(
            artifact_payload=record.artifact_payload,
            candidates_payload=record.candidates_payload,
        )
        model = self._session.get(RadarRunOutputModel, record.run_id)
        now = utc_now()
        if model is None:
            model = RadarRunOutputModel(run_id=record.run_id, created_at=record.created_at or now)
            self._session.add(model)
        model.artifact_version = record.artifact_version
        model.radar_payload_json = dict(record.radar_payload)
        model.search_plan_json = dict(record.search_plan_payload)
        model.sources_json = [dict(item) for item in record.sources_payload]
        model.candidates_json = [dict(item) for item in record.candidates_payload]
        model.contract_validation_json = [dict(item) for item in record.contract_validation_payload]
        model.source_count = len(record.sources_payload)
        model.candidate_count = public_surface.candidate_count
        model.contract_issue_count = len(record.contract_validation_payload)
        model.visible_candidate_count = public_surface.candidate_count
        model.accepted_candidate_count = public_surface.accepted_count
        model.review_needed_candidate_count = public_surface.review_needed_count
        model.artifact_payload_json = dict(record.artifact_payload)
        model.updated_at = record.updated_at or now
        self._session.flush()
        return _run_output_record(model)

    def get(self, run_id: str) -> RadarRunOutputRecord | None:
        model = self._session.get(RadarRunOutputModel, run_id)
        return _run_output_record(model) if model is not None else None

    def get_summary(self, run_id: str) -> RadarRunOutputSummaryRecord | None:
        row = self._session.execute(
            select(
                RadarRunOutputModel.run_id,
                RadarRunOutputModel.artifact_version,
                RadarRunOutputModel.source_count,
                RadarRunOutputModel.candidate_count,
                RadarRunOutputModel.contract_issue_count,
                RadarRunOutputModel.visible_candidate_count,
                RadarRunOutputModel.accepted_candidate_count,
                RadarRunOutputModel.review_needed_candidate_count,
                RadarRunOutputModel.updated_at,
            ).where(RadarRunOutputModel.run_id == run_id)
        ).one_or_none()
        if row is None:
            return None
        return RadarRunOutputSummaryRecord(
            run_id=row.run_id,
            artifact_version=row.artifact_version,
            source_count=row.source_count,
            candidate_count=row.candidate_count,
            contract_issue_count=row.contract_issue_count,
            visible_candidate_count=row.visible_candidate_count,
            accepted_candidate_count=row.accepted_candidate_count,
            review_needed_candidate_count=row.review_needed_candidate_count,
            updated_at=row.updated_at,
        )

    def list_all(self) -> tuple[RadarRunOutputRecord, ...]:
        stmt = select(RadarRunOutputModel).order_by(RadarRunOutputModel.run_id)
        return tuple(_run_output_record(model) for model in self._session.scalars(stmt).all())

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
        return _review_decision_record(model)

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
        return _review_decision_record(model) if model is not None else None

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
        return tuple(_review_decision_record(model) for model in self._session.scalars(stmt).all())

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


class SqlAlchemyRadarRunEventRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def append(self, record: RadarRunEventRecord) -> RadarRunEventRecord:
        model = RadarRunEventModel(
            event_id=record.event_id,
            run_id=record.run_id,
            sequence=record.sequence,
            event_type=record.event_type,
            phase=record.phase,
            actor=record.actor,
            node_name=record.node_name,
            visibility=record.visibility,
            summary=record.summary,
            payload_json=dict(record.payload),
            source_refs_json=list(record.source_refs),
            candidate_refs_json=list(record.candidate_refs),
            created_at=record.created_at or utc_now(),
        )
        self._session.add(model)
        self._session.flush()
        return _run_event_record(model)

    def list_for_run(self, run_id: str) -> tuple[RadarRunEventRecord, ...]:
        stmt = (
            select(RadarRunEventModel)
            .where(RadarRunEventModel.run_id == run_id)
            .order_by(RadarRunEventModel.sequence)
        )
        return tuple(_run_event_record(model) for model in self._session.scalars(stmt).all())

    def next_sequence(self, run_id: str) -> int:
        value = self._session.scalar(
            select(func.max(RadarRunEventModel.sequence)).where(RadarRunEventModel.run_id == run_id)
        )
        return int(value or 0) + 1


class SqlAlchemyRadarRunTechnicalTraceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def append(self, record: RadarRunTechnicalTraceRecord) -> RadarRunTechnicalTraceRecord:
        model = RadarRunTechnicalTraceModel(
            trace_id=record.trace_id,
            run_id=record.run_id,
            sequence=record.sequence,
            phase=record.phase,
            node_name=record.node_name,
            trace_type=record.trace_type,
            title=record.title,
            summary=record.summary,
            duration_ms=record.duration_ms,
            payload_json=dict(record.payload),
            redaction_report_json=dict(record.redaction_report),
            created_at=record.created_at or utc_now(),
        )
        self._session.add(model)
        self._session.flush()
        return _technical_trace_record(model)

    def list_for_run(self, run_id: str) -> tuple[RadarRunTechnicalTraceRecord, ...]:
        stmt = (
            select(RadarRunTechnicalTraceModel)
            .where(RadarRunTechnicalTraceModel.run_id == run_id)
            .order_by(RadarRunTechnicalTraceModel.sequence)
        )
        return tuple(_technical_trace_record(model) for model in self._session.scalars(stmt).all())

    def next_sequence(self, run_id: str) -> int:
        value = self._session.scalar(
            select(func.max(RadarRunTechnicalTraceModel.sequence)).where(RadarRunTechnicalTraceModel.run_id == run_id)
        )
        return int(value or 0) + 1
