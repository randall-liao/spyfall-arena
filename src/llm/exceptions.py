class MaxRetriesExceededError(Exception):
    """Raised when the maximum number of retries is exceeded."""

    def __init__(self, original_exception: Exception, attempts: int):
        self.original_exception = original_exception
        self.attempts = attempts
        super().__init__(
            f"Max retries ({attempts}) exceeded. Last error: {original_exception}"
        )
