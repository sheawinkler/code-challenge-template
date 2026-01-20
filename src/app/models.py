from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base


class WeatherStation(Base):
    __tablename__ = "weather_stations"

    station_id = Column(String, primary_key=True)

    records = relationship("WeatherRecord", back_populates="station")
    stats = relationship("WeatherStats", back_populates="station")


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    station_id = Column(String, ForeignKey("weather_stations.station_id"), primary_key=True)
    date = Column(Date, primary_key=True)
    max_temp_tenths_c = Column(Integer, nullable=True)
    min_temp_tenths_c = Column(Integer, nullable=True)
    precip_tenths_mm = Column(Integer, nullable=True)
    max_temp_raw_id = Column(Integer, nullable=True)
    min_temp_raw_id = Column(Integer, nullable=True)
    precip_raw_id = Column(Integer, nullable=True)

    station = relationship("WeatherStation", back_populates="records")

    __table_args__ = (
        Index("ix_weather_records_date", "date"),
        Index("ix_weather_records_station_date", "station_id", "date"),
    )


class WeatherStats(Base):
    __tablename__ = "weather_stats"

    station_id = Column(String, ForeignKey("weather_stations.station_id"), primary_key=True)
    year = Column(Integer, primary_key=True)
    avg_max_temp_c = Column(Float, nullable=True)
    avg_min_temp_c = Column(Float, nullable=True)
    total_precip_cm = Column(Float, nullable=True)

    station = relationship("WeatherStation", back_populates="stats")

    __table_args__ = (Index("ix_weather_stats_station_year", "station_id", "year"),)


class CropYield(Base):
    __tablename__ = "crop_yield"

    year = Column(Integer, primary_key=True)
    yield_value = Column(Integer, nullable=False)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    processed_count = Column(Integer, nullable=False, default=0)
    inserted_raw_count = Column(Integer, nullable=False, default=0)
    upserted_curated_count = Column(Integer, nullable=False, default=0)
    conflicts_count = Column(Integer, nullable=False, default=0)


class IngestionEvent(Base):
    __tablename__ = "ingestion_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ingestion_run_id = Column(Integer, ForeignKey("ingestion_runs.id"), nullable=False)
    level = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)


class WeatherRecordRaw(Base):
    __tablename__ = "weather_records_raw"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String, ForeignKey("weather_stations.station_id"), nullable=False)
    date = Column(Date, nullable=False)
    max_temp_tenths_c = Column(Integer, nullable=True)
    min_temp_tenths_c = Column(Integer, nullable=True)
    precip_tenths_mm = Column(Integer, nullable=True)
    source_file = Column(String, nullable=False)
    source_line = Column(Integer, nullable=False)
    ingested_at = Column(DateTime, nullable=False)
    ingestion_run_id = Column(Integer, ForeignKey("ingestion_runs.id"), nullable=False)

    __table_args__ = (
        Index("ix_weather_raw_station_date", "station_id", "date"),
        Index("ix_weather_raw_run", "ingestion_run_id"),
    )


class WeatherConflict(Base):
    __tablename__ = "weather_conflicts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ingestion_run_id = Column(Integer, ForeignKey("ingestion_runs.id"), nullable=False)
    station_id = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    field = Column(String, nullable=False)
    existing_value = Column(Integer, nullable=True)
    incoming_value = Column(Integer, nullable=True)
    existing_raw_id = Column(Integer, nullable=True)
    incoming_raw_id = Column(Integer, nullable=True)
    source_file = Column(String, nullable=False)
    source_line = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
