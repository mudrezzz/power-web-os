"""Persistence adapter for product-safe Radar technical traces."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from power_web_os.application.radar.lifecycle.records import RadarRunTechnicalTraceRecord
from power_web_os.persistence.models import RadarRunTechnicalTraceModel, utc_now
from power_web_os.persistence.record_mappers import technical_trace_record


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
        return technical_trace_record(model)

    def list_for_run(self, run_id: str) -> tuple[RadarRunTechnicalTraceRecord, ...]:
        stmt = (
            select(RadarRunTechnicalTraceModel)
            .where(RadarRunTechnicalTraceModel.run_id == run_id)
            .order_by(RadarRunTechnicalTraceModel.sequence)
        )
        return tuple(technical_trace_record(model) for model in self._session.scalars(stmt).all())

    def next_sequence(self, run_id: str) -> int:
        value = self._session.scalar(
            select(func.max(RadarRunTechnicalTraceModel.sequence)).where(RadarRunTechnicalTraceModel.run_id == run_id)
        )
        return int(value or 0) + 1
