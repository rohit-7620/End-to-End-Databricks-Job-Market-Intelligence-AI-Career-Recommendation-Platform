-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 05 - Databricks SQL Dashboard Queries
-- MAGIC
-- MAGIC **What we're building:** the exact SQL queries backing a 7-visualization
-- MAGIC Databricks SQL Dashboard, built directly on top of the Gold tables from
-- MAGIC Notebook 04. Each query below is a candidate SQL Editor query -- in
-- MAGIC Databricks SQL, save each as its own query, then add each to a new
-- MAGIC Dashboard and pick the chart type noted in the comment above it.
-- MAGIC
-- MAGIC **How to build the dashboard in the UI:**
-- MAGIC 1. Go to **Databricks SQL -> Queries -> Create Query**.
-- MAGIC 2. Paste each SQL block below as a separate saved query (name it as
-- MAGIC    shown in the `-- Query name:` comment).
-- MAGIC 3. Go to **Dashboards -> Create Dashboard**, add each query as a widget,
-- MAGIC    and set the visualization type noted below.
-- MAGIC 4. Arrange widgets: KPI counters at top, bar charts in a 2-column grid,
-- MAGIC    trend line full-width beneath.

-- COMMAND ----------

-- MAGIC %sql
-- MAGIC USE CATALOG job_market;  -- change if you used a different catalog name in config.yaml

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 1. Top 10 Most-Demanded Skills
-- MAGIC **Chart type:** Horizontal Bar Chart
-- MAGIC **X-axis:** demand_pct | **Y-axis:** skill (sorted descending)
-- MAGIC **Why this chart:** horizontal bars read skill names more easily than
-- MAGIC a vertical bar chart when labels are long.

-- COMMAND ----------

-- MAGIC %sql
-- MAGIC -- Query name: top_10_skills
-- MAGIC SELECT skill, posting_count, demand_pct
-- MAGIC FROM gold.top_skills_by_demand
-- MAGIC ORDER BY posting_count DESC
-- MAGIC LIMIT 10;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 2. Top Hiring Locations
-- MAGIC **Chart type:** Bar Chart (or Map, if lat/long is added later)
-- MAGIC **X-axis:** location | **Y-axis:** posting_count

-- COMMAND ----------

-- MAGIC %sql
-- MAGIC -- Query name: top_hiring_locations
-- MAGIC SELECT location, posting_count, avg_salary_inr
-- MAGIC FROM gold.jobs_by_location
-- MAGIC ORDER BY posting_count DESC
-- MAGIC LIMIT 10;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 3. Top Job Roles
-- MAGIC **Chart type:** Pie or Bar Chart
-- MAGIC **Legend/X-axis:** job_role | **Values/Y-axis:** posting_count

-- COMMAND ----------

-- MAGIC %sql
-- MAGIC -- Query name: top_job_roles
-- MAGIC SELECT job_role, posting_count, avg_salary_inr
-- MAGIC FROM gold.top_job_roles
-- MAGIC ORDER BY posting_count DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 4. Average Salary by Role
-- MAGIC **Chart type:** Bar Chart, grouped by experience_level
-- MAGIC **X-axis:** job_role | **Y-axis:** avg_salary_inr | **Group/Color:** experience_level

-- COMMAND ----------

-- MAGIC %sql
-- MAGIC -- Query name: avg_salary_by_role
-- MAGIC SELECT job_role, experience_level, avg_salary_inr, posting_count
-- MAGIC FROM gold.avg_salary_by_role
-- MAGIC ORDER BY job_role,
-- MAGIC   CASE experience_level
-- MAGIC     WHEN 'Entry Level' THEN 1
-- MAGIC     WHEN 'Mid Level' THEN 2
-- MAGIC     WHEN 'Senior Level' THEN 3
-- MAGIC     WHEN 'Lead / Principal' THEN 4
-- MAGIC     ELSE 5
-- MAGIC   END;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 5. Job Postings Over Time
-- MAGIC **Chart type:** Line Chart
-- MAGIC **X-axis:** posting_month | **Y-axis:** total_postings (sum across roles)
-- MAGIC **Why:** a single aggregated line is the clearest "market is growing /
-- MAGIC shrinking" signal; role-level detail is one drill-down query below.

