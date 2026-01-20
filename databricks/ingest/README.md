# Databricks ingestion scaffolding

These stubs outline how a Databricks Job could ingest the raw files into Delta tables.

- Configure the input path (S3/DBFS) in the job parameters.
- Use PySpark to parse the fixed-width/tab-delimited files.
- Write to raw Delta tables, then merge into curated tables with a deterministic rule.

See `weather_ingest_job.py` and `yield_ingest_job.py` for placeholders.
