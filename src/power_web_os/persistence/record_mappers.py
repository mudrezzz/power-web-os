"""Translate persisted Radar ORM rows into application records."""

from __future__ import annotations

from datetime import UTC, datetime

from power_web_os.application.radar_records import (
    RadarDefinitionRecord,
    RadarRecord,
    RadarReviewDecisionRecord,
    RadarRunEventRecord,
    RadarRunOutputRecord,
    RadarRunRecord,
    RadarRunStatus,
    RadarRunTechnicalTraceRecord,
    SignalMonitoringRunOutputRecord,
)
from power_web_os.persistence.models import (
    RadarDefinitionModel,
    RadarModel,
    RadarReviewDecisionModel,
    RadarRunEventModel,
    RadarRunModel,
    RadarRunOutputModel,
    RadarRunTechnicalTraceModel,
    SignalMonitoringRunOutputModel,
)


def radar_record(model: RadarModel) -> RadarRecord:
    return RadarRecord(
        radar_id=model.radar_id,
        name=model.name,
        status=model.status,
        owner=model.owner,
        profile=dict(model.profile_json),
        summary=dict(model.summary_json),
        artifact_path=model.artifact_path,
        created_at=aware_utc(model.created_at),
        updated_at=aware_utc(model.updated_at),
    )


def definition_record(model: RadarDefinitionModel) -> RadarDefinitionRecord:
    return RadarDefinitionRecord(
        definition_id=model.definition_id,
        radar_id=model.radar_id,
        definition_payload=dict(model.definition_json),
        definition_version=model.definition_version,
        is_active=model.is_active,
        created_at=aware_utc(model.created_at),
        updated_at=aware_utc(model.updated_at),
    )


def run_record(model: RadarRunModel) -> RadarRunRecord:
    return RadarRunRecord(
        run_id=model.run_id,
        radar_id=model.radar_id,
        pipeline_id=model.pipeline_id,
        source_run_id=model.source_run_id,
        status=RadarRunStatus(model.status),
        queued_at=aware_utc(model.queued_at),
        started_at=aware_utc(model.started_at),
        completed_at=aware_utc(model.completed_at),
        idempotency_key=model.idempotency_key,
        correlation_id=model.correlation_id,
        error_message=model.error_message,
        error_metadata=dict(model.error_metadata_json),
        run_metadata=dict(model.run_metadata_json),
        created_at=aware_utc(model.created_at),
        updated_at=aware_utc(model.updated_at),
    )


def run_output_record(model: RadarRunOutputModel) -> RadarRunOutputRecord:
    return RadarRunOutputRecord(
        run_id=model.run_id,
        artifact_version=model.artifact_version,
        radar_payload=dict(model.radar_payload_json),
        search_plan_payload=dict(model.search_plan_json),
        sources_payload=[dict(item) for item in model.sources_json],
        candidates_payload=[dict(item) for item in model.candidates_json],
        contract_validation_payload=[dict(item) for item in model.contract_validation_json],
        artifact_payload=dict(model.artifact_payload_json),
        created_at=aware_utc(model.created_at),
        updated_at=aware_utc(model.updated_at),
    )


def signal_monitoring_output_record(model: SignalMonitoringRunOutputModel) -> SignalMonitoringRunOutputRecord:
    return SignalMonitoringRunOutputRecord(
        run_id=model.run_id,
        source_run_id=model.source_run_id,
        artifact_version=model.artifact_version,
        input_snapshot_payload=dict(model.input_snapshot_json),
        plan_payload=dict(model.plan_json),
        observations_payload=[dict(item) for item in model.observations_json],
        artifact_payload=dict(model.artifact_payload_json),
        created_at=aware_utc(model.created_at),
        updated_at=aware_utc(model.updated_at),
    )


def review_decision_record(model: RadarReviewDecisionModel) -> RadarReviewDecisionRecord:
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
        reviewed_at=aware_utc(model.reviewed_at),
        created_at=aware_utc(model.created_at),
        updated_at=aware_utc(model.updated_at),
    )


def run_event_record(model: RadarRunEventModel) -> RadarRunEventRecord:
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
        created_at=aware_utc(model.created_at),
    )


def technical_trace_record(model: RadarRunTechnicalTraceModel) -> RadarRunTechnicalTraceRecord:
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
        created_at=aware_utc(model.created_at),
    )


def aware_utc(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)
