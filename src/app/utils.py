from __future__ import annotations

from datetime import date


def clamp_page_size(page_size: int, max_size: int) -> int:
    if page_size <= 0:
        return 1
    return min(page_size, max_size)


def to_celsius(value_tenths: int | None) -> float | None:
    if value_tenths is None:
        return None
    return value_tenths / 10.0


def to_cm_from_tenths_mm(value_tenths_mm: int | None) -> float | None:
    if value_tenths_mm is None:
        return None
    return value_tenths_mm / 100.0


def ensure_date_range(date_value: date | None, start: date | None, end: date | None):
    if date_value and (start or end):
        raise ValueError("Use either date or start_date/end_date, not both.")
