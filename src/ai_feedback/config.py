"""Configuration for the AI feedback tool."""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ai_feedback.config")


def _mask_api_key(key: str) -> str:
    """Return masked API key (first 4 + last 4 chars) for logging."""
    if not key or len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def get_base_url() -> str | None:
    """Get the LLM API base URL. None means standard OpenAI."""
    value = os.getenv("LLM_BASE_URL") or None
    logger.debug("base_url=%s", value)
    return value


def get_api_key() -> str:
    """Get API key. When using a local server (e.g. LM Studio), returns placeholder."""
    key = os.getenv("OPENAI_API_KEY")
    if key:
        logger.debug("api_key=%s", _mask_api_key(key))
        return key
    if get_base_url():
        logger.debug("api_key=lm-studio (placeholder for local)")
        return "lm-studio"  # SDK needs non-empty string; LM Studio ignores it
    logger.debug("api_key=(none)")
    return ""


def get_model() -> str:
    """Get the model name to use."""
    model = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL")
    if model:
        logger.debug("model=%s", model)
        return model
    value = "local" if get_base_url() else "gpt-4o"
    logger.debug("model=%s (default)", value)
    return value


def get_temperature() -> float:
    """Get the temperature for LLM calls."""
    value = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    logger.debug("temperature=%s", value)
    return value
