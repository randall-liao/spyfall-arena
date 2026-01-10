"""Enum definitions for LLM clients."""

from enum import auto
from enum import StrEnum


class LLMClientType(StrEnum):
    """Supported LLM types."""

    OPEN_ROUTER = auto()
    GOOGLE_AI_STUDIO = auto()
