#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install uv or use the pip workflow in README.md." >&2
  exit 1
fi

CMD=${1:-all}
DATA_DIR=${DATA_DIR:-wx_data}
YIELD_FILE=${YIELD_FILE:-yld_data/US_corn_grain_yield.txt}
export PYTHONPATH=${PYTHONPATH:-src}

case "$CMD" in
  setup)
    uv venv
    uv pip install -r requirements.txt -r requirements-dev.txt
    ;;
  migrate)
    uv run alembic upgrade head
    ;;
  ingest)
    uv run python -m app.ingest.weather --data-dir "$DATA_DIR"
    uv run python -m app.ingest.yield --file "$YIELD_FILE"
    ;;
  stats)
    uv run python -m app.stats
    ;;
  api)
    uv run uvicorn app.main:app --reload --app-dir src
    ;;
  lint)
    uv run ruff check .
    uv run black --check .
    ;;
  check)
    uv run ruff check .
    uv run black --check .
    uv run pytest
    ;;
  all)
    uv run alembic upgrade head
    uv run python -m app.ingest.weather --data-dir "$DATA_DIR"
    uv run python -m app.ingest.yield --file "$YIELD_FILE"
    uv run python -m app.stats
    ;;
  *)
    echo "Usage: scripts/run.sh {setup|migrate|ingest|stats|api|lint|check|all}" >&2
    exit 1
    ;;
esac
