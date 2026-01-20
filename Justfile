set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

default:
  @just --list

setup:
  uv venv
  uv pip install -r requirements.txt -r requirements-dev.txt

migrate:
  uv run alembic upgrade head

ingest:
  uv run python -m app.ingest.weather --data-dir "{{DATA_DIR}}"
  uv run python -m app.ingest.yield --file "{{YIELD_FILE}}"

stats:
  uv run python -m app.stats

api:
  uv run uvicorn app.main:app --reload --app-dir src

test:
  uv run pytest

lint:
  uv run ruff check .
  uv run black --check .

check:
  uv run ruff check .
  uv run black --check .
  uv run pytest

all:
  just migrate
  just ingest
  just stats

ingest-and-launch-api:
  just migrate
  just ingest
  just stats
  just api

docker-all:
  docker compose up --build -d
  docker compose run --rm app uv run alembic upgrade head
  docker compose run --rm app uv run python -m app.ingest.weather --data-dir "{{DATA_DIR}}"
  docker compose run --rm app uv run python -m app.ingest.yield --file "{{YIELD_FILE}}"
  docker compose run --rm app uv run python -m app.stats

# Defaults
DATA_DIR := "wx_data"
YIELD_FILE := "yld_data/US_corn_grain_yield.txt"
