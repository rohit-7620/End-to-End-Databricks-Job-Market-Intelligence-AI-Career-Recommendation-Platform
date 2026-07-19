# Databricks notebook source
# MAGIC %md
# MAGIC # 04 - Gold Layer
# MAGIC
# MAGIC **What we're building:** a set of small, analytics-ready aggregate
# MAGIC Delta tables, each answering one specific business question. These
# MAGIC tables power the Databricks SQL dashboard (Notebook 05) directly --
# MAGIC no further joins/aggregation needed at query time.
# MAGIC
# MAGIC **Why this design:** Gold tables should be *pre-aggregated* and *wide*
# MAGIC rather than normalized, so dashboard queries are simple `SELECT *`
# MAGIC statements that render fast even on large datasets.

# COMMAND ----------

import os, sys, yaml
from pyspark.sql import functions as F

REPO_ROOT = os.path.abspath(os.path.join(os.getcwd(), ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

with open(os.path.join(REPO_ROOT, "config", "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

CATALOG = config["catalog"]["name"]
SILVER_SCHEMA = config["catalog"]["silver_schema"]
GOLD_SCHEMA = config["catalog"]["gold_schema"]

SILVER_TABLE = f"{CATALOG}.{SILVER_SCHEMA}.job_postings_silver"
GOLD_PREFIX = f"{CATALOG}.{GOLD_SCHEMA}"

silver_df = spark.table(SILVER_TABLE)
silver_df.createOrReplaceTempView("silver_jobs")
print(f"Silver rows available for aggregation: {silver_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold table 1 - `dim_job_postings`
# MAGIC A denormalized fact table joining nothing further (Silver is already
# MAGIC flat) -- this is effectively Silver renamed/exposed as the Gold "fact"
# MAGIC table other Gold aggregates and the ML notebooks read from. Keeping a
# MAGIC copy in the Gold schema signals "this is the trusted, query-ready
# MAGIC version" to downstream consumers/BI tools.

# COMMAND ----------

(silver_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
 .saveAsTable(f"{GOLD_PREFIX}.dim_job_postings"))
print(f"Wrote {GOLD_PREFIX}.dim_job_postings")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold table 2 - `top_skills_by_demand`
# MAGIC Explodes the comma-separated `clean_skills` column into one row per
# MAGIC skill per posting, then counts postings per skill.

# COMMAND ----------

top_skills_df = spark.sql("""
    SELECT
        trim(skill) AS skill,
        COUNT(*) AS posting_count,
        ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM silver_jobs), 2) AS demand_pct
    FROM silver_jobs
    LATERAL VIEW explode(split(clean_skills, ',\\\\s*')) AS skill
    WHERE clean_skills IS NOT NULL AND clean_skills != ''
    GROUP BY trim(skill)
    ORDER BY posting_count DESC
""")

top_skills_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{GOLD_PREFIX}.top_skills_by_demand")
print(f"Wrote {GOLD_PREFIX}.top_skills_by_demand")
display(top_skills_df.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold table 3 - `top_job_roles`

# COMMAND ----------

top_roles_df = spark.sql("""
    SELECT
        standardized_title AS job_role,
        COUNT(*) AS posting_count,
        ROUND(AVG(salary_annual_inr), 0) AS avg_salary_inr
    FROM silver_jobs
    GROUP BY standardized_title
    ORDER BY posting_count DESC
""")

top_roles_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{GOLD_PREFIX}.top_job_roles")
print(f"Wrote {GOLD_PREFIX}.top_job_roles")
display(top_roles_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold table 4 - `jobs_by_location`

# COMMAND ----------

jobs_by_location_df = spark.sql("""
    SELECT
        location,
        COUNT(*) AS posting_count,
        ROUND(AVG(salary_annual_inr), 0) AS avg_salary_inr
    FROM silver_jobs
    GROUP BY location
    ORDER BY posting_count DESC
""")

jobs_by_location_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{GOLD_PREFIX}.jobs_by_location")
print(f"Wrote {GOLD_PREFIX}.jobs_by_location")
display(jobs_by_location_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold table 5 - `avg_salary_by_role`
# MAGIC (Distinct from `top_job_roles` -- this one breaks salary down further
# MAGIC by experience level, useful for a drill-down chart.)

# COMMAND ----------

salary_by_role_df = spark.sql("""
    SELECT
        standardized_title AS job_role,
        experience_level,
        COUNT(*) AS posting_count,
        ROUND(AVG(salary_annual_inr), 0) AS avg_salary_inr,
        ROUND(MIN(salary_annual_inr), 0) AS min_salary_inr,
        ROUND(MAX(salary_annual_inr), 0) AS max_salary_inr
    FROM silver_jobs
    WHERE salary_annual_inr IS NOT NULL
    GROUP BY standardized_title, experience_level
    ORDER BY job_role, experience_level
""")

salary_by_role_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{GOLD_PREFIX}.avg_salary_by_role")
print(f"Wrote {GOLD_PREFIX}.avg_salary_by_role")
display(salary_by_role_df.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold table 6 - `avg_salary_by_skill`

# COMMAND ----------

salary_by_skill_df = spark.sql("""
    SELECT
        trim(skill) AS skill,
        COUNT(*) AS posting_count,
        ROUND(AVG(salary_annual_inr), 0) AS avg_salary_inr
    FROM silver_jobs
    LATERAL VIEW explode(split(clean_skills, ',\\\\s*')) AS skill
    WHERE clean_skills IS NOT NULL AND clean_skills != '' AND salary_annual_inr IS NOT NULL
    GROUP BY trim(skill)
    HAVING COUNT(*) >= 5
    ORDER BY avg_salary_inr DESC
""")

salary_by_skill_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{GOLD_PREFIX}.avg_salary_by_skill")
print(f"Wrote {GOLD_PREFIX}.avg_salary_by_skill")
display(salary_by_skill_df.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold table 7 - `skills_required_by_role`
# MAGIC This is the exact table `src/career_assistant.py` uses for its skill
# MAGIC gap analysis, so keep the column names stable.

# COMMAND ----------

skills_by_role_df = spark.sql("""
    SELECT
        standardized_title AS job_role,
        trim(skill) AS skill,
        COUNT(*) AS posting_count,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY standardized_title), 1) AS demand_pct_within_role
    FROM silver_jobs
    LATERAL VIEW explode(split(clean_skills, ',\\\\s*')) AS skill
    WHERE clean_skills IS NOT NULL AND clean_skills != ''
    GROUP BY standardized_title, trim(skill)
    ORDER BY job_role, posting_count DESC
""")

skills_by_role_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{GOLD_PREFIX}.skills_required_by_role")
print(f"Wrote {GOLD_PREFIX}.skills_required_by_role")
display(skills_by_role_df.limit(15))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold table 8 - `monthly_job_demand_trends`

# COMMAND ----------

monthly_trends_df = spark.sql("""
    SELECT
        date_format(posting_date, 'yyyy-MM') AS posting_month,
        standardized_title AS job_role,
        COUNT(*) AS posting_count
    FROM silver_jobs
    WHERE posting_date IS NOT NULL
    GROUP BY date_format(posting_date, 'yyyy-MM'), standardized_title
    ORDER BY posting_month, job_role
""")

monthly_trends_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{GOLD_PREFIX}.monthly_job_demand_trends")
print(f"Wrote {GOLD_PREFIX}.monthly_job_demand_trends")
display(monthly_trends_df.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold table 9 - `experience_level_distribution`

# COMMAND ----------

experience_dist_df = spark.sql("""
    SELECT
        experience_level,
        COUNT(*) AS posting_count,
        ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM silver_jobs), 2) AS pct_of_total
    FROM silver_jobs
    GROUP BY experience_level
    ORDER BY posting_count DESC
""")

experience_dist_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{GOLD_PREFIX}.experience_level_distribution")
print(f"Wrote {GOLD_PREFIX}.experience_level_distribution")
display(experience_dist_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Summary of all Gold tables created

# COMMAND ----------

gold_tables = [
    "dim_job_postings", "top_skills_by_demand", "top_job_roles",
    "jobs_by_location", "avg_salary_by_role", "avg_salary_by_skill",
    "skills_required_by_role", "monthly_job_demand_trends",
    "experience_level_distribution",
]
for t in gold_tables:
    cnt = spark.table(f"{GOLD_PREFIX}.{t}").count()
    print(f"{GOLD_PREFIX}.{t}: {cnt} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC Proceed to **05_data_analysis.sql** to build the Databricks SQL dashboard,
# MAGIC or **06_job_recommendation.py** to build the ML recommender.
