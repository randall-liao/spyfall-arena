from loguru import logger

from config.api_key_manager import ApiKeyManager
from config.config_schema import LLMProvider
from llm.base_client import BaseLLMClient
from llm.gemini_client import GeminiClient
from llm.openai_client import OpenAIClient


class LLMClientFactory:
    """A factory for creating LLM clients."""

    def __init__(self, api_key_manager: ApiKeyManager):
        self.api_key_manager = api_key_manager

    def create_client(
        self,
        model_name: str,
        provider: LLMProvider,
        temperature: float = 0.7,
    ) -> BaseLLMClient:
        """
        Factory method to create an LLM client.
        Supports OpenRouter and Google Gemini.
        """
        logger.debug(
            f"Creating LLM client for model: {model_name} (provider={provider}, temp={temperature})"
        )

        if provider == LLMProvider.GOOGLE_AI_STUDIO:
            api_key = self.api_key_manager.get_google_api_key()
            return GeminiClient(
                model_name=model_name,
                api_key=api_key,
                temperature=temperature,
            )
        elif provider == LLMProvider.OPEN_ROUTER:
            api_key = self.api_key_manager.get_api_key()
            return OpenAIClient(
                model_name=model_name,
                api_key=api_key,
                temperature=temperature,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
