-- Base schema (SQLite / generic). Postgres partitioning is handled via Alembic migration 0004.
CREATE TABLE weather_stations (
  station_id TEXT PRIMARY KEY
);

CREATE TABLE weather_records (
  station_id TEXT NOT NULL,
  date DATE NOT NULL,
  max_temp_tenths_c INTEGER,
  min_temp_tenths_c INTEGER,
  precip_tenths_mm INTEGER,
  max_temp_raw_id INTEGER,
  min_temp_raw_id INTEGER,
  precip_raw_id INTEGER,
  PRIMARY KEY (station_id, date),
  FOREIGN KEY (station_id) REFERENCES weather_stations(station_id)
);

CREATE TABLE ingestion_runs (
  id INTEGER PRIMARY KEY,
  dataset TEXT NOT NULL,
  started_at TIMESTAMP NOT NULL,
  finished_at TIMESTAMP,
  processed_count INTEGER NOT NULL DEFAULT 0,
  inserted_raw_count INTEGER NOT NULL DEFAULT 0,
  upserted_curated_count INTEGER NOT NULL DEFAULT 0,
  conflicts_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE ingestion_events (
  id INTEGER PRIMARY KEY,
  ingestion_run_id INTEGER NOT NULL,
  level TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(id)
);

CREATE TABLE weather_records_raw (
  id INTEGER PRIMARY KEY,
  station_id TEXT NOT NULL,
  date DATE NOT NULL,
  max_temp_tenths_c INTEGER,
  min_temp_tenths_c INTEGER,
  precip_tenths_mm INTEGER,
  source_file TEXT NOT NULL,
  source_line INTEGER NOT NULL,
  ingested_at TIMESTAMP NOT NULL,
  ingestion_run_id INTEGER NOT NULL,
  FOREIGN KEY (station_id) REFERENCES weather_stations(station_id),
  FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(id)
);

CREATE TABLE weather_conflicts (
  id INTEGER PRIMARY KEY,
  ingestion_run_id INTEGER NOT NULL,
  station_id TEXT NOT NULL,
  date DATE NOT NULL,
  field TEXT NOT NULL,
  existing_value INTEGER,
  incoming_value INTEGER,
  existing_raw_id INTEGER,
  incoming_raw_id INTEGER,
  source_file TEXT NOT NULL,
  source_line INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL,
  FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(id)
);

CREATE TABLE weather_stats (
  station_id TEXT NOT NULL,
  year INTEGER NOT NULL,
  avg_max_temp_c REAL,
  avg_min_temp_c REAL,
  total_precip_cm REAL,
  PRIMARY KEY (station_id, year),
  FOREIGN KEY (station_id) REFERENCES weather_stations(station_id)
);

CREATE TABLE crop_yield (
  year INTEGER PRIMARY KEY,
  yield_value INTEGER NOT NULL
);

CREATE INDEX ix_weather_records_date ON weather_records(date);
CREATE INDEX ix_weather_records_station_date ON weather_records(station_id, date);
CREATE INDEX ix_weather_stats_station_year ON weather_stats(station_id, year);
CREATE INDEX ix_weather_raw_station_date ON weather_records_raw(station_id, date);
CREATE INDEX ix_weather_raw_run ON weather_records_raw(ingestion_run_id);
CREATE INDEX ix_ingestion_events_run ON ingestion_events(ingestion_run_id);