-- COMMAND ----------

-- MAGIC %sql
-- MAGIC -- Query name: job_postings_over_time
-- MAGIC SELECT posting_month, SUM(posting_count) AS total_postings
-- MAGIC FROM gold.monthly_job_demand_trends
-- MAGIC GROUP BY posting_month
-- MAGIC ORDER BY posting_month;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 5b. (Drill-down) Job Postings Over Time by Role
-- MAGIC **Chart type:** Multi-series Line Chart
-- MAGIC **X-axis:** posting_month | **Y-axis:** posting_count | **Series:** job_role

-- COMMAND ----------

-- MAGIC %sql
-- MAGIC -- Query name: job_postings_over_time_by_role
-- MAGIC SELECT posting_month, job_role, posting_count
-- MAGIC FROM gold.monthly_job_demand_trends
-- MAGIC ORDER BY posting_month, job_role;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 6. Skills Demand by Job Role
-- MAGIC **Chart type:** Heatmap (or stacked bar if heatmap isn't available)
-- MAGIC **X-axis:** job_role | **Y-axis:** skill | **Value/Color:** demand_pct_within_role
-- MAGIC **Why a heatmap:** this is inherently a role x skill matrix -- a heatmap
-- MAGIC lets viewers spot which skills cluster around which roles at a glance.

-- COMMAND ----------

-- MAGIC %sql
-- MAGIC -- Query name: skills_demand_by_role
-- MAGIC SELECT job_role, skill, demand_pct_within_role
-- MAGIC FROM gold.skills_required_by_role
-- MAGIC QUALIFY ROW_NUMBER() OVER (PARTITION BY job_role ORDER BY posting_count DESC) <= 8
-- MAGIC ORDER BY job_role, demand_pct_within_role DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 7. Experience-Level Distribution
-- MAGIC **Chart type:** Pie Chart or Donut Chart
-- MAGIC **Legend:** experience_level | **Values:** posting_count

-- COMMAND ----------

-- MAGIC %sql
-- MAGIC -- Query name: experience_level_distribution
-- MAGIC SELECT experience_level, posting_count, pct_of_total
-- MAGIC FROM gold.experience_level_distribution
-- MAGIC ORDER BY posting_count DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Bonus KPI counters (single-value widgets for the dashboard header)

-- COMMAND ----------

-- MAGIC %sql
-- MAGIC -- Query name: kpi_total_postings
-- MAGIC SELECT COUNT(*) AS total_job_postings FROM gold.dim_job_postings;

-- COMMAND ----------

-- MAGIC %sql
-- MAGIC -- Query name: kpi_avg_salary
-- MAGIC SELECT ROUND(AVG(salary_annual_inr), 0) AS avg_salary_inr_all_roles
-- MAGIC FROM gold.dim_job_postings
-- MAGIC WHERE salary_annual_inr IS NOT NULL;

-- COMMAND ----------

-- MAGIC %sql
-- MAGIC -- Query name: kpi_unique_companies
-- MAGIC SELECT COUNT(DISTINCT company) AS unique_companies FROM gold.dim_job_postings;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Suggested dashboard layout
-- MAGIC
-- MAGIC ```
-- MAGIC [KPI: total postings] [KPI: avg salary] [KPI: unique companies]
-- MAGIC [Top 10 Skills - bar]         [Top Hiring Locations - bar]
-- MAGIC [Top Job Roles - pie]         [Avg Salary by Role - grouped bar]
-- MAGIC [Job Postings Over Time - line, full width]
-- MAGIC [Skills Demand by Role - heatmap, full width]
-- MAGIC [Experience Level Distribution - donut]
-- MAGIC ```
-- MAGIC
-- MAGIC Proceed to **06_job_recommendation.py** to build the ML recommendation engine.
