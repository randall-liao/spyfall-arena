from llm.enum import LLMClientType
from loguru import logger

from config.api_key_manager import ApiKeyManager
from config.config_schema import LLMProvider
from typing import Any, Dict, Optional, TYPE_CHECKING

from llm.base_client import BaseLLMClient
from llm.gemini_client import GeminiClient
from llm.openai_client import OpenAIClient

if TYPE_CHECKING:
    from config.config_schema import GameConfig


class LLMClientFactory:
    """
    Abstracts the creation of LLM clients.

    Implements 'Req 4.2: LLM Player Management', allowing the system to
    support multiple models from different providers (OpenAI, Google, etc.)
    interchangeably.
    """

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
        provider: LLMProvider,
        temperature: float = 0.7,
        client_type: LLMClientType | None = None,
        reasoning_config: Optional[Dict[str, Any]] = None,
    ) -> BaseLLMClient:
        """
        Instantiates the appropriate LLM client based on provider and configuration.

        Handles:
        - Provider selection (Google vs OpenRouter).
        - API key retrieval via ApiKeyManager.
        - Rate limiter injection (Req 6 - optional extension for stability).
        - Retry configuration setup (Req 7: Error Handling & Stability).
        """
        logger.debug(
            f"Creating LLM client for model: {model_name} (provider={provider}, temp={temperature})"
        )

        max_retries = 2
        retry_min_wait = 1.0
        retry_max_wait = 10.0

        if self.config:
            if hasattr(self.config, "llm") and self.config.llm:
                max_retries = self.config.llm.max_retries
                retry_min_wait = self.config.llm.retry_min_wait
                retry_max_wait = self.config.llm.retry_max_wait

        # Heuristic detection for provider is retained for backward compatibility,
        # but explicit 'provider' argument is preferred.
        if provider == LLMProvider.GOOGLE_AI_STUDIO or (
            provider is None and (
                model_name.lower().startswith("gemini")
                or model_name.lower().startswith("models/gemini")
                or model_name.lower().startswith("gemma")
                or model_name.lower().startswith("models/gemma")
                or client_type == LLMClientType.GOOGLE_AI_STUDIO
            )
        ):
            api_key = self.api_key_manager.get_google_api_key()
            return GeminiClient(
                model_name=model_name,
                api_key=api_key,
                temperature=temperature,
                rate_limiter=self.rate_limiter,
                reasoning_config=reasoning_config,
                max_retries=max_retries,
                retry_min_wait=retry_min_wait,
                retry_max_wait=retry_max_wait,
            )
        elif provider == LLMProvider.OPEN_ROUTER or provider is None:
            api_key = self.api_key_manager.get_api_key()
            return OpenAIClient(
                model_name=model_name,
                api_key=api_key,
                temperature=temperature,
                rate_limiter=self.rate_limiter,
                reasoning_config=reasoning_config,
                max_retries=max_retries,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
