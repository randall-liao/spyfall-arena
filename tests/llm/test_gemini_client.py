import json
import unittest
from unittest.mock import MagicMock, patch

from google.genai import types

from llm.gemini_client import GeminiClient


class TestGeminiClient(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_google_key"
        self.model_name = "gemini-2.5-flash"
        # Patch the genai.Client
        self.patcher = patch("llm.gemini_client.genai.Client")
        self.mock_client_class = self.patcher.start()
        self.mock_client_instance = self.mock_client_class.return_value
        self.client = GeminiClient(self.model_name, self.api_key)

    def tearDown(self):
        self.patcher.stop()

    def test_init(self):
        self.mock_client_class.assert_called_with(api_key=self.api_key)
        self.assertEqual(self.client.model_name, self.model_name)

    def test_validate_config(self):
        with self.assertRaises(ValueError):
            GeminiClient("", self.api_key)
        with self.assertRaises(ValueError):
            GeminiClient(self.model_name, "")

    def test_map_messages_to_gemini_format(self):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]

        system_instruction, contents = self.client._map_messages_to_gemini_format(
            messages
        )

        self.assertEqual(system_instruction, "You are a helpful assistant.")
        self.assertEqual(len(contents), 3)
        self.assertEqual(contents[0].role, "user")
        self.assertEqual(contents[0].parts[0].text, "Hello")
        self.assertEqual(contents[1].role, "model")
        self.assertEqual(contents[1].parts[0].text, "Hi there")
        self.assertEqual(contents[2].role, "user")
        self.assertEqual(contents[2].parts[0].text, "How are you?")

    def test_map_messages_multiple_system_prompts(self):
        messages = [
            {"role": "system", "content": "Sys 1"},
            {"role": "system", "content": "Sys 2"},
            {"role": "user", "content": "User msg"},
        ]
        system_instruction, contents = self.client._map_messages_to_gemini_format(
            messages
        )
        self.assertEqual(system_instruction, "Sys 1\nSys 2")
        self.assertEqual(len(contents), 1)

    def test_map_messages_empty_content(self):
        messages = [
            {"role": "user", "content": "User msg"},
            {"role": "user", "content": ""},  # Should be ignored
        ]
        _, contents = self.client._map_messages_to_gemini_format(messages)
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0].parts[0].text, "User msg")

    def test_make_api_call_text(self):
        messages = [{"role": "user", "content": "Hello"}]
        mock_response = MagicMock()
        mock_response.text = "Hello world"
        self.mock_client_instance.models.generate_content.return_value = mock_response

        response = self.client._make_api_call(messages, temperature=0.5)

        self.assertEqual(response, {"text": "Hello world"})

        # Verify call arguments
        self.mock_client_instance.models.generate_content.assert_called_once()
        call_args = self.mock_client_instance.models.generate_content.call_args
        self.assertEqual(call_args.kwargs["model"], self.model_name)
        self.assertEqual(len(call_args.kwargs["contents"]), 1)
        config = call_args.kwargs["config"]
        self.assertEqual(config.temperature, 0.5)
        self.assertIsNone(config.response_mime_type)

    def test_make_api_call_json(self):
        messages = [{"role": "user", "content": "Give me JSON"}]
        mock_response = MagicMock()
        mock_response.text = '{"key": "value"}'
        self.mock_client_instance.models.generate_content.return_value = mock_response

        response = self.client._make_api_call(
            messages, temperature=0.1, response_format={"type": "json_object"}
        )

        self.assertEqual(response, {"text": '{"key": "value"}'})

        config = self.mock_client_instance.models.generate_content.call_args.kwargs[
            "config"
        ]
        self.assertEqual(config.response_mime_type, "application/json")

    def test_extract_text(self):
        response = {"text": "some text"}
        self.assertEqual(self.client._extract_text(response), "some text")

    def test_extract_structured_data(self):
        response = {"text": '{"answer": 42}'}
        self.assertEqual(self.client._extract_structured_data(response), {"answer": 42})

    def test_extract_structured_data_invalid_json(self):
        response = {"text": "not json"}
        with self.assertRaises(ValueError):
            self.client._extract_structured_data(response)

    def test_make_api_call_empty_response(self):
        messages = [{"role": "user", "content": "Hello"}]
        mock_response = MagicMock()
        mock_response.text = None  # Simulate blocked or empty
        self.mock_client_instance.models.generate_content.return_value = mock_response

        response = self.client._make_api_call(messages, temperature=0.5)
        self.assertEqual(response, {"text": ""})
