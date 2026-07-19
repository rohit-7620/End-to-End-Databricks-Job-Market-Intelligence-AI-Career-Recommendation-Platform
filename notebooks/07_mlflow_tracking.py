# Databricks notebook source
# MAGIC %md
# MAGIC # 07 - MLflow Experiment Tracking
# MAGIC
# MAGIC **What we're building:** we wrap the TF-IDF recommender as an MLflow
# MAGIC `pyfunc` model, log parameters/metrics for a few vectorizer
# MAGIC configurations, then register the best-performing configuration to the
# MAGIC MLflow Model Registry.
# MAGIC
# MAGIC **Why this matters for the resume:** experiment tracking + model
# MAGIC registry is the exact workflow interviewers expect when they ask
# MAGIC "how do you manage model versions in production?"

# COMMAND ----------

import os, sys, yaml
import pandas as pd
import mlflow
import mlflow.pyfunc
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

REPO_ROOT = os.path.abspath(os.path.join(os.getcwd(), ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from src.recommender import JobRecommender, CandidateProfile

with open(os.path.join(REPO_ROOT, "config", "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

CATALOG = config["catalog"]["name"]
GOLD_SCHEMA = config["catalog"]["gold_schema"]
GOLD_TABLE = f"{CATALOG}.{GOLD_SCHEMA}.dim_job_postings"
EXPERIMENT_PATH = config["paths"]["mlflow_experiment"]

mlflow.set_experiment(EXPERIMENT_PATH)

# COMMAND ----------

jobs_pdf = (spark.table(GOLD_TABLE)
            .filter("clean_skills IS NOT NULL AND clean_skills != ''")
            .select("job_id", "standardized_title", "company", "location",
                    "experience_level", "salary_annual_inr", "clean_skills")
            .toPandas())

print(f"Training/evaluation set size: {len(jobs_pdf)} job postings")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Define an evaluation metric
# MAGIC
# MAGIC Since this is an unsupervised similarity model (no labeled "correct
# MAGIC match" data), we use a simple, defensible proxy metric:
# MAGIC **role-match precision@k** -- for a held-out sample of jobs, treat each
# MAGIC job's own skills as a "candidate profile", ask the model for its top-K
# MAGIC recommendations, and measure what fraction of those recommendations
# MAGIC share the same standardized role as the source job. A good skill-based
# MAGIC matcher should naturally recover jobs of the same role even though role
# MAGIC is never used as the *only* signal.

# COMMAND ----------

def evaluate_precision_at_k(jobs_pdf: pd.DataFrame, vectorizer_params: dict,
                             k: int = 5, n_eval_samples: int = 200, seed: int = 42) -> dict:
    recommender = JobRecommender(jobs_pdf.copy(), skills_col="clean_skills")
    # Rebuild vectorizer with the params under test
    recommender.vectorizer = TfidfVectorizer(**vectorizer_params)
    recommender.job_matrix = recommender.vectorizer.fit_transform(recommender.jobs_df["_document"])

    sample = jobs_pdf.sample(n=min(n_eval_samples, len(jobs_pdf)), random_state=seed)

    hits, total = 0, 0
    for _, row in sample.iterrows():
        skills = row["clean_skills"].split(", ") if isinstance(row["clean_skills"], str) else []
        profile = CandidateProfile(
            skills=skills,
            preferred_role=row["standardized_title"],
            experience_level=row["experience_level"],
            preferred_location=row["location"],
        )
        recs = recommender.recommend(profile, top_n=k + 1)  # +1 since the job may recommend itself
        recs = recs[recs["job_id"] != row["job_id"]].head(k)
        if len(recs) == 0:
            continue
        matches = (recs["standardized_title"] == row["standardized_title"]).sum()
        hits += matches
        total += len(recs)

    precision_at_k = hits / total if total else 0.0
    return {"precision_at_k": precision_at_k, "k": k, "n_eval_samples": len(sample)}

# COMMAND ----------

# MAGIC %md
# MAGIC ### Run multiple experiments with different vectorizer configurations
# MAGIC
# MAGIC We compare 3 configurations, log each as its own MLflow run, and pick
# MAGIC the best `precision_at_k` to register.

# COMMAND ----------

experiment_configs = [
    {"name": "baseline_unigram", "params": {"stop_words": "english"}},
    {"name": "unigram_bigram", "params": {"stop_words": "english", "ngram_range": (1, 2)}},
    {"name": "min_df_filtered", "params": {"stop_words": "english", "min_df": 2}},
]

results = []

for cfg in experiment_configs:
    with mlflow.start_run(run_name=cfg["name"]) as run:
        # ---- Log parameters ----
        mlflow.log_param("vectorizer_config_name", cfg["name"])
        for k, v in cfg["params"].items():
            mlflow.log_param(f"tfidf_{k}", str(v))
        mlflow.log_param("similarity_metric", "cosine")
        mlflow.log_param("training_rows", len(jobs_pdf))

        # ---- Evaluate ----
        metrics = evaluate_precision_at_k(jobs_pdf, cfg["params"], k=5)

        # ---- Log metrics ----
        mlflow.log_metric("precision_at_5", metrics["precision_at_k"])
        mlflow.log_metric("eval_sample_size", metrics["n_eval_samples"])

        print(f"Run '{cfg['name']}': precision@5 = {metrics['precision_at_k']:.4f} "
              f"(run_id={run.info.run_id})")

        results.append({
            "run_id": run.info.run_id,
            "name": cfg["name"],
            "params": cfg["params"],
            "precision_at_5": metrics["precision_at_k"],
        })

# COMMAND ----------

# MAGIC %md
# MAGIC ### Pick the best run and log the full model artifact

# COMMAND ----------

best_result = max(results, key=lambda r: r["precision_at_5"])
print(f"Best configuration: {best_result['name']} "
      f"(precision@5 = {best_result['precision_at_5']:.4f})")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Wrap the recommender as an MLflow `pyfunc` model
# MAGIC
# MAGIC This lets the model be loaded generically via `mlflow.pyfunc.load_model()`
# MAGIC regardless of the underlying library, and registered/served like any
# MAGIC other MLflow model.

# COMMAND ----------

class JobRecommenderWrapper(mlflow.pyfunc.PythonModel):
    """
    MLflow pyfunc wrapper around JobRecommender.

    Expected `model_input` (a pandas DataFrame) columns:
        skills (str, comma-separated), preferred_role, experience_level,
        preferred_location
    Returns a DataFrame of recommendations for the FIRST row of the input
    (mirrors how a real-time single-candidate scoring endpoint would be used).
    """

    def load_context(self, context):
        import pandas as pd
        jobs_pdf = pd.read_parquet(context.artifacts["jobs_data"])
        from src.recommender import JobRecommender
        self.recommender = JobRecommender(jobs_pdf, skills_col="clean_skills")

    def predict(self, context, model_input: pd.DataFrame, params=None):
        from src.recommender import CandidateProfile
        row = model_input.iloc[0]
        profile = CandidateProfile(
            skills=[s.strip() for s in str(row["skills"]).split(",") if s.strip()],
            preferred_role=row.get("preferred_role"),
            experience_level=row.get("experience_level"),
            preferred_location=row.get("preferred_location"),
        )
        return self.recommender.recommend(profile, top_n=int(row.get("top_n", 10)))


# Persist the jobs dataset as a parquet artifact the model can load at inference time
artifact_path = "/tmp/jobs_data_for_model.parquet"
jobs_pdf.to_parquet(artifact_path, index=False)

with mlflow.start_run(run_name=f"{best_result['name']}_registered_model") as run:
    mlflow.log_param("vectorizer_config_name", best_result["name"])
    mlflow.log_metric("precision_at_5", best_result["precision_at_5"])

    mlflow.pyfunc.log_model(
        artifact_path="job_recommender_model",
        python_model=JobRecommenderWrapper(),
        artifacts={"jobs_data": artifact_path},
        code_path=[os.path.join(REPO_ROOT, "src")],
        pip_requirements=["scikit-learn", "pandas", "pyarrow"],
    )

    model_uri = f"runs:/{run.info.run_id}/job_recommender_model"
    print(f"Logged model at: {model_uri}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Register the model to the MLflow Model Registry

# COMMAND ----------

REGISTERED_MODEL_NAME = "job_market_recommender"

registered_model = mlflow.register_model(model_uri=model_uri, name=REGISTERED_MODEL_NAME)
print(f"Registered model '{REGISTERED_MODEL_NAME}' version {registered_model.version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Sanity check: load the registered model back and score one candidate

# COMMAND ----------

loaded_model = mlflow.pyfunc.load_model(model_uri=f"models:/{REGISTERED_MODEL_NAME}/{registered_model.version}")

test_input = pd.DataFrame([{
    "skills": "Python, SQL, PySpark",
    "preferred_role": "Data Engineer",
    "experience_level": "Mid Level",
    "preferred_location": "Pune, India",
    "top_n": 5,
}])

display(loaded_model.predict(test_input))

# COMMAND ----------

# MAGIC %md
# MAGIC Proceed to **08_ai_career_assistant.py** for the skill-gap analysis feature.
