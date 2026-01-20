# Code Challenge Template

## Quick start

Prereqs: `uv` (recommended). If you don’t have `uv`, no worries — you can use `python -m venv` + `pip install -r requirements.txt -r requirements-dev.txt` instead.

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-dev.txt

export PYTHONPATH=src

# Optional env vars (defaults shown)
# DATABASE_URL=sqlite:///./weather_yield.db
# PAGE_SIZE_DEFAULT=100
# PAGE_SIZE_MAX=1000
# DATA_DIR=wx_data
# YIELD_FILE=yld_data/US_corn_grain_yield.txt

# Run migrations
uv run alembic upgrade head

# Ingest data
uv run python -m app.ingest.weather --data-dir wx_data
uv run python -m app.ingest.yield --file yld_data/US_corn_grain_yield.txt

# Compute stats
uv run python -m app.stats

# Run API
uv run uvicorn app.main:app --reload --app-dir src --port 3767
```

API docs: `http://127.0.0.1:3767/docs`

## Tests

```bash
uv run pytest
```

Optional Postgres smoke test (only runs if you set a Postgres URL):

```bash
POSTGRES_TEST_URL=postgresql://user:pass@localhost:5432/weather uv run pytest -m postgres
```

## Optional helpers

If you want shortcuts, `scripts/run.sh` wraps common commands (requires `uv`):

```bash
scripts/run.sh all
```

You can also use the included `Justfile` (install `just` via your package manager):

```bash
just check
just ingest-and-launch-api
just docker-all
just api-test # api must be live
```

## Database configuration

- Default: SQLite file at `./weather_yield.db`.
- Postgres: set `DATABASE_URL`, then run `alembic upgrade head`.
  - On Postgres, migration `0004_postgres_partition_raw` converts `weather_records_raw` into yearly range partitions with hash subpartitions on `station_id`.
  - If you plan to use Postgres, it’s best to run migrations before a large ingestion to avoid a big copy step.

## Endpoints

- `GET /api/weather`
- `GET /api/weather/stats`
- `GET /api/yield`
- `GET /api/ingestion/events`

All endpoints support pagination (`page`, `page_size`) and filtering via query parameters.

## Examples (API + SQL)

### Weather
API:
```bash
curl "http://127.0.0.1:3767/api/weather?station_id=USC00110072&start_date=2010-01-01&end_date=2010-12-31&page=1&page_size=100"
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
curl "http://127.0.0.1:3767/api/weather/stats?station_id=USC00110072&year_start=2010&year_end=2014"
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
curl "http://127.0.0.1:3767/api/yield?year_start=2000&year_end=2010"
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
curl "http://127.0.0.1:3767/api/ingestion/events?ingestion_run_id=1&level=INFO"
```
SQL:
```sql
SELECT *
FROM ingestion_events
WHERE message LIKE '%conflicts logged%'
ORDER BY created_at DESC;
```

## Data layers

- Raw ingestion: `weather_records_raw` (append-only with provenance).
- Curated data: `weather_records` (deduped by station/date).
- Conflicts: `weather_conflicts` (raw rows that disagree with curated values).
- Ingestion tracking: `ingestion_runs` and `ingestion_events`.

## Docker (optional)

If you want a containerized run, build and run the API with SQLite (data persisted in a named volume):

```bash
docker compose up --build
docker compose run --rm app uv run alembic upgrade head
docker compose run --rm app uv run python -m app.ingest.weather --data-dir wx_data
docker compose run --rm app uv run python -m app.ingest.yield --file yld_data/US_corn_grain_yield.txt
docker compose run --rm app uv run python -m app.stats
```

To use Postgres instead of SQLite:

```bash
DATABASE_URL=postgresql://weather:weather@db:5432/weather \\
  docker compose --profile postgres up --build

DATABASE_URL=postgresql://weather:weather@db:5432/weather \\
  docker compose run --rm app uv run alembic upgrade head
```

## Databricks scaffolding

See `databricks/README.md` for a separate migration/ingestion path targeting Databricks SQL/Delta.
