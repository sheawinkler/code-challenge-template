from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import case, func, literal, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app import db
from app.models import (
    IngestionRun,
    IngestionEvent,
    WeatherConflict,
    WeatherRecord,
    WeatherRecordRaw,
    WeatherStation,
)

MISSING_VALUE = -9999


def _rowcount(result) -> int:
    if result is None:
        return 0
    try:
        count = result.rowcount
    except Exception:
        return 0
    if count is None or count < 0:
        return 0
    return count


def _insert_ignore(session, table, rows, conflict_cols=None) -> int:
    if not rows:
        return 0
    if conflict_cols:
        if db.engine.dialect.name == "sqlite":
            stmt = sqlite_insert(table).values(rows)
            stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)
        elif db.engine.dialect.name == "postgresql":
            stmt = pg_insert(table).values(rows)
            stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)
        else:
            stmt = table.insert().values(rows)
    else:
        stmt = table.insert().values(rows)
    result = session.execute(stmt)
    return _rowcount(result)


def _parse_value(raw: str) -> int | None:
    value = int(raw)
    if value == MISSING_VALUE:
        return None
    return value


def _parse_line(line: str):
    parts = line.strip().split()
    if len(parts) != 4:
        return None
    date_raw, max_raw, min_raw, precip_raw = parts
    date = datetime.strptime(date_raw, "%Y%m%d").date()
    return {
        "date": date,
        "max_temp_tenths_c": _parse_value(max_raw),
        "min_temp_tenths_c": _parse_value(min_raw),
        "precip_tenths_mm": _parse_value(precip_raw),
    }


def _log_conflicts(session, run_id: int, created_at: datetime) -> int:
    fields = [
        ("max_temp_tenths_c", WeatherRecord.max_temp_tenths_c, WeatherRecord.max_temp_raw_id),
        ("min_temp_tenths_c", WeatherRecord.min_temp_tenths_c, WeatherRecord.min_temp_raw_id),
        ("precip_tenths_mm", WeatherRecord.precip_tenths_mm, WeatherRecord.precip_raw_id),
    ]

    total_conflicts = 0
    for field_name, curated_value_col, curated_raw_id_col in fields:
        raw_value_col = getattr(WeatherRecordRaw, field_name)

        conflict_select = (
            select(
                literal(run_id),
                WeatherRecordRaw.station_id,
                WeatherRecordRaw.date,
                literal(field_name),
                curated_value_col,
                raw_value_col,
                curated_raw_id_col,
                WeatherRecordRaw.id,
                WeatherRecordRaw.source_file,
                WeatherRecordRaw.source_line,
                literal(created_at),
            )
            .select_from(WeatherRecordRaw)
            .join(
                WeatherRecord,
                (WeatherRecord.station_id == WeatherRecordRaw.station_id)
                & (WeatherRecord.date == WeatherRecordRaw.date),
            )
            .where(
                WeatherRecordRaw.ingestion_run_id == run_id,
                raw_value_col.is_not(None),
                curated_value_col.is_not(None),
                raw_value_col != curated_value_col,
            )
        )

        insert_stmt = WeatherConflict.__table__.insert().from_select(
            [
                "ingestion_run_id",
                "station_id",
                "date",
                "field",
                "existing_value",
                "incoming_value",
                "existing_raw_id",
                "incoming_raw_id",
                "source_file",
                "source_line",
                "created_at",
            ],
            conflict_select,
        )
        result = session.execute(insert_stmt)
        total_conflicts += _rowcount(result)

    return total_conflicts


def _log_event(session, run_id: int, level: str, message: str, created_at: datetime) -> None:
    session.add(
        IngestionEvent(
            ingestion_run_id=run_id,
            level=level,
            message=message,
            created_at=created_at,
        )
    )


