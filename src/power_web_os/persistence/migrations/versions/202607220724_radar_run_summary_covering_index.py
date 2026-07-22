"""add covering index for lightweight Radar run summaries

Revision ID: 202607220724
Revises: 202607220723
Create Date: 2026-07-22 12:00:00
"""

from alembic import op


revision = "202607220724"
down_revision = "202607220723"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_radar_runs_summary_covering",
        "radar_runs",
        [
            "pipeline_id",
            "status",
            "radar_id",
            "queued_at",
            "run_id",
            "source_run_id",
            "started_at",
            "completed_at",
            "idempotency_key",
            "correlation_id",
            "error_message",
            "created_at",
            "updated_at",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_radar_runs_summary_covering", table_name="radar_runs")
