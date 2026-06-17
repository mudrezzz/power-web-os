"""SQLAlchemy implementations of application Radar repository ports.

This module is the adapter boundary: it translates between ORM models and
application records, while callers own transactions and use only ports.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from power_web_os.application.radar_records import (
    RadarDefinitionRecord,
    RadarRecord,
    RadarRunOutputRecord,
    RadarRunRecord,
    RadarRunStatus,
)
from power_web_os.persistence.models import (
    RadarDefinitionModel,
    RadarModel,
    RadarRunModel,
    RadarRunOutputModel,
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


def _aware_utc(value: datetime | None) -> datetime | None:
    # SQLite returns timezone-naive values even for timezone=True columns.
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)
