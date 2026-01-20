"""add raw ingestion and conflict logging

Revision ID: 0002_raw_and_conflicts
Revises: 0001_create_tables
Create Date: 2026-01-20

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002_raw_and_conflicts"
down_revision = "0001_create_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("weather_records", sa.Column("max_temp_raw_id", sa.Integer(), nullable=True))
    op.add_column("weather_records", sa.Column("min_temp_raw_id", sa.Integer(), nullable=True))
    op.add_column("weather_records", sa.Column("precip_raw_id", sa.Integer(), nullable=True))

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dataset", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inserted_raw_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("upserted_curated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conflicts_count", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "weather_records_raw",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("station_id", sa.String(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("max_temp_tenths_c", sa.Integer(), nullable=True),
        sa.Column("min_temp_tenths_c", sa.Integer(), nullable=True),
        sa.Column("precip_tenths_mm", sa.Integer(), nullable=True),
        sa.Column("source_file", sa.String(), nullable=False),
        sa.Column("source_line", sa.Integer(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(), nullable=False),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["station_id"], ["weather_stations.station_id"]),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"]),
        sa.UniqueConstraint("source_file", "source_line", name="uq_weather_raw_source_line"),
    )
    op.create_index("ix_weather_raw_station_date", "weather_records_raw", ["station_id", "date"])
    op.create_index("ix_weather_raw_run", "weather_records_raw", ["ingestion_run_id"])

    op.create_table(
        "weather_conflicts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.String(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("field", sa.String(), nullable=False),
        sa.Column("existing_value", sa.Integer(), nullable=True),
        sa.Column("incoming_value", sa.Integer(), nullable=True),
        sa.Column("existing_raw_id", sa.Integer(), nullable=True),
        sa.Column("incoming_raw_id", sa.Integer(), nullable=True),
        sa.Column("source_file", sa.String(), nullable=False),
        sa.Column("source_line", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"]),
    )


def downgrade() -> None:
    op.drop_table("weather_conflicts")
    op.drop_index("ix_weather_raw_run", table_name="weather_records_raw")
    op.drop_index("ix_weather_raw_station_date", table_name="weather_records_raw")
    op.drop_table("weather_records_raw")
    op.drop_table("ingestion_runs")

    op.drop_column("weather_records", "precip_raw_id")
    op.drop_column("weather_records", "min_temp_raw_id")
    op.drop_column("weather_records", "max_temp_raw_id")
