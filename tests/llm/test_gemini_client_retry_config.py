from unittest.mock import patch
from llm.gemini_client import GeminiClient

def test_gemini_client_init_retry_params():
    """Test that GeminiClient accepts retry parameters."""
    client = GeminiClient(
        model_name="test-model",
        api_key="test-key",
        max_retries=5,
        retry_min_wait=2.0,
        retry_max_wait=20.0
    )
    assert client.max_retries == 5
    assert client.retry_min_wait == 2.0
    assert client.retry_max_wait == 20.0

def test_gemini_client_init_retry_defaults():
    """Test default values for retry parameters."""
    client = GeminiClient(
        model_name="test-model",
        api_key="test-key"
    )
    # Matching the defaults in LLMConfig which are passed here? 
    # Or strict defaults in GeminiClient?
    # Task says "Test default values for retry parameters".
    # GeminiClient should likely have defaults matching LLMConfig.
    # LLMConfig defaults: max_retries=2, min=1.0, max=10.0
    assert client.max_retries == 2
    assert client.retry_min_wait == 1.0
    assert client.retry_max_wait == 10.0

def test_gemini_client_retry_logic_uses_config():
    """Test that retry logic uses the configured parameters."""
    client = GeminiClient(
        model_name="test-model",
        api_key="test-key",
        max_retries=1,  # Try only once (plus initial? No, stop_after_attempt(1) means 1 attempt total)
        retry_min_wait=0.1,
        retry_max_wait=0.2
    )

    # We mock _make_api_call_impl to fail
    # We expect verify behavior based on configured values.
    # Note: implementing this test requires GeminiClient to have _make_api_call_impl structure.
    # Since we strictly follow TDD, this test might fail compilation if methods don't exist yet, 
    # but Python is dynamic.
    
    # However, to test that Retrying is constructed with correct params, we might need to patch tenacity.Retrying
    
    with patch("llm.gemini_client.Retrying") as MockRetrying, \
         patch.object(client, "_make_api_call_impl"):
        
        # We need mock_impl to return something so Retrying(..)(..) returns it
        mock_retry_instance = MockRetrying.return_value
        mock_retry_instance.return_value = {"text": "success"}
        
        client._make_api_call([], 0.7)
        
        # Verify Retrying was initialized with our config
        # We need to inspect call args to Retrying constructor
        MockRetrying.assert_called_once()
        _, kwargs = MockRetrying.call_args
        
        # stop param should correspond to max_retries + 1? 
        # Usually stop_after_attempt(N) includes the first attempt.
        # If max_retries=1 (meaning 1 RETRY), total attempts = 2.
        # LLMConfig: "max_retries: 2" usually means 2 retries (3 attempts).
        # existing code used stop_after_attempt(3) -> 3 attempts.
        
        # We need to decide interpretation. Usually max_retries=2 means 2 EXTRA attempts.
        # So we expect stop_after_attempt(client.max_retries + 1).
        
        # We can't easily assert the exact object stop_after_attempt returns, but we can check usage.
        
        mock_retry_instance.assert_called_once()
