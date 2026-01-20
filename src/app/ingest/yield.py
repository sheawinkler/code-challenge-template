from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app import db
from app.models import CropYield


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


def _insert_ignore(session, rows) -> int:
    if not rows:
        return 0
    if db.engine.dialect.name == "sqlite":
        stmt = sqlite_insert(CropYield.__table__).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["year"])
    elif db.engine.dialect.name == "postgresql":
        stmt = pg_insert(CropYield.__table__).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["year"])
    else:
        stmt = CropYield.__table__.insert().values(rows)
    result = session.execute(stmt)
    return _rowcount(result)


def ingest_yield(file_path: Path) -> dict[str, int]:
    if not file_path.exists():
        raise FileNotFoundError(f"Yield data file not found: {file_path}")

    session = db.SessionLocal()
    try:
        start = datetime.now(timezone.utc)
        logging.info("Yield ingestion started at %s", start.isoformat())

        total_processed = 0
        total_inserted = 0
        rows = []

        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                parts = line.strip().split()
                if len(parts) != 2:
                    continue
                year_raw, yield_raw = parts
                rows.append({"year": int(year_raw), "yield_value": int(yield_raw)})
                total_processed += 1

        total_inserted += _insert_ignore(session, rows)
        session.commit()

        end = datetime.now(timezone.utc)
        logging.info("Yield ingestion finished at %s", end.isoformat())
        logging.info("Yield records processed: %s", total_processed)
        logging.info("Yield records inserted: %s", total_inserted)

        return {"processed": total_processed, "inserted": total_inserted}
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Ingest crop yield data.")
    parser.add_argument(
        "--file",
        default="yld_data/US_corn_grain_yield.txt",
        help="Path to crop yield data file",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ingest_yield(Path(args.file))


if __name__ == "__main__":
    main()
