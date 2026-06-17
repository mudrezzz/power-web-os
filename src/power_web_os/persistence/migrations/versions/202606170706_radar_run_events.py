"""add radar run events

Revision ID: 202606170706
Revises: 202606170704
Create Date: 2026-06-17 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202606170706"
down_revision = "202606170704"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "radar_run_events",
        sa.Column("event_id", sa.String(length=220), nullable=False),
        sa.Column("run_id", sa.String(length=160), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("phase", sa.String(length=80), nullable=False),
        sa.Column("actor", sa.String(length=80), nullable=False),
        sa.Column("node_name", sa.String(length=160), nullable=False),
        sa.Column("visibility", sa.String(length=40), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("source_refs_json", sa.JSON(), nullable=False),
        sa.Column("candidate_refs_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("visibility in ('user', 'operator', 'debug')", name="ck_radar_run_events_visibility"),
        sa.ForeignKeyConstraint(["run_id"], ["radar_runs.run_id"]),
        sa.PrimaryKeyConstraint("event_id"),
        sa.UniqueConstraint("run_id", "sequence", name="uq_radar_run_events_run_sequence"),
    )
    op.create_index("ix_radar_run_events_run_id", "radar_run_events", ["run_id"])
    op.create_index("ix_radar_run_events_event_type", "radar_run_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_radar_run_events_event_type", table_name="radar_run_events")
    op.drop_index("ix_radar_run_events_run_id", table_name="radar_run_events")
    op.drop_table("radar_run_events")
