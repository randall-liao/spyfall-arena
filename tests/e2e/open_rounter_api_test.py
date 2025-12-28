"""
End-to-end tests for the OpenRouter API implementation.

This module contains tests that perform actual API calls to verify the OpenRouter
client and API key functionality. These tests should not be run in CI/CD environments.
"""

from config.api_key_manager import ApiKeyManager
from llm.base_client import BaseLLMClient
from llm.llm_client_factory import LLMClientFactory

api_key_manager: ApiKeyManager = ApiKeyManager()
client_factory: LLMClientFactory = LLMClientFactory(api_key_manager)
open_router_client: BaseLLMClient = client_factory.create_client(
    model_name="xiaomi/mimo-v2-flash:free",
    temperature=0.7,
    reasoning_config={
        "enabled": True,
    },
)


if __name__ == "__main__":
    response: str = open_router_client.generate_response("Hello", "Hello")
    print(response)
