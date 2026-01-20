FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir uv && uv pip install -r requirements.txt

COPY alembic ./alembic
COPY alembic.ini ./
COPY src ./src

ENV PYTHONPATH=src

EXPOSE 3767

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3767", "--app-dir", "src"]
