"""
Databricks Job placeholder for ingesting weather data into Delta tables.
"""

from __future__ import annotations

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

MISSING_VALUE = -9999


def main(input_path: str, output_table: str) -> None:
    spark = SparkSession.builder.getOrCreate()

    # Raw lines: YYYYMMDD <tab> max <tab> min <tab> precip
    df = spark.read.text(input_path)
    parts = F.split(F.trim(F.col("value")), "\\s+")

    df = df.select(
        parts.getItem(0).alias("date_raw"),
        parts.getItem(1).alias("max_temp_tenths_c"),
        parts.getItem(2).alias("min_temp_tenths_c"),
        parts.getItem(3).alias("precip_tenths_mm"),
    )

    df = (
        df.withColumn("date", F.to_date(F.col("date_raw"), "yyyyMMdd"))
        .drop("date_raw")
        .withColumn("max_temp_tenths_c", F.col("max_temp_tenths_c").cast("int"))
        .withColumn("min_temp_tenths_c", F.col("min_temp_tenths_c").cast("int"))
        .withColumn("precip_tenths_mm", F.col("precip_tenths_mm").cast("int"))
        .replace(
            MISSING_VALUE,
            None,
            subset=["max_temp_tenths_c", "min_temp_tenths_c", "precip_tenths_mm"],
        )
    )

    # TODO: add station_id column from file path or upstream metadata
    # TODO: write to weather_records_raw and then merge into weather_records

    df.write.format("delta").mode("append").saveAsTable(output_table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", required=True, help="S3/DBFS path to weather files")
    parser.add_argument("--output-table", default="weather_records", help="Delta table name")
    args = parser.parse_args()

    main(args.input_path, args.output_table)
