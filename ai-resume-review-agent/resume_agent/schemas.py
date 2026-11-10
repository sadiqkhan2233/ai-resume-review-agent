"""Pydantic models that validate the AI's structured response."""
import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class CategoryScore(BaseModel):
    score: float = Field(..., description="Points awarded (must not exceed the category maximum).")
    explanation: str = Field(..., description="2-3 sentences justifying the score using resume evidence.")

    @field_validator("score", mode="before")
    @classmethod
    def _coerce_score(cls, value):
        # Accept things like "15", "15/20" or "15 points"
        if isinstance(value, str):
            match = re.search(r"-?\d+(\.\d+)?", value)
            if not match:
                raise ValueError("score must contain a number")
            return float(match.group())
        return value


class CategoryScores(BaseModel):
    skills_relevance: CategoryScore
    work_experience: CategoryScore
    education: CategoryScore
    ats_formatting: CategoryScore
    professional_summary: CategoryScore
    achievements: CategoryScore
    grammar_clarity: CategoryScore


class SectionFeedback(BaseModel):
    section: str = Field(..., description="Name of the resume area being reviewed.")
    status: str = Field(..., description="One of: Strong, Adequate, Weak, Missing.")
    feedback: str = Field(..., description="Specific, actionable feedback for this area.")


class BulletRewrite(BaseModel):
    original: str = Field(..., description="Exact weak bullet point copied from the resume.")
    improved: str = Field(..., description="Professional rewrite. Use [placeholders] for unknown facts.")
    note: str = Field("", description="Short reason for the change.")


class ResumeReview(BaseModel):
    candidate_name: Optional[str] = None
    target_role: str = ""
    category_scores: CategoryScores
    section_analysis: List[SectionFeedback] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    suggested_skills: List[str] = Field(default_factory=list)
    rewritten_bullets: List[BulletRewrite] = Field(default_factory=list)
    improved_summary: str = ""
    recommended_certifications: List[str] = Field(default_factory=list)
    education_suggestions: List[str] = Field(default_factory=list)
    experience_suggestions: List[str] = Field(default_factory=list)
    job_specific_recommendations: List[str] = Field(default_factory=list)
    action_plan: List[str] = Field(default_factory=list)
