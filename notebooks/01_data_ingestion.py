# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Data Ingestion
# MAGIC
# MAGIC **What we're building:** the raw landing data for the pipeline.
# MAGIC
# MAGIC **Why:** rather than depending on an external Kaggle download (which
# MAGIC can break the demo if the dataset is renamed/removed), this notebook
# MAGIC generates a realistic, intentionally messy synthetic dataset using
# MAGIC `src/data_generator.py`. If you'd rather use a real dataset, drop your
# MAGIC CSV at the path in `config.yaml -> data_generation.output_filename`
# MAGIC and set `USE_SYNTHETIC = False` below.

# COMMAND ----------

# MAGIC %pip install faker pyyaml --quiet
dbutils.library.restartPython()

# COMMAND ----------

import os
import sys
import yaml

REPO_ROOT = os.path.abspath(os.path.join(os.getcwd(), ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from src.data_generator import generate_job_postings

with open(os.path.join(REPO_ROOT, "config", "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

# Set to False to use real data from postings.csv
USE_SYNTHETIC = False  # Changed to use real LinkedIn data
NUM_RECORDS = config["data_generation"]["num_records"]
SEED = config["data_generation"]["random_seed"]
FILENAME = config["data_generation"]["output_filename"]

# COMMAND ----------

# MAGIC %md
# MAGIC ### Generate (or load) raw data

# COMMAND ----------

if USE_SYNTHETIC:
    pdf = generate_job_postings(num_records=NUM_RECORDS, seed=SEED)
    print(f"Generated {len(pdf)} synthetic job postings.")
else:
    # Point this at your real dataset (e.g. downloaded LinkedIn job postings CSV)
    local_path = os.path.join(REPO_ROOT, "data", "raw", FILENAME)
    import pandas as pd
    pdf = pd.read_csv(local_path)
    print(f"Loaded {len(pdf)} real job postings from {local_path}")

pdf.head()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Write to DBFS landing zone as CSV, then read back with Spark
# MAGIC
# MAGIC We intentionally round-trip through CSV (rather than `spark.createDataFrame`
# MAGIC directly) so that the "raw" layer genuinely mirrors what an external
# MAGIC source would look like -- untyped text -- and the Bronze layer has to
# MAGIC do real schema-on-read work.

# COMMAND ----------

raw_dir = config["paths"]["raw_data_dir"]
local_tmp_path = f"/tmp/{FILENAME}"
pdf.to_csv(local_tmp_path, index=False)

dbutils.fs.cp(f"file:{local_tmp_path}", f"{raw_dir}/{FILENAME}")
print(f"Raw CSV landed at: {raw_dir}/{FILENAME}")

# COMMAND ----------

raw_df = (spark.read
          .option("header", True)
          .option("inferSchema", False)  # keep everything as string; Bronze layer will cast
          .csv(f"{raw_dir}/{FILENAME}"))

print(f"Row count landed in Spark: {raw_df.count()}")
raw_df.printSchema()
display(raw_df.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC Proceed to **02_bronze_layer.py** to persist this as a Delta Bronze table.
