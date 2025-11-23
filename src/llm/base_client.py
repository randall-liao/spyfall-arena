from abc import ABC, abstractmethod
from typing import Optional

from loguru import logger


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients, using the Template Method pattern."""

    def __init__(self, model_name: str, temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:  # pragma: no cover
        """Hook method: Validate the client's configuration."""
        pass

    @abstractmethod
    def _make_api_call(  # pragma: no cover
        self, messages: list, temperature: float, response_format: Optional[dict] = None
    ) -> dict:
        """Hook method: Make the actual API call to the LLM provider."""
        pass

    @abstractmethod
    def _extract_text(self, response: dict) -> str:  # pragma: no cover
        """Hook method: Extract the text content from the API response."""
        pass

    @abstractmethod
    def _extract_structured_data(self, response: dict) -> dict:  # pragma: no cover
        """Hook method: Extract structured data from the API response."""
        pass

    def generate_response(
        self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None
    ) -> str:
        """Template method: Orchestrates the generation of a text response."""
        temp = temperature if temperature is not None else self.temperature
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        logger.debug(f"Generating text response for model {self.model_name}")
        logger.debug(f"Messages: {messages}")

        try:
            response = self._make_api_call(messages, temp)
            logger.debug(f"Raw LLM response: {response}")
            return self._extract_text(response)
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise

    def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict,
        temperature: Optional[float] = None,
    ) -> dict:
        """Template method: Orchestrates the generation of a structured response."""
        temp = temperature if temperature is not None else self.temperature
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        logger.debug(f"Generating structured response for model {self.model_name}")
        logger.debug(f"Messages: {messages}")
        logger.debug(f"Schema: {response_schema}")

        try:
            response = self._make_api_call(messages, temp, response_schema)
            logger.debug(f"Raw LLM structured response: {response}")
            return self._extract_structured_data(response)
        except Exception as e:
            logger.error(f"LLM structured API call failed: {e}")
            raise
