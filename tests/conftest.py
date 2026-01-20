from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import db
from app.db import Base
from app.main import create_app


@pytest.fixture()
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    db.engine = engine
    db.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db.enable_sqlite_foreign_keys(engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(test_engine):
    app = create_app()
    return TestClient(app)
