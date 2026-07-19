"""
data_quality.py
-----------------
Lightweight, dependency-free data-quality checks used across the Bronze and
Silver notebooks. Returns a structured report (list of dicts) rather than
raising exceptions immediately, so a notebook can log every failed check and
decide whether to halt the pipeline or just warn.

Usage:
    from src.data_quality import run_dq_checks
    report = run_dq_checks(df, stage="silver")
    for check in report:
        print(check)
    assert all(c["passed"] for c in report if c["severity"] == "error")
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def _check(name, passed, severity, details):
    return {"check": name, "passed": bool(passed), "severity": severity, "details": details}


def check_not_empty(df: DataFrame) -> dict:
    count = df.count()
    return _check("row_count_not_zero", count > 0, "error", f"row_count={count}")


def check_no_null_business_keys(df: DataFrame, key_cols=("job_id",)) -> dict:
    null_counts = {}
    passed = True
    for c in key_cols:
        if c in df.columns:
            n = df.filter(F.col(c).isNull()).count()
            null_counts[c] = n
            if n > 0:
                passed = False
    return _check("no_null_business_keys", passed, "error", null_counts)


def check_no_duplicate_ids(df: DataFrame, id_col: str = "job_id") -> dict:
    if id_col not in df.columns:
        return _check("no_duplicate_ids", True, "warning", f"{id_col} not present, skipped")
    total = df.count()
    distinct = df.select(id_col).distinct().count()
    dup_count = total - distinct
    return _check("no_duplicate_ids", dup_count == 0, "warning",
                  f"total={total}, distinct={distinct}, duplicates={dup_count}")


def check_salary_within_bounds(df: DataFrame, col: str = "salary_annual_inr",
                                min_val: float = 100000, max_val: float = 10000000) -> dict:
    if col not in df.columns:
        return _check("salary_within_bounds", True, "warning", f"{col} not present, skipped")
    out_of_bounds = df.filter(
        F.col(col).isNotNull() & ((F.col(col) < min_val) | (F.col(col) > max_val))
    ).count()
    return _check("salary_within_bounds", out_of_bounds == 0, "warning",
                  f"out_of_bounds_rows={out_of_bounds}")


def check_valid_dates(df: DataFrame, col: str = "posting_date_parsed") -> dict:
    if col not in df.columns:
        return _check("valid_posting_dates", True, "warning", f"{col} not present, skipped")
    null_dates = df.filter(F.col(col).isNull()).count()
    total = df.count()
    ratio = null_dates / total if total else 0
    # Warn if more than 5% of dates failed to parse
    return _check("valid_posting_dates", ratio <= 0.05, "warning",
                  f"unparsed={null_dates}/{total} ({ratio:.2%})")


def check_known_standardized_title(df: DataFrame, col: str = "standardized_title",
                                    valid_roles=None) -> dict:
    if col not in df.columns:
        return _check("known_standardized_title", True, "warning", f"{col} not present, skipped")
    if valid_roles is None:
        valid_roles = [
            "Data Engineer", "Data Scientist", "Data Analyst",
            "Machine Learning Engineer", "AI Engineer", "Databricks Developer",
            "Business Intelligence Analyst", "Analytics Engineer", "Big Data Engineer",
        ]
    unknown_count = df.filter(~F.col(col).isin(valid_roles)).count()
    total = df.count()
    ratio = unknown_count / total if total else 0
    return _check("known_standardized_title", ratio <= 0.10, "warning",
                  f"unmapped={unknown_count}/{total} ({ratio:.2%})")


def run_dq_checks(df: DataFrame, stage: str = "bronze") -> list:
    """
    Run the standard suite of DQ checks appropriate for a given pipeline
    stage and return a list of check-result dicts.
    """
    checks = [
        check_not_empty(df),
        check_no_null_business_keys(df),
        check_no_duplicate_ids(df),
    ]

    if stage == "silver":
        checks.extend([
            check_salary_within_bounds(df),
            check_valid_dates(df),
            check_known_standardized_title(df),
        ])

    return checks


def assert_no_critical_failures(report: list) -> None:
    """Raise if any 'error' severity check failed. 'warning' failures are logged only."""
    failures = [c for c in report if c["severity"] == "error" and not c["passed"]]
    if failures:
        raise ValueError(f"Critical data quality checks failed: {failures}")
