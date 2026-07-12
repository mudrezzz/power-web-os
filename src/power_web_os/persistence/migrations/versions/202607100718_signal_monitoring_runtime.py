"""add standalone signal monitoring runtime persistence

Revision ID: 202607100718
Revises: 202606180707
Create Date: 2026-07-10 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202607100718"
down_revision = "202606180707"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("radar_runs") as batch:
        batch.add_column(sa.Column("pipeline_id", sa.String(length=60), nullable=False, server_default="candidate_discovery"))
        batch.add_column(sa.Column("source_run_id", sa.String(length=160), nullable=True))
        batch.create_check_constraint(
            "ck_radar_runs_pipeline_id",
            "pipeline_id in ('candidate_discovery', 'signal_monitoring')",
        )
        batch.create_foreign_key("fk_radar_runs_source_run_id", "radar_runs", ["source_run_id"], ["run_id"])
        batch.create_index("ix_radar_runs_pipeline_id", ["pipeline_id"])
        batch.create_index("ix_radar_runs_source_run_id", ["source_run_id"])

    op.create_table(
        "radar_signal_monitoring_outputs",
        sa.Column("run_id", sa.String(length=160), nullable=False),
        sa.Column("source_run_id", sa.String(length=160), nullable=False),
        sa.Column("artifact_version", sa.String(length=80), nullable=False),
        sa.Column("input_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("plan_json", sa.JSON(), nullable=False),
        sa.Column("observations_json", sa.JSON(), nullable=False),
        sa.Column("artifact_payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["radar_runs.run_id"]),
        sa.ForeignKeyConstraint(["source_run_id"], ["radar_runs.run_id"]),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_index(
        "ix_radar_signal_monitoring_outputs_source_run_id",
        "radar_signal_monitoring_outputs",
        ["source_run_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_radar_signal_monitoring_outputs_source_run_id",
        table_name="radar_signal_monitoring_outputs",
    )
    op.drop_table("radar_signal_monitoring_outputs")
    with op.batch_alter_table("radar_runs") as batch:
        batch.drop_index("ix_radar_runs_source_run_id")
        batch.drop_index("ix_radar_runs_pipeline_id")
        batch.drop_constraint("fk_radar_runs_source_run_id", type_="foreignkey")
        batch.drop_constraint("ck_radar_runs_pipeline_id", type_="check")
        batch.drop_column("source_run_id")
        batch.drop_column("pipeline_id")
