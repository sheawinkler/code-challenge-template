# Approach

## Database choice
- SQLAlchemy + Alembic for schema management.
- Defaults to SQLite for easy local runs; set `DATABASE_URL` for Postgres.

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
- Raw inserts are append-only but de-duped by station/date/values so re-uploaded files don’t create duplicates.
- Curated table merge rules:
  1) prefer non-missing fields, 
  2) latest raw record wins for conflicts.
- Conflicts are logged to `weather_conflicts`.
- `ingestion_runs` + `ingestion_events` store per-run totals and key log events (so we’re not relying on text logs).

## Partitioning (Postgres)
- For Postgres, `weather_records_raw` is partitioned by year (range on date).
- Each year is subpartitioned by hash on `station_id` to keep station filters fast.

## API
- FastAPI with `/api/weather`, `/api/weather/stats`, and `/api/yield` endpoints.
- FastAPI because...
  - shortest path to typed APIs and docs in one place
  - much faster setup and lighter to get going than pulling in Django stack.
- Added `/api/ingestion/events` for ingestion event logs.
- Filters for station/date/year and pagination are supported.
- Responses return values converted to standard units (°C, cm).
- Defaults to 3767 to avoid common ports; set `PORT=port_number` w/ a launch command

## Databricks scaffolding
- Databricks scaffolding exists to mirror the raw→curated pattern; it’s intentionally light with work remaining.

## What I'd do next 
- Set retention policy for raw data.
- GitHub CI/CD integration.
- Smoke testing in CI/CD.
- Credentials management.
- Test deployment to AWS.
