# Approach

## Database choice
- Primary workflow uses SQLAlchemy + Alembic with a SQLite default for zero-setup local runs.
- Set `DATABASE_URL` to point at Postgres for production-like usage.

## Weather data model
- `weather_stations`: one row per station ID.
- `weather_records_raw`: append-only raw ingestion with provenance (file + line) and run metadata.
- `weather_records`: curated, one row per (`station_id`, `date`) with deterministic merge rules.
- Raw values are stored as provided (tenths of °C, tenths of mm) with `-9999` mapped to `NULL`.

## Stats model
- `weather_stats`: composite primary key (`station_id`, `year`).
- Aggregations ignore `NULL` automatically.
- Units are converted during aggregation: temp (°C), precip (cm).

## Crop yield model
- `crop_yield`: one row per year with the raw yield value from the provided file.

## Ingestion
- Raw inserts are append-only; duplicates across runs are preserved for audit.
- Curated table merge rules:
  1) prefer non-missing fields, 2) latest raw record wins for conflicts.
- Conflicts are logged to `weather_conflicts` for auditability.
- `ingestion_runs` stores per-run totals (processed, raw inserts, curated upserts, conflicts).

## API
- FastAPI with `/api/weather`, `/api/weather/stats`, and `/api/yield` endpoints.
- Filters for station/date/year and pagination are supported.
- Responses return values in standard units (°C, cm) where applicable.

## Databricks scaffolding
- Separate DDL for raw + curated + conflict tables.
- Job stubs load raw data then merge into curated with the same rule order.

## Post-implementation analysis (brief)
- Strengths: deterministic ingestion, audit trail, idempotent stats, and clear API surface.
- Tradeoffs: raw table grows per run; no retention policy or partitioning included.
- Next steps: add retention/partitioning strategy, Postgres smoke test, and optional ingestion run API.
