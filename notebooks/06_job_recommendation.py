# Databricks notebook source
# MAGIC %md
# MAGIC # 06 - Job Recommendation Engine
# MAGIC
# MAGIC **What we're building:** a candidate-to-job matcher using TF-IDF +
# MAGIC cosine similarity (see `src/recommender.py` for the implementation).
# MAGIC
# MAGIC **Why start with TF-IDF instead of embeddings:** it's fast, needs no
# MAGIC GPU/external API, and -- critically for an interview talking point --
# MAGIC it's fully explainable: you can point to exactly which words drove a
# MAGIC match score. We discuss embeddings as a natural next step at the end.

# COMMAND ----------

import os, sys, yaml
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.getcwd(), ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from src.recommender import JobRecommender, build_candidate_profile

with open(os.path.join(REPO_ROOT, "config", "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

CATALOG = config["catalog"]["name"]
GOLD_SCHEMA = config["catalog"]["gold_schema"]
GOLD_TABLE = f"{CATALOG}.{GOLD_SCHEMA}.dim_job_postings"

# COMMAND ----------

# MAGIC %md
# MAGIC ### Load Gold job postings into a pandas DataFrame
# MAGIC
# MAGIC scikit-learn's TF-IDF vectorizer operates on a single-machine pandas
# MAGIC DataFrame. For a dataset of this size (thousands of rows) this is
# MAGIC perfectly fine and much simpler than a distributed implementation --
# MAGIC collecting to the driver is the right call here. For millions of rows,
# MAGIC you'd instead use Spark ML's `HashingTF` + `IDF` + a distributed
# MAGIC similarity join, which we mention in the "next steps" section below.

# COMMAND ----------

jobs_spark_df = spark.table(GOLD_TABLE).filter("clean_skills IS NOT NULL AND clean_skills != ''")
jobs_pdf = jobs_spark_df.select(
    "job_id", "standardized_title", "company", "location",
    "experience_level", "salary_annual_inr", "clean_skills",
).toPandas()

print(f"Jobs available for recommendation: {len(jobs_pdf)}")
jobs_pdf.head()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Build the recommender

# COMMAND ----------

recommender = JobRecommender(jobs_pdf, skills_col="clean_skills")
print("Vocabulary size:", len(recommender.vectorizer.vocabulary_))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Example: recommend jobs for a sample candidate
# MAGIC
# MAGIC Change these values to try different candidate profiles.

# COMMAND ----------

candidate = build_candidate_profile(
    raw_skills_text="Python, SQL, PySpark, Databricks",
    preferred_role="Data Engineer",
    experience_level="Mid Level",
    preferred_location="Pune, India",
)

recommendations = recommender.recommend(candidate, top_n=10)
display(recommendations)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Widget-driven version (for interactive use in Databricks)
# MAGIC
# MAGIC Uncomment and run this cell to drive the recommender from Databricks
# MAGIC notebook widgets instead of hardcoded values above.

# COMMAND ----------

# dbutils.widgets.text("candidate_skills", "Python, SQL, Tableau")
# dbutils.widgets.text("preferred_role", "Data Analyst")
# dbutils.widgets.text("experience_level", "Entry Level")
# dbutils.widgets.text("preferred_location", "Remote - India")
#
# candidate = build_candidate_profile(
#     raw_skills_text=dbutils.widgets.get("candidate_skills"),
#     preferred_role=dbutils.widgets.get("preferred_role"),
#     experience_level=dbutils.widgets.get("experience_level"),
#     preferred_location=dbutils.widgets.get("preferred_location"),
# )
# display(recommender.recommend(candidate, top_n=10))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Next steps: improving the recommender with embeddings
# MAGIC
# MAGIC TF-IDF treats skills as independent keywords, so it cannot tell that
# MAGIC "PyTorch" and "TensorFlow" are conceptually related, or that "AWS" and
# MAGIC "cloud computing" mean similar things. A natural upgrade path:
# MAGIC
# MAGIC 1. **Sentence embeddings** (e.g. `sentence-transformers` or the
# MAGIC    Databricks Foundation Model API) to embed each job document and
# MAGIC    candidate profile into a dense vector space that captures semantic
# MAGIC    similarity, not just exact keyword overlap.
# MAGIC 2. **Vector search** (Databricks Vector Search, or FAISS locally) to
# MAGIC    do approximate nearest-neighbor lookup at scale instead of a dense
# MAGIC    cosine-similarity matrix multiply.
# MAGIC 3. **Hybrid ranking**: combine the TF-IDF score (interpretable,
# MAGIC    exact-match signal) with the embedding similarity score (semantic
# MAGIC    signal) as two features into a lightweight re-ranking model.
# MAGIC
# MAGIC This keeps the resume story clean: "shipped an explainable baseline,
# MAGIC then identified and scoped the next iteration" -- exactly what a real
# MAGIC ML team does.
# MAGIC
# MAGIC Proceed to **07_mlflow_tracking.py** to log this model with MLflow.
