# Databricks scaffolding

This directory provides a separate migration/ingestion path tailored to Databricks SQL/Delta Lake.

- `migrations/`: Databricks SQL DDL scripts (Delta tables, minimal constraints), including raw, curated, and conflict-log tables.
- `ingest/`: placeholders for Databricks Jobs (PySpark) that load raw weather/yield data into Delta tables and then merge into curated tables.

Typical flow:
1) Upload raw files to S3/DBFS.
2) Run SQL scripts in `migrations/` via a Databricks SQL Warehouse or dbt.
3) Execute the ingestion job(s) in `ingest/` on a scheduled Databricks Job.
