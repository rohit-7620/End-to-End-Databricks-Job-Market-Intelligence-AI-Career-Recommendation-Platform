"""
recommender.py
----------------
A simple, explainable job-recommendation engine.

Approach: represent each job posting's skill set (plus role and location) as
a text "document", vectorize all documents with TF-IDF, and compute cosine
similarity between a candidate's profile document and every job document.
Return the top-N most similar jobs as recommendations, along with a
human-readable match score and the specific overlapping skills (for
explainability -- an important thing to call out in interviews: this model
is fully interpretable, unlike a black-box embedding model).

This module is intentionally framework-agnostic (pure pandas/scikit-learn)
so it can be:
  - called directly from a Databricks notebook after collecting a Gold
    table to a pandas DataFrame,
  - unit tested easily with pytest,
  - wrapped as an MLflow pyfunc model for registration.
"""

from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.skill_extractor import standardize_skills


@dataclass
class CandidateProfile:
    skills: List[str]
    preferred_role: Optional[str] = None
    experience_level: Optional[str] = None
    preferred_location: Optional[str] = None

    def to_document(self) -> str:
        """Convert the profile into a single text blob for vectorization."""
        parts = list(self.skills)
        if self.preferred_role:
            parts.append(self.preferred_role)
        if self.experience_level:
            parts.append(self.experience_level)
        if self.preferred_location:
            parts.append(self.preferred_location)
        return " ".join(parts).lower()


class JobRecommender:
    """
    TF-IDF + cosine-similarity job recommender.

    Parameters
    ----------
    jobs_df : pd.DataFrame
        Must contain at minimum: job_id, standardized_title, location,
        experience_level, and a clean skills column (list or comma-separated
        string) - see `skills_col`.
    skills_col : str
        Name of the column holding the job's cleaned skill list/string.
    """

    def __init__(self, jobs_df: pd.DataFrame, skills_col: str = "clean_skills"):
        self.jobs_df = jobs_df.reset_index(drop=True).copy()
        self.skills_col = skills_col
        self._build_documents()
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.job_matrix = self.vectorizer.fit_transform(self.jobs_df["_document"])

    def _row_to_document(self, row) -> str:
        skills = row[self.skills_col]
        if isinstance(skills, list):
            skills_text = " ".join(skills)
        else:
            skills_text = str(skills) if pd.notna(skills) else ""
        role = str(row.get("standardized_title", "") or "")
        location = str(row.get("location", "") or "")
        experience = str(row.get("experience_level", "") or "")
        # Repeat role text 2x so it carries slightly more TF-IDF weight than
        # a single incidental keyword match -- a simple, transparent boost.
        return f"{skills_text} {role} {role} {location} {experience}".lower()

    def _build_documents(self):
        self.jobs_df["_document"] = self.jobs_df.apply(self._row_to_document, axis=1)

    def recommend(self, candidate: CandidateProfile, top_n: int = 10) -> pd.DataFrame:
        """
        Return the top_n job recommendations for a candidate profile, with
        a match_score (0-100) and the list of overlapping skills for
        explainability.
        """
        candidate_vec = self.vectorizer.transform([candidate.to_document()])
        similarities = cosine_similarity(candidate_vec, self.job_matrix).flatten()

        results = self.jobs_df.copy()
        results["match_score"] = (similarities * 100).round(1)

        candidate_skill_set = set(s.lower() for s in candidate.skills)

        def overlap(row):
            job_skills = row[self.skills_col]
            if isinstance(job_skills, str):
                job_skills = [s.strip() for s in job_skills.split(",") if s.strip()]
            job_skill_set = set(s.lower() for s in (job_skills or []))
            return sorted(candidate_skill_set & job_skill_set)

        results["matching_skills"] = results.apply(overlap, axis=1)
        results["missing_skills"] = results.apply(
            lambda row: sorted(
                set(
                    (row[self.skills_col].split(", ") if isinstance(row[self.skills_col], str)
                     else row[self.skills_col] or [])
                ) - candidate_skill_set
            ),
            axis=1,
        )

        display_cols = [c for c in [
            "job_id", "standardized_title", "company", "location",
            "experience_level", "salary_annual_inr", "match_score",
            "matching_skills", "missing_skills",
        ] if c in results.columns]

        return (results
                .sort_values("match_score", ascending=False)
                .head(top_n)[display_cols]
                .reset_index(drop=True))


def build_candidate_profile(raw_skills_text: str, preferred_role: str = None,
                            experience_level: str = None,
                            preferred_location: str = None) -> CandidateProfile:
    """Convenience wrapper: parse free-text candidate skills through the same
    standardization pipeline used for job postings, so candidate and job
    skill vocabularies line up."""
    matched, other = standardize_skills(raw_skills_text)
    return CandidateProfile(
        skills=matched + other,
        preferred_role=preferred_role,
        experience_level=experience_level,
        preferred_location=preferred_location,
    )
