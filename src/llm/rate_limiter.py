import time
import threading
from typing import Optional
from loguru import logger


class TokenBucketLimiter:
    """
    A thread-safe Token Bucket rate limiter.

    The bucket fills with tokens at a specific rate (requests_per_minute).
    Each request consumes one token. If the bucket is empty, the caller blocks
    until a token becomes available.
    """

    def __init__(self, requests_per_minute: int, burst_limit: int):
        self.capacity = burst_limit
        self.tokens = float(burst_limit)
        self.rate = requests_per_minute / 60.0  # tokens per second
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

        logger.info(
            f"Rate Limiter initialized: {requests_per_minute} req/min, burst={burst_limit}"
        )

    def _refill(self):
        """Refills the bucket based on time passed since last refill."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate

        if new_tokens > 0:
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now

    def wait_for_token(self):
        """
        Blocks until a token is available, then consumes it.
        """
        while True:
            with self.lock:
                self._refill()

                if self.tokens >= 1:
                    self.tokens -= 1
                    return

                # Calculate time to wait for next token
                # We need 1 token. We have self.tokens.
                # Needed: 1 - self.tokens
                missing = 1.0 - self.tokens
                wait_time = missing / self.rate

            # Sleep outside the lock to allow other threads to potentially access
            # (though in this simple blocking model, they'd also have to wait)
            if wait_time > 0:
                logger.debug(f"Rate limit hit. Sleeping for {wait_time:.3f}s")
                time.sleep(wait_time)
