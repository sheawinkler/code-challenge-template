from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class WeatherRecordOut(BaseModel):
    station_id: str
    date: date
    max_temp_c: float | None
    min_temp_c: float | None
    precip_cm: float | None


class WeatherStatsOut(BaseModel):
    station_id: str
    year: int
    avg_max_temp_c: float | None
    avg_min_temp_c: float | None
    total_precip_cm: float | None


class CropYieldOut(BaseModel):
    year: int
    yield_value: int


class AnnualYieldWeatherSummaryOut(BaseModel):
    year: int
    yield_value: int
    avg_max_temp_c: float | None
    avg_min_temp_c: float | None
    avg_total_precip_cm: float | None
    station_count: int


class PaginatedWeatherResponse(BaseModel):
    data: list[WeatherRecordOut]
    page: int
    page_size: int
    total: int


class PaginatedStatsResponse(BaseModel):
    data: list[WeatherStatsOut]
    page: int
    page_size: int
    total: int


class PaginatedYieldResponse(BaseModel):
    data: list[CropYieldOut]
    page: int
    page_size: int
    total: int


class PaginatedAnnualYieldWeatherSummaryResponse(BaseModel):
    data: list[AnnualYieldWeatherSummaryOut]
    page: int
    page_size: int
    total: int


class IngestionEventOut(BaseModel):
    ingestion_run_id: int
    level: str
    message: str
    created_at: str


class PaginatedIngestionEventsResponse(BaseModel):
    data: list[IngestionEventOut]
    page: int
    page_size: int
    total: int
