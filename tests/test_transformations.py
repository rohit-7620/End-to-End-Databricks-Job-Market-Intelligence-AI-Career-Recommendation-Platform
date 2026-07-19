"""
Unit tests for src/transformations.py

Run with:
    pytest tests/test_transformations.py -v
"""

import pytest
from pyspark.sql import SparkSession

from src.transformations import (
    standardize_job_titles, clean_company_name, clean_location,
    normalize_experience_level, normalize_salary, parse_posting_date,
    normalize_employment_type, deduplicate_records, drop_fully_null_rows,
)


@pytest.fixture(scope="module")
def spark():
    spark = (SparkSession.builder
             .master("local[2]")
             .appName("pytest-transformations")
             .getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    yield spark
    spark.stop()


def test_standardize_job_titles(spark):
    df = spark.createDataFrame(
        [("Sr. Data Engineer",), ("data  scientist",), ("BI Analyst",)],
        ["job_title"],
    )
    result = standardize_job_titles(df).select("standardized_title").collect()
    values = [r["standardized_title"] for r in result]
    assert values == ["Data Engineer", "Data Scientist", "Business Intelligence Analyst"]


def test_clean_company_name(spark):
    df = spark.createDataFrame([("  acme   corp  ",), (None,)], ["company"])
    result = clean_company_name(df).select("company").collect()
    assert result[0]["company"] == "Acme Corp"
    assert result[1]["company"] is None


def test_clean_location_aliases(spark):
    df = spark.createDataFrame(
        [("Bangalore, India",), ("PUNE",), (None,), ("remote india",)],
        ["location"],
    )
    result = [r["location"] for r in clean_location(df).select("location").collect()]
    assert result[0] == "Bengaluru, India"
    assert result[1] == "Pune, India"
    assert result[2] == "Unknown"
    assert result[3] == "Remote - India"


def test_normalize_experience_level(spark):
    df = spark.createDataFrame(
        [("senior",), ("Entry Level",), ("mid-level",), (None,)],
        ["experience_level"],
    )
    result = [r["experience_level"] for r in
              normalize_experience_level(df).select("experience_level").collect()]
    assert result == ["Senior Level", "Entry Level", "Mid Level", "Not Specified"]


def test_normalize_salary_range(spark):
    df = spark.createDataFrame(
        [("INR 900,000 - 1,800,000",), ("900K - 1800K INR",), ("Competitive",), (None,)],
        ["salary"],
    )
    result = [r["salary_annual_inr"] for r in
              normalize_salary(df).select("salary_annual_inr").collect()]
    assert result[0] == 1350000.0
    assert result[1] == 1350000.0
    assert result[2] is None
    assert result[3] is None


def test_parse_posting_date_multiple_formats(spark):
    df = spark.createDataFrame(
        [("2025-01-15",), ("15/01/2025",), ("01-15-2025",), ("15 Jan 2025",)],
        ["posting_date"],
    )
    result = [str(r["posting_date_parsed"]) for r in
              parse_posting_date(df).select("posting_date_parsed").collect()]
    assert all(r == "2025-01-15" for r in result)


def test_normalize_employment_type(spark):
    df = spark.createDataFrame(
        [("Full Time",), ("part-time",), ("Contract",), (None,)],
        ["employment_type"],
    )
    result = [r["employment_type"] for r in
              normalize_employment_type(df).select("employment_type").collect()]
    assert result == ["Full-time", "Part-time", "Contract", "Not Specified"]


def test_deduplicate_records(spark):
    df = spark.createDataFrame(
        [
            ("Data Engineer", "Acme", "Pune", "2025-01-01"),
            ("Data Engineer", "Acme", "Pune", "2025-01-01"),  # exact duplicate
            ("Data Scientist", "Beta", "Mumbai", "2025-01-02"),
        ],
        ["job_title", "company", "location", "posting_date"],
    )
    result = deduplicate_records(df)
    assert result.count() == 2


def test_drop_fully_null_rows(spark):
    df = spark.createDataFrame(
        [("Data Engineer", "Acme"), (None, None), ("Data Scientist", "Beta")],
        ["job_title", "company"],
    )
    result = drop_fully_null_rows(df)
    assert result.count() == 2
