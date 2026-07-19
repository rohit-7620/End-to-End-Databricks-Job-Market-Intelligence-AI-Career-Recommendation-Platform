"""
Unit tests for src/recommender.py

Run with:
    pytest tests/test_recommender.py -v
"""

import pandas as pd
import pytest

from src.recommender import JobRecommender, CandidateProfile, build_candidate_profile


@pytest.fixture
def sample_jobs():
    return pd.DataFrame([
        {"job_id": "1", "standardized_title": "Data Engineer", "company": "Acme",
         "location": "Pune, India", "experience_level": "Mid Level",
         "salary_annual_inr": 1200000, "clean_skills": "python, sql, spark, airflow"},
        {"job_id": "2", "standardized_title": "Data Scientist", "company": "Beta",
         "location": "Remote - India", "experience_level": "Mid Level",
         "salary_annual_inr": 1400000, "clean_skills": "python, machine learning, statistics"},
        {"job_id": "3", "standardized_title": "Data Engineer", "company": "Gamma",
         "location": "Bengaluru, India", "experience_level": "Senior Level",
         "salary_annual_inr": 2000000, "clean_skills": "python, sql, databricks, delta lake"},
    ])


def test_recommender_returns_top_n(sample_jobs):
    rec = JobRecommender(sample_jobs)
    profile = CandidateProfile(skills=["python", "sql", "spark"], preferred_role="Data Engineer")
    results = rec.recommend(profile, top_n=2)
    assert len(results) == 2


def test_recommender_ranks_best_match_first(sample_jobs):
    rec = JobRecommender(sample_jobs)
    # This candidate's skills exactly match job_id "1"
    profile = CandidateProfile(skills=["python", "sql", "spark", "airflow"],
                                preferred_role="Data Engineer")
    results = rec.recommend(profile, top_n=3)
    assert results.iloc[0]["job_id"] == "1"
    assert results.iloc[0]["match_score"] > results.iloc[1]["match_score"]


def test_recommender_computes_matching_and_missing_skills(sample_jobs):
    rec = JobRecommender(sample_jobs)
    profile = CandidateProfile(skills=["python", "sql"], preferred_role="Data Engineer")
    results = rec.recommend(profile, top_n=1)
    top = results.iloc[0]
    assert "python" in top["matching_skills"]
    assert "sql" in top["matching_skills"]
    assert isinstance(top["missing_skills"], list)


def test_build_candidate_profile_standardizes_skills():
    profile = build_candidate_profile("PYTHON, Sql, ML", preferred_role="Data Scientist")
    assert "python" in profile.skills
    assert "sql" in profile.skills
    assert "machine learning" in profile.skills


def test_candidate_profile_to_document_includes_all_fields():
    profile = CandidateProfile(
        skills=["python", "sql"],
        preferred_role="Data Engineer",
        experience_level="Mid Level",
        preferred_location="Pune, India",
    )
    doc = profile.to_document()
    assert "python" in doc
    assert "data engineer" in doc
    assert "mid level" in doc
    assert "pune, india" in doc
