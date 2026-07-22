"""add lightweight Radar run display metadata projection

Revision ID: 202607220725
Revises: 202607220724
Create Date: 2026-07-22 13:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "202607220725"
down_revision = "202607220724"
branch_labels = None
depends_on = None


_DISPLAY_COLUMNS = (
    ("display_execution_mode", 80),
    ("display_requester", 160),
    ("display_run_profile", 120),
    ("display_benchmark_profile", 120),
    ("display_benchmark_mode", 80),
    ("display_signal_execution_mode", 80),
)


def upgrade() -> None:
    for name, length in _DISPLAY_COLUMNS:
        op.add_column("radar_runs", sa.Column(name, sa.String(length), nullable=False, server_default=""))

    runs = sa.table(
        "radar_runs",
        sa.column("run_id", sa.String()),
        sa.column("run_metadata_json", sa.JSON()),
        *(sa.column(name, sa.String(length)) for name, length in _DISPLAY_COLUMNS),
    )
    connection = op.get_bind()
    for row in connection.execute(sa.select(runs.c.run_id, runs.c.run_metadata_json)):
        metadata = row.run_metadata_json if isinstance(row.run_metadata_json, dict) else {}
        context_value = metadata.get("task_context")
        context = context_value if isinstance(context_value, dict) else {}
        connection.execute(
            runs.update().where(runs.c.run_id == row.run_id).values(
                display_execution_mode=str(metadata.get("execution_mode") or ""),
                display_requester=str(metadata.get("requester") or ""),
                display_run_profile=str(context.get("run_profile") or metadata.get("run_profile") or ""),
                display_benchmark_profile=str(context.get("benchmark_profile") or ""),
                display_benchmark_mode=str(context.get("benchmark_mode") or metadata.get("benchmark_mode") or ""),
                display_signal_execution_mode=str(context.get("signal_execution_mode") or ""),
            )
        )

    op.drop_index("ix_radar_runs_summary_covering", table_name="radar_runs")
    op.create_index(
        "ix_radar_runs_summary_covering",
        "radar_runs",
        [
            "pipeline_id", "status", "radar_id", "queued_at", "run_id", "source_run_id",
            "started_at", "completed_at", "idempotency_key", "correlation_id", "error_message",
            *[name for name, _ in _DISPLAY_COLUMNS], "created_at", "updated_at",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_radar_runs_summary_covering", table_name="radar_runs")
    for name, _ in reversed(_DISPLAY_COLUMNS):
        op.drop_column("radar_runs", name)
    op.create_index(
        "ix_radar_runs_summary_covering",
        "radar_runs",
        [
            "pipeline_id", "status", "radar_id", "queued_at", "run_id", "source_run_id",
            "started_at", "completed_at", "idempotency_key", "correlation_id", "error_message",
            "created_at", "updated_at",
        ],
        unique=False,
    )
