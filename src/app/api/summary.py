from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import CropYield, WeatherStats
from app.schemas import AnnualYieldWeatherSummaryOut, PaginatedAnnualYieldWeatherSummaryResponse
from app.utils import clamp_page_size

router = APIRouter()


@router.get("/summary/annual_yield_and_weather", response_model=PaginatedAnnualYieldWeatherSummaryResponse)
def list_annual_yield_and_weather(
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

    yearly_stats = (
        select(
            WeatherStats.year.label("year"),
            func.avg(WeatherStats.avg_max_temp_c).label("avg_max_temp_c"),
            func.avg(WeatherStats.avg_min_temp_c).label("avg_min_temp_c"),
            func.avg(WeatherStats.total_precip_cm).label("avg_total_precip_cm"),
            func.count().label("station_count"),
        )
        .group_by(WeatherStats.year)
        .subquery()
    )

    stmt = (
        select(
            CropYield.year.label("year"),
            CropYield.yield_value.label("yield_value"),
            yearly_stats.c.avg_max_temp_c,
            yearly_stats.c.avg_min_temp_c,
            yearly_stats.c.avg_total_precip_cm,
            yearly_stats.c.station_count,
        )
        .join(yearly_stats, yearly_stats.c.year == CropYield.year)
        .order_by(CropYield.year)
    )

    if year is not None:
        stmt = stmt.where(CropYield.year == year)
    if year_start is not None:
        stmt = stmt.where(CropYield.year >= year_start)
    if year_end is not None:
        stmt = stmt.where(CropYield.year <= year_end)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.execute(count_stmt).scalar_one()

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = session.execute(stmt).all()

    data = [AnnualYieldWeatherSummaryOut(**row._mapping) for row in rows]

    return PaginatedAnnualYieldWeatherSummaryResponse(data=data, page=page, page_size=page_size, total=total)
