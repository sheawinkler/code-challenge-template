"""add ingestion events table

Revision ID: 0005_ingestion_events
Revises: 0004_postgres_partition_raw
Create Date: 2026-01-20

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0005_ingestion_events"
down_revision = "0004_postgres_partition_raw"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"]),
    )
    op.create_index("ix_ingestion_events_run", "ingestion_events", ["ingestion_run_id"])


def downgrade() -> None:
    op.drop_index("ix_ingestion_events_run", table_name="ingestion_events")
    op.drop_table("ingestion_events")
