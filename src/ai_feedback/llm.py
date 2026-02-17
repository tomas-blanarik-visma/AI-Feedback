"""OpenAI integration for analyzing interview notes and generating scores."""

import json
import logging
import re

from openai import OpenAI

from .config import get_api_key, get_base_url, get_model, get_temperature

logger = logging.getLogger("ai_feedback.llm")
from .models import (
    FeedbackReport,
    NON_TECHNICAL_AREAS,
    OVERALL_LEVELS,
    TECHNICAL_AREAS,
)

SYSTEM_PROMPT = """You are an expert technical interviewer evaluating candidates. Your task is to analyze interview notes and produce structured feedback scores.

Scoring rubric (1 = worst, 5 = best):
- 1: No knowledge/demonstrated ability, major red flags
- 2: Limited knowledge, significant gaps, below expectations
- 3: Adequate knowledge, meets basic expectations, some gaps
- 4: Good knowledge, above average, minor gaps
- 5: Strong/excellent knowledge, exceeds expectations, no significant gaps

For each assessment area, provide a score (1-5) and a brief comment (1-2 sentences) explaining why you gave that score based on the interview notes. Be objective and cite specific evidence from the notes when possible.

For non-technical areas, infer scores from behavioral cues and personality observations in the notes:
- Potential & Motivation (Drive): willingness to learn, seeking challenges, career ambitions, enthusiasm
- Communication: how the candidate explained decisions, asked questions, responded to feedback, clarity
- Self impression: how they presented themselves, confidence, professionalism, personality descriptions

Only use null when there is absolutely no information to infer a score. Behavioral observations and personality descriptions count as evidence for non-technical areas.

You MUST return scores for ALL of these areas exactly as named:

Technical areas:
- C# Basic
- C# Intermediate
- C# Advanced
- DBs relational
- DBs no sql
- Security
- Cloud
- Personal projects
- Last work project
- DevOps
- Web development
- Web SPA - Angular

Non-technical areas:
- Potential & Motivation a.k.a Drive
- Communication
- Self impression

Also provide an overall_level (one of: Junior, Medior, Senior, Lead) and an overall_comment (2-4 sentences) summarizing the candidate's strengths, weaknesses, and hiring recommendation."""


AI_EVALUATION_PROMPT = """You are an expert interviewer coach. Given an interviewer's feedback on a candidate (both the raw notes and the structured assessment), provide a brief meta-evaluation (2-4 paragraphs) that:

1. Evaluates the quality and thoroughness of the interviewer's feedback
2. Identifies any areas that could have been explored more deeply
3. Provides concrete recommendations for the candidate's future development and growth path

Be constructive and specific. Write in plain text, no bullet points or JSON."""


def _format_report_for_evaluation(report: FeedbackReport) -> str:
    """Format a FeedbackReport as text for the AI evaluation prompt."""
    lines = [f"Candidate: {report.candidate_name}", f"Overall level: {report.overall_level}", f"Overall comment: {report.overall_comment}", "", "Technical scores:"]
    for s in report.technical_scores:
        lines.append(f"  - {s.name}: {s.display_score} - {s.comment}")
    lines.extend(["", "Non-technical scores:"])
    for s in report.non_technical_scores:
        lines.append(f"  - {s.name}: {s.display_score} - {s.comment}")
    return "\n".join(lines)


