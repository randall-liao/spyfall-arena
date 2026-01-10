from config.api_key_manager import ApiKeyManager
from llm.llm_client_factory import LLMClientFactory
from llm.base_llm_client import BaseLLMClient


MODEL_NAME = "gemini-flash-latest"


api_key_manager = ApiKeyManager()
client_factory = LLMClientFactory(api_key_manager)
gemini_client: BaseLLMClient = client_factory.create_client(
    model_name=MODEL_NAME,
    temperature=0.9,
)
