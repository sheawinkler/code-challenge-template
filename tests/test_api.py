from __future__ import annotations

from datetime import date

from app import db
from app.models import CropYield, WeatherRecord, WeatherStation, WeatherStats


def test_weather_endpoint(client, test_engine):
    with db.SessionLocal() as session:
        session.add(WeatherStation(station_id="STATION1"))
        session.add_all(
            [
                WeatherRecord(
                    station_id="STATION1",
                    date=date(2001, 1, 1),
                    max_temp_tenths_c=100,
                    min_temp_tenths_c=0,
                    precip_tenths_mm=100,
                ),
                WeatherRecord(
                    station_id="STATION1",
                    date=date(2001, 1, 2),
                    max_temp_tenths_c=200,
                    min_temp_tenths_c=50,
                    precip_tenths_mm=0,
                ),
            ]
        )
        session.commit()

    response = client.get("/api/weather", params={"station_id": "STATION1", "page": 1, "page_size": 1})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["data"]) == 1
    assert payload["data"][0]["max_temp_c"] == 10.0


def test_weather_endpoint_invalid_date_range(client, test_engine):
    response = client.get(
        "/api/weather",
        params={"date": "2001-01-01", "start_date": "2001-01-01"},
    )
    assert response.status_code == 400


def test_yield_endpoint(client, test_engine):
    with db.SessionLocal() as session:
        session.add_all([CropYield(year=2000, yield_value=123), CropYield(year=2001, yield_value=456)])
        session.commit()

    response = client.get("/api/yield", params={"page": 1, "page_size": 10})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["data"][0]["year"] == 2000


def test_stats_endpoint_filters(client, test_engine):
    with db.SessionLocal() as session:
        session.add(WeatherStation(station_id="STATION1"))
        session.add_all(
            [
                WeatherStats(
                    station_id="STATION1",
                    year=2000,
                    avg_max_temp_c=10.0,
                    avg_min_temp_c=1.0,
                    total_precip_cm=1.0,
                ),
                WeatherStats(
                    station_id="STATION1",
                    year=2001,
                    avg_max_temp_c=12.0,
                    avg_min_temp_c=2.0,
                    total_precip_cm=2.0,
                ),
            ]
        )
        session.commit()

    response = client.get(
        "/api/weather/stats",
        params={"station_id": "STATION1", "year_start": 2001},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["data"][0]["year"] == 2001


def test_stats_endpoint_invalid_year_range(client, test_engine):
    response = client.get(
        "/api/weather/stats",
        params={"year": 2000, "year_start": 1999},
    )
    assert response.status_code == 400
