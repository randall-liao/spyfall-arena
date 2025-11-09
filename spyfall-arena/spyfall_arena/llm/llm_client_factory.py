from spyfall_arena.llm.base_client import BaseLLMClient
from spyfall_arena.llm.openrouter_client import OpenRouterClient


class LLMClientFactory:
    """A Singleton factory for creating LLM clients."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_client(
        self,
        model_name: str,
        api_key: str,
        temperature: float = 0.7,
    ) -> BaseLLMClient:
        """
        Factory method to create an LLM client.
        Currently, it only supports OpenRouter.
        """
        # In the future, this could be extended to support other providers.
        return OpenRouterClient(
            model_name=model_name,
            api_key=api_key,
            temperature=temperature,
        )