def generate_ai_evaluation(report: FeedbackReport, notes: str) -> str:
    """
    Generate an AI meta-evaluation of the interviewer's feedback.

    Args:
        report: The completed feedback report
        notes: Original interview notes

    Returns:
        Plain text evaluation with recommendations
    """
    api_key = get_api_key()
    base_url = get_base_url()
    if not base_url and not api_key:
        return ""

    client = OpenAI(api_key=api_key, base_url=base_url or None)
    report_text = _format_report_for_evaluation(report)

    user_prompt = f"""Interview notes:
---
{notes}
---

Structured assessment derived from the notes:
---
{report_text}
---

{AI_EVALUATION_PROMPT}"""

    logger.debug("Generating AI evaluation...")
    try:
        response = client.chat.completions.create(
            model=get_model(),
            temperature=get_temperature(),
            messages=[
                {"role": "system", "content": "You are an expert interviewer coach."},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        logger.debug("AI evaluation response: %s", content[:500] + "..." if len(content) > 500 else content)
        return content.strip()
    except Exception as e:
        logger.warning("AI evaluation failed: %s", e, exc_info=True)
        return ""


def _extract_json(text: str) -> str:
    """Extract JSON object from model output (handles markdown code blocks)."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if match:
        return match.group(1)
    match = re.search(r"(\{[\s\S]*\})", text)
    if match:
        return match.group(1)
    return text


def analyze_interview_notes(notes: str, candidate_name: str) -> FeedbackReport:
    """
    Analyze interview notes and return structured feedback with scores.

    Args:
        notes: Raw interview notes (free text)
        candidate_name: Name of the candidate

    Returns:
        FeedbackReport with scores and comments for all areas
    """
    api_key = get_api_key()
    base_url = get_base_url()
    if not base_url and not api_key:
        raise ValueError(
            "OPENAI_API_KEY not set. Set it in your environment or .env file. "
            "For LM Studio, set LLM_BASE_URL=http://localhost:1234/v1 instead."
        )

    client = OpenAI(api_key=api_key, base_url=base_url or None)

    user_prompt = f"""Candidate: {candidate_name}

Interview notes:
---
{notes}
---

Analyze these notes and return a JSON object with this exact structure:
{{
  "candidate_name": "{candidate_name}",
  "technical_scores": [
    {{"name": "<area name>", "score": <1-5 or null>, "comment": "<brief explanation>"}}
  ],
  "non_technical_scores": [
    {{"name": "<area name>", "score": <1-5 or null>, "comment": "<brief explanation>"}}
  ],
  "overall_level": "<Junior|Medior|Senior|Lead>",
  "overall_comment": "<2-4 sentence overall assessment>"
}}

Use score: null and comment: "Not evaluated/not enough data" when there is insufficient evidence. Include all 12 technical areas and all 3 non-technical areas in the exact order listed in the system prompt."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    model = get_model()
    temperature = get_temperature()
    kwargs: dict = {
        "model": model,
        "temperature": temperature,
        "messages": messages,
    }
    logger.debug(
        "LLM call: model=%s base_url=%s temperature=%s",
        model,
        base_url,
        temperature,
    )
    logger.debug("User prompt (truncated): %s...", user_prompt[:200])

    content: str
    if base_url:
        # Local models (LM Studio etc.) have inconsistent response_format support; rely on prompt
        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        logger.debug("Raw LLM response: %s", content[:500] + "..." if len(content) > 500 else content)
    else:
        try:
            response = client.chat.completions.create(
                **kwargs,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
            logger.debug("Raw LLM response: %s", content[:500] + "..." if len(content) > 500 else content)
        except Exception as e:
            logger.error("response_format failed, retrying without: %s", e)
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            logger.debug("Retry response: %s", content[:500] + "..." if len(content) > 500 else content)

    content = _extract_json(content)
    try:
        data = json.loads(content) if content else {}
    except json.JSONDecodeError as e:
        logger.warning("JSON parse failed: %s. Content: %s", e, content[:200])
        data = {}

    if not isinstance(data, dict):
        data = {}
        logger.warning("Parsed data is not a dict, using empty")

    logger.debug(
        "Parsed JSON keys=%s technical_count=%d non_technical_count=%d",
        list(data.keys()),
        len(data.get("technical_scores", [])),
        len(data.get("non_technical_scores", [])),
    )

    # Validate and ensure correct area names/order (use canonical names from template)
    def matches(resp_name: str, canonical: str) -> bool:
        def norm(s: str) -> str:
            return s.lower().strip().replace("a.k.a.", "aka").replace("a.k.a", "aka")

        return norm(resp_name) == norm(canonical)

    def parse_score(val: object) -> int | None:
        """Parse score from LLM response: int 1-5 or None for N/A."""
        if val is None:
            return None
        if isinstance(val, int) and 1 <= val <= 5:
            return val
        return None

    def parse_comment(val: object) -> str:
        """Parse comment from LLM response."""
        if isinstance(val, str):
            return val
        return "Not evaluated/not enough data"

    na_fallback = {"score": None, "comment": "Not evaluated/not enough data"}

    technical_scores = []
    for area in TECHNICAL_AREAS:
        found = next(
            (
                s
                for s in data.get("technical_scores", [])
                if matches(s.get("name", ""), area)
            ),
            None,
        )
        if found:
            technical_scores.append(
                {
                    "name": area,
                    "score": parse_score(found.get("score")),
                    "comment": parse_comment(found.get("comment")),
                }
            )
        else:
            logger.warning("Technical area '%s' missing from response, using N/A", area)
            technical_scores.append({"name": area, **na_fallback})

    non_technical_scores = []
    for area in NON_TECHNICAL_AREAS:
        found = next(
            (
                s
                for s in data.get("non_technical_scores", [])
                if matches(s.get("name", ""), area)
            ),
            None,
        )
        if found:
            non_technical_scores.append(
                {
                    "name": area,
                    "score": parse_score(found.get("score")),
                    "comment": parse_comment(found.get("comment")),
                }
            )
        else:
            logger.warning("Non-technical area '%s' missing from response, using N/A", area)
            non_technical_scores.append({"name": area, **na_fallback})

    overall_level = data.get("overall_level", "Medior")
    if overall_level not in OVERALL_LEVELS:
        overall_level = "Medior"

    report = FeedbackReport(
        candidate_name=data.get("candidate_name", candidate_name),
        technical_scores=technical_scores,
        non_technical_scores=non_technical_scores,
        overall_level=overall_level,
        overall_comment=data.get(
            "overall_comment", "See interview notes for details."
        ),
    )

    ai_evaluation = generate_ai_evaluation(report, notes)
    return report.model_copy(update={"ai_evaluation": ai_evaluation})
