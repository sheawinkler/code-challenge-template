"""partition raw weather records by year and station (postgres only)

Revision ID: 0004_postgres_partition_raw
Revises: 0003_allow_raw_duplicates
Create Date: 2026-01-20

"""

from __future__ import annotations

from alembic import op

revision = "0004_postgres_partition_raw"
down_revision = "0003_allow_raw_duplicates"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return

    op.execute("ALTER TABLE weather_records_raw RENAME TO weather_records_raw_old")

    op.execute("""
        CREATE TABLE weather_records_raw (
          id SERIAL PRIMARY KEY,
          station_id TEXT NOT NULL REFERENCES weather_stations(station_id),
          date DATE NOT NULL,
          max_temp_tenths_c INTEGER,
          min_temp_tenths_c INTEGER,
          precip_tenths_mm INTEGER,
          source_file TEXT NOT NULL,
          source_line INTEGER NOT NULL,
          ingested_at TIMESTAMP NOT NULL,
          ingestion_run_id INTEGER NOT NULL REFERENCES ingestion_runs(id)
        ) PARTITION BY RANGE (date);
        """)

    for year in range(1985, 2016):
        op.execute(f"""
            CREATE TABLE weather_records_raw_{year} PARTITION OF weather_records_raw
            FOR VALUES FROM ('{year}-01-01') TO ('{year + 1}-01-01')
            PARTITION BY HASH (station_id);
            """)
        for remainder in range(4):
            op.execute(f"""
                CREATE TABLE weather_records_raw_{year}_p{remainder}
                PARTITION OF weather_records_raw_{year}
                FOR VALUES WITH (MODULUS 4, REMAINDER {remainder});
                """)

    op.execute("CREATE INDEX ix_weather_raw_station_date ON weather_records_raw (station_id, date)")
    op.execute("CREATE INDEX ix_weather_raw_run ON weather_records_raw (ingestion_run_id)")

    op.execute("INSERT INTO weather_records_raw SELECT * FROM weather_records_raw_old")
    op.execute("DROP TABLE weather_records_raw_old")


def downgrade() -> None:
    if not _is_postgres():
        return

    op.execute("ALTER TABLE weather_records_raw RENAME TO weather_records_raw_part")
    op.execute("""
        CREATE TABLE weather_records_raw (
          id SERIAL PRIMARY KEY,
          station_id TEXT NOT NULL REFERENCES weather_stations(station_id),
          date DATE NOT NULL,
          max_temp_tenths_c INTEGER,
          min_temp_tenths_c INTEGER,
          precip_tenths_mm INTEGER,
          source_file TEXT NOT NULL,
          source_line INTEGER NOT NULL,
          ingested_at TIMESTAMP NOT NULL,
          ingestion_run_id INTEGER NOT NULL REFERENCES ingestion_runs(id)
        );
        """)
    op.execute("CREATE INDEX ix_weather_raw_station_date ON weather_records_raw (station_id, date)")
    op.execute("CREATE INDEX ix_weather_raw_run ON weather_records_raw (ingestion_run_id)")
    op.execute("INSERT INTO weather_records_raw SELECT * FROM weather_records_raw_part")
    op.execute("DROP TABLE weather_records_raw_part")
