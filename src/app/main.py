from __future__ import annotations

from fastapi import FastAPI

from app.api import ingestion, stats, weather, yield_data


def create_app() -> FastAPI:
    app = FastAPI(title="Weather Data API", version="1.0.0")

    app.include_router(weather.router, prefix="/api")
    app.include_router(stats.router, prefix="/api")
    app.include_router(yield_data.router, prefix="/api")
    app.include_router(ingestion.router, prefix="/api")

    @app.get("/")
    def root():
        return {"status": "ok"}

    return app


app = create_app()
