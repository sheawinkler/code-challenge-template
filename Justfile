set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

default:
  @just --list

setup:
  if [[ "${UV_VENV_CLEAR:-0}" == "1" ]]; then uv venv --clear; else uv venv --allow-existing; fi
  uv pip install -r requirements.txt -r requirements-dev.txt

migrate:
  uv run alembic upgrade head

ingest:
  uv run python -m app.ingest.weather --data-dir "{{DATA_DIR}}"
  uv run python -m app.ingest.yield --file "{{YIELD_FILE}}"

stats:
  uv run python -m app.stats

api:
  uv run uvicorn app.main:app --reload --app-dir src --port "{{PORT}}"

test:
  uv run pytest

lint:
  uv run ruff check .
  uv run black --check .

check:
  just lint
  just test

ingest-and-launch-api:
  just setup
  just migrate
  just ingest
  just stats
  just api

docker-all:
  docker compose run --rm app uv run alembic upgrade head
  docker compose run --rm app uv run python -m app.ingest.weather --data-dir "{{DATA_DIR}}"
  docker compose run --rm app uv run python -m app.ingest.yield --file "{{YIELD_FILE}}"
  docker compose run --rm app uv run python -m app.stats
  docker compose up -d
  @echo "API should be running at http://127.0.0.1:{{PORT}}"

docker-all-postgres:
  docker compose --profile postgres up -d db
  just docker-all

example:
  @echo "Assumes API is already running on port {{PORT}}"
  curl "http://127.0.0.1:{{PORT}}/api/weather?station_id=USC00110072&start_date=2010-01-01&end_date=2010-12-31&page=1&page_size=5"

# Defaults
DATA_DIR := "wx_data"
YIELD_FILE := "yld_data/US_corn_grain_yield.txt"
PORT := "3767"
