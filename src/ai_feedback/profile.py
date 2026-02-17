"""Configuration profile for feedback report structure."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from .models import NON_TECHNICAL_AREAS, OVERALL_LEVELS, TECHNICAL_AREAS


class FeedbackProfile(BaseModel):
    """Configuration for assessment areas and overall levels."""

    technical: list[str] = Field(description="Technical assessment areas")
    non_technical: list[str] = Field(description="Non-technical assessment areas")
    personal_assessment: list[str] = Field(
        default_factory=list,
        description="Personal assessment areas",
    )
    overall_levels: list[str] = Field(description="Valid overall levels")


def _default_profile() -> FeedbackProfile:
    """Return built-in defaults (no personal assessment when no config exists)."""
    return FeedbackProfile(
        technical=TECHNICAL_AREAS,
        non_technical=NON_TECHNICAL_AREAS,
        personal_assessment=[],
        overall_levels=OVERALL_LEVELS,
    )


def load_profile(path: Path | None = None) -> FeedbackProfile:
    """
    Load feedback profile from YAML file.

    If path is None, look for feedback-config.yaml in the current directory.
    If not found, return built-in defaults (without personal assessment).
    """
    if path is None:
        path = Path.cwd() / "feedback-config.yaml"

    if not path.exists():
        return _default_profile()

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return _default_profile()

    if not isinstance(data, dict):
        return _default_profile()

    return FeedbackProfile(
        technical=data.get("technical", TECHNICAL_AREAS),
        non_technical=data.get("non_technical", NON_TECHNICAL_AREAS),
        personal_assessment=data.get("personal_assessment", []),
        overall_levels=data.get("overall_levels", OVERALL_LEVELS),
    )
