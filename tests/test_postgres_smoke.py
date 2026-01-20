from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.postgres
def test_postgres_smoke():
    url = os.getenv("POSTGRES_TEST_URL") or os.getenv("DATABASE_URL")
    if not url or not url.startswith("postgresql"):
        pytest.skip("POSTGRES_TEST_URL or DATABASE_URL not set to a Postgres URL")

    engine = create_engine(url, future=True)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
