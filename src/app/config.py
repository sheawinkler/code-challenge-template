from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./weather_yield.db")
    page_size_default: int = int(os.getenv("PAGE_SIZE_DEFAULT", "100"))
    page_size_max: int = int(os.getenv("PAGE_SIZE_MAX", "1000"))
    data_dir: str = os.getenv("DATA_DIR", "wx_data")
    yield_file: str = os.getenv("YIELD_FILE", "yld_data/US_corn_grain_yield.txt")


settings = Settings()
