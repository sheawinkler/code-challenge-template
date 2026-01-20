# Code Challenge Template

## Quick start

Prereqs: `uv` (recommended). If you don’t have `uv`, you can use `python -m venv` + `pip install -r requirements.txt -r requirements-dev.txt` instead.

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

## Optional helpers

`scripts/run.sh` wraps common commands (requires `uv`):

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

## Endpoints

- `GET /api/weather`
- `GET /api/weather/stats`
- `GET /api/yield`

All endpoints support pagination (`page`, `page_size`) and filtering via query parameters.

## Data layers

- Raw ingestion: `weather_records_raw` (append-only with provenance).
- Curated data: `weather_records` (deduped by station/date).
- Conflicts: `weather_conflicts` (raw rows that disagree with curated values).

## Docker (optional)

Build and run the API with SQLite (data persisted in a named volume):

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
