from unittest.mock import MagicMock, patch

import pytest

from llm.llm_client_factory import LLMClientFactory
from llm.openai_client import OpenAIClient
from llm.exceptions import MaxRetriesExceededError
from openai import RateLimitError
import httpx


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


def test_openai_retry_success_after_failure():
    """Test that the client retries on RateLimitError and eventually succeeds."""
    mock_response = MagicMock()
    mock_response.dict.return_value = {"choices": [{"message": {"content": "Success"}}]}

    # Create a mock client that raises RateLimitError twice then succeeds
    mock_openai_instance = MagicMock()

    mock_http_response = httpx.Response(
        status_code=429, request=httpx.Request("POST", "http://test")
    )
    error = RateLimitError(
        "Rate limit exceeded", response=mock_http_response, body=None
    )

    # side_effect: fail, fail, success
    mock_openai_instance.chat.completions.create.side_effect = [
        error,
        error,
        mock_response,
    ]

    with patch("llm.openai_client.OpenAI", return_value=mock_openai_instance):
        client = OpenAIClient(model_name="test-model", api_key="test-key")

        # Patch sleep to speed up test
        with patch("time.sleep"):
            response = client._make_api_call([], 0.7)

    assert response["choices"][0]["message"]["content"] == "Success"
    assert mock_openai_instance.chat.completions.create.call_count == 3


def test_openai_max_retries_exceeded():
    """Test that MaxRetriesExceededError is raised after max retries."""
    mock_openai_instance = MagicMock()
    mock_http_response = httpx.Response(
        status_code=429, request=httpx.Request("POST", "http://test")
    )
    error = RateLimitError(
        "Rate limit exceeded", response=mock_http_response, body=None
    )

    mock_openai_instance.chat.completions.create.side_effect = error

    with patch("llm.openai_client.OpenAI", return_value=mock_openai_instance):
        client = OpenAIClient(model_name="test-model", api_key="test-key")

        with patch("time.sleep"):
            with pytest.raises(MaxRetriesExceededError) as exc_info:
                client._make_api_call([], 0.7)

    assert exc_info.value.attempts == 3
