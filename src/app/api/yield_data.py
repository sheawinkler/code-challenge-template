from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import CropYield
from app.schemas import CropYieldOut, PaginatedYieldResponse
from app.utils import clamp_page_size

router = APIRouter()


@router.get("/yield", response_model=PaginatedYieldResponse)
def list_yield(
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
    if year is not None:
        filters.append(CropYield.year == year)
    if year_start is not None:
        filters.append(CropYield.year >= year_start)
    if year_end is not None:
        filters.append(CropYield.year <= year_end)

    count_stmt = select(func.count()).select_from(CropYield)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = session.execute(count_stmt).scalar_one()

    stmt = select(CropYield).order_by(CropYield.year)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    records = session.execute(stmt).scalars().all()

    data = [CropYieldOut(year=record.year, yield_value=record.yield_value) for record in records]

    return PaginatedYieldResponse(data=data, page=page, page_size=page_size, total=total)
