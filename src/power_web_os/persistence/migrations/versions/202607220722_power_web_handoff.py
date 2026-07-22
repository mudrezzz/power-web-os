"""add immutable Radar Power Web policy and handoff records

Revision ID: 202607220722
Revises: 202607210721
Create Date: 2026-07-22 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "202607220722"
down_revision = "202607210721"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "radar_power_web_policy_versions",
        sa.Column("policy_version_id", sa.String(180), primary_key=True),
        sa.Column("radar_id", sa.String(120), sa.ForeignKey("radars.radar_id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("radar_id", "version_number", name="uq_radar_power_web_policy_version"),
    )
    op.create_index("ix_radar_power_web_policy_versions_radar_id", "radar_power_web_policy_versions", ["radar_id"])
    op.create_table(
        "radar_power_web_policy_product_bindings",
        sa.Column("policy_version_id", sa.String(180), sa.ForeignKey("radar_power_web_policy_versions.policy_version_id"), primary_key=True),
        sa.Column("product_id", sa.String(160), sa.ForeignKey("products.product_id"), primary_key=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint("policy_version_id", "position", name="uq_radar_power_web_policy_position"),
    )
    op.create_table(
        "radar_power_web_policy_heads",
        sa.Column("radar_id", sa.String(120), sa.ForeignKey("radars.radar_id"), primary_key=True),
        sa.Column("active_policy_version_id", sa.String(180), sa.ForeignKey("radar_power_web_policy_versions.policy_version_id"), nullable=False, unique=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "power_web_handoffs",
        sa.Column("handoff_id", sa.String(180), primary_key=True),
        sa.Column("radar_id", sa.String(120), sa.ForeignKey("radars.radar_id"), nullable=False),
        sa.Column("policy_version_id", sa.String(180), sa.ForeignKey("radar_power_web_policy_versions.policy_version_id"), nullable=False),
        sa.Column("source_candidate_run_id", sa.String(160), sa.ForeignKey("radar_runs.run_id"), nullable=False),
        sa.Column("source_candidate_id", sa.String(200), nullable=False),
        sa.Column("source_signal_run_id", sa.String(160), sa.ForeignKey("radar_runs.run_id"), nullable=True),
        sa.Column("account_id", sa.String(200), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("request_fingerprint", sa.String(80), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_power_web_handoff_idempotency"),
    )
    op.create_index("ix_power_web_handoffs_radar_id", "power_web_handoffs", ["radar_id"])
    op.create_index("ix_power_web_handoffs_source_candidate_run_id", "power_web_handoffs", ["source_candidate_run_id"])
    op.create_index("ix_power_web_handoffs_source_candidate_id", "power_web_handoffs", ["source_candidate_id"])
    op.create_index("ix_power_web_handoffs_account_id", "power_web_handoffs", ["account_id"])


def downgrade() -> None:
    op.drop_table("power_web_handoffs")
    op.drop_table("radar_power_web_policy_heads")
    op.drop_table("radar_power_web_policy_product_bindings")
    op.drop_table("radar_power_web_policy_versions")
