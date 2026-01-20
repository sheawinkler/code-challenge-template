from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app import db
from app.models import WeatherRecord, WeatherStats


def _year_expression():
    if db.engine.dialect.name == "sqlite":
        return cast(func.strftime("%Y", WeatherRecord.date), Integer)
    return cast(func.extract("year", WeatherRecord.date), Integer)


def _upsert_stats_from_select(session, aggregate_select):
    columns = ["station_id", "year", "avg_max_temp_c", "avg_min_temp_c", "total_precip_cm"]
    if db.engine.dialect.name == "sqlite":
        stmt = sqlite_insert(WeatherStats.__table__).from_select(columns, aggregate_select)
        stmt = stmt.on_conflict_do_update(
            index_elements=["station_id", "year"],
            set_={
                "avg_max_temp_c": stmt.excluded.avg_max_temp_c,
                "avg_min_temp_c": stmt.excluded.avg_min_temp_c,
                "total_precip_cm": stmt.excluded.total_precip_cm,
            },
        )
    elif db.engine.dialect.name == "postgresql":
        stmt = pg_insert(WeatherStats.__table__).from_select(columns, aggregate_select)
        stmt = stmt.on_conflict_do_update(
            index_elements=["station_id", "year"],
            set_={
                "avg_max_temp_c": stmt.excluded.avg_max_temp_c,
                "avg_min_temp_c": stmt.excluded.avg_min_temp_c,
                "total_precip_cm": stmt.excluded.total_precip_cm,
            },
        )
    else:
        stmt = WeatherStats.__table__.insert().from_select(columns, aggregate_select)
    session.execute(stmt)


def compute_weather_stats() -> dict[str, int]:
    session = db.SessionLocal()
    try:
        start = datetime.now(timezone.utc)
        logging.info("Weather stats computation started at %s", start.isoformat())

        year_expr = _year_expression().label("year")
        aggregate_stmt = (
            select(
                WeatherRecord.station_id.label("station_id"),
                year_expr,
                (func.avg(WeatherRecord.max_temp_tenths_c) / 10.0).label("avg_max_temp_c"),
                (func.avg(WeatherRecord.min_temp_tenths_c) / 10.0).label("avg_min_temp_c"),
                (func.sum(WeatherRecord.precip_tenths_mm) / 100.0).label("total_precip_cm"),
            )
            .group_by(WeatherRecord.station_id, year_expr)
            .order_by(WeatherRecord.station_id, year_expr)
        )

        count_stmt = select(func.count()).select_from(aggregate_stmt.subquery())
        total_rows = session.execute(count_stmt).scalar_one()

        _upsert_stats_from_select(session, aggregate_stmt)
        session.commit()

        end = datetime.now(timezone.utc)
        logging.info("Weather stats computation finished at %s", end.isoformat())
        logging.info("Weather stats rows upserted: %s", total_rows)

        return {"upserted": total_rows}
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Compute and store weather statistics.")
    _ = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    compute_weather_stats()


if __name__ == "__main__":
    main()
