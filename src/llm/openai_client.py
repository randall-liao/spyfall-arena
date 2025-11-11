import json
from typing import Optional, Any, Dict, cast

from openai import OpenAI

from llm.base_client import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    """A client for interacting with the OpenRouter API using the OpenAI SDK."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        temperature: float = 0.7,
    ):
        self.api_key = api_key
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
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
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            response_format=response_format,
        )
        return cast(Dict[str, Any], completion.dict())

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
