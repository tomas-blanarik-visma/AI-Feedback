"""Pydantic models for feedback report data."""

from pydantic import BaseModel, Field


# Assessment area names as they appear in the template
TECHNICAL_AREAS = [
    "C# Basic",
    "C# Intermediate",
    "C# Advanced",
    "DBs relational",
    "DBs no sql",
    "Security",
    "Cloud",
    "Personal projects",
    "Last work project",
    "DevOps",
    "Web development",
    "Web SPA - Angular",
]

NON_TECHNICAL_AREAS = [
    "Potential & Motivation a.k.a Drive",
    "Communication",
    "Self impression",
]

OVERALL_LEVELS = ["Junior", "Medior", "Senior", "Lead"]

PERSONAL_ASSESSMENT_AREAS: list[str] = []


class AreaScore(BaseModel):
    """Score and comment for a single assessment area."""

    name: str = Field(description="Name of the assessment area")
    score: int | None = Field(
        default=None,
        description="Score from 1 (worst) to 5 (best), or None for N/A",
    )
    comment: str = Field(description="Brief comment explaining the score")

    @property
    def display_score(self) -> str:
        """Return 'N/A' or the score as string."""
        return "N/A" if self.score is None else str(self.score)


class FeedbackReport(BaseModel):
    """Complete feedback report with all assessment areas."""

    candidate_name: str = Field(description="Name of the candidate")
    technical_scores: list[AreaScore] = Field(
        description="Scores for technical assessment areas"
    )
    non_technical_scores: list[AreaScore] = Field(
        description="Scores for non-technical assessment areas"
    )
    personal_assessment_scores: list[AreaScore] = Field(
        default_factory=list,
        description="Scores for personal assessment areas",
    )
    overall_level: str = Field(
        description="Overall level: Junior, Medior, Senior, or Lead"
    )
    overall_comment: str = Field(description="Overall assessment summary")
    ai_evaluation: str = Field(
        default="",
        description="AI meta-evaluation of the feedback",
    )