def ingest_weather(data_dir: Path, batch_size: int = 10000) -> dict[str, int]:
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    session = db.SessionLocal()
    try:
        run_started_at = datetime.now(timezone.utc)
        run = IngestionRun(dataset="weather", started_at=run_started_at)
        session.add(run)
        session.commit()
        session.refresh(run)

        if db.engine.dialect.name == "sqlite":
            max_sqlite_vars = 999
            columns_per_row = 9
            max_rows = max_sqlite_vars // columns_per_row
            batch_size = min(batch_size, max_rows if max_rows > 0 else 1)

        start = datetime.now(timezone.utc)
        logging.info("Weather ingestion started at %s", start.isoformat())
        _log_event(session, run.id, "INFO", "weather ingestion started", start)
        session.commit()

        total_processed = 0
        total_inserted = 0
        batch = []

        for file_path in sorted(data_dir.glob("*.txt")):
            station_id = file_path.stem
            _insert_ignore(
                session,
                WeatherStation.__table__,
                [{"station_id": station_id}],
                ["station_id"],
            )

            with file_path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    parsed = _parse_line(line)
                    if not parsed:
                        continue
                    batch.append(
                        {
                            "station_id": station_id,
                            "date": parsed["date"],
                            "max_temp_tenths_c": parsed["max_temp_tenths_c"],
                            "min_temp_tenths_c": parsed["min_temp_tenths_c"],
                            "precip_tenths_mm": parsed["precip_tenths_mm"],
                            "source_file": str(file_path),
                            "source_line": line_number,
                            "ingested_at": run_started_at,
                            "ingestion_run_id": run.id,
                        }
                    )
                    total_processed += 1

                    if len(batch) >= batch_size:
                        total_inserted += _insert_ignore(
                            session,
                            WeatherRecordRaw.__table__,
                            batch,
                        )
                        session.commit()
                        batch.clear()

        if batch:
            total_inserted += _insert_ignore(
                session,
                WeatherRecordRaw.__table__,
                batch,
            )
            session.commit()

        raw_select = select(
            WeatherRecordRaw.station_id,
            WeatherRecordRaw.date,
            WeatherRecordRaw.max_temp_tenths_c,
            WeatherRecordRaw.min_temp_tenths_c,
            WeatherRecordRaw.precip_tenths_mm,
            case(
                (WeatherRecordRaw.max_temp_tenths_c.is_not(None), WeatherRecordRaw.id),
                else_=None,
            ).label("max_temp_raw_id"),
            case(
                (WeatherRecordRaw.min_temp_tenths_c.is_not(None), WeatherRecordRaw.id),
                else_=None,
            ).label("min_temp_raw_id"),
            case(
                (WeatherRecordRaw.precip_tenths_mm.is_not(None), WeatherRecordRaw.id),
                else_=None,
            ).label("precip_raw_id"),
        ).where(WeatherRecordRaw.ingestion_run_id == run.id)

        if db.engine.dialect.name == "sqlite":
            insert_stmt = sqlite_insert(WeatherRecord.__table__).from_select(
                [
                    "station_id",
                    "date",
                    "max_temp_tenths_c",
                    "min_temp_tenths_c",
                    "precip_tenths_mm",
                    "max_temp_raw_id",
                    "min_temp_raw_id",
                    "precip_raw_id",
                ],
                raw_select,
            )
        else:
            insert_stmt = pg_insert(WeatherRecord.__table__).from_select(
                [
                    "station_id",
                    "date",
                    "max_temp_tenths_c",
                    "min_temp_tenths_c",
                    "precip_tenths_mm",
                    "max_temp_raw_id",
                    "min_temp_raw_id",
                    "precip_raw_id",
                ],
                raw_select,
            )

        excluded = insert_stmt.excluded
        update_stmt = insert_stmt.on_conflict_do_update(
            index_elements=["station_id", "date"],
            set_={
                "max_temp_tenths_c": case(
                    (
                        excluded.max_temp_tenths_c.is_not(None)
                        & (
                            WeatherRecord.max_temp_tenths_c.is_(None)
                            | (
                                excluded.max_temp_raw_id
                                > func.coalesce(WeatherRecord.max_temp_raw_id, 0)
                            )
                        ),
                        excluded.max_temp_tenths_c,
                    ),
                    else_=WeatherRecord.max_temp_tenths_c,
                ),
                "max_temp_raw_id": case(
                    (
                        excluded.max_temp_tenths_c.is_not(None)
                        & (
                            WeatherRecord.max_temp_tenths_c.is_(None)
                            | (
                                excluded.max_temp_raw_id
                                > func.coalesce(WeatherRecord.max_temp_raw_id, 0)
                            )
                        ),
                        excluded.max_temp_raw_id,
                    ),
                    else_=WeatherRecord.max_temp_raw_id,
                ),
                "min_temp_tenths_c": case(
                    (
                        excluded.min_temp_tenths_c.is_not(None)
                        & (
                            WeatherRecord.min_temp_tenths_c.is_(None)
                            | (
                                excluded.min_temp_raw_id
                                > func.coalesce(WeatherRecord.min_temp_raw_id, 0)
                            )
                        ),
                        excluded.min_temp_tenths_c,
                    ),
                    else_=WeatherRecord.min_temp_tenths_c,
                ),
                "min_temp_raw_id": case(
                    (
                        excluded.min_temp_tenths_c.is_not(None)
                        & (
                            WeatherRecord.min_temp_tenths_c.is_(None)
                            | (
                                excluded.min_temp_raw_id
                                > func.coalesce(WeatherRecord.min_temp_raw_id, 0)
                            )
                        ),
                        excluded.min_temp_raw_id,
                    ),
                    else_=WeatherRecord.min_temp_raw_id,
                ),
                "precip_tenths_mm": case(
                    (
                        excluded.precip_tenths_mm.is_not(None)
                        & (
                            WeatherRecord.precip_tenths_mm.is_(None)
                            | (
                                excluded.precip_raw_id
                                > func.coalesce(WeatherRecord.precip_raw_id, 0)
                            )
                        ),
                        excluded.precip_tenths_mm,
                    ),
                    else_=WeatherRecord.precip_tenths_mm,
                ),
                "precip_raw_id": case(
                    (
                        excluded.precip_tenths_mm.is_not(None)
                        & (
                            WeatherRecord.precip_tenths_mm.is_(None)
                            | (
                                excluded.precip_raw_id
                                > func.coalesce(WeatherRecord.precip_raw_id, 0)
                            )
                        ),
                        excluded.precip_raw_id,
                    ),
                    else_=WeatherRecord.precip_raw_id,
                ),
            },
        )
        session.execute(update_stmt)
        session.commit()
        _log_event(
            session,
            run.id,
            "INFO",
            f"curated upsert completed for run {run.id}",
            datetime.now(timezone.utc),
        )
        session.commit()

        conflict_created_at = datetime.now(timezone.utc)
        conflicts_logged = _log_conflicts(session, run.id, conflict_created_at)
        _log_event(
            session,
            run.id,
            "INFO",
            f"conflicts logged: {conflicts_logged}",
            conflict_created_at,
        )
        session.commit()

        distinct_pairs = (
            select(WeatherRecordRaw.station_id, WeatherRecordRaw.date)
            .where(WeatherRecordRaw.ingestion_run_id == run.id)
            .distinct()
            .subquery()
        )
        upserted_curated = session.execute(select(func.count()).select_from(distinct_pairs)).scalar_one()

        end = datetime.now(timezone.utc)
        logging.info("Weather ingestion finished at %s", end.isoformat())
        logging.info("Weather records processed: %s", total_processed)
        logging.info("Weather raw records inserted: %s", total_inserted)
        logging.info("Weather conflicts logged: %s", conflicts_logged)
        logging.info("Weather curated rows upserted: %s", upserted_curated)

        _log_event(
            session,
            run.id,
            "INFO",
            f"processed={total_processed} raw_inserted={total_inserted} curated_upserted={upserted_curated}",
            end,
        )

        run.finished_at = end
        run.processed_count = total_processed
        run.inserted_raw_count = total_inserted
        run.conflicts_count = conflicts_logged
        run.upserted_curated_count = upserted_curated
        session.commit()

        return {
            "processed": total_processed,
            "inserted": total_inserted,
            "conflicts": conflicts_logged,
            "curated_upserted": upserted_curated,
        }
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Ingest weather data files.")
    parser.add_argument("--data-dir", default="wx_data", help="Directory with weather data files")
    parser.add_argument("--batch-size", type=int, default=10000, help="Batch size for inserts")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ingest_weather(Path(args.data_dir), batch_size=args.batch_size)


if __name__ == "__main__":
    main()
