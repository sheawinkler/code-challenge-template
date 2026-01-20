"""add row hash to raw weather records

Revision ID: 0006_raw_row_hash
Revises: 0005_ingestion_events
Create Date: 2026-01-20

"""

from __future__ import annotations

import hashlib

import sqlalchemy as sa

from alembic import op

revision = "0006_raw_row_hash"
down_revision = "0005_ingestion_events"
branch_labels = None
depends_on = None


def _row_hash(row) -> str:
    def _value(value):
        return "NA" if value is None else str(value)

    date_value = row.date.isoformat() if hasattr(row.date, "isoformat") else str(row.date)
    payload = "|".join(
        [
            row.station_id,
            date_value,
            _value(row.max_temp_tenths_c),
            _value(row.min_temp_tenths_c),
            _value(row.precip_tenths_mm),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _backfill_hashes(conn) -> None:
    batch_size = 10000
    last_id = 0

    while True:
        rows = conn.execute(
            sa.text("""
                SELECT id, station_id, date, max_temp_tenths_c, min_temp_tenths_c, precip_tenths_mm
                FROM weather_records_raw
                WHERE id > :last_id
                ORDER BY id
                LIMIT :limit
                """),
            {"last_id": last_id, "limit": batch_size},
        ).fetchall()

        if not rows:
            break

        updates = []
        for row in rows:
            updates.append({"id": row.id, "row_hash": _row_hash(row)})
            last_id = row.id

        conn.execute(
            sa.text("UPDATE weather_records_raw SET row_hash = :row_hash WHERE id = :id"),
            updates,
        )


def _dedupe_by_hash(conn) -> None:
    conn.execute(sa.text("""
            DELETE FROM weather_records_raw
            WHERE id IN (
              SELECT id
              FROM (
                SELECT id,
                       ROW_NUMBER() OVER (PARTITION BY row_hash ORDER BY id) AS rn
                FROM weather_records_raw
              ) AS dedupe
              WHERE dedupe.rn > 1
            )
            """))


def upgrade() -> None:
    with op.batch_alter_table("weather_records_raw") as batch:
        batch.add_column(sa.Column("row_hash", sa.String(length=64), nullable=True))

    conn = op.get_bind()
    _backfill_hashes(conn)
    _dedupe_by_hash(conn)

    with op.batch_alter_table("weather_records_raw") as batch:
        batch.alter_column("row_hash", nullable=False)
        batch.create_unique_constraint("uq_weather_raw_row_hash", ["row_hash"])


def downgrade() -> None:
    with op.batch_alter_table("weather_records_raw") as batch:
        batch.drop_constraint("uq_weather_raw_row_hash", type_="unique")
        batch.drop_column("row_hash")
