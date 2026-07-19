# Architecture Documentation

## Overview

This project implements the **Medallion Architecture** (Bronze -> Silver ->
Gold) on Databricks, followed by an analytics dashboard, an ML
recommendation engine, and an AI-assisted career-coaching feature.

```
Synthetic/Real Data --> Bronze (Delta) --> Silver (Delta) --> Gold (Delta)
                                                                    |
                                        +---------------------------+---------------------------+
                                        |                                                       |
                             Databricks SQL Dashboard                                Job Recommender (TF-IDF)
                             (7 visualizations + KPIs)                                      |
                                                                                     MLflow Tracking + Registry
                                                                                              |
                                                                                     AI Career Assistant
```

## Layer Responsibilities

### Bronze
- Purpose: immutable landing zone for raw data, as received.
- Transformations: **none** on business values -- only audit columns added
  (`_ingested_at`, `_source_file`).
- Table: `job_market.bronze.job_postings_bronze`

### Silver
- Purpose: single source of truth -- clean, deduplicated, standardized.
- Transformations: title standardization, company/location cleanup, salary
  parsing into a single numeric field, date parsing across multiple
  formats, skill extraction/standardization, employment-type normalization,
  deduplication, null-row removal.
- Data quality gate: critical checks (row count > 0, no null job_id) will
  halt the pipeline; warnings (unparsed dates, unmapped titles) are logged
  but non-blocking.
- Table: `job_market.silver.job_postings_silver`

### Gold
- Purpose: analytics-ready, pre-aggregated tables that BI tools and ML
  notebooks read directly, with no further joins needed.
- 9 tables: `dim_job_postings`, `top_skills_by_demand`, `top_job_roles`,
  `jobs_by_location`, `avg_salary_by_role`, `avg_salary_by_skill`,
  `skills_required_by_role`, `monthly_job_demand_trends`,
  `experience_level_distribution`.

## Why Medallion Architecture?

Separating raw/clean/aggregated data into distinct layers gives you:
- **Reprocessing safety**: if a cleaning rule changes, Silver and Gold can
  be rebuilt from Bronze without re-ingesting from the source.
- **Clear ownership boundaries**: Bronze = "what we received", Silver =
  "what we trust", Gold = "what the business consumes".
- **Incremental complexity**: each layer does one job well instead of one
  giant notebook doing ingestion + cleaning + aggregation + serving.

## ML Design Decisions

- **TF-IDF + cosine similarity** was chosen over embeddings as a first
  iteration because it is fast, requires no GPU/external API, and is fully
  explainable -- you can point to exactly which overlapping skill tokens
  drove a match score. This is a deliberate "ship the simple, explainable
  baseline first" engineering decision, not a limitation of understanding.
- **MLflow** tracks 3 vectorizer configurations (unigram baseline,
  unigram+bigram, min-df filtered) using a proxy metric (`precision@5`:
  do the top-5 recommendations for a job's own skill profile share its
  role?), then registers the best-performing configuration.
- **Embeddings as a stated next step**: sentence embeddings + vector search
  would capture semantic skill relationships (e.g. PyTorch ~ TensorFlow)
  that pure keyword TF-IDF cannot. This is documented in
  `notebooks/06_job_recommendation.py` as the natural v2.

## AI Career Assistant Design

The skill-gap analysis is **always computed locally/rule-based first** --
it reads real market-demand percentages from the Gold
`skills_required_by_role` table, ranks missing skills by demand, and
attaches a rationale. The optional LLM call (`generate_llm_narrative`) only
rephrases this already-computed, already-correct structured data into
warmer prose -- it is explicitly instructed not to invent new skills or
numbers, so enabling the LLM can never make the assistant less accurate.
This is what makes the AI feature genuinely optional rather than a
paper-thin wrapper the whole feature depends on.
