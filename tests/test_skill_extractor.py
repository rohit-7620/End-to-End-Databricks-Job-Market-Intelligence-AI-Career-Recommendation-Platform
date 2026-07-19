"""
Unit tests for src/skill_extractor.py

Run with:
    pytest tests/test_skill_extractor.py -v
"""

from src.skill_extractor import parse_raw_skills, standardize_skills, skills_to_string


def test_parse_raw_skills_handles_multiple_separators():
    assert parse_raw_skills("Python; SQL, Spark | Docker") == ["python", "sql", "spark", "docker"]


def test_parse_raw_skills_handles_none():
    assert parse_raw_skills(None) == []
    assert parse_raw_skills("") == []


def test_parse_raw_skills_deduplicates():
    result = parse_raw_skills("Python, python, PYTHON")
    assert result == ["python"]


def test_standardize_skills_matches_taxonomy():
    matched, other = standardize_skills("Python, SQL, Databricks")
    assert matched == ["python", "sql", "databricks"]
    assert other == []


def test_standardize_skills_handles_aliases():
    matched, other = standardize_skills("ML, k8s, sklearn")
    assert "machine learning" in matched
    assert "kubernetes" in matched
    assert "scikit-learn" in matched


def test_standardize_skills_keeps_unmatched_as_other():
    matched, other = standardize_skills("Python, Blockchain, SQL")
    assert "python" in matched
    assert "sql" in matched
    assert "blockchain" in other


def test_standardize_skills_handles_messy_casing_and_spacing():
    matched, other = standardize_skills("PYTHON ,  Sql,spark")
    assert matched == ["python", "sql", "spark"]


def test_skills_to_string_sorts_alphabetically():
    assert skills_to_string(["sql", "python", "aws"]) == "aws, python, sql"
