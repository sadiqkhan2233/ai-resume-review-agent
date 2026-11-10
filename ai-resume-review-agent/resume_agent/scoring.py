"""Transparent scoring helpers. Totals are calculated in Python, not by the AI."""
from typing import Dict, List, Optional

from .config import SCORE_RUBRIC
from .schemas import ResumeReview


def build_score_rows(review: ResumeReview) -> List[Dict]:
    """One row per rubric category with the score clamped to its allowed range."""
    rows = []
    for key, (label, max_points) in SCORE_RUBRIC.items():
        item = getattr(review.category_scores, key)
        score = max(0.0, min(float(item.score), float(max_points)))
        rows.append(
            {
                "key": key,
                "label": label,
                "score": round(score, 1),
                "max": max_points,
                "explanation": item.explanation,
            }
        )
    return rows


def overall_score(rows: List[Dict]) -> float:
    return round(sum(r["score"] for r in rows), 1)


def grade_label(score: float) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 55:
        return "Needs improvement"
    return "Needs major work"


def job_match(review: ResumeReview) -> Optional[Dict]:
    """Explainable match score = matched required skills / all required skills."""
    matched = [s.strip() for s in review.matching_skills if s.strip()]
    missing = [s.strip() for s in review.missing_skills if s.strip()]
    total = len(matched) + len(missing)
    if total == 0:
        return None
    percent = round(100 * len(matched) / total)
    return {
        "percent": percent,
        "matched": matched,
        "missing": missing,
        "formula": f"{len(matched)} matched skills / {total} skills required by the job = {percent}%",
    }
