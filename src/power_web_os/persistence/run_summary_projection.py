"""Product-safe scalar projection for lightweight Radar run summaries."""

from __future__ import annotations

from power_web_os.application.radar.lifecycle.records import RadarRunRecord, RadarRunStatus


def summary_run_record(row: object) -> RadarRunRecord:
    task_context = {
        "run_profile": row.display_run_profile,
        "benchmark_profile": row.display_benchmark_profile,
        "benchmark_mode": row.display_benchmark_mode,
        "signal_execution_mode": row.display_signal_execution_mode,
    }
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
        run_metadata={
            "execution_mode": row.display_execution_mode,
            "requester": row.display_requester,
            "task_context": task_context,
        },
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def run_display_metadata(metadata: dict[str, object]) -> dict[str, str]:
    context_value = metadata.get("task_context")
    context = context_value if isinstance(context_value, dict) else {}
    return {
        "display_execution_mode": str(metadata.get("execution_mode") or ""),
        "display_requester": str(metadata.get("requester") or ""),
        "display_run_profile": str(context.get("run_profile") or metadata.get("run_profile") or ""),
        "display_benchmark_profile": str(context.get("benchmark_profile") or ""),
        "display_benchmark_mode": str(context.get("benchmark_mode") or metadata.get("benchmark_mode") or ""),
        "display_signal_execution_mode": str(context.get("signal_execution_mode") or ""),
    }
