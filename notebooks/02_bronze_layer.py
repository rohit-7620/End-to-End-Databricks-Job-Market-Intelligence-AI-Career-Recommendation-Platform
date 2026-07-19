# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Bronze Layer
# MAGIC
# MAGIC **What we're building:** the first Delta table in the medallion
# MAGIC architecture -- raw data, persisted as-is (all strings), plus audit
# MAGIC columns (`_ingested_at`, `_source_file`) for lineage.
# MAGIC
# MAGIC **Why:** Bronze is our system of record for "what we received". We
# MAGIC never mutate business values here -- only append audit metadata --
# MAGIC so we can always replay Silver/Gold from this table if logic changes.

# COMMAND ----------

import os, sys, yaml
from pyspark.sql import functions as F

REPO_ROOT = os.path.abspath(os.path.join(os.getcwd(), ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

with open(os.path.join(REPO_ROOT, "config", "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

CATALOG = config["catalog"]["name"]
BRONZE_SCHEMA = config["catalog"]["bronze_schema"]
RAW_DIR = config["paths"]["raw_data_dir"]
FILENAME = config["data_generation"]["output_filename"]

BRONZE_TABLE = f"{CATALOG}.{BRONZE_SCHEMA}.job_postings_bronze"

# COMMAND ----------

# MAGIC %md
# MAGIC ### Read the raw CSV landed in Notebook 01

# COMMAND ----------

raw_df = (spark.read
          .option("header", True)
          .option("inferSchema", False)
          .csv(f"{RAW_DIR}/{FILENAME}"))

print(f"Rows read from raw landing zone: {raw_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Add audit / lineage columns
# MAGIC
# MAGIC - `_ingested_at`: when this row entered Bronze (helps debug re-runs)
# MAGIC - `_source_file`: which file it came from (useful once you have
# MAGIC   multiple daily drops)

# COMMAND ----------

bronze_df = (raw_df
             .withColumn("_ingested_at", F.current_timestamp())
             .withColumn("_source_file", F.lit(FILENAME)))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Basic Bronze-level data quality checks
# MAGIC
# MAGIC At Bronze we only check structural sanity (file not empty, expected
# MAGIC columns present) -- we do NOT reject rows for messy values yet. That
# MAGIC cleaning happens in Silver, where we have more context to fix rather
# MAGIC than discard.

# COMMAND ----------

from src.data_quality import run_dq_checks

expected_columns = {
    "job_id", "job_title", "company", "location", "experience_level",
    "salary", "required_skills", "job_description", "employment_type",
    "posting_date",
}
missing_cols = expected_columns - set(bronze_df.columns)
assert not missing_cols, f"Bronze source is missing expected columns: {missing_cols}"

dq_report = run_dq_checks(bronze_df, stage="bronze")
for check in dq_report:
    print(check)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Write Bronze Delta table (append mode)
# MAGIC
# MAGIC Using `mode("overwrite")` here for repeatable demo runs. In a real
# MAGIC production job you would use `mode("append")` with a merge/upsert on
# MAGIC `job_id` to avoid reloading history every run.

# COMMAND ----------

(bronze_df.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(BRONZE_TABLE))

print(f"Bronze table written: {BRONZE_TABLE}")
display(spark.table(BRONZE_TABLE).limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC Proceed to **03_silver_layer.py** to clean and standardize this data.
