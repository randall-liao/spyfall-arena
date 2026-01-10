import json
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, cast

from openai import APIConnectionError, OpenAI, RateLimitError

from llm.base_client import BaseLLMClient
from llm.exceptions import MaxRetriesExceededError

logger = logging.getLogger(__name__)



if TYPE_CHECKING:
    from llm.rate_limiter import TokenBucketLimiter


class OpenAIClient(BaseLLMClient):
    """OpenRouter API client using the OpenAI SDK.

    Implements PRD Section 4.2 (LLM Player Management). Uses OpenAI SDK's
    built-in retry mechanism for rate limit errors.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str,
        temperature: float = 0.7,
        rate_limiter: Optional["TokenBucketLimiter"] = None,
        reasoning_config: Optional[Dict[str, Any]] = None,
        max_retries: int = 2,
    ):
        self.api_key = api_key
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            max_retries=max_retries,
        )
        self.rate_limiter = rate_limiter
        self.reasoning_config = reasoning_config
        self.max_retries = max_retries
        super().__init__(model_name, temperature)

    def _validate_config(self) -> None:
        """Validates that the API key and model name are provided."""
        if not self.api_key:
            raise ValueError("OpenRouter API key is required.")
        if not self.model_name:
            raise ValueError("A model name is required.")

    def _make_api_call(
        self, messages: list, temperature: float, response_format: Optional[dict] = None
    ) -> Dict[str, Any]:
        """Makes an API call to OpenRouter using the OpenAI SDK."""
        extra_body = {}
        if self.reasoning_config:
            # Filter out None values
            reasoning = {
                k: v for k, v in self.reasoning_config.items() if v is not None
            }
            if reasoning:
                extra_body["reasoning"] = reasoning

        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                response_format=cast(Any, response_format),
                extra_body=extra_body if extra_body else None,
            )
            return cast(Dict[str, Any], completion.dict())
        except (RateLimitError, APIConnectionError) as e:
            logger.error(f"Max retries ({self.max_retries}) exceeded. Final error: {e}")
            raise MaxRetriesExceededError(e, self.max_retries + 1) from e

    def _extract_text(self, response: dict) -> str:
        """Extracts the text content from a standard API response."""
        try:
            return cast(str, response["choices"][0]["message"]["content"])
        except (KeyError, IndexError) as e:
            raise ValueError("Invalid response format from LLM API") from e

    def _extract_structured_data(self, response: dict) -> dict:
        """Extracts and parses a structured (JSON) response."""
        try:
            content = response["choices"][0]["message"]["content"]
            return cast(dict, json.loads(content))
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise ValueError("Invalid structured response from LLM API") from e
