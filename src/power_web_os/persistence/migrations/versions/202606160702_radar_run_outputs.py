"""add persisted live radar output snapshots

Revision ID: 202606160702
Revises: 202606160701
Create Date: 2026-06-16 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202606160702"
down_revision = "202606160701"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "radar_run_outputs",
        sa.Column("run_id", sa.String(length=160), nullable=False),
        sa.Column("artifact_version", sa.String(length=80), nullable=False),
        sa.Column("radar_payload_json", sa.JSON(), nullable=False),
        sa.Column("search_plan_json", sa.JSON(), nullable=False),
        sa.Column("sources_json", sa.JSON(), nullable=False),
        sa.Column("candidates_json", sa.JSON(), nullable=False),
        sa.Column("contract_validation_json", sa.JSON(), nullable=False),
        sa.Column("artifact_payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["radar_runs.run_id"]),
        sa.PrimaryKeyConstraint("run_id"),
    )


def downgrade() -> None:
    op.drop_table("radar_run_outputs")
