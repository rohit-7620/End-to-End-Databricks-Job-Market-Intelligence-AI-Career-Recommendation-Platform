# MLflow Guide

This project uses MLflow for experiment tracking and model registry, all
implemented in `notebooks/07_mlflow_tracking.py`.

## What gets tracked

For each of 3 TF-IDF vectorizer configurations, we log an MLflow **run**
containing:

**Parameters**
- `vectorizer_config_name` -- which configuration this run represents
- `tfidf_*` -- the actual scikit-learn `TfidfVectorizer` kwargs used
- `similarity_metric` -- always "cosine" in this project
- `training_rows` -- size of the dataset used

**Metrics**
- `precision_at_5` -- our proxy accuracy metric (see below)
- `eval_sample_size` -- how many jobs were sampled for evaluation

**Artifacts** (on the final registered run only)
- The full `pyfunc` model (`job_recommender_model`), which bundles:
  - the fitted `TfidfVectorizer` + job similarity matrix (via the
    `JobRecommender` class, re-instantiated from a saved parquet snapshot
    of the jobs dataset at `load_context` time)
  - the `src/` code path, so the model is self-contained and loadable
    without depending on the original notebook's Python session

## Why `precision@5` as the evaluation metric

This is an **unsupervised** similarity model -- there's no labeled
"correct match" dataset to compute standard classification metrics against.
Instead, we use a simple, honest proxy: take each job's own skill list as
if it were a candidate profile, ask the model for its top-5
recommendations, and measure what fraction of those recommendations share
the same standardized job role. A good skill-based matcher should
naturally recover same-role jobs even though role is never the *only*
matching signal (skills, location, and experience level all contribute).

This metric is intentionally simple and explainable enough to defend in an
interview ("I didn't have labeled click-through data, so I designed a
self-supervised proxy metric") rather than a black-box number.

## Model Registry Workflow

1. All 3 configurations run and log to the experiment at
   `/Shared/job_market_intelligence` (configurable in `config.yaml`).
2. The configuration with the highest `precision_at_5` is selected.
3. That configuration is **re-run and logged as a full pyfunc model**
   (separately from the 3 comparison runs, to keep the comparison runs
   lightweight).
4. `mlflow.register_model()` registers it under the name
   `job_market_recommender` in the Model Registry, creating version 1 (or
   incrementing if you re-run the notebook).
5. The notebook then loads the model back via
   `mlflow.pyfunc.load_model("models:/job_market_recommender/<version>")`
   and scores a test candidate, as a sanity check that registration worked
   end-to-end.

## Viewing results in the UI

- **Experiments tab** (left sidebar) -> `/Shared/job_market_intelligence`
  shows all runs, sortable by `precision_at_5`.
- **Models tab** -> `job_market_recommender` shows the registered version,
  its lineage back to the originating run, and (if you promote it) its
  stage (Staging/Production).

## Promoting to Production (manual step, not automated in this project)

```python
from mlflow.tracking import MlflowClient
client = MlflowClient()
client.transition_model_version_stage(
    name="job_market_recommender",
    version=registered_model.version,
    stage="Production",
)
```

This step is left manual/commented-out in the notebook deliberately --
promoting to Production should be a reviewed decision, not something a
scheduled job does silently.
