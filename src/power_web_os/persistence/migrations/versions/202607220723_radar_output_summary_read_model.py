"""add lightweight Radar output summary read model

Revision ID: 202607220723
Revises: 202607220722
Create Date: 2026-07-22 09:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "202607220723"
down_revision = "202607220722"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "radar_run_output_summaries",
        sa.Column("run_id", sa.String(160), sa.ForeignKey("radar_runs.run_id"), primary_key=True),
        sa.Column("artifact_version", sa.String(80), nullable=False),
        sa.Column("source_count", sa.Integer(), nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("contract_issue_count", sa.Integer(), nullable=False),
        sa.Column("visible_candidate_count", sa.Integer(), nullable=False),
        sa.Column("accepted_candidate_count", sa.Integer(), nullable=False),
        sa.Column("review_needed_candidate_count", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(sa.text(
        "insert into radar_run_output_summaries "
        "(run_id, artifact_version, source_count, candidate_count, contract_issue_count, "
        "visible_candidate_count, accepted_candidate_count, review_needed_candidate_count, updated_at) "
        "select run_id, artifact_version, source_count, candidate_count, contract_issue_count, "
        "visible_candidate_count, accepted_candidate_count, review_needed_candidate_count, updated_at "
        "from radar_run_outputs"
    ))


def downgrade() -> None:
    op.drop_table("radar_run_output_summaries")
