import json
from typing import Any, Dict, Optional, cast, TYPE_CHECKING

from google import genai
from google.genai import types

from llm.base_client import BaseLLMClient

if TYPE_CHECKING:
    from llm.rate_limiter import TokenBucketLimiter


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
