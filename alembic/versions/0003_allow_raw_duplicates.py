"""allow duplicate raw rows across ingestion runs

Revision ID: 0003_allow_raw_duplicates
Revises: 0002_raw_and_conflicts
Create Date: 2026-01-20

"""
from __future__ import annotations

from alembic import op

revision = "0003_allow_raw_duplicates"
down_revision = "0002_raw_and_conflicts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("weather_records_raw") as batch_op:
        batch_op.drop_constraint("uq_weather_raw_source_line", type_="unique")


def downgrade() -> None:
    with op.batch_alter_table("weather_records_raw") as batch_op:
        batch_op.create_unique_constraint(
            "uq_weather_raw_source_line",
            ["source_file", "source_line"],
        )
