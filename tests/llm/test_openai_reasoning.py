import unittest
from unittest.mock import patch

from llm.openai_client import OpenAIClient


class TestOpenAIClientReasoning(unittest.TestCase):
    def setUp(self):
        self.api_key = "test-key"
        self.model_name = "test-model"
        self.temperature = 0.5
        self.mock_client_patcher = patch("llm.openai_client.OpenAI")
        self.mock_openai_class = self.mock_client_patcher.start()
        self.mock_openai_instance = self.mock_openai_class.return_value
        self.mock_completions = self.mock_openai_instance.chat.completions.create

    def tearDown(self):
        self.mock_client_patcher.stop()

    def test_init_without_reasoning(self):
        client = OpenAIClient(
            model_name=self.model_name,
            api_key=self.api_key,
            temperature=self.temperature,
        )
        self.assertIsNone(client.reasoning_config)

    def test_init_with_reasoning(self):
        reasoning = {"effort": "high", "exclude": False}
        client = OpenAIClient(
            model_name=self.model_name,
            api_key=self.api_key,
            temperature=self.temperature,
            reasoning_config=reasoning,
        )
        self.assertEqual(client.reasoning_config, reasoning)

    def test_make_api_call_without_reasoning(self):
        client = OpenAIClient(
            model_name=self.model_name,
            api_key=self.api_key,
            temperature=self.temperature,
        )
        self.mock_completions.return_value.dict.return_value = {
            "choices": [{"message": {"content": "response"}}],
            "usage": {},
        }

        messages = [{"role": "user", "content": "hello"}]
        client._make_api_call(messages, self.temperature)

        self.mock_completions.assert_called_once()
        call_kwargs = self.mock_completions.call_args.kwargs
        # self.assertNotIn("extra_body", call_kwargs) # This fails because extra_body is present as None
        # Actually my implementation passes `extra_body=extra_body if extra_body else None`
        # So it might be None.
        self.assertIsNone(call_kwargs.get("extra_body"))

    def test_make_api_call_with_reasoning(self):
        reasoning = {"effort": "high", "exclude": False, "max_tokens": None}
        client = OpenAIClient(
            model_name=self.model_name,
            api_key=self.api_key,
            temperature=self.temperature,
            reasoning_config=reasoning,
        )
        self.mock_completions.return_value.dict.return_value = {
            "choices": [{"message": {"content": "response"}}],
            "usage": {},
        }

        messages = [{"role": "user", "content": "hello"}]
        client._make_api_call(messages, self.temperature)

        self.mock_completions.assert_called_once()
        call_kwargs = self.mock_completions.call_args.kwargs
        self.assertIn("extra_body", call_kwargs)
        expected_reasoning = {"effort": "high", "exclude": False}
        self.assertEqual(call_kwargs["extra_body"]["reasoning"], expected_reasoning)

    def test_make_api_call_with_reasoning_filter_none(self):
        reasoning = {"effort": "medium", "max_tokens": None, "exclude": None}
        client = OpenAIClient(
            model_name=self.model_name,
            api_key=self.api_key,
            temperature=self.temperature,
            reasoning_config=reasoning,
        )
        self.mock_completions.return_value.dict.return_value = {
            "choices": [{"message": {"content": "response"}}],
            "usage": {},
        }

        messages = [{"role": "user", "content": "hello"}]
        client._make_api_call(messages, self.temperature)

        call_kwargs = self.mock_completions.call_args.kwargs
        expected_reasoning = {"effort": "medium"}
        self.assertEqual(call_kwargs["extra_body"]["reasoning"], expected_reasoning)
