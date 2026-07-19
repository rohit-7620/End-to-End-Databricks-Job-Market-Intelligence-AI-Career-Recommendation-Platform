"""
data_generator.py
------------------
Generates a realistic, messy synthetic job-postings dataset so the entire
pipeline can be demoed end-to-end without depending on a Kaggle download or
any external API.

The data is generated with INTENTIONAL messiness (duplicate rows, missing
values, inconsistent casing, inconsistent salary formats, free-text skills)
so that the Bronze -> Silver cleaning steps have real work to do. This is
what a hiring manager expects to see: proof that you can clean genuinely
dirty data, not a already-perfect CSV.

Usage (local or inside a Databricks notebook):
    from src.data_generator import generate_job_postings
    df = generate_job_postings(num_records=8000, seed=42)
    df.to_csv("data/raw/job_postings_raw.csv", index=False)
"""

import random
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Reference data used to build realistic postings
# ---------------------------------------------------------------------------

JOB_ROLES = [
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

# Messy title variants that map back to a canonical role in JOB_ROLES.
# The Silver layer will need to standardize these back down.
TITLE_VARIANTS = {
    "Data Engineer": [
        "Data Engineer", "data engineer", "DATA ENGINEER", "Sr. Data Engineer",
        "Senior Data Engineer", "Jr Data Engineer", "Data Engineer II",
        "Data Engineer (Remote)", "Data  Engineer",
    ],
    "Data Scientist": [
        "Data Scientist", "data scientist", "Sr Data Scientist",
        "Senior Data Scientist", "Data Scientist - AI/ML", "Data Sci.",
    ],
    "Data Analyst": [
        "Data Analyst", "data analyst", "Junior Data Analyst",
        "Business Data Analyst", "Data  Analyst", "DATA ANALYST",
    ],
    "Machine Learning Engineer": [
        "Machine Learning Engineer", "ML Engineer", "ml engineer",
        "Senior ML Engineer", "Machine Learning Engineer II",
    ],
    "AI Engineer": [
        "AI Engineer", "Artificial Intelligence Engineer", "ai engineer",
        "Generative AI Engineer", "AI/ML Engineer",
    ],
    "Databricks Developer": [
        "Databricks Developer", "Databricks Engineer", "databricks developer",
        "Senior Databricks Developer", "Databricks Platform Engineer",
    ],
    "Business Intelligence Analyst": [
        "Business Intelligence Analyst", "BI Analyst", "bi analyst",
        "Business Intelligence Developer",
    ],
    "Analytics Engineer": [
        "Analytics Engineer", "analytics engineer", "Senior Analytics Engineer",
    ],
    "Big Data Engineer": [
        "Big Data Engineer", "big data engineer", "Big Data Developer",
    ],
}

SKILLS_BY_ROLE = {
    "Data Engineer": ["python", "sql", "pyspark", "spark", "databricks", "delta lake",
                      "airflow", "aws", "etl", "data modeling", "docker", "git"],
    "Data Scientist": ["python", "sql", "machine learning", "statistics", "scikit-learn",
                       "pandas", "deep learning", "nlp", "r", "tensorflow"],
    "Data Analyst": ["sql", "excel", "tableau", "power bi", "python", "statistics",
                     "data modeling"],
    "Machine Learning Engineer": ["python", "machine learning", "tensorflow", "pytorch",
                                  "mlflow", "docker", "kubernetes", "aws", "deep learning"],
    "AI Engineer": ["python", "machine learning", "deep learning", "nlp", "pytorch",
                    "tensorflow", "mlflow", "rest api"],
    "Databricks Developer": ["python", "pyspark", "sql", "databricks", "delta lake",
                             "spark", "azure", "aws", "mlflow"],
    "Business Intelligence Analyst": ["sql", "power bi", "tableau", "excel",
                                      "data warehousing", "etl"],
    "Analytics Engineer": ["sql", "dbt", "python", "data modeling", "data warehousing",
                           "airflow"],
    "Big Data Engineer": ["python", "spark", "hadoop", "kafka", "sql", "aws", "scala",
                          "linux"],
}

COMPANY_SUFFIXES = ["Inc.", "LLC", "Technologies", "Solutions", "Systems", "Labs",
                    "Analytics", "Group", "Corp", "Software", ""]

LOCATIONS = [
    "Bengaluru, India", "bengaluru", "BENGALURU, INDIA", "Bangalore, India",
    "Pune, India", "pune", "Pune,India",
    "Hyderabad, India", "hyderabad",
    "Mumbai, India", "mumbai",
    "Remote - India", "remote india", "Remote(India)",
    "New York, USA", "New York, NY", "new york",
    "San Francisco, USA", "San Francisco, CA",
    "Austin, USA", "Austin, TX",
    "Remote - USA", "remote usa",
    "London, UK", "london",
    "Berlin, Germany", "berlin",
    "Toronto, Canada", "toronto",
    None,  # missing location
]

EXPERIENCE_LEVELS = ["Entry Level", "entry level", "Mid Level", "mid-level",
                    "Senior Level", "senior", "Lead / Principal", "Lead", None]

EMPLOYMENT_TYPES = ["Full-time", "Full Time", "full-time", "Contract", "Part-time",
                    "Internship", None]

SALARY_RANGES_BY_LEVEL = {
    "Entry Level": (400000, 900000),
    "Mid Level": (900000, 1800000),
    "Senior Level": (1800000, 3200000),
    "Lead / Principal": (3000000, 5500000),
}

# Different messy salary string formats seen "in the wild"
def _format_salary(low, high, currency="INR"):
    fmt = random.choice([
        f"{currency} {low:,} - {high:,}",
        f"{low}-{high} {currency}",
        f"₹{low:,} to ₹{high:,}",
        f"{low//1000}K - {high//1000}K {currency}",
        str(round((low + high) / 2)),
        "Competitive",
        "Not Disclosed",
        None,
    ])
    return fmt


def _random_date(start_days_ago=365, end_days_ago=0):
    days_ago = random.randint(end_days_ago, start_days_ago)
    dt = datetime.now() - timedelta(days=days_ago)
    fmt = random.choice(["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%d %b %Y"])
    return dt.strftime(fmt)


def _build_description(role, skills):
    fake = Faker()
    intro = fake.sentence(nb_words=12)
    skills_text = ", ".join(skills)
    return (f"{intro} We are looking for a {role} with hands-on experience in "
            f"{skills_text}. {fake.sentence(nb_words=15)}")


def generate_job_postings(num_records: int = 8000, seed: int = 42) -> pd.DataFrame:
    """
    Generate a synthetic, intentionally messy job-postings dataset.

    Parameters
    ----------
    num_records : int
        Number of job posting rows to generate.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Raw synthetic job postings with realistic data-quality issues.
    """
    random.seed(seed)
    np.random.seed(seed)
    fake = Faker()
    Faker.seed(seed)

    records = []
    for _ in range(num_records):
        role = random.choice(JOB_ROLES)
        title = random.choice(TITLE_VARIANTS[role])
        level = random.choice(EXPERIENCE_LEVELS)
        level_key = level if level in SALARY_RANGES_BY_LEVEL else "Mid Level"
        low, high = SALARY_RANGES_BY_LEVEL[level_key]

        # Pick 3-7 skills for this role, occasionally with messy casing/spacing
        base_skills = SKILLS_BY_ROLE[role]
        k = random.randint(3, min(7, len(base_skills)))
        chosen_skills = random.sample(base_skills, k)
        # Introduce messiness: random case, extra spaces, semicolon/comma mix
        messy_skills = []
        for s in chosen_skills:
            variant = random.choice([s, s.upper(), s.title(), f" {s} ", s.replace(" ", "  ")])
            messy_skills.append(variant)
        separator = random.choice([", ", ";", " | ", ","])
        skills_str = separator.join(messy_skills)

        company = fake.company() + " " + random.choice(COMPANY_SUFFIXES)

        record = {
            "job_id": str(uuid.uuid4())[:8],
            "job_title": title,
            "company": company,
            "location": random.choice(LOCATIONS),
            "experience_level": level,
            "salary": _format_salary(low, high),
            "required_skills": skills_str if random.random() > 0.02 else None,
            "job_description": _build_description(role, chosen_skills),
            "employment_type": random.choice(EMPLOYMENT_TYPES),
            "posting_date": _random_date(),
            "_canonical_role": role,  # hidden helper column, dropped before saving raw
        }
        records.append(record)

    df = pd.DataFrame(records)

    # Inject exact duplicate rows (~3%) to simulate re-scraped postings
    dupe_count = int(num_records * 0.03)
    dupes = df.sample(n=dupe_count, random_state=seed, replace=True)
    df = pd.concat([df, dupes], ignore_index=True)

    # Inject a handful of fully-null rows (bad scrapes)
    for _ in range(int(num_records * 0.005)):
        df.loc[len(df)] = [None] * len(df.columns)

    # Shuffle rows
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    # Drop helper column before returning "raw" data (keeps Bronze layer honest —
    # it should not have privileged access to the ground-truth role label)
    df = df.drop(columns=["_canonical_role"])

    return df


if __name__ == "__main__":
    import os

    df = generate_job_postings(num_records=8000, seed=42)
    os.makedirs("data/raw", exist_ok=True)
    out_path = "data/raw/job_postings_raw.csv"
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} rows -> {out_path}")
    print(df.head())
