

from llm.enum import LLMClientType
from llm.gemini_client import GeminiClient
from llm.llm_client_factory import LLMClientFactory
from config.api_key_manager import ApiKeyManager


api_key_manager: ApiKeyManager = ApiKeyManager()
client_factory: LLMClientFactory = LLMClientFactory(api_key_manager)
gemini_client: GeminiClient = client_factory.create_client(
    model_name="models/gemini-flash-lite-latest",
    client_type=LLMClientType.GOOGLE_AI_STUDIO,
    temperature=0.7,
)


if __name__ == "__main__":
    request_str: str = "Hello, how are you?"
    response: str = gemini_client.generate_response(request_str, request_str)
    print(response)
