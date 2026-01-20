from __future__ import annotations

"""
Databricks Job placeholder for ingesting crop yield data into Delta tables.
"""

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def main(input_path: str, output_table: str) -> None:
    spark = SparkSession.builder.getOrCreate()

    df = spark.read.text(input_path)
    parts = F.split(F.trim(F.col("value")), "\\s+")

    df = df.select(
        parts.getItem(0).cast("int").alias("year"),
        parts.getItem(1).cast("int").alias("yield_value"),
    )

    # TODO: handle deduplication on year

    df.write.format("delta").mode("append").saveAsTable(output_table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", required=True, help="S3/DBFS path to yield file")
    parser.add_argument("--output-table", default="crop_yield", help="Delta table name")
    args = parser.parse_args()

    main(args.input_path, args.output_table)
