"""SQLAlchemy repository for pipeline-specific Signal Monitoring output."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from power_web_os.application.radar_records import SignalMonitoringRunOutputRecord
from power_web_os.persistence.models import (
    RadarRunModel,
    SignalMonitoringRunOutputModel,
    utc_now,
)
from power_web_os.persistence.record_mappers import signal_monitoring_output_record


class SqlAlchemySignalMonitoringRunOutputRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, record: SignalMonitoringRunOutputRecord) -> SignalMonitoringRunOutputRecord:
        model = self._session.get(SignalMonitoringRunOutputModel, record.run_id)
        now = utc_now()
        if model is None:
            model = SignalMonitoringRunOutputModel(run_id=record.run_id, created_at=record.created_at or now)
            self._session.add(model)
        model.source_run_id = record.source_run_id
        model.artifact_version = record.artifact_version
        model.input_snapshot_json = dict(record.input_snapshot_payload)
        model.plan_json = dict(record.plan_payload)
        model.observations_json = [dict(item) for item in record.observations_payload]
        model.artifact_payload_json = dict(record.artifact_payload)
        model.updated_at = record.updated_at or now
        self._session.flush()
        return signal_monitoring_output_record(model)

    def get(self, run_id: str) -> SignalMonitoringRunOutputRecord | None:
        model = self._session.get(SignalMonitoringRunOutputModel, run_id)
        return signal_monitoring_output_record(model) if model is not None else None

    def list_for_radar(self, radar_id: str) -> tuple[SignalMonitoringRunOutputRecord, ...]:
        stmt = (
            select(SignalMonitoringRunOutputModel)
            .join(RadarRunModel, RadarRunModel.run_id == SignalMonitoringRunOutputModel.run_id)
            .where(RadarRunModel.radar_id == radar_id, RadarRunModel.pipeline_id == "signal_monitoring")
            .order_by(RadarRunModel.queued_at)
        )
        return tuple(signal_monitoring_output_record(model) for model in self._session.scalars(stmt).all())
