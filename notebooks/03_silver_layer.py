# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - Silver Layer
# MAGIC
# MAGIC **What we're building:** a cleaned, standardized, deduplicated version
# MAGIC of the Bronze table -- the "single source of truth" that both the Gold
# MAGIC analytics layer and the ML models will read from.
# MAGIC
# MAGIC **Why:** raw job postings are messy (inconsistent casing, multiple
# MAGIC salary formats, duplicate postings, free-text skills). Silver applies
# MAGIC every cleaning function from `src/transformations.py` and
# MAGIC `src/skill_extractor.py`, then runs data-quality checks before writing.

# COMMAND ----------

import os, sys, yaml
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, StringType

REPO_ROOT = os.path.abspath(os.path.join(os.getcwd(), ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from src.transformations import (
    standardize_job_titles, clean_company_name, clean_location,
    normalize_experience_level, normalize_salary, parse_posting_date,
    normalize_employment_type, deduplicate_records, drop_fully_null_rows,
)
from src.skill_extractor import standardize_skills, skills_to_string
from src.data_quality import run_dq_checks, assert_no_critical_failures

with open(os.path.join(REPO_ROOT, "config", "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

CATALOG = config["catalog"]["name"]
BRONZE_SCHEMA = config["catalog"]["bronze_schema"]
SILVER_SCHEMA = config["catalog"]["silver_schema"]

BRONZE_TABLE = f"{CATALOG}.{BRONZE_SCHEMA}.job_postings_bronze"
SILVER_TABLE = f"{CATALOG}.{SILVER_SCHEMA}.job_postings_silver"

# COMMAND ----------

bronze_df = spark.table(BRONZE_TABLE)
print(f"Bronze row count: {bronze_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1 - Drop fully-null rows and deduplicate
# MAGIC
# MAGIC We do this FIRST, before any expensive cleaning, so we don't waste
# MAGIC compute standardizing rows we're going to throw away anyway.

# COMMAND ----------

step1_df = (bronze_df
            .transform(drop_fully_null_rows)
            .transform(deduplicate_records))

print(f"Row count after null/duplicate removal: {step1_df.count()} "
      f"(removed {bronze_df.count() - step1_df.count()})")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2 - Standardize titles, company, location, experience,
# MAGIC ### employment type, salary, and posting date
# MAGIC
# MAGIC Each transformation is a pure function imported from
# MAGIC `src/transformations.py` -- see that file for exact regex/logic and
# MAGIC unit tests in `tests/test_transformations.py`.

# COMMAND ----------

step2_df = (step1_df
            .transform(standardize_job_titles)
            .transform(clean_company_name)
            .transform(clean_location)
            .transform(normalize_experience_level)
            .transform(normalize_employment_type)
            .transform(normalize_salary)
            .transform(parse_posting_date))

display(step2_df.select(
    "job_title", "standardized_title", "company", "location",
    "experience_level", "salary", "salary_annual_inr",
    "posting_date", "posting_date_parsed", "employment_type",
).limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 3 - Extract and standardize technical skills
# MAGIC
# MAGIC `standardize_skills()` is a Python function (not natively vectorized
# MAGIC in Spark), so we wrap it in a `pandas_udf` for efficient distributed
# MAGIC execution instead of a plain row-at-a-time UDF.

# COMMAND ----------

import pandas as pd
from pyspark.sql.functions import pandas_udf

@pandas_udf(StringType())
def extract_clean_skills_udf(raw_skills: pd.Series) -> pd.Series:
    def _process(raw):
        matched, other = standardize_skills(raw)
        return skills_to_string(matched)  # only keep taxonomy-matched skills for Gold aggregates
    return raw_skills.apply(_process)


@pandas_udf(StringType())
def extract_other_skills_udf(raw_skills: pd.Series) -> pd.Series:
    def _process(raw):
        matched, other = standardize_skills(raw)
        return ", ".join(sorted(other))
    return raw_skills.apply(_process)


step3_df = (step2_df
            .withColumn("clean_skills", extract_clean_skills_udf(F.col("required_skills")))
            .withColumn("other_skills", extract_other_skills_udf(F.col("required_skills"))))

display(step3_df.select("required_skills", "clean_skills", "other_skills").limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 4 - Select final Silver schema
# MAGIC
# MAGIC We keep both the cleaned columns AND the original raw columns
# MAGIC (renamed with `_raw` suffix) for a couple of business-critical raw
# MAGIC fields, so analysts can always trace a cleaned value back to source.

# COMMAND ----------

silver_df = step3_df.select(
    F.col("job_id"),
    F.col("job_title").alias("job_title_raw"),
    F.col("standardized_title"),
    F.col("company"),
    F.col("location"),
    F.col("experience_level"),
    F.col("salary").alias("salary_raw"),
    F.col("salary_annual_inr"),
    F.col("clean_skills"),
    F.col("other_skills"),
    F.col("job_description"),
    F.col("employment_type"),
    F.col("posting_date").alias("posting_date_raw"),
    F.col("posting_date_parsed").alias("posting_date"),
    F.col("_ingested_at"),
    F.col("_source_file"),
).withColumn("_silver_processed_at", F.current_timestamp())

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 5 - Data quality gate
# MAGIC
# MAGIC Critical checks (`severity == "error"`) will halt the notebook if they
# MAGIC fail. Warnings are printed but do not block the write -- appropriate
# MAGIC for a portfolio project where "some unparsed dates" shouldn't fail the
# MAGIC whole pipeline, but "zero rows" or "null job_id" absolutely should.

# COMMAND ----------

dq_report = run_dq_checks(silver_df, stage="silver")
for check in dq_report:
    print(check)

assert_no_critical_failures(dq_report)
print("All critical DQ checks passed.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 6 - Write Silver Delta table

# COMMAND ----------

(silver_df.write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(SILVER_TABLE))

print(f"Silver table written: {SILVER_TABLE}")
print(f"Final Silver row count: {silver_df.count()}")
display(spark.table(SILVER_TABLE).limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC Proceed to **04_gold_layer.py** to build analytics-ready aggregate tables.
