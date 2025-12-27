import json
from typing import Any, Dict, Optional, cast, TYPE_CHECKING
from tenacity import (
    stop_after_attempt,
    retry_if_exception,
    retry,
    RetryCallState,
    before_sleep_log,
)
import logging

from google import genai
from google.genai import types

from llm.base_client import BaseLLMClient
from llm.exceptions import MaxRetriesExceededError

if TYPE_CHECKING:
    from llm.rate_limiter import TokenBucketLimiter

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from llm.rate_limiter import TokenBucketLimiter

logger = logging.getLogger(__name__)


def wait_from_google_retry_info(retry_state: "RetryCallState") -> float:
    """
    Custom wait strategy that inspects the exception for Google's retryDelay.
    Defaults to 15 seconds if no retry info is found.
    """
    default_wait = 15.0
    """
    Custom wait strategy that inspects the exception for Google's retryDelay.
    Defaults to 15 seconds if no retry info is found.
    """
    default_wait = 15.0
    if not retry_state.outcome or not retry_state.outcome.exception():
        logger.debug("No exception found in retry state, using default wait.")
        return default_wait

    exc = retry_state.outcome.exception()
    logger.debug(f"Parsing retry delay from exception: {exc}")

    # Check for details in the exception (common in Google RPC errors)
    # The structure usually involves a 'details' list.
    # Validating against dictionary structure shown in logs.

    # We try to access the `details` attribute if it exists (e.g. google.api_core.exceptions.GoogleAPICallError)
    # Or strict dict access if the exception itself carries the payload (less common in Python SDK objects but possible)

    details = getattr(exc, "details", [])
    if isinstance(details, dict):
        # google.genai.errors.ClientError stores the full response JSON in .details
        # We need to traverse down to find the actual list of details
        # Structure: {'error': {'details': [...]}} or just {'details': [...]}
        retry_info = details.get("details", [])
        if not retry_info:
            retry_info = details.get("error", {}).get("details", [])
        details = retry_info

    if not details and hasattr(exc, "args") and len(exc.args) > 0:
        # Sometimes the error details are in the args[0] if it's a raw dict wrapper
        arg0 = exc.args[0]
        if isinstance(arg0, dict):
            details = arg0.get("details", [])

    # If details is still empty/not found, we might need to inspect message text or other properties
    # But based on user log, it looks like a structured error object.

    # Iterate through details to find RetryInfo
    # The structure in log: {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '21s'}

    # Note: `details` might be a list of dicts (if parsed) or protobuf messages.
    # We will assume list of dicts or objects we can getattr/getitem.

    for detail in details:
        # Handle dict case
        if isinstance(detail, dict):
            type_url = detail.get("@type", "")
            if "google.rpc.RetryInfo" in type_url:
                delay_str = detail.get("retryDelay", "")
                if delay_str:
                    try:
                        # Format is usually "21s" or "21.123s"
                        wait_time = float(delay_str.rstrip("s"))
                        logger.debug(
                            f"Found explicit retryDelay in details: {wait_time}s"
                        )
                        # Add buffer to ensure we don't hit rate limit again immediately
                        return wait_time + 3.0
                    except ValueError:
                        pass
        # Handle object case (if protobuf)
        elif hasattr(detail, "retry_delay"):
            # Some google runtimes convert this
            try:
                wait_time = (
                    float(detail.retry_delay.seconds)
                    + float(detail.retry_delay.nanos) / 1e9
                )
                logger.debug(f"Found explicit retryDelay in protobuf: {wait_time}s")
                # Add buffer to ensure we don't hit rate limit again immediately
                return wait_time + 3.0
            except (ValueError, AttributeError):
                pass

    logger.debug(f"No explicit retry info found, using default wait: {default_wait}s")
    return default_wait


def on_retry_error(retry_state: "RetryCallState"):
    """Callback for when retries are exhausted."""
    exc = retry_state.outcome.exception()
    attempts = retry_state.attempt_number
    logger.error(f"Max retries ({attempts}) exceeded. Final error: {exc}")
    raise MaxRetriesExceededError(exc, attempts) from exc


class GeminiClient(BaseLLMClient):
    """A client for interacting with the Google Gemini API using the Google Gen AI SDK."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        temperature: float = 0.7,
        rate_limiter: Optional["TokenBucketLimiter"] = None,
    ):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.rate_limiter = rate_limiter
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
        """
        Maps standard message format to Gemini format.

        Returns:
            A tuple containing (system_instruction, contents).
        """
        system_instruction = None
        contents = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if not content:
                continue

            if role == "system":
                # If there are multiple system messages, we'll concatenate them or just take the last one.
                # Usually there's one. Let's concatenate if multiple.
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
            # Ignore other roles if any

        return system_instruction, contents

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_from_google_retry_info,
        retry=retry_if_exception(
            lambda e: "429" in str(e) or getattr(e, "code", 0) == 429
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        retry_error_callback=on_retry_error,
        reraise=True,
    )
    def _make_api_call(
        self, messages: list, temperature: float, response_format: Optional[dict] = None
    ) -> Dict[str, Any]:
        """Makes an API call to Gemini."""

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
            # Handle case where response might be blocked or empty
            # Check finish_reason if available, but for now just return empty text
            # If blocked, response.text might raise or be None.
            # According to docs, we should check candidates.
            # But simplistic access:
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
