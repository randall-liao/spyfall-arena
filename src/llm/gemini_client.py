import json
from typing import Any, Dict, Optional, cast, TYPE_CHECKING
from tenacity import (
    stop_after_attempt,
    retry_if_exception,
    RetryCallState,
    before_sleep_log,
    Retrying,
    wait_exponential,
)
import logging

from google import genai
from google.genai import types

from llm.base_client import BaseLLMClient
from llm.exceptions import MaxRetriesExceededError

if TYPE_CHECKING:
    from llm.rate_limiter import TokenBucketLimiter

logger = logging.getLogger(__name__)


def wait_from_google_retry_info(retry_state: "RetryCallState") -> float:
    """Extract retryDelay from Google API 429 errors, or return 15s default."""
    default_wait = 15.0
    if not retry_state.outcome or not retry_state.outcome.exception():
        logger.debug("No exception found in retry state, using default wait.")
        return default_wait

    exc = retry_state.outcome.exception()

    # Check for details in the exception (common in Google RPC errors)
    details = getattr(exc, "details", [])
    if isinstance(details, dict):
        retry_info = details.get("details", [])
        if not retry_info:
            retry_info = details.get("error", {}).get("details", [])
        details = retry_info

    if not details and hasattr(exc, "args") and len(exc.args) > 0:
        arg0 = exc.args[0]
        if isinstance(arg0, dict):
            details = arg0.get("details", [])

    for detail in details:
        # Handle dict case
        if isinstance(detail, dict):
            type_url = detail.get("@type", "")
            if "google.rpc.RetryInfo" in type_url:
                delay_str = detail.get("retryDelay", "")
                if delay_str:
                    try:
                        wait_time = float(delay_str.rstrip("s"))
                        logger.debug(
                            f"Found explicit retryDelay in details: {wait_time}s"
                        )
                        return wait_time + 3.0
                    except ValueError:
                        pass
        # Handle object case (if protobuf)
        elif hasattr(detail, "retry_delay"):
            try:
                wait_time = (
                    float(detail.retry_delay.seconds)
                    + float(detail.retry_delay.nanos) / 1e9
                )
                logger.debug(f"Found explicit retryDelay in protobuf: {wait_time}s")
                return wait_time + 3.0
            except (ValueError, AttributeError):
                pass

    logger.debug(f"No explicit retry info found, using default wait: {default_wait}s")
    return default_wait


def on_retry_error(retry_state: "RetryCallState"):
    """Tenacity callback invoked when all retry attempts are exhausted."""
    exc = retry_state.outcome.exception()
    attempts = retry_state.attempt_number
    logger.error(f"Max retries ({attempts}) exceeded. Final error: {exc}")
    raise MaxRetriesExceededError(exc, attempts) from exc


class GeminiClient(BaseLLMClient):
    """Google Gemini API client with configurable retry logic.

    Implements PRD Section 4.2 (LLM Player Management) for Google AI
    Studio models. Handles 429 rate limit errors via tenacity with
    exponential backoff and Google's explicit retryDelay hints.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str,
        temperature: float = 0.7,
        rate_limiter: Optional["TokenBucketLimiter"] = None,
        reasoning_config: Optional[Dict[str, Any]] = None,
        max_retries: int = 2,
        retry_min_wait: float = 1.0,
        retry_max_wait: float = 10.0,
    ):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.rate_limiter = rate_limiter
        self.reasoning_config = reasoning_config
        self.max_retries = max_retries
        self.retry_min_wait = retry_min_wait
        self.retry_max_wait = retry_max_wait
        super().__init__(model_name, temperature)

    def _validate_config(self) -> None:
        """Validates that the API key and model name are provided."""
        if not self.api_key:
            raise ValueError("Google API key is required.")
        if not self.model_name:
            raise ValueError("A model name is required.")

    def _map_messages_to_gemini_format(
        self, messages: list
    ) -> tuple[Optional[str], list[types.Content]]:
        """Convert standard chat messages to Gemini API format."""
        system_instruction = None
        contents = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if not content:
                continue

            if role == "system":
                if system_instruction:
                    system_instruction += "\n" + content
                else:
                    system_instruction = content
            elif role == "user":
                contents.append(
                    types.Content(
                        role="user", parts=[types.Part.from_text(text=content)]
                    )
                )
            elif role == "assistant":
                contents.append(
                    types.Content(
                        role="model", parts=[types.Part.from_text(text=content)]
                    )
                )

        return system_instruction, contents

    def _wait_strategy(self, retry_state: "RetryCallState") -> float:
        """Compute wait time using Google's retry hints or exponential backoff.

        Google 429 errors often include explicit retryDelay hints. When
        present, we honor those. Otherwise, fall back to configurable
        exponential backoff (see PRD Section 6 - API rate constraints).
        """
        explicit_wait = self._try_get_google_retry_delay(retry_state)
        if explicit_wait is not None:
            return explicit_wait

        exp_wait = wait_exponential(min=self.retry_min_wait, max=self.retry_max_wait)
        return exp_wait(retry_state)

    def _try_get_google_retry_delay(
        self, retry_state: "RetryCallState"
    ) -> Optional[float]:
        """Return exponential backoff wait time using configured min/max bounds."""
        return wait_exponential(min=self.retry_min_wait, max=self.retry_max_wait)(
            retry_state
        )

    def _make_api_call(
        self, messages: list, temperature: float, response_format: Optional[dict] = None
    ) -> Dict[str, Any]:
        """Make API call with tenacity retry wrapper for 429 errors."""
        retryer = Retrying(
            stop=stop_after_attempt(self.max_retries + 1),
            wait=self._wait_strategy,
            retry=retry_if_exception(
                lambda e: "429" in str(e) or getattr(e, "code", 0) == 429
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            retry_error_callback=on_retry_error,
            reraise=True,
        )
        return retryer(
            self._make_api_call_impl,
            messages=messages,
            temperature=temperature,
            response_format=response_format,
        )

    def _make_api_call_impl(
        self, messages: list, temperature: float, response_format: Optional[dict] = None
    ) -> Dict[str, Any]:
        """Internal method for actual API call."""

        if self.rate_limiter:
            self.rate_limiter.wait_for_token()

        system_instruction, contents = self._map_messages_to_gemini_format(messages)

        response_mime_type = None
        if response_format and response_format.get("type") == "json_object":
            response_mime_type = "application/json"

        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
            response_mime_type=response_mime_type,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )

        # We return a dict wrapping the response text, as BaseLLMClient expects a dict
        # The actual text extraction happens in _extract_text
        if not response.text:
            return {"text": ""}

        return {"text": response.text}

    def _extract_text(self, response: dict) -> str:
        """Extracts the text content from the response dict."""
        return cast(str, response.get("text", ""))

    def _extract_structured_data(self, response: dict) -> dict:
        """Extracts and parses a structured (JSON) response."""
        text = self._extract_text(response)
        try:
            return cast(dict, json.loads(text))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid structured response from LLM API: {text}") from e
