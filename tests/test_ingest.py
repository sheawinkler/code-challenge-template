from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

from app import db
from app.ingest.weather import ingest_weather
from app.models import IngestionEvent, WeatherConflict, WeatherRecord, WeatherRecordRaw


def test_weather_ingest_idempotent(test_engine, tmp_path):
    station_file = tmp_path / "TESTSTATION.txt"
    station_file.write_text(
        "19850101\t10\t-20\t30\n19850101\t15\t-20\t30\n19850102\t-9999\t-9999\t-9999\n",
        encoding="utf-8",
    )

    ingest_weather(tmp_path, batch_size=1)

    with db.SessionLocal() as session:
        raw_count = session.execute(select(func.count()).select_from(WeatherRecordRaw)).scalar_one()
        assert raw_count == 3
        curated_count = session.execute(select(func.count()).select_from(WeatherRecord)).scalar_one()
        assert curated_count == 2
        record = session.get(WeatherRecord, {"station_id": "TESTSTATION", "date": date(1985, 1, 2)})
        assert record.max_temp_tenths_c is None
        assert record.min_temp_tenths_c is None
        assert record.precip_tenths_mm is None
        record_with_values = session.get(
            WeatherRecord, {"station_id": "TESTSTATION", "date": date(1985, 1, 1)}
        )
        assert record_with_values.max_temp_tenths_c == 15
        conflicts = session.execute(select(func.count()).select_from(WeatherConflict)).scalar_one()
        assert conflicts == 1
        events = session.execute(select(func.count()).select_from(IngestionEvent)).scalar_one()
        assert events >= 1

    ingest_weather(tmp_path, batch_size=1)

    with db.SessionLocal() as session:
        raw_count = session.execute(select(func.count()).select_from(WeatherRecordRaw)).scalar_one()
        assert raw_count == 6
        curated_count = session.execute(select(func.count()).select_from(WeatherRecord)).scalar_one()
        assert curated_count == 2
        conflicts = session.execute(select(func.count()).select_from(WeatherConflict)).scalar_one()
        assert conflicts == 2
