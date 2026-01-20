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
  1) prefer non-missing fields, 2) latest raw record wins for conflicts.
- Conflicts are logged to `weather_conflicts`.
- `ingestion_runs` + `ingestion_events` store per-run totals and key log events (so we’re not relying on text logs).

## Partitioning (Postgres)
- For Postgres, `weather_records_raw` is partitioned by year (range on date).
- Each year is subpartitioned by hash on `station_id` to keep station filters fast.

## API
- FastAPI with `/api/weather`, `/api/weather/stats`, and `/api/yield` endpoints.
- Added `/api/ingestion/events` for ingestion event logs.
- Filters for station/date/year and pagination are supported.
- Responses return values in standard units (°C, cm) where applicable.

## Logs table
- `ingestion_events` is a lightweight log table tied to `ingestion_runs`.
- It captures key ingestion milestones (start, merge, conflicts, end) in a queryable format.
## Examples (API + SQL)
### Weather
API:
```bash
curl "http://127.0.0.1:8000/api/weather?station_id=USC00110072&start_date=2010-01-01&end_date=2010-12-31&page=1&page_size=100"
```
SQL:
```sql
SELECT *
FROM weather_records
WHERE station_id = 'USC00110072'
  AND date BETWEEN '2010-01-01' AND '2010-12-31'
ORDER BY date;
```

### Weather stats
API:
```bash
curl "http://127.0.0.1:8000/api/weather/stats?station_id=USC00110072&year_start=2010&year_end=2014"
```
SQL:
```sql
SELECT *
FROM weather_stats
WHERE station_id = 'USC00110072'
  AND year BETWEEN 2010 AND 2014
ORDER BY year;
```

### Crop yield
API:
```bash
curl "http://127.0.0.1:8000/api/yield?year_start=2000&year_end=2010"
```
SQL:
```sql
SELECT *
FROM crop_yield
WHERE year BETWEEN 2000 AND 2010
ORDER BY year;
```

### Ingestion events
API:
```bash
curl "http://127.0.0.1:8000/api/ingestion/events?ingestion_run_id=1&level=INFO"
```
SQL:
```sql
SELECT *
FROM ingestion_events
WHERE message LIKE '%conflicts logged%'
ORDER BY created_at DESC;
```

## Databricks scaffolding
- Separate DDL for raw + curated + conflict tables.
- Job stubs load raw data then merge into curated with the same rule order.

## Post-implementation analysis (brief)
- Strengths: deterministic ingestion, audit trail, idempotent stats, clear API surface.
- Tradeoffs: raw table grows per run; no retention policy or partition pruning for non-Postgres.
- Next steps: retention/partition maintenance, Postgres smoke test in CI, optional ingestion run API.
