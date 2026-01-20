"""create initial tables

Revision ID: 0001_create_tables
Revises: 
Create Date: 2026-01-20

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_create_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weather_stations",
        sa.Column("station_id", sa.String(), primary_key=True),
    )

    op.create_table(
        "weather_records",
        sa.Column("station_id", sa.String(), sa.ForeignKey("weather_stations.station_id"), primary_key=True),
        sa.Column("date", sa.Date(), primary_key=True),
        sa.Column("max_temp_tenths_c", sa.Integer(), nullable=True),
        sa.Column("min_temp_tenths_c", sa.Integer(), nullable=True),
        sa.Column("precip_tenths_mm", sa.Integer(), nullable=True),
    )
    op.create_index("ix_weather_records_date", "weather_records", ["date"])
    op.create_index(
        "ix_weather_records_station_date", "weather_records", ["station_id", "date"]
    )

    op.create_table(
        "weather_stats",
        sa.Column("station_id", sa.String(), sa.ForeignKey("weather_stations.station_id"), primary_key=True),
        sa.Column("year", sa.Integer(), primary_key=True),
        sa.Column("avg_max_temp_c", sa.Float(), nullable=True),
        sa.Column("avg_min_temp_c", sa.Float(), nullable=True),
        sa.Column("total_precip_cm", sa.Float(), nullable=True),
    )
    op.create_index("ix_weather_stats_station_year", "weather_stats", ["station_id", "year"])

    op.create_table(
        "crop_yield",
        sa.Column("year", sa.Integer(), primary_key=True),
        sa.Column("yield_value", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("crop_yield")
    op.drop_index("ix_weather_stats_station_year", table_name="weather_stats")
    op.drop_table("weather_stats")
    op.drop_index("ix_weather_records_station_date", table_name="weather_records")
    op.drop_index("ix_weather_records_date", table_name="weather_records")
    op.drop_table("weather_records")
    op.drop_table("weather_stations")
