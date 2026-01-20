from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import WeatherStats
from app.schemas import PaginatedStatsResponse, WeatherStatsOut
from app.utils import clamp_page_size

router = APIRouter()


@router.get("/weather/stats", response_model=PaginatedStatsResponse)
def list_weather_stats(
    station_id: str | None = None,
    year: int | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    page: int = 1,
    page_size: int = Query(default=settings.page_size_default, ge=1),
    session: Session = Depends(get_session),
):
    if year and (year_start or year_end):
        raise HTTPException(status_code=400, detail="Use either year or year_start/year_end, not both.")

    page = max(page, 1)
    page_size = clamp_page_size(page_size, settings.page_size_max)

    filters = []
    if station_id:
        filters.append(WeatherStats.station_id == station_id)
    if year is not None:
        filters.append(WeatherStats.year == year)
    if year_start is not None:
        filters.append(WeatherStats.year >= year_start)
    if year_end is not None:
        filters.append(WeatherStats.year <= year_end)

    count_stmt = select(func.count()).select_from(WeatherStats)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = session.execute(count_stmt).scalar_one()

    stmt = select(WeatherStats).order_by(WeatherStats.station_id, WeatherStats.year)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    records = session.execute(stmt).scalars().all()

    data = [
        WeatherStatsOut(
            station_id=record.station_id,
            year=record.year,
            avg_max_temp_c=record.avg_max_temp_c,
            avg_min_temp_c=record.avg_min_temp_c,
            total_precip_cm=record.total_precip_cm,
        )
        for record in records
    ]

    return PaginatedStatsResponse(data=data, page=page, page_size=page_size, total=total)
