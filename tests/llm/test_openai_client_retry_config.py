from unittest.mock import patch

from llm.openai_client import OpenAIClient


def test_openai_client_init_max_retries():
    """Test that OpenAIClient accepts and stores max_retries."""
    api_key = "test-key"
    model_name = "test-model"

    # Test with default (if we were to change init signature default, but here
    # we verify it accepts it and passes it to OpenAI)

    with patch("llm.openai_client.OpenAI") as mock_openai:
        OpenAIClient(model_name=model_name, api_key=api_key, max_retries=5)
        mock_openai.assert_called_once()
        _, kwargs = mock_openai.call_args
        assert kwargs["max_retries"] == 5


def test_openai_client_init_default_max_retries():
    """Test that OpenAIClient uses a default for max_retries if not specified."""
    api_key = "test-key"
    model_name = "test-model"

    with patch("llm.openai_client.OpenAI") as mock_openai:
        # Assuming we will set a default in __init__ or use OpenAI's default.
        # But wait, we need to decide what the default is in __init__.
        # The spec says "Test default max_retries value".
        OpenAIClient(model_name=model_name, api_key=api_key)
        mock_openai.assert_called_once()
        _, kwargs = mock_openai.call_args
        # We need to know what we expect as default.
        # OpenAI SDK default is 2.
        # If we add the arg to __init__, we should probably set a default there or pass None.
        # Let's assume we want to default to 2 to match OpenAI default or our Config default.
        # The LLMConfig default is 2.
        # Let's say we expect 2.
        assert kwargs.get("max_retries") == 2
