"""add scalar radar output summaries

Revision ID: 202607120719
Revises: 202607100718
Create Date: 2026-07-12 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202607120719"
down_revision = "202607100718"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("radar_run_outputs") as batch:
        batch.add_column(sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("candidate_count", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("contract_issue_count", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("visible_candidate_count", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("accepted_candidate_count", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("review_needed_candidate_count", sa.Integer(), nullable=False, server_default="0"))
    connection = op.get_bind()
    rows = connection.execute(sa.text(
        "select run_id, sources_json, candidates_json, contract_validation_json from radar_run_outputs"
    )).mappings()
    import json
    for row in rows:
        def items(value: object) -> list[dict[str, object]]:
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    return []
            return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

        def count(value: object) -> int:
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    return 0
            return len(value) if isinstance(value, list) else 0
        candidates = items(row["candidates_json"])
        accepted = sum(
            item.get("candidate_surface_status") == "accepted_product_candidate"
            or item.get("product_acceptance_status") == "product_candidate"
            for item in candidates
        )
        review = sum(
            item.get("candidate_surface_status") == "review_needed_candidate"
            or item.get("product_acceptance_status") == "review_required"
            for item in candidates
        )
        connection.execute(sa.text(
            "update radar_run_outputs set source_count=:s, candidate_count=:c, contract_issue_count=:i, "
            "visible_candidate_count=:c, accepted_candidate_count=:a, review_needed_candidate_count=:v where run_id=:r"
        ), {
            "s": count(row["sources_json"]),
            "c": len(candidates),
            "i": count(row["contract_validation_json"]),
            "a": accepted,
            "v": review,
            "r": row["run_id"],
        })


def downgrade() -> None:
    with op.batch_alter_table("radar_run_outputs") as batch:
        batch.drop_column("review_needed_candidate_count")
        batch.drop_column("accepted_candidate_count")
        batch.drop_column("visible_candidate_count")
        batch.drop_column("contract_issue_count")
        batch.drop_column("candidate_count")
        batch.drop_column("source_count")
