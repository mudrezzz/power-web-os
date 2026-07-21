"""add versioned product and sales playbook configuration

Revision ID: 202607190720
Revises: 202607120719
Create Date: 2026-07-19 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202607190720"
down_revision = "202607120719"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("product_id", sa.String(160), primary_key=True),
        sa.Column("product_code", sa.String(80), nullable=False),
        sa.Column("lifecycle", sa.String(40), nullable=False, server_default="draft"),
        sa.Column("active_version_id", sa.String(180), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("lifecycle in ('draft', 'active', 'archived')", name="ck_products_lifecycle"),
        sa.UniqueConstraint("product_code", name="uq_products_product_code"),
    )
    op.create_index("ix_products_lifecycle", "products", ["lifecycle"])
    op.create_table(
        "sales_playbook_drafts",
        sa.Column("product_id", sa.String(160), sa.ForeignKey("products.product_id"), primary_key=True),
        sa.Column("draft_revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("base_version_id", sa.String(180), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("updated_by", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for table, payload_type in (
        ("product_definition_versions", sa.JSON()),
        ("buying_role_policy_versions", sa.JSON()),
        ("access_playbook_versions", sa.JSON()),
    ):
        op.create_table(
            table,
            sa.Column("version_id", sa.String(180), primary_key=True),
            sa.Column("product_id", sa.String(160), sa.ForeignKey("products.product_id"), nullable=False),
            sa.Column("version_number", sa.Integer(), nullable=False),
            sa.Column("payload_json", payload_type, nullable=False),
            sa.Column("published_by", sa.String(160), nullable=False),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(f"ix_{table}_product_id", table, ["product_id"])
    op.create_table(
        "sales_playbook_definition_versions",
        sa.Column("version_id", sa.String(180), primary_key=True),
        sa.Column("product_id", sa.String(160), sa.ForeignKey("products.product_id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("product_definition_version_id", sa.String(180), sa.ForeignKey("product_definition_versions.version_id"), nullable=False),
        sa.Column("buying_role_policy_version_id", sa.String(180), sa.ForeignKey("buying_role_policy_versions.version_id"), nullable=False),
        sa.Column("access_playbook_version_id", sa.String(180), sa.ForeignKey("access_playbook_versions.version_id"), nullable=False),
        sa.Column("published_by", sa.String(160), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("product_id", "version_number", name="uq_sales_playbook_product_version"),
    )
    op.create_index("ix_sales_playbook_definition_versions_product_id", "sales_playbook_definition_versions", ["product_id"])


def downgrade() -> None:
    op.drop_table("sales_playbook_definition_versions")
    op.drop_table("access_playbook_versions")
    op.drop_table("buying_role_policy_versions")
    op.drop_table("product_definition_versions")
    op.drop_table("sales_playbook_drafts")
    op.drop_table("products")
