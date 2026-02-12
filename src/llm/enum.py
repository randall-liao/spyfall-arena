"""Enum definitions for LLM clients."""

from enum import StrEnum, auto


class LLMClientType(StrEnum):
    """Supported LLM types."""

    OPEN_ROUTER = auto()
    GOOGLE_AI_STUDIO = auto()
