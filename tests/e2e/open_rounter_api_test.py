from config.api_key_manager import ApiKeyManager
from llm.base_client import BaseLLMClient
from llm.llm_client_factory import LLMClientFactory

api_key_manager: ApiKeyManager = ApiKeyManager()
client_factory: LLMClientFactory = LLMClientFactory(api_key_manager)
open_router_client: BaseLLMClient = client_factory.create_client(
    model_name="google/gemma-3-27b-it",
    temperature=0.7,
)



if __name__ == "__main__":
    '''
    This test will actually call the OpenRouter API to test the API key.
    So don't run it with pytest or in CI/CD
    '''

    response:str = open_router_client.generate_response("Hello", "Hello")
    print(response)
