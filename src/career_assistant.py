"""
career_assistant.py
---------------------
The "AI Career Assistant" feature.

Given a candidate's current skills and a target role, this module:
  1. Computes market demand for skills within that target role (from the
     Gold "skills required for each role" table).
  2. Identifies which in-demand skills the candidate is missing.
  3. Ranks missing skills by importance (= how frequently that skill appears
     in postings for the target role -- a simple, transparent proxy for
     "how much the market wants this").
  4. Produces a learning roadmap (ordered list with rationale).

This works entirely offline/rule-based by default (no API key required),
satisfying the "optional AI" requirement. If `use_llm=True` and an API key
is configured, `generate_llm_narrative()` will additionally call the
Anthropic API to turn the structured roadmap into a friendly, prose-style
explanation. The structured analysis is always computed locally first --
the LLM call, if enabled, only reformats it into nicer prose. This means
the LLM can never invent skills or numbers that didn't come from the data.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional

import pandas as pd

from src.skill_extractor import standardize_skills


@dataclass
class SkillGapResult:
    target_role: str
    candidate_skills: List[str]
    market_top_skills: List[Dict]      # [{"skill": "python", "demand_pct": 82.0}, ...]
    matching_skills: List[str]
    missing_skills_ranked: List[Dict]  # [{"skill": "airflow", "demand_pct": 45.0, "rank": 1}, ...]
    coverage_score: float              # % of top market skills the candidate already has


def compute_role_skill_demand(gold_jobs_df: pd.DataFrame, target_role: str,
                               skills_col: str = "clean_skills",
                               role_col: str = "standardized_title") -> List[Dict]:
    """
    Compute the % of postings for `target_role` that mention each skill,
    sorted descending. This is the "market demand" signal the rest of the
    assistant is built on.
    """
    role_jobs = gold_jobs_df[gold_jobs_df[role_col] == target_role]
    total = len(role_jobs)
    if total == 0:
        return []

    skill_counts: Dict[str, int] = {}
    for skills in role_jobs[skills_col]:
        if isinstance(skills, str):
            skill_list = [s.strip() for s in skills.split(",") if s.strip()]
        else:
            skill_list = skills or []
        for s in set(skill_list):  # count each skill once per posting
            skill_counts[s] = skill_counts.get(s, 0) + 1

    ranked = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"skill": s, "demand_pct": round(100.0 * c / total, 1)} for s, c in ranked]


def analyze_skill_gap(gold_jobs_df: pd.DataFrame, candidate_skills_raw: str,
                       target_role: str, top_k_market_skills: int = 15) -> SkillGapResult:
    """
    Core rule-based skill-gap analysis. No API key needed.
    """
    matched, other = standardize_skills(candidate_skills_raw)
    candidate_skills = set(s.lower() for s in (matched + other))

    market_demand = compute_role_skill_demand(gold_jobs_df, target_role)
    top_market_skills = market_demand[:top_k_market_skills]

    matching = [d["skill"] for d in top_market_skills if d["skill"] in candidate_skills]
    missing = [d for d in top_market_skills if d["skill"] not in candidate_skills]

    # Rank missing skills by demand (already sorted descending from compute_role_skill_demand)
    missing_ranked = [
        {"rank": i + 1, "skill": d["skill"], "demand_pct": d["demand_pct"]}
        for i, d in enumerate(missing)
    ]

    coverage_score = round(
        100.0 * len(matching) / len(top_market_skills), 1
    ) if top_market_skills else 0.0

    return SkillGapResult(
        target_role=target_role,
        candidate_skills=sorted(candidate_skills),
        market_top_skills=top_market_skills,
        matching_skills=sorted(matching),
        missing_skills_ranked=missing_ranked,
        coverage_score=coverage_score,
    )


SKILL_RATIONALE = {
    "python": "The de-facto language for data engineering and ML scripting; nearly universal requirement.",
    "sql": "Core skill for querying and transforming relational data; expected in almost every data role.",
    "pyspark": "Enables distributed data processing at scale, especially within Databricks environments.",
    "spark": "Underlying distributed compute engine behind most modern big-data pipelines.",
    "databricks": "The platform itself -- direct experience signals you can work in the target company's stack.",
    "delta lake": "Adds ACID transactions and time travel to data lakes; standard in Lakehouse architectures.",
    "airflow": "Widely used for orchestrating multi-step data pipelines in production.",
    "machine learning": "Foundational for building predictive models and is central to Data Scientist/ML roles.",
    "mlflow": "Industry-standard tool for experiment tracking and model lifecycle management.",
    "docker": "Containerization is expected for reproducible ML/data deployments.",
    "aws": "Most common cloud provider referenced in job postings; hands-on cloud experience is highly valued.",
    "tableau": "Leading BI visualization tool for communicating insights to stakeholders.",
    "power bi": "Microsoft's BI tool, heavily used in enterprise reporting.",
}


def default_rationale(skill: str) -> str:
    return SKILL_RATIONALE.get(
        skill,
        f"Frequently requested in postings for this role -- demonstrates alignment with current market demand."
    )


def build_learning_roadmap(gap_result: SkillGapResult, max_skills: int = 5) -> List[Dict]:
    """
    Turn the ranked missing-skills list into a step-by-step roadmap with a
    rationale for each skill (why the market wants it).
    """
    roadmap = []
    for item in gap_result.missing_skills_ranked[:max_skills]:
        roadmap.append({
            "step": item["rank"],
            "skill": item["skill"],
            "market_demand_pct": item["demand_pct"],
            "why_it_matters": default_rationale(item["skill"]),
        })
    return roadmap


def format_report_text(gap_result: SkillGapResult, roadmap: List[Dict]) -> str:
    """Render the analysis as clean, readable plain text (used when the LLM
    narrative is disabled -- i.e. the project's default, no-API-key mode)."""
    lines = []
    lines.append(f"=== Career Gap Analysis: {gap_result.target_role} ===\n")
    lines.append(f"Your current skills: {', '.join(gap_result.candidate_skills) or 'None provided'}")
    lines.append(f"Market coverage score: {gap_result.coverage_score}% "
                 f"of the top skills required for this role\n")

    lines.append("Skills you already have that the market wants:")
    if gap_result.matching_skills:
        for s in gap_result.matching_skills:
            lines.append(f"  - {s}")
    else:
        lines.append("  (none of the top market skills matched yet)")

    lines.append("\nRecommended learning roadmap (highest impact first):")
    for step in roadmap:
        lines.append(
            f"  {step['step']}. {step['skill']} "
            f"(appears in {step['market_demand_pct']}% of {gap_result.target_role} postings)"
        )
        lines.append(f"     Why: {step['why_it_matters']}")

    return "\n".join(lines)


def generate_llm_narrative(gap_result: SkillGapResult, roadmap: List[Dict],
                           api_key: Optional[str] = None,
                           model: str = "claude-sonnet-4-5") -> str:
    """
    OPTIONAL enhancement: turn the structured, locally-computed analysis into
    friendlier prose using the Anthropic API. This function is never called
    unless the notebook explicitly enables it AND a valid API key is
    available -- the project fully works without this.

    The LLM is only asked to rephrase data we already computed; it is
    instructed not to add new skills or numbers, which keeps the assistant
    grounded and avoids hallucinated claims.
    """
    try:
        import anthropic
    except ImportError:
        return ("[AI narrative unavailable: 'anthropic' package not installed. "
                "Falling back to structured report below.]\n\n" +
                format_report_text(gap_result, roadmap))

    if not api_key:
        return ("[AI narrative disabled: no API key provided. "
                "Falling back to structured report below.]\n\n" +
                format_report_text(gap_result, roadmap))

    client = anthropic.Anthropic(api_key=api_key)
    structured_summary = format_report_text(gap_result, roadmap)

    prompt = (
        "You are a friendly career coach. Rewrite the following structured "
        "skill-gap report as warm, encouraging, well-organized prose for the "
        "candidate. Do NOT invent any new skills, percentages, or facts -- "
        "only rephrase what is given below.\n\n"
        f"{structured_summary}"
    )

    response = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if hasattr(block, "text"))
