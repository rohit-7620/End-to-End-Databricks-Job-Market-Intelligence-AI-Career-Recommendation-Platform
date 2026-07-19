# Databricks notebook source
# MAGIC %md
# MAGIC # 08 - AI Career Assistant
# MAGIC
# MAGIC **What we're building:** a skill-gap analyzer that compares a
# MAGIC candidate's current skills against real market demand (from the Gold
# MAGIC `skills_required_by_role` table) and produces a ranked learning roadmap.
# MAGIC
# MAGIC **Fully optional AI/LLM layer:** by default this notebook runs 100%
# MAGIC rule-based (see `src/career_assistant.py`) -- no API key required, so
# MAGIC the whole project works for free. Set `USE_LLM = True` and provide an
# MAGIC API key via a Databricks secret to get a nicer prose write-up of the
# MAGIC exact same, locally-computed analysis.

# COMMAND ----------

import os, sys, yaml
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.getcwd(), ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from src.career_assistant import (
    analyze_skill_gap, build_learning_roadmap, format_report_text,
    generate_llm_narrative,
)

with open(os.path.join(REPO_ROOT, "config", "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

CATALOG = config["catalog"]["name"]
GOLD_SCHEMA = config["catalog"]["gold_schema"]
GOLD_TABLE = f"{CATALOG}.{GOLD_SCHEMA}.dim_job_postings"

USE_LLM = config["ai_assistant"]["use_llm"]  # default False in config.yaml

# COMMAND ----------

jobs_pdf = (spark.table(GOLD_TABLE)
            .select("standardized_title", "clean_skills")
            .toPandas())

print(f"Loaded {len(jobs_pdf)} postings for skill-gap analysis")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Configure the candidate (edit these values, or wire to widgets below)

# COMMAND ----------

CANDIDATE_SKILLS = "Python, SQL, Excel"
TARGET_ROLE = "Data Engineer"   # must match a standardized_title value

# COMMAND ----------

# dbutils.widgets.text("candidate_skills", CANDIDATE_SKILLS)
# dbutils.widgets.text("target_role", TARGET_ROLE)
# CANDIDATE_SKILLS = dbutils.widgets.get("candidate_skills")
# TARGET_ROLE = dbutils.widgets.get("target_role")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1 - Compute the skill gap (always runs locally, no API needed)

# COMMAND ----------

gap_result = analyze_skill_gap(jobs_pdf, CANDIDATE_SKILLS, TARGET_ROLE, top_k_market_skills=15)

print(f"Target role: {gap_result.target_role}")
print(f"Coverage score: {gap_result.coverage_score}%")
print(f"Matching skills: {gap_result.matching_skills}")
print(f"Top missing skills: {[m['skill'] for m in gap_result.missing_skills_ranked[:5]]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2 - Build the ranked learning roadmap

# COMMAND ----------

roadmap = build_learning_roadmap(gap_result, max_skills=5)
display(pd.DataFrame(roadmap))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 3 - Render the final report
# MAGIC
# MAGIC Rule-based mode (default) prints clean structured text. If
# MAGIC `USE_LLM = True` and a valid Anthropic API key is set as a Databricks
# MAGIC secret, this instead calls the LLM to rephrase the SAME structured
# MAGIC data as friendlier prose -- it cannot invent new skills or numbers.

# COMMAND ----------

if USE_LLM:
    try:
        api_key = dbutils.secrets.get(scope="career-assistant", key="anthropic-api-key")
    except Exception:
        api_key = None
        print("No secret found at scope='career-assistant', key='anthropic-api-key'; "
              "falling back to rule-based report.")
    report_text = generate_llm_narrative(gap_result, roadmap, api_key=api_key,
                                          model=config["ai_assistant"]["model"])
else:
    report_text = format_report_text(gap_result, roadmap)

print(report_text)

# COMMAND ----------

# MAGIC %md
# MAGIC ### How to enable the optional LLM narrative
# MAGIC 1. Create a Databricks secret scope: `databricks secrets create-scope career-assistant`
# MAGIC 2. Add your Anthropic API key:
# MAGIC    `databricks secrets put-secret career-assistant anthropic-api-key`
# MAGIC 3. Set `ai_assistant.use_llm: true` in `config/config.yaml`.
# MAGIC 4. Re-run this notebook.
# MAGIC
# MAGIC This is the final notebook in the pipeline. See the project README for
# MAGIC how to wire notebooks 00-08 into a scheduled Databricks Workflow.
