import pytest
from unittest.mock import MagicMock, patch
from config.config_schema import LLMConfig, LLMProvider
from llm.llm_client_factory import LLMClientFactory

@pytest.fixture
def mock_api_key_manager():
    m = MagicMock()
    m.get_api_key.return_value = "key"
    m.get_google_api_key.return_value = "gkey"
    return m

def test_factory_passes_retry_config_to_openai(mock_api_key_manager):
    llm_conf = LLMConfig(max_retries=5, retry_min_wait=2.0, retry_max_wait=8.0)
    
    mock_config = MagicMock()
    mock_config.llm = llm_conf
    mock_config.rate_limit.enabled = False
    
    factory = LLMClientFactory(mock_api_key_manager, config=mock_config)
    
    with patch("llm.llm_client_factory.OpenAIClient") as MockOpenAIClient:
        factory.create_client("test-model", LLMProvider.OPEN_ROUTER)
        
        MockOpenAIClient.assert_called_once()
        _, kwargs = MockOpenAIClient.call_args
        assert kwargs["max_retries"] == 5

def test_factory_passes_retry_config_to_gemini(mock_api_key_manager):
    llm_conf = LLMConfig(max_retries=3, retry_min_wait=1.5, retry_max_wait=5.0)
    mock_config = MagicMock()
    mock_config.llm = llm_conf
    mock_config.rate_limit.enabled = False
    
    factory = LLMClientFactory(mock_api_key_manager, config=mock_config)
    
    with patch("llm.llm_client_factory.GeminiClient") as MockGeminiClient:
        factory.create_client("gemini-test", LLMProvider.GOOGLE_AI_STUDIO)
        
        MockGeminiClient.assert_called_once()
        _, kwargs = MockGeminiClient.call_args
        assert kwargs["max_retries"] == 3
        assert kwargs["retry_min_wait"] == 1.5
        assert kwargs["retry_max_wait"] == 5.0

def test_factory_uses_defaults_when_no_config(mock_api_key_manager):
    # If config passed is None
    factory = LLMClientFactory(mock_api_key_manager, config=None)
    
    with patch("llm.llm_client_factory.OpenAIClient") as MockOpenAIClient:
        factory.create_client("model", LLMProvider.OPEN_ROUTER)
        _, kwargs = MockOpenAIClient.call_args
        assert "max_retries" not in kwargs or kwargs["max_retries"] == 2

    with patch("llm.llm_client_factory.GeminiClient") as MockGeminiClient:
        factory.create_client("gemini", LLMProvider.GOOGLE_AI_STUDIO)
        _, kwargs = MockGeminiClient.call_args
        assert "max_retries" not in kwargs or kwargs["max_retries"] == 2
