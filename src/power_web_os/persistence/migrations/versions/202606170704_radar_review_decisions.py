"""add radar review decisions

Revision ID: 202606170704
Revises: 202606160702
Create Date: 2026-06-17 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202606170704"
down_revision = "202606160702"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "radar_review_decisions",
        sa.Column("decision_id", sa.String(length=360), nullable=False),
        sa.Column("run_id", sa.String(length=160), nullable=False),
        sa.Column("radar_id", sa.String(length=120), nullable=False),
        sa.Column("candidate_id", sa.String(length=160), nullable=False),
        sa.Column("subject_type", sa.String(length=40), nullable=False),
        sa.Column("subject_id", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("reviewer", sa.String(length=160), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("decision_payload_json", sa.JSON(), nullable=False),
        sa.Column("score_impact_json", sa.JSON(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("subject_type in ('qualification', 'signal')", name="ck_radar_review_subject_type"),
        sa.ForeignKeyConstraint(["run_id"], ["radar_runs.run_id"]),
        sa.PrimaryKeyConstraint("decision_id"),
        sa.UniqueConstraint(
            "run_id",
            "candidate_id",
            "subject_type",
            "subject_id",
            name="uq_radar_review_decision_subject",
        ),
    )
    op.create_index("ix_radar_review_decisions_run_id", "radar_review_decisions", ["run_id"])
    op.create_index("ix_radar_review_decisions_radar_id", "radar_review_decisions", ["radar_id"])
    op.create_index("ix_radar_review_decisions_candidate_id", "radar_review_decisions", ["candidate_id"])


def downgrade() -> None:
    op.drop_index("ix_radar_review_decisions_candidate_id", table_name="radar_review_decisions")
    op.drop_index("ix_radar_review_decisions_radar_id", table_name="radar_review_decisions")
    op.drop_index("ix_radar_review_decisions_run_id", table_name="radar_review_decisions")
    op.drop_table("radar_review_decisions")
