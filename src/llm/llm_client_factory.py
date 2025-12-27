from llm.enum import LLMClientType
from loguru import logger

from config.api_key_manager import ApiKeyManager
from llm.base_client import BaseLLMClient
from llm.gemini_client import GeminiClient
from llm.openai_client import OpenAIClient
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config.config_schema import GameConfig


class LLMClientFactory:
    """A factory for creating LLM clients."""

    def __init__(self, api_key_manager: ApiKeyManager, config: "GameConfig" = None):
        self.api_key_manager = api_key_manager
        self.config = config
        self.rate_limiter = None

        if self.config and self.config.rate_limit.enabled:
            from llm.rate_limiter import TokenBucketLimiter

            self.rate_limiter = TokenBucketLimiter(
                requests_per_minute=self.config.rate_limit.requests_per_minute,
                burst_limit=self.config.rate_limit.burst_limit,
            )

    def create_client(
        self,
        model_name: str,
        temperature: float = 0.7,
        client_type: LLMClientType | None = None,
    ) -> BaseLLMClient:
        """
        Factory method to create an LLM client.
        Supports OpenRouter and Google Gemini.
        """
        logger.debug(
            f"Creating LLM client for model: {model_name} (temp={temperature})"
        )
        if (
            model_name.lower().startswith("gemini")
            or model_name.lower().startswith("models/gemini")
            or client_type == LLMClientType.GOOGLE_AI_STUDIO
        ):
            api_key = self.api_key_manager.get_google_api_key()
            return GeminiClient(
                model_name=model_name,
                api_key=api_key,
                temperature=temperature,
                rate_limiter=self.rate_limiter,
            )
        else:
            api_key = self.api_key_manager.get_api_key()
            return OpenAIClient(
                model_name=model_name,
                api_key=api_key,
                temperature=temperature,
                rate_limiter=self.rate_limiter,
            )
