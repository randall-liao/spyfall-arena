from unittest.mock import MagicMock, patch

import httpx
import pytest

from llm.llm_client_factory import LLMClientFactory
from llm.openrouter_client import OpenRouterClient


@pytest.fixture
def mock_httpx_client():
    """Fixture to mock the httpx.Client."""
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        yield mock_client


def test_openrouter_client_success(mock_httpx_client):
    """Tests a successful text generation call."""
    client = OpenRouterClient(model_name="test-model", api_key="test-key")
    response = client.generate_response("system prompt", "user prompt")
    assert response == "Test response"
    mock_httpx_client.post.assert_called_once()


def test_openrouter_structured_response_success(mock_httpx_client):
    """Tests a successful structured response generation call."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"key": "value"}'}}]
    }
    mock_httpx_client.post.return_value = mock_response

    client = OpenRouterClient(model_name="test-model", api_key="test-key")
    response = client.generate_structured_response(
        "system", "user", {"type": "json_object"}
    )
    assert response == {"key": "value"}


def test_openrouter_client_retry(mock_httpx_client):
    """Tests the retry mechanism on request failure."""
    mock_httpx_client.post.side_effect = [
        httpx.RequestError("Connection error"),
        mock_httpx_client.post.return_value,  # Success on the second try
    ]
    client = OpenRouterClient(model_name="m", api_key="k", max_retries=1)
    response = client.generate_response("system", "user")
    assert response == "Test response"
    assert mock_httpx_client.post.call_count == 2


def test_openrouter_client_retry_fails():
    """Tests when the API call fails after all retries."""
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.RequestError("Connection error")
        mock_client_class.return_value.__enter__.return_value = mock_client

        client = OpenRouterClient(model_name="m", api_key="k", max_retries=1)
        with pytest.raises(ConnectionError):
            client.generate_response("system", "user")
        assert mock_client.post.call_count == 2


def test_invalid_text_response_format(mock_httpx_client):
    """Tests that an error is raised for an invalid text response format."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"invalid": "format"}
    mock_httpx_client.post.return_value = mock_response
    client = OpenRouterClient(model_name="m", api_key="k")
    with pytest.raises(ValueError, match="Invalid response format"):
        client.generate_response("system", "user")


def test_invalid_structured_response_format(mock_httpx_client):
    """Tests that an error is raised for an invalid structured response."""
    # Test for malformed JSON content
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "not json"}}]
    }
    mock_httpx_client.post.return_value = mock_response
    client = OpenRouterClient(model_name="m", api_key="k")
    with pytest.raises(ValueError, match="Invalid structured response"):
        client.generate_structured_response("s", "u", {})

    # Test for missing keys
    mock_response.json.return_value = {"invalid": "format"}
    with pytest.raises(ValueError, match="Invalid structured response"):
        client.generate_structured_response("s", "u", {})


def test_config_validation():
    """Tests that configuration validation raises errors."""
    with pytest.raises(ValueError, match="API key is required"):
        OpenRouterClient(model_name="m", api_key="")
    with pytest.raises(ValueError, match="model name is required"):
        OpenRouterClient(model_name="", api_key="k")


def test_llm_client_factory():
    """Tests the LLMClientFactory."""
    mock_api_key_manager = MagicMock()
    mock_api_key_manager.get_api_key.return_value = "test-key"
    factory = LLMClientFactory(mock_api_key_manager)
    client = factory.create_client(model_name="test-model")
    assert isinstance(client, OpenRouterClient)
    assert client.model_name == "test-model"
