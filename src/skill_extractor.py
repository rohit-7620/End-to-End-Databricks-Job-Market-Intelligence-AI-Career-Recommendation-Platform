"""
skill_extractor.py
-------------------
Parses messy, free-text "required_skills" strings into a clean, standardized
list of skills matched against a master taxonomy. Used by the Silver layer
notebook (03_silver_layer.py) and by the recommendation engine.

Design notes:
- We normalize case/whitespace, then split on common separators (comma,
  semicolon, pipe).
- Each raw token is matched against the master taxonomy using simple
  containment matching (e.g. "ml" -> not matched, "machine learning" ->
  matched) plus a small alias map for common abbreviations.
- Unmatched tokens are kept as "other_skills" so we don't silently drop
  information the business might still care about.
"""

import re
from typing import List, Tuple

# Master taxonomy - keep this list in sync with config/config.yaml
MASTER_SKILLS = [
    "python", "sql", "pyspark", "spark", "scala", "java", "databricks",
    "delta lake", "airflow", "aws", "azure", "gcp", "snowflake", "tableau",
    "power bi", "excel", "machine learning", "deep learning", "tensorflow",
    "pytorch", "scikit-learn", "nlp", "mlflow", "docker", "kubernetes",
    "kafka", "hadoop", "git", "linux", "r", "statistics", "etl",
    "data modeling", "data warehousing", "rest api", "dbt", "pandas",
]

# Common aliases / abbreviations mapped to canonical taxonomy terms
ALIAS_MAP = {
    "ml": "machine learning",
    "dl": "deep learning",
    "k8s": "kubernetes",
    "sklearn": "scikit-learn",
    "postgres": "sql",
    "mysql": "sql",
    "bi": "power bi",
    "aws cloud": "aws",
    "gcp cloud": "gcp",
}

_SEPARATOR_PATTERN = re.compile(r"[;,|/]+")


def _normalize_token(token: str) -> str:
    """Lowercase, strip, and collapse internal whitespace for one skill token."""
    token = token.strip().lower()
    token = re.sub(r"\s+", " ", token)
    return token


def parse_raw_skills(raw_skills: str) -> List[str]:
    """
    Split a raw, messy skills string into normalized tokens.

    Example:
        "DATA MODELING;excel;tableau, Statistics ,power bi"
        -> ["data modeling", "excel", "tableau", "statistics", "power bi"]
    """
    if not raw_skills or not isinstance(raw_skills, str):
        return []

    tokens = _SEPARATOR_PATTERN.split(raw_skills)
    normalized = [_normalize_token(t) for t in tokens if t.strip()]
    # Deduplicate while preserving order
    seen = set()
    result = []
    for t in normalized:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


def standardize_skills(raw_skills: str) -> Tuple[List[str], List[str]]:
    """
    Convert a raw skills string into (matched_skills, other_skills).

    matched_skills: tokens successfully mapped to the master taxonomy
    other_skills:   tokens that could not be matched (kept for visibility,
                     not used in aggregate "top skills" reporting since they
                     are not standardized)
    """
    tokens = parse_raw_skills(raw_skills)
    matched, other = [], []

    for token in tokens:
        canonical = ALIAS_MAP.get(token, token)
        if canonical in MASTER_SKILLS:
            if canonical not in matched:
                matched.append(canonical)
        else:
            # Try substring match (e.g. "python3" contains "python")
            hit = next((m for m in MASTER_SKILLS if m in canonical), None)
            if hit and hit not in matched:
                matched.append(hit)
            elif not hit:
                other.append(token)

    return matched, other


def skills_to_string(skills: List[str]) -> str:
    """Join a clean skills list back into a single comma-separated string
    for storage in a Delta column (arrays are also fine in Delta, but a
    string representation is convenient for TF-IDF vectorization later)."""
    return ", ".join(sorted(skills))
