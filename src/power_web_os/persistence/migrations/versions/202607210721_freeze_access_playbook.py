"""freeze access playbook and make its composite reference optional

Revision ID: 202607210721
Revises: 202607190720
Create Date: 2026-07-21 00:00:00
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202607210721"
down_revision = "202607190720"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sales_playbook_definition_versions") as batch:
        batch.alter_column(
            "access_playbook_version_id",
            existing_type=sa.String(180),
            nullable=True,
        )


def downgrade() -> None:
    connection = op.get_bind()
    metadata = sa.MetaData()
    access_versions = sa.Table("access_playbook_versions", metadata, autoload_with=connection)
    definitions = sa.Table("sales_playbook_definition_versions", metadata, autoload_with=connection)
    empty_payload = {
        "route_rules": [],
        "blocked_channels": [],
        "available_assets": [],
        "required_review_for": [],
    }
    rows = connection.execute(
        sa.select(definitions.c.version_id, definitions.c.product_id, definitions.c.version_number)
        .where(definitions.c.access_playbook_version_id.is_(None))
    ).mappings()
    for row in rows:
        access_version_id = f"access-playbook-downgrade-{uuid4()}"
        connection.execute(access_versions.insert().values(
            version_id=access_version_id,
            product_id=row["product_id"],
            version_number=row["version_number"],
            payload_json=empty_payload,
            published_by="migration-downgrade",
            published_at=datetime.now(UTC),
        ))
        connection.execute(
            definitions.update()
            .where(definitions.c.version_id == row["version_id"])
            .values(access_playbook_version_id=access_version_id)
        )
    with op.batch_alter_table("sales_playbook_definition_versions") as batch:
        batch.alter_column(
            "access_playbook_version_id",
            existing_type=sa.String(180),
            nullable=False,
        )
