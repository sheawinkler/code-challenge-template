# Code Challenge Template

## Quick start

Prereqs: `uv` (recommended). If you don’t have `uv`, no worries — you can use `python -m venv` + `pip install -r requirements.txt -r requirements-dev.txt` instead.

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-dev.txt

export PYTHONPATH=src

# Run migrations
uv run alembic upgrade head

# Ingest data
uv run python -m app.ingest.weather --data-dir wx_data
uv run python -m app.ingest.yield --file yld_data/US_corn_grain_yield.txt

# Compute stats
uv run python -m app.stats

# Run API
uv run uvicorn app.main:app --reload --app-dir src
```

API docs: `http://127.0.0.1:8000/docs`

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
scripts/run.sh api
```

You can also use the included `Justfile` (install `just` via your package manager):

```bash
just all
just api
just ingest-and-launch-api
just docker-all
just lint
just check
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
