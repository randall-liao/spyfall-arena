from config.api_key_manager import ApiKeyManager
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
        temperature: float = 0.7,
    ) -> BaseLLMClient:
        """
        Factory method to create an LLM client.
        Supports OpenRouter and Google Gemini.
        """
        if model_name.lower().startswith("gemini"):
            api_key = self.api_key_manager.get_google_api_key()
            return GeminiClient(
                model_name=model_name,
                api_key=api_key,
                temperature=temperature,
            )
        else:
            api_key = self.api_key_manager.get_api_key()
            return OpenAIClient(
                model_name=model_name,
                api_key=api_key,
                temperature=temperature,
            )
