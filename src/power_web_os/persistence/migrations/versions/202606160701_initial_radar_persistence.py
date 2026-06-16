"""initial radar persistence

Revision ID: 202606160701
Revises:
Create Date: 2026-06-16 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202606160701"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "radars",
        sa.Column("radar_id", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("owner", sa.String(length=160), nullable=False),
        sa.Column("profile_json", sa.JSON(), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("artifact_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("radar_id"),
    )
    op.create_table(
        "radar_definitions",
        sa.Column("definition_id", sa.String(length=160), nullable=False),
        sa.Column("radar_id", sa.String(length=120), nullable=False),
        sa.Column("definition_version", sa.String(length=80), nullable=False),
        sa.Column("definition_json", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["radar_id"], ["radars.radar_id"]),
        sa.PrimaryKeyConstraint("definition_id"),
    )
    op.create_index(op.f("ix_radar_definitions_radar_id"), "radar_definitions", ["radar_id"])
    op.create_table(
        "radar_runs",
        sa.Column("run_id", sa.String(length=160), nullable=False),
        sa.Column("radar_id", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=200), nullable=True),
        sa.Column("correlation_id", sa.String(length=200), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_metadata_json", sa.JSON(), nullable=False),
        sa.Column("run_metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status in ('queued', 'running', 'waiting_human', 'completed', 'failed', 'cancelled')",
            name="ck_radar_runs_status",
        ),
        sa.ForeignKeyConstraint(["radar_id"], ["radars.radar_id"]),
        sa.PrimaryKeyConstraint("run_id"),
        sa.UniqueConstraint("idempotency_key", name="uq_radar_runs_idempotency_key"),
    )
    op.create_index(op.f("ix_radar_runs_correlation_id"), "radar_runs", ["correlation_id"])
    op.create_index(op.f("ix_radar_runs_radar_id"), "radar_runs", ["radar_id"])
    op.create_index(op.f("ix_radar_runs_status"), "radar_runs", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_radar_runs_status"), table_name="radar_runs")
    op.drop_index(op.f("ix_radar_runs_radar_id"), table_name="radar_runs")
    op.drop_index(op.f("ix_radar_runs_correlation_id"), table_name="radar_runs")
    op.drop_table("radar_runs")
    op.drop_index(op.f("ix_radar_definitions_radar_id"), table_name="radar_definitions")
    op.drop_table("radar_definitions")
    op.drop_table("radars")
