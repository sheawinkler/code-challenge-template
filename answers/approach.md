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
- Raw inserts are append-only; duplicates across runs are preserved for audit.
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
  - built-in OpenAPI/Swagger/redoc docs w/o need to configure
  - built-in Pydantic: type hints, validation, docs automatically
  - async-ready for on-demand jobs if required 
  - lighter weight than most other options, still built to scale (flask, django, etc.)
- Added `/api/ingestion/events` for ingestion event logs.
- Added `/api/summary/annual_yield_and_weather` for yearly crop yield + station-averaged weather stats (dataset covers NE/IA/IL/IN/OH, so we treat this as a Midwest rollup).
- Filters for station/date/year and pagination are supported.
- Responses return values converted to standard units (°C, cm).
- Defaults to 3767 to avoid common ports; set `PORT=port_number` w/ a launch commmand

## Databricks scaffolding
- Separate DDL definitions for raw + curated + conflict tables (Delta Lake format tables).
- Job stubs load raw data then merge into curated with the same rule order.
- Not fully implemented

## Post-implementation analysis (brief)
- **Strengths**: deterministic ingestion resolves conflicts (duplicate `station_id`, `year`), audit trail, idempotent stats, simple API endpoints w/ uniform filters & pagintion, database versioning
- **Tradeoffs**: raw table grows per run; no retention policy or partition pruning for non-Postgres;  
- **Next steps**: set retention policy, Github CI/CD integration, Postgres & API smoke test in CI/CD, SSO for app / other required credentials for AWS services (and any data input APIs) stored in application env space via k8s or accessed as application secrets via AWS, etc.
