from __future__ import annotations

from datetime import datetime, timezone

from app import db
from app.models import IngestionEvent, IngestionRun


def test_ingestion_events_endpoint(client, test_engine):
    with db.SessionLocal() as session:
        run = IngestionRun(dataset="weather", started_at=datetime.now(timezone.utc))
        session.add(run)
        session.commit()
        session.refresh(run)
        run_id = run.id

        event = IngestionEvent(
            ingestion_run_id=run_id,
            level="INFO",
            message="test event",
            created_at=datetime.now(timezone.utc),
        )
        session.add(event)
        session.commit()

    response = client.get("/api/ingestion/events", params={"ingestion_run_id": run_id})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["data"][0]["message"] == "test event"
