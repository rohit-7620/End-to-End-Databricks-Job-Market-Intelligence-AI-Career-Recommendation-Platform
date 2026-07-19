# Job Market Intelligence & AI Career Recommendation Platform

An end-to-end Databricks data platform that ingests job-posting data, cleans
and aggregates it through a Medallion Architecture (Bronze -> Silver ->
Gold), powers a Databricks SQL analytics dashboard, trains an explainable
job-recommendation model tracked with MLflow, and includes an AI Career
Assistant that identifies skill gaps and builds a personalized learning
roadmap.

Built to demonstrate practical, job-ready skills in **Databricks, PySpark,
Delta Lake, Databricks SQL, Databricks Workflows, MLflow, ML, and
Generative AI** for entry-level Data Engineer / Databricks Developer /
Data Scientist / AI-ML Engineer roles.

## Why this project

Real job-market data is messy: inconsistent titles, five different salary
formats, duplicate postings, free-text skill lists. This project doesn't
hide that -- the synthetic data generator (`src/data_generator.py`)
deliberately injects that messiness, so the cleaning logic in the Silver
layer is solving a real problem, not polishing an already-perfect CSV.

## Architecture

```
Raw Data (synthetic or real CSV)
        |
        v
Bronze Layer (Delta) -- raw ingestion, audit columns only
        |
        v
Silver Layer (Delta) -- dedup, standardize titles/salary/dates/skills, DQ gate
        |
        v
Gold Layer (Delta) -- 9 analytics-ready aggregate tables
        |
        +----------------------------+----------------------------+
        v                            v                            v
Databricks SQL Dashboard    Job Recommender (TF-IDF)        AI Career Assistant
  (7 charts + 3 KPIs)         + MLflow tracking/registry      (skill-gap + roadmap)
```

See `docs/architecture.md` for the full design rationale.

## Tech Stack

Databricks, PySpark, Delta Lake, Spark SQL, Databricks SQL, Databricks
Workflows, scikit-learn (TF-IDF + cosine similarity), MLflow, Faker
(synthetic data), pytest, Git/GitHub. Optional: Anthropic API for the AI
Career Assistant's prose narrative.

## Project Structure

```
job-market-intelligence-databricks/
├── README.md
├── requirements.txt
├── .gitignore
├── config/
│   └── config.yaml                 # all paths, schema names, taxonomies in one place
├── data/
│   ├── raw/                        # generated/real raw CSV lands here
│   └── sample/
├── notebooks/
│   ├── 00_setup_environment.py     # catalog/schema creation
│   ├── 01_data_ingestion.py        # synthetic data generation / raw load
│   ├── 02_bronze_layer.py          # raw -> Bronze Delta
│   ├── 03_silver_layer.py          # cleaning, standardization, DQ gate
│   ├── 04_gold_layer.py            # 9 analytics-ready Gold tables
│   ├── 05_data_analysis.sql        # Databricks SQL dashboard queries
│   ├── 06_job_recommendation.py    # TF-IDF + cosine similarity recommender
│   ├── 07_mlflow_tracking.py       # experiment tracking + model registry
│   └── 08_ai_career_assistant.py   # skill-gap analysis + learning roadmap
├── src/                            # importable, unit-tested modules
│   ├── data_generator.py
│   ├── data_quality.py
│   ├── transformations.py
│   ├── skill_extractor.py
│   ├── recommender.py
│   └── career_assistant.py
├── tests/                          # pytest suite (22 tests, all passing)
├── workflows/
│   └── job_pipeline.json           # exportable Databricks Workflow definition
├── dashboards/
│   └── dashboard_config.md         # widget-by-widget dashboard build guide
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   └── mlflow_guide.md
└── screenshots/                    # add your dashboard/pipeline screenshots here
```

## Quickstart

### Option A: Run locally first (recommended before touching Databricks)

```bash
git clone <your-repo-url>
cd job-market-intelligence-databricks
pip install -r requirements.txt

# Generate the synthetic dataset
python src/data_generator.py
# -> writes data/raw/job_postings_raw.csv

# Run the test suite
pytest tests/ -v
```

### Option B: Run the full pipeline in Databricks

1. **Import as a Databricks Repo**: Repos -> Add Repo -> paste your GitHub
   URL.
2. Open and run notebooks **in order**: `00` -> `01` -> `02` -> `03` ->
   `04` -> `06` -> `07` -> `08`. (`05` is SQL-editor queries, not a
   notebook to "run" top-to-bottom -- see below.)
3. Build the dashboard: follow `dashboards/dashboard_config.md`, pasting
   each query block from `05_data_analysis.sql` into the SQL Editor.
4. (Optional) Import `workflows/job_pipeline.json` as a Databricks
   Workflow to schedule notebooks 00-08 automatically -- update the
   `notebook_path` values to match your Repo path first.

### Using a real dataset instead of synthetic data

Download the [LinkedIn Job Postings dataset](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings)
from Kaggle, place it at `data/raw/job_postings_raw.csv` matching the
expected columns (see `docs/data_dictionary.md`), and set
`USE_SYNTHETIC = False` in `notebooks/01_data_ingestion.py`.

## Machine Learning: Job Recommendation Engine

- **Approach**: TF-IDF vectorization of each job's skills + role + location
  + experience level, matched against a candidate profile via cosine
  similarity. Chosen deliberately over embeddings as an explainable,
  no-GPU-required first iteration -- see `notebooks/06_job_recommendation.py`
  for the documented upgrade path to embeddings + vector search.
- **Evaluation**: since this is unsupervised, we use a self-supervised
  proxy metric, `precision@5` (see `docs/mlflow_guide.md` for the full
  rationale).
- **Tracking**: 3 vectorizer configurations logged as MLflow runs; the
  best is registered to the MLflow Model Registry as
  `job_market_recommender`.

## AI Career Assistant

Given a candidate's current skills and a target role, the assistant:
1. Computes real market skill-demand percentages for that role (from Gold
   data, not guesses).
2. Identifies which in-demand skills the candidate is missing.
3. Ranks missing skills by market demand.
4. Produces a 5-step learning roadmap with a rationale for each skill.

This runs **entirely rule-based by default -- no API key required**. An
optional LLM call can rephrase the same, already-computed analysis as
friendlier prose (see `src/career_assistant.py` and
`notebooks/08_ai_career_assistant.py`); it is explicitly prompted not to
invent new facts, so enabling it can never make the assistant less
accurate.

## Testing

```bash
pytest tests/ -v
```

22 unit tests covering the Silver-layer transformation functions, the
skill extractor/standardizer, and the recommendation engine's ranking
logic -- all runnable locally without a Databricks cluster.

## Screenshots

_Add screenshots of your running dashboard, MLflow experiment runs, and
Workflow DAG here once built in your workspace._

## License

MIT (or your preferred license) -- see `LICENSE`.
