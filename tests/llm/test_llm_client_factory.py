import unittest
from unittest.mock import MagicMock, patch

from config.api_key_manager import ApiKeyManager
from config.config_schema import LLMProvider
from llm.gemini_client import GeminiClient
from llm.llm_client_factory import LLMClientFactory
from llm.openai_client import OpenAIClient


class TestLLMClientFactory(unittest.TestCase):
    def setUp(self):
        self.mock_api_key_manager = MagicMock(spec=ApiKeyManager)
        self.factory = LLMClientFactory(self.mock_api_key_manager)

    def test_create_openai_client(self):
        self.mock_api_key_manager.get_api_key.return_value = "sk-openai-key"

        client = self.factory.create_client(
            model_name="gpt-4", provider=LLMProvider.OPEN_ROUTER, temperature=0.5
        )

        self.assertIsInstance(client, OpenAIClient)
        self.assertEqual(client.model_name, "gpt-4")
        self.assertEqual(client.temperature, 0.5)
        self.mock_api_key_manager.get_api_key.assert_called_once()
        self.mock_api_key_manager.get_google_api_key.assert_not_called()

    @patch("llm.gemini_client.genai.Client")
    def test_create_gemini_client(self, mock_genai_client):
        self.mock_api_key_manager.get_google_api_key.return_value = "AIza-google-key"

        client = self.factory.create_client(
            model_name="gemini-1.5-flash",
            provider=LLMProvider.GOOGLE_AI_STUDIO,
            temperature=0.8,
        )

        self.assertIsInstance(client, GeminiClient)
        self.assertEqual(client.model_name, "gemini-1.5-flash")
        self.assertEqual(client.temperature, 0.8)
        self.mock_api_key_manager.get_google_api_key.assert_called_once()
        self.mock_api_key_manager.get_api_key.assert_not_called()

    @patch("llm.gemini_client.genai.Client")
    def test_create_gemini_client_case_insensitive(self, mock_genai_client):
        self.mock_api_key_manager.get_google_api_key.return_value = "AIza-google-key"

        client = self.factory.create_client(
            model_name="Gemini-Pro",
            provider=LLMProvider.GOOGLE_AI_STUDIO,
            temperature=0.8,
        )

        self.assertIsInstance(client, GeminiClient)
