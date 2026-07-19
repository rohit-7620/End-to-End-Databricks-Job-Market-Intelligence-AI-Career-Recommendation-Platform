# Data Dictionary

## Bronze: `job_market.bronze.job_postings_bronze`

| Column | Type | Description |
|---|---|---|
| job_id | string | Unique identifier for the posting (as received) |
| job_title | string | Raw, unstandardized job title |
| company | string | Raw company name |
| location | string | Raw location string |
| experience_level | string | Raw experience level free text |
| salary | string | Raw salary string in any of several formats |
| required_skills | string | Raw, delimiter-separated skills free text |
| job_description | string | Free-text job description |
| employment_type | string | Raw employment type free text |
| posting_date | string | Raw date string in any of several formats |
| _ingested_at | timestamp | When the row was written to Bronze |
| _source_file | string | Source filename for lineage |

## Silver: `job_market.silver.job_postings_silver`

| Column | Type | Description |
|---|---|---|
| job_id | string | Unique posting identifier |
| job_title_raw | string | Original raw title, kept for traceability |
| standardized_title | string | Canonical role (one of 9 fixed values) |
| company | string | Cleaned, title-cased company name |
| location | string | Standardized location (fixed set of city/country strings, or "Unknown") |
| experience_level | string | One of: Entry Level, Mid Level, Senior Level, Lead / Principal, Not Specified |
| salary_raw | string | Original raw salary string |
| salary_annual_inr | double | Parsed numeric annual salary estimate in INR (nullable) |
| clean_skills | string | Comma-separated, taxonomy-matched standardized skills |
| other_skills | string | Comma-separated skills that didn't match the master taxonomy |
| job_description | string | Free-text description (unchanged) |
| employment_type | string | One of: Full-time, Part-time, Contract, Internship, Not Specified |
| posting_date_raw | string | Original raw date string |
| posting_date | date | Parsed date |
| _ingested_at | timestamp | Inherited from Bronze |
| _source_file | string | Inherited from Bronze |
| _silver_processed_at | timestamp | When this row was processed into Silver |

## Gold Tables

**`dim_job_postings`** -- exact copy of Silver, exposed as the Gold "fact" table.

**`top_skills_by_demand`** -- `skill`, `posting_count`, `demand_pct` (% of all postings mentioning this skill).

**`top_job_roles`** -- `job_role`, `posting_count`, `avg_salary_inr`.

**`jobs_by_location`** -- `location`, `posting_count`, `avg_salary_inr`.

**`avg_salary_by_role`** -- `job_role`, `experience_level`, `posting_count`, `avg_salary_inr`, `min_salary_inr`, `max_salary_inr`.

**`avg_salary_by_skill`** -- `skill`, `posting_count`, `avg_salary_inr` (min 5 postings to reduce noise).

**`skills_required_by_role`** -- `job_role`, `skill`, `posting_count`, `demand_pct_within_role` (% of postings for that specific role).

**`monthly_job_demand_trends`** -- `posting_month` (yyyy-MM), `job_role`, `posting_count`.

**`experience_level_distribution`** -- `experience_level`, `posting_count`, `pct_of_total`.

## Master Skills Taxonomy

python, sql, pyspark, spark, scala, java, databricks, delta lake, airflow,
aws, azure, gcp, snowflake, tableau, power bi, excel, machine learning,
deep learning, tensorflow, pytorch, scikit-learn, nlp, mlflow, docker,
kubernetes, kafka, hadoop, git, linux, r, statistics, etl, data modeling,
data warehousing, rest api, dbt, pandas

(kept in sync between `config/config.yaml` and `src/skill_extractor.py`)

## Canonical Job Roles

Data Engineer, Data Scientist, Data Analyst, Machine Learning Engineer,
AI Engineer, Databricks Developer, Business Intelligence Analyst,
Analytics Engineer, Big Data Engineer
