from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import IngestionEvent
from app.schemas import IngestionEventOut, PaginatedIngestionEventsResponse
from app.utils import clamp_page_size

router = APIRouter()


@router.get("/ingestion/events", response_model=PaginatedIngestionEventsResponse)
def list_ingestion_events(
    ingestion_run_id: int | None = None,
    level: str | None = None,
    page: int = 1,
    page_size: int = Query(default=settings.page_size_default, ge=1),
    session: Session = Depends(get_session),
):
    page = max(page, 1)
    page_size = clamp_page_size(page_size, settings.page_size_max)

    filters = []
    if ingestion_run_id is not None:
        filters.append(IngestionEvent.ingestion_run_id == ingestion_run_id)
    if level:
        filters.append(IngestionEvent.level == level)

    count_stmt = select(func.count()).select_from(IngestionEvent)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = session.execute(count_stmt).scalar_one()

    stmt = select(IngestionEvent).order_by(IngestionEvent.created_at.desc(), IngestionEvent.id.desc())
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    records = session.execute(stmt).scalars().all()

    data = [
        IngestionEventOut(
            ingestion_run_id=record.ingestion_run_id,
            level=record.level,
            message=record.message,
            created_at=record.created_at.isoformat(),
        )
        for record in records
    ]

    return PaginatedIngestionEventsResponse(
        data=data,
        page=page,
        page_size=page_size,
        total=total,
    )
