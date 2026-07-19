"""
transformations.py
--------------------
Reusable PySpark transformation functions used by the Silver layer notebook
(03_silver_layer.py). Kept as importable functions (rather than inline
notebook code) so they can be unit tested with pytest and reused across
notebooks/jobs.

Each function takes a Spark DataFrame and returns a Spark DataFrame, so they
can be chained:

    df = (bronze_df
          .transform(standardize_job_titles)
          .transform(clean_location)
          .transform(normalize_salary)
          .transform(parse_posting_date)
          .transform(deduplicate_records))
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType

# ---------------------------------------------------------------------------
# Canonical role list + a title -> role mapping table, expressed as a Spark
# `when` chain built dynamically. Keep in sync with src/data_generator.py.
# ---------------------------------------------------------------------------

CANONICAL_ROLES = [
    "Data Engineer",
    "Data Scientist",
    "Data Analyst",
    "Machine Learning Engineer",
    "AI Engineer",
    "Databricks Developer",
    "Business Intelligence Analyst",
    "Analytics Engineer",
    "Big Data Engineer",
]

# Keyword patterns (lowercased, checked via `contains`) mapped to the
# canonical role. Order matters: more specific patterns should come first.
ROLE_KEYWORD_MAP = [
    ("databricks", "Databricks Developer"),
    ("machine learning", "Machine Learning Engineer"),
    ("ml engineer", "Machine Learning Engineer"),
    ("ai engineer", "AI Engineer"),
    ("artificial intelligence", "AI Engineer"),
    ("business intelligence", "Business Intelligence Analyst"),
    ("bi analyst", "Business Intelligence Analyst"),
    ("analytics engineer", "Analytics Engineer"),
    ("big data", "Big Data Engineer"),
    ("data engineer", "Data Engineer"),
    ("data scientist", "Data Scientist"),
    ("data sci", "Data Scientist"),
    ("data analyst", "Data Analyst"),
]


def standardize_job_titles(df: DataFrame, title_col: str = "job_title",
                            output_col: str = "standardized_title") -> DataFrame:
    """
    Map messy free-text job titles (varying case, seniority prefixes, extra
    whitespace) to a small set of canonical role names.

    Adds a new column `standardized_title` and keeps the original
    `job_title` for traceability/debugging.
    """
    cleaned = F.lower(F.trim(F.regexp_replace(F.col(title_col), r"\s+", " ")))

    role_expr = F.lit("Other")
    # Build a CASE WHEN chain, most specific pattern first, using `contains`
    for keyword, role in ROLE_KEYWORD_MAP:
        role_expr = F.when(cleaned.contains(keyword), F.lit(role)).otherwise(role_expr)

    # Reverse the chain application so the FIRST keyword in the list wins
    # (Spark `when/otherwise` evaluates top-down, but since we built it by
    # folding, the LAST applied `when` is checked FIRST at runtime - so we
    # iterate the keyword list in reverse to get intuitive priority).
    role_expr = F.lit("Other")
    for keyword, role in reversed(ROLE_KEYWORD_MAP):
        role_expr = F.when(cleaned.contains(keyword), F.lit(role)).otherwise(role_expr)

    return df.withColumn(output_col, role_expr)


def clean_company_name(df: DataFrame, company_col: str = "company") -> DataFrame:
    """Trim whitespace, collapse internal spaces, and title-case company names."""
    return df.withColumn(
        company_col,
        F.when(F.col(company_col).isNull(), F.lit(None))
         .otherwise(F.initcap(F.trim(F.regexp_replace(F.col(company_col), r"\s+", " "))))
    )


def clean_location(df: DataFrame, location_col: str = "location") -> DataFrame:
    """
    Standardize location strings: fix case, trim whitespace, normalize
    common city aliases (e.g. "Bangalore" -> "Bengaluru"), and fill missing
    values with "Unknown".
    """
    loc = F.lower(F.trim(F.regexp_replace(F.col(location_col), r"\s+", " ")))
    loc = F.regexp_replace(loc, r",\s*", ", ")  # normalize "City,Country" -> "City, Country"

    alias_expr = (
        F.when(loc.contains("bangalore"), F.lit("Bengaluru, India"))
         .when(loc.contains("bengaluru"), F.lit("Bengaluru, India"))
         .when(loc.contains("pune"), F.lit("Pune, India"))
         .when(loc.contains("hyderabad"), F.lit("Hyderabad, India"))
         .when(loc.contains("mumbai"), F.lit("Mumbai, India"))
         .when(loc.contains("remote") & loc.contains("india"), F.lit("Remote - India"))
         .when(loc.contains("remote") & loc.contains("usa"), F.lit("Remote - USA"))
         .when(loc.contains("new york"), F.lit("New York, USA"))
         .when(loc.contains("san francisco"), F.lit("San Francisco, USA"))
         .when(loc.contains("austin"), F.lit("Austin, USA"))
         .when(loc.contains("london"), F.lit("London, UK"))
         .when(loc.contains("berlin"), F.lit("Berlin, Germany"))
         .when(loc.contains("toronto"), F.lit("Toronto, Canada"))
         .otherwise(F.lit("Unknown"))
    )

    return df.withColumn(location_col, F.when(F.col(location_col).isNull(), F.lit("Unknown"))
                                          .otherwise(alias_expr))


def normalize_experience_level(df: DataFrame, col: str = "experience_level") -> DataFrame:
    """Standardize experience level free text into 4 canonical buckets."""
    lvl = F.lower(F.trim(F.coalesce(F.col(col), F.lit(""))))
    normalized = (
        F.when(lvl.contains("lead") | lvl.contains("principal"), F.lit("Lead / Principal"))
         .when(lvl.contains("senior") | (lvl == "senior level"), F.lit("Senior Level"))
         .when(lvl.contains("mid"), F.lit("Mid Level"))
         .when(lvl.contains("entry"), F.lit("Entry Level"))
         .otherwise(F.lit("Not Specified"))
    )
    return df.withColumn(col, normalized)


def normalize_salary(df: DataFrame, salary_col: str = "salary",
                      output_col: str = "salary_annual_inr") -> DataFrame:
    """
    Extract a single numeric annual salary estimate (in INR) from wildly
    inconsistent salary strings such as:
        "INR 900,000 - 1,800,000"   -> midpoint = 1,350,000
        "900K - 1800K INR"          -> midpoint = 1,350,000
        "₹900,000 to ₹1,800,000"    -> midpoint = 1,350,000
        "1350000"                   -> 1,350,000
        "Competitive" / "Not Disclosed" / null -> null

    This uses a regex to pull out all numeric groups in the string, expands
    "K" shorthand, and averages the first two numbers found (treated as a
    low/high range). Single numbers are used as-is.
    """
    raw = F.coalesce(F.col(salary_col), F.lit(""))

    # Single regex with 4 capture groups: (num1)(k-suffix1) ... (num2)(k-suffix2)
    # Calling regexp_extract multiple times with different group indices on the
    # same pattern lets us pull both numbers out of a range string in one pass,
    # without relying on regexp_extract_all (not available on older DBR versions).
    pattern = r"(\d[\d,]*\.?\d*)\s*([kK]?)[^\d]*(?:(\d[\d,]*\.?\d*)\s*([kK]?))?"

    first_num_str = F.regexp_extract(raw, pattern, 1)
    first_k = F.regexp_extract(raw, pattern, 2)
    second_num_str = F.regexp_extract(raw, pattern, 3)
    second_k = F.regexp_extract(raw, pattern, 4)

    def _to_double(num_str, k_flag):
        cleaned = F.regexp_replace(num_str, ",", "")
        val = F.when(cleaned == "", F.lit(None).cast(DoubleType())).otherwise(cleaned.cast(DoubleType()))
        return F.when(k_flag != "", val * F.lit(1000.0)).otherwise(val)

    low_val = _to_double(first_num_str, first_k)
    high_val = _to_double(second_num_str, second_k)

    salary_value = (
        F.when((low_val.isNotNull()) & (high_val.isNotNull()) & (high_val > 0),
               (low_val + high_val) / 2.0)
         .when(low_val.isNotNull(), low_val)
         .otherwise(F.lit(None).cast(DoubleType()))
    )

    # Sanity bound: discard obviously broken values (e.g. parsed "2025" from a date)
    salary_value = F.when((salary_value >= 100000) & (salary_value <= 10000000), salary_value) \
                     .otherwise(F.lit(None).cast(DoubleType()))

    return df.withColumn(output_col, salary_value)


def parse_posting_date(df: DataFrame, date_col: str = "posting_date",
                        output_col: str = "posting_date_parsed") -> DataFrame:
    """
    Parse multiple inconsistent date formats into a single DateType column.
    Formats seen in source data: yyyy-MM-dd, dd/MM/yyyy, MM-dd-yyyy, dd MMM yyyy.
    """
    raw = F.col(date_col)
    parsed = F.coalesce(
        F.to_date(raw, "yyyy-MM-dd"),
        F.to_date(raw, "dd/MM/yyyy"),
        F.to_date(raw, "MM-dd-yyyy"),
        F.to_date(raw, "dd MMM yyyy"),
    )
    return df.withColumn(output_col, parsed)


def normalize_employment_type(df: DataFrame, col: str = "employment_type") -> DataFrame:
    """Standardize employment type free text."""
    val = F.lower(F.trim(F.coalesce(F.col(col), F.lit(""))))
    normalized = (
        F.when(val.contains("full"), F.lit("Full-time"))
         .when(val.contains("part"), F.lit("Part-time"))
         .when(val.contains("contract"), F.lit("Contract"))
         .when(val.contains("intern"), F.lit("Internship"))
         .otherwise(F.lit("Not Specified"))
    )
    return df.withColumn(col, normalized)


def deduplicate_records(df: DataFrame, subset_cols=None) -> DataFrame:
    """
    Remove exact duplicate job postings. We dedupe on a business key
    (title + company + location + posting date) rather than job_id alone,
    since re-scraped postings can carry different job_ids for the same ad.
    """
    if subset_cols is None:
        subset_cols = ["job_title", "company", "location", "posting_date"]
    return df.dropDuplicates(subset_cols)


def drop_fully_null_rows(df: DataFrame, required_cols=None) -> DataFrame:
    """Drop rows where all business-critical columns are null (bad scrapes)."""
    if required_cols is None:
        required_cols = ["job_title", "company"]
    condition = None
    for c in required_cols:
        cond = F.col(c).isNotNull()
        condition = cond if condition is None else (condition | cond)
    return df.filter(condition)
