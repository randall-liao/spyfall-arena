import json
import time
from typing import Optional, Any, Dict, cast

import httpx

from spyfall_arena.llm.base_client import BaseLLMClient


class OpenRouterClient(BaseLLMClient):
    """A client for interacting with the OpenRouter API."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        model_name: str,
        api_key: str,
        temperature: float = 0.7,
        max_retries: int = 1,
        backoff_factor: float = 0.5,
    ):
        self.api_key = api_key
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
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
        """Makes an API call to OpenRouter with a retry mechanism."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(self.BASE_URL, json=payload, headers=headers)
                    response.raise_for_status()
                    return cast(Dict[str, Any], response.json())
            except httpx.RequestError as e:
                if attempt >= self.max_retries:
                    raise ConnectionError(
                        f"API request failed after {self.max_retries} retries: {e}"
                    ) from e
                time.sleep(self.backoff_factor * (2**attempt))
        raise ConnectionError("API request failed after all retries.")

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
