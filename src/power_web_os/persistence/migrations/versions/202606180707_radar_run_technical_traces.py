"""add radar run technical traces

Revision ID: 202606180707
Revises: 202606170706
Create Date: 2026-06-18 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202606180707"
down_revision = "202606170706"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "radar_run_technical_traces",
        sa.Column("trace_id", sa.String(length=220), nullable=False),
        sa.Column("run_id", sa.String(length=160), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("phase", sa.String(length=80), nullable=False),
        sa.Column("node_name", sa.String(length=160), nullable=False),
        sa.Column("trace_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("redaction_report_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "trace_type in ('pipeline_input', 'pipeline_output', 'provider_request', 'provider_response', 'provider_error', 'normalization_result', 'validation_result')",
            name="ck_radar_run_technical_traces_type",
        ),
        sa.ForeignKeyConstraint(["run_id"], ["radar_runs.run_id"]),
        sa.PrimaryKeyConstraint("trace_id"),
        sa.UniqueConstraint("run_id", "sequence", name="uq_radar_run_technical_traces_run_sequence"),
    )
    op.create_index("ix_radar_run_technical_traces_run_id", "radar_run_technical_traces", ["run_id"])
    op.create_index("ix_radar_run_technical_traces_trace_type", "radar_run_technical_traces", ["trace_type"])


def downgrade() -> None:
    op.drop_index("ix_radar_run_technical_traces_trace_type", table_name="radar_run_technical_traces")
    op.drop_index("ix_radar_run_technical_traces_run_id", table_name="radar_run_technical_traces")
    op.drop_table("radar_run_technical_traces")
