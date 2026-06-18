"""SQLAlchemy implementations of application Radar repository ports.

This module is the adapter boundary: it translates between ORM models and
application records, while callers own transactions and use only ports.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from power_web_os.application.radar_records import (
    RadarDefinitionRecord,
    RadarRecord,
    RadarRunEventRecord,
    RadarRunOutputRecord,
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

    def list_for_radar(self, radar_id: str) -> tuple[RadarRunRecord, ...]:
        stmt = select(RadarRunModel).where(RadarRunModel.radar_id == radar_id).order_by(RadarRunModel.queued_at)
        return tuple(_run_record(model) for model in self._session.scalars(stmt).all())

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
        model.artifact_payload_json = dict(record.artifact_payload)
        model.updated_at = record.updated_at or now
        self._session.flush()
        return _run_output_record(model)

    def get(self, run_id: str) -> RadarRunOutputRecord | None:
        model = self._session.get(RadarRunOutputModel, run_id)
        return _run_output_record(model) if model is not None else None


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


def _radar_record(model: RadarModel) -> RadarRecord:
    return RadarRecord(
        radar_id=model.radar_id,
        name=model.name,
        status=model.status,
        owner=model.owner,
        profile=dict(model.profile_json),
        summary=dict(model.summary_json),
        artifact_path=model.artifact_path,
        created_at=_aware_utc(model.created_at),
        updated_at=_aware_utc(model.updated_at),
    )


def _definition_record(model: RadarDefinitionModel) -> RadarDefinitionRecord:
    return RadarDefinitionRecord(
        definition_id=model.definition_id,
        radar_id=model.radar_id,
        definition_payload=dict(model.definition_json),
        definition_version=model.definition_version,
        is_active=model.is_active,
        created_at=_aware_utc(model.created_at),
        updated_at=_aware_utc(model.updated_at),
    )


def _run_record(model: RadarRunModel) -> RadarRunRecord:
    return RadarRunRecord(
        run_id=model.run_id,
        radar_id=model.radar_id,
        status=RadarRunStatus(model.status),
        queued_at=_aware_utc(model.queued_at),
        started_at=_aware_utc(model.started_at),
        completed_at=_aware_utc(model.completed_at),
        idempotency_key=model.idempotency_key,
        correlation_id=model.correlation_id,
        error_message=model.error_message,
        error_metadata=dict(model.error_metadata_json),
        run_metadata=dict(model.run_metadata_json),
        created_at=_aware_utc(model.created_at),
        updated_at=_aware_utc(model.updated_at),
    )


def _run_output_record(model: RadarRunOutputModel) -> RadarRunOutputRecord:
    return RadarRunOutputRecord(
        run_id=model.run_id,
        artifact_version=model.artifact_version,
        radar_payload=dict(model.radar_payload_json),
        search_plan_payload=dict(model.search_plan_json),
        sources_payload=[dict(item) for item in model.sources_json],
        candidates_payload=[dict(item) for item in model.candidates_json],
        contract_validation_payload=[dict(item) for item in model.contract_validation_json],
        artifact_payload=dict(model.artifact_payload_json),
        created_at=_aware_utc(model.created_at),
        updated_at=_aware_utc(model.updated_at),
    )


def _review_decision_record(model: RadarReviewDecisionModel) -> RadarReviewDecisionRecord:
    return RadarReviewDecisionRecord(
        decision_id=model.decision_id,
        run_id=model.run_id,
        radar_id=model.radar_id,
        candidate_id=model.candidate_id,
        subject_type=model.subject_type,
        subject_id=model.subject_id,
        status=model.status,
        reviewer=model.reviewer,
        comment=model.comment,
        decision_payload=dict(model.decision_payload_json),
        score_impact=dict(model.score_impact_json),
        reviewed_at=_aware_utc(model.reviewed_at),
        created_at=_aware_utc(model.created_at),
        updated_at=_aware_utc(model.updated_at),
    )


def _run_event_record(model: RadarRunEventModel) -> RadarRunEventRecord:
    return RadarRunEventRecord(
        event_id=model.event_id,
        run_id=model.run_id,
        sequence=model.sequence,
        event_type=model.event_type,
        phase=model.phase,
        actor=model.actor,
        node_name=model.node_name,
        visibility=model.visibility,
        summary=model.summary,
        payload=dict(model.payload_json),
        source_refs=[str(item) for item in model.source_refs_json],
        candidate_refs=[str(item) for item in model.candidate_refs_json],
        created_at=_aware_utc(model.created_at),
    )


def _technical_trace_record(model: RadarRunTechnicalTraceModel) -> RadarRunTechnicalTraceRecord:
    return RadarRunTechnicalTraceRecord(
        trace_id=model.trace_id,
        run_id=model.run_id,
        sequence=model.sequence,
        phase=model.phase,
        node_name=model.node_name,
        trace_type=model.trace_type,
        title=model.title,
        summary=model.summary,
        duration_ms=model.duration_ms,
        payload=dict(model.payload_json),
        redaction_report=dict(model.redaction_report_json),
        created_at=_aware_utc(model.created_at),
    )


def _aware_utc(value: datetime | None) -> datetime | None:
    # SQLite returns timezone-naive values even for timezone=True columns.
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)
