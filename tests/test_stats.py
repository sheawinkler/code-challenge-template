from __future__ import annotations

from datetime import date

from app import db
from app.models import WeatherRecord, WeatherStation, WeatherStats
from app.stats import compute_weather_stats


def test_compute_weather_stats(test_engine):
    with db.SessionLocal() as session:
        session.add(WeatherStation(station_id="STATION1"))
        session.add_all(
            [
                WeatherRecord(
                    station_id="STATION1",
                    date=date(2000, 1, 1),
                    max_temp_tenths_c=100,
                    min_temp_tenths_c=0,
                    precip_tenths_mm=100,
                ),
                WeatherRecord(
                    station_id="STATION1",
                    date=date(2000, 1, 2),
                    max_temp_tenths_c=None,
                    min_temp_tenths_c=20,
                    precip_tenths_mm=None,
                ),
            ]
        )
        session.commit()

    compute_weather_stats()

    with db.SessionLocal() as session:
        stats = session.get(WeatherStats, {"station_id": "STATION1", "year": 2000})
        assert stats is not None
        assert stats.avg_max_temp_c == 10.0
        assert stats.avg_min_temp_c == 1.0
        assert stats.total_precip_cm == 1.0
