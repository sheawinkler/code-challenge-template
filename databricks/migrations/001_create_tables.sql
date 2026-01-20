-- Databricks SQL / Delta Lake DDL
-- Note: Primary/foreign keys are not enforced in Delta; keep them informational in docs.

CREATE TABLE IF NOT EXISTS weather_stations (
  station_id STRING NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS weather_records (
  station_id STRING NOT NULL,
  date DATE NOT NULL,
  max_temp_tenths_c INT,
  min_temp_tenths_c INT,
  precip_tenths_mm INT,
  max_temp_raw_id BIGINT,
  min_temp_raw_id BIGINT,
  precip_raw_id BIGINT
) USING DELTA;

CREATE TABLE IF NOT EXISTS ingestion_runs (
  id BIGINT,
  dataset STRING NOT NULL,
  started_at TIMESTAMP NOT NULL,
  finished_at TIMESTAMP,
  processed_count BIGINT,
  inserted_raw_count BIGINT,
  upserted_curated_count BIGINT,
  conflicts_count BIGINT
) USING DELTA;

CREATE TABLE IF NOT EXISTS ingestion_events (
  id BIGINT,
  ingestion_run_id BIGINT NOT NULL,
  level STRING NOT NULL,
  message STRING NOT NULL,
  created_at TIMESTAMP NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS weather_records_raw (
  id BIGINT,
  station_id STRING NOT NULL,
  date DATE NOT NULL,
  max_temp_tenths_c INT,
  min_temp_tenths_c INT,
  precip_tenths_mm INT,
  source_file STRING NOT NULL,
  source_line INT NOT NULL,
  ingested_at TIMESTAMP NOT NULL,
  ingestion_run_id BIGINT NOT NULL,
  row_hash STRING NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS weather_conflicts (
  id BIGINT,
  ingestion_run_id BIGINT NOT NULL,
  station_id STRING NOT NULL,
  date DATE NOT NULL,
  field STRING NOT NULL,
  existing_value INT,
  incoming_value INT,
  existing_raw_id BIGINT,
  incoming_raw_id BIGINT,
  source_file STRING NOT NULL,
  source_line INT NOT NULL,
  created_at TIMESTAMP NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS weather_stats (
  station_id STRING NOT NULL,
  year INT NOT NULL,
  avg_max_temp_c DOUBLE,
  avg_min_temp_c DOUBLE,
  total_precip_cm DOUBLE
) USING DELTA;

CREATE TABLE IF NOT EXISTS crop_yield (
  year INT NOT NULL,
  yield_value INT NOT NULL
) USING DELTA;
