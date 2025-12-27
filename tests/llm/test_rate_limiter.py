import time
from unittest.mock import MagicMock, patch
import pytest

from llm.rate_limiter import TokenBucketLimiter


class TestTokenBucketLimiter:
    def test_initialization(self):
        limiter = TokenBucketLimiter(requests_per_minute=60, burst_limit=5)
        assert limiter.tokens == 5.0
        assert limiter.capacity == 5
        assert limiter.rate == 1.0  # 60/60

    def test_consume_token_immediate(self):
        limiter = TokenBucketLimiter(requests_per_minute=60, burst_limit=5)
        start_tokens = limiter.tokens
        limiter.wait_for_token()
        # Should have consumed 1 token roughly, plus any refill (should be negligible)
        assert limiter.tokens < start_tokens

    @patch("time.sleep")
    @patch("time.monotonic")
    def test_rate_limiting_wait(self, mock_time, mock_sleep):
        # Configure Initial time BEFORE creating the limiter to ensure init gets a float
        mock_time.return_value = 0.0

        # Setup: 60 req/min (1 req/sec), burst 1
        limiter = TokenBucketLimiter(requests_per_minute=60, burst_limit=1)

        # First request consumes the burst token
        # This calls time.monotonic() which returns 0.0
        limiter.wait_for_token()
        assert limiter.tokens <= 0

        # Now we want simulated time progression.
        # We need a mutable reference for side_effect to use
        current_time = [0.0]

        def side_effect_time():
            return current_time[0]

        def side_effect_sleep(seconds):
            current_time[0] += seconds

        # Switch to side_effect
        mock_time.return_value = (
            None  # Important: clear return_value to enable side_effect
        )
        mock_time.side_effect = side_effect_time
        mock_sleep.side_effect = side_effect_sleep

        # Reset limiter or Manually update last_refill to match new simulation start?
        # limiter.last_refill is 0.0. current_time is 0.0. Detailed alignment is fine.

        # However, to avoid any drift issues from previous calls, creating a fresh one is safer
        # AS LONG AS it uses the current mocked time.
        # But wait, if we create a new one, it has full burst again! we don't want that if we want to test waiting.
        # Actually, let's just stick with the existing limiter, but we've consumed the burst.

        # 1. Second consume (should wait 1s)
        # tokens <= 0. Needs 1. Missing 1. Rate 1. Wait 1s.
        limiter.wait_for_token()
        mock_sleep.assert_called_with(1.0)

        # 2. Third consume (should wait another 1s)
        limiter.wait_for_token()
        # Called with roughly 1.0 again
        assert mock_sleep.call_count == 2
