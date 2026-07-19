# Career Materials

## Resume Bullet Points

Pick 3-4 depending on the role you're targeting:

- Designed and built an end-to-end Databricks data platform using the
  Medallion Architecture (Bronze/Silver/Gold), processing 8,000+ job
  postings through PySpark cleaning pipelines with automated data-quality
  gates.
- Built a Silver-layer transformation suite in PySpark that standardized
  9 job-title variants, parsed 4 inconsistent date formats, and extracted
  numeric salary values from 6+ free-text formats, reducing data-quality
  warnings by standardizing 95%+ of records.
- Developed 9 Gold-layer aggregate Delta tables and a 7-visualization
  Databricks SQL dashboard surfacing skill demand, salary trends, and
  hiring-location insights.
- Built an explainable job-recommendation engine (TF-IDF + cosine
  similarity) achieving [X]% precision@5 on a self-supervised evaluation
  metric, tracked across 3 model configurations using MLflow.
- Registered and version-controlled ML models via the MLflow Model
  Registry, wrapping the recommender as a portable `pyfunc` model.
- Built an AI-powered Career Assistant that performs data-driven skill-gap
  analysis, ranking missing skills by real market demand and generating
  personalized learning roadmaps.
- Wrote a 22-test pytest suite covering data transformation, skill
  standardization, and recommendation-ranking logic, enabling local CI
  without requiring a live Spark cluster.

*(Fill in [X]% after you run Notebook 07 in your own workspace and note the
actual `precision_at_5` value from MLflow.)*

## GitHub Project Description (short)

> End-to-end Databricks data platform: Medallion architecture (Bronze/
> Silver/Gold) in PySpark + Delta Lake, a Databricks SQL analytics
> dashboard, an explainable TF-IDF job-recommendation engine tracked with
> MLflow, and an AI-powered career-coaching assistant for skill-gap
> analysis.

## LinkedIn Project Post (draft)

> Just shipped a project I'm proud of: an end-to-end **Job Market
> Intelligence & AI Career Recommendation Platform** built entirely on
> Databricks.
>
> The pipeline ingests messy, realistic job-posting data and pushes it
> through a full Medallion Architecture (Bronze -> Silver -> Gold) in
> PySpark and Delta Lake -- standardizing inconsistent job titles, parsing
> six different salary formats, and cleaning free-text skill lists along
> the way.
>
> On top of the Gold layer, I built:
> - A 7-visualization Databricks SQL dashboard covering skill demand,
>   salary trends, and hiring locations
> - An explainable job-recommendation engine (TF-IDF + cosine similarity)
>   with experiments tracked and a model registered in MLflow
> - An AI Career Assistant that compares a candidate's skills against real
>   market demand and builds a personalized, ranked learning roadmap
>
> The whole thing runs on Databricks' free tier, with a synthetic data
> generator so anyone can reproduce it without a paid dataset. Code, docs,
> and architecture write-up are on GitHub: [your repo link]
>
> #Databricks #DataEngineering #MachineLearning #MLflow #PySpark

## Interview Questions & Answers Based on This Project

**Q: Walk me through your architecture.**
A: I used the Medallion pattern -- Bronze holds raw data untouched except
for audit columns, Silver applies all cleaning/standardization plus a
data-quality gate, and Gold has nine pre-aggregated tables built
specifically to answer the business questions the dashboard and ML layer
need, so nothing downstream has to re-aggregate from scratch.

**Q: Why did you choose TF-IDF over embeddings for the recommender?**
A: I wanted a fast, fully explainable first iteration that needs no GPU or
external API call -- I can point to the exact overlapping skill tokens
that produced a match score, which matters for a feature end users will
question. I documented the upgrade path to sentence embeddings + vector
search as the natural v2 once semantic similarity (e.g. PyTorch ~
TensorFlow) becomes valuable.

**Q: How did you evaluate a model with no labeled data?**
A: I designed a self-supervised proxy metric, precision@5: treat each
job's own skills as a candidate profile, get its top-5 recommendations,
and measure what fraction share that job's own standardized role. It's a
defensible, honest metric given the constraint rather than an ungrounded
number.

**Q: How do you handle bad or missing data in the pipeline?**
A: Bronze is untouched raw data; Silver is where I run structural checks
(row count, no null business keys) as blocking errors, and softer checks
(unparsed dates, salary out-of-bounds) as non-blocking warnings that still
get logged. That split keeps demo-grade messiness from halting the whole
pipeline while still surfacing real problems.

**Q: What would you change for a production version of this?**
A: Move the recommender's TF-IDF matrix computation to incremental
updates instead of full rebuilds, use `merge`/upsert into Bronze instead
of overwrite, add Unity Catalog data lineage and column-level access
control, and add embeddings + vector search once semantic matching quality
becomes the bottleneck rather than pipeline correctness.

**Q: Why keep the AI assistant optional / rule-based by default?**
A: I wanted the core feature to work without recurring API cost and to be
fully auditable -- the skill-gap numbers come directly from the Gold
table, not from a model that could hallucinate a percentage. The LLM, when
enabled, is only allowed to rephrase that already-correct data as nicer
prose, never to add new facts.
