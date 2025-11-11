from unittest.mock import MagicMock, patch

import pytest

from llm.llm_client_factory import LLMClientFactory
from llm.openai_client import OpenAIClient


@pytest.fixture
def mock_openai_client():
    """Fixture to mock the openai.Client."""
    with patch("llm.openai_client.OpenAI") as mock_client_class:
        mock_client_instance = MagicMock()
        mock_completion = MagicMock()
        mock_completion.dict.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_client_instance.chat.completions.create.return_value = mock_completion
        mock_client_class.return_value = mock_client_instance
        yield mock_client_instance


def test_openai_client_success(mock_openai_client):
    """Tests a successful text generation call."""
    client = OpenAIClient(model_name="test-model", api_key="test-key")
    response = client.generate_response("system prompt", "user prompt")
    assert response == "Test response"
    mock_openai_client.chat.completions.create.assert_called_once()


def test_openai_structured_response_success(mock_openai_client):
    """Tests a successful structured response generation call."""
    mock_completion = MagicMock()
    mock_completion.dict.return_value = {
        "choices": [{"message": {"content": '{"key": "value"}'}}]
    }
    mock_openai_client.chat.completions.create.return_value = mock_completion

    client = OpenAIClient(model_name="test-model", api_key="test-key")
    response = client.generate_structured_response(
        "system", "user", {"type": "json_object"}
    )
    assert response == {"key": "value"}


def test_invalid_text_response_format(mock_openai_client):
    """Tests that an error is raised for an invalid text response format."""
    mock_completion = MagicMock()
    mock_completion.dict.return_value = {"invalid": "format"}
    mock_openai_client.chat.completions.create.return_value = mock_completion
    client = OpenAIClient(model_name="m", api_key="k")
    with pytest.raises(ValueError, match="Invalid response format"):
        client.generate_response("system", "user")


def test_invalid_structured_response_format(mock_openai_client):
    """Tests that an error is raised for an invalid structured response."""
    # Test for malformed JSON content
    mock_completion = MagicMock()
    mock_completion.dict.return_value = {
        "choices": [{"message": {"content": "not json"}}]
    }
    mock_openai_client.chat.completions.create.return_value = mock_completion
    client = OpenAIClient(model_name="m", api_key="k")
    with pytest.raises(ValueError, match="Invalid structured response"):
        client.generate_structured_response("s", "u", {})

    # Test for missing keys
    mock_completion.dict.return_value = {"invalid": "format"}
    mock_openai_client.chat.completions.create.return_value = mock_completion
    with pytest.raises(ValueError, match="Invalid structured response"):
        client.generate_structured_response("s", "u", {})


def test_config_validation():
    """Tests that configuration validation raises errors."""
    with pytest.raises(ValueError, match="API key is required"):
        OpenAIClient(model_name="m", api_key="")
    with pytest.raises(ValueError, match="model name is required"):
        OpenAIClient(model_name="", api_key="k")


def test_llm_client_factory():
    """Tests the LLMClientFactory."""
    mock_api_key_manager = MagicMock()
    mock_api_key_manager.get_api_key.return_value = "test-key"
    factory = LLMClientFactory(mock_api_key_manager)
    client = factory.create_client(model_name="test-model")
    assert isinstance(client, OpenAIClient)
    assert client.model_name == "test-model"
