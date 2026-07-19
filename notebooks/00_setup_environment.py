# Databricks notebook source
# MAGIC %md
# MAGIC # 00 - Environment Setup
# MAGIC
# MAGIC **What we're building:** the catalog/schema scaffolding and repo path
# MAGIC wiring that every downstream notebook depends on.
# MAGIC
# MAGIC **Why:** keeping this in one place means changing a catalog/schema name
# MAGIC later is a one-line edit, not a search-and-replace across 8 notebooks.
# MAGIC
# MAGIC **Run this notebook once** before running 01-08, or attach it as the
# MAGIC first task in the Databricks Workflow (see `workflows/job_pipeline.json`).

# COMMAND ----------

# MAGIC %pip install faker pyyaml --quiet
dbutils.library.restartPython()

# COMMAND ----------

import os
import sys
import yaml

# Make the repo's `src/` package importable from every notebook.
# When this repo is added as a Databricks Repo, `%pwd` will be the repo root.
REPO_ROOT = os.path.abspath(os.path.join(os.getcwd(), ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

print(f"Repo root added to sys.path: {REPO_ROOT}")

# COMMAND ----------

with open(os.path.join(REPO_ROOT, "config", "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

CATALOG = config["catalog"]["name"]
BRONZE_SCHEMA = config["catalog"]["bronze_schema"]
SILVER_SCHEMA = config["catalog"]["silver_schema"]
GOLD_SCHEMA = config["catalog"]["gold_schema"]

print(f"catalog={CATALOG}, bronze={BRONZE_SCHEMA}, silver={SILVER_SCHEMA}, gold={GOLD_SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create catalog/schemas
# MAGIC
# MAGIC If your workspace has **Unity Catalog** enabled, this creates a real
# MAGIC catalog. If not (e.g. Community Edition / a workspace without UC),
# MAGIC this cell falls back to using the `hive_metastore` catalog with
# MAGIC plain databases -- everything downstream still works, since we always
# MAGIC reference tables through the `CATALOG.SCHEMA.TABLE` variables set here.

# COMMAND ----------

try:
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
    spark.sql(f"USE CATALOG {CATALOG}")
    print(f"Using Unity Catalog catalog: {CATALOG}")
except Exception as e:
    print(f"Unity Catalog not available ({e}); falling back to hive_metastore.")
    CATALOG = "hive_metastore"

for schema in [BRONZE_SCHEMA, SILVER_SCHEMA, GOLD_SCHEMA]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{schema}")
    print(f"Ensured schema exists: {CATALOG}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create DBFS working directories for raw data + checkpoints

# COMMAND ----------

dbutils.fs.mkdirs(config["paths"]["raw_data_dir"])
dbutils.fs.mkdirs(config["paths"]["checkpoint_dir"])
print("DBFS directories ready:")
print(" -", config["paths"]["raw_data_dir"])
print(" -", config["paths"]["checkpoint_dir"])

# COMMAND ----------

# MAGIC %md
# MAGIC ### Save resolved config as widgets/values for downstream notebooks
# MAGIC
# MAGIC Each downstream notebook re-reads `config/config.yaml` directly (simpler
# MAGIC and more explicit than passing dozens of task values through Workflows),
# MAGIC but we print a final confirmation here so you can eyeball everything
# MAGIC before proceeding.

# COMMAND ----------

print("Environment setup complete. You can now run 01_data_ingestion.py")
print(f"CATALOG={CATALOG}")
print(f"BRONZE={CATALOG}.{BRONZE_SCHEMA}")
print(f"SILVER={CATALOG}.{SILVER_SCHEMA}")
print(f"GOLD={CATALOG}.{GOLD_SCHEMA}")
