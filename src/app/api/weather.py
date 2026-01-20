from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import WeatherRecord
from app.schemas import PaginatedWeatherResponse, WeatherRecordOut
from app.utils import clamp_page_size, ensure_date_range, to_celsius, to_cm_from_tenths_mm

router = APIRouter()


@router.get("/weather", response_model=PaginatedWeatherResponse)
def list_weather(
    station_id: str | None = None,
    date_value: date | None = Query(default=None, alias="date"),
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    page_size: int = Query(default=settings.page_size_default, ge=1),
    session: Session = Depends(get_session),
):
    try:
        ensure_date_range(date_value, start_date, end_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    page = max(page, 1)
    page_size = clamp_page_size(page_size, settings.page_size_max)

    filters = []
    if station_id:
        filters.append(WeatherRecord.station_id == station_id)
    if date_value:
        filters.append(WeatherRecord.date == date_value)
    if start_date:
        filters.append(WeatherRecord.date >= start_date)
    if end_date:
        filters.append(WeatherRecord.date <= end_date)

    count_stmt = select(func.count()).select_from(WeatherRecord)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = session.execute(count_stmt).scalar_one()

    stmt = select(WeatherRecord).order_by(WeatherRecord.station_id, WeatherRecord.date)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    records = session.execute(stmt).scalars().all()

    data = [
        WeatherRecordOut(
            station_id=record.station_id,
            date=record.date,
            max_temp_c=to_celsius(record.max_temp_tenths_c),
            min_temp_c=to_celsius(record.min_temp_tenths_c),
            precip_cm=to_cm_from_tenths_mm(record.precip_tenths_mm),
        )
        for record in records
    ]

    return PaginatedWeatherResponse(data=data, page=page, page_size=page_size, total=total)
