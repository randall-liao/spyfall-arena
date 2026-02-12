import unittest
from unittest.mock import MagicMock, patch

from tenacity import RetryCallState

from llm.exceptions import MaxRetriesExceededError
from llm.gemini_client import GeminiClient, wait_from_google_retry_info


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

    @patch("time.sleep", return_value=None)
    def test_make_api_call_retry_success(self, mock_sleep):
        messages = [{"role": "user", "content": "Retry me"}]
        mock_response = MagicMock()
        mock_response.text = "Success"

        # Simulate 2 failures then success
        # We need an exception that triggers the retry.
        # Our predicate checks "429" in str(e) or e.code == 429.
        error_429 = Exception("429 RESOURCE_EXHAUSTED")

        self.mock_client_instance.models.generate_content.side_effect = [
            error_429,
            error_429,
            mock_response,
        ]

        response = self.client._make_api_call(messages, temperature=0.5)

        self.assertEqual(response, {"text": "Success"})
        self.assertEqual(
            self.mock_client_instance.models.generate_content.call_count, 3
        )

    @patch("time.sleep", return_value=None)
    def test_make_api_call_retry_failure(self, mock_sleep):
        messages = [{"role": "user", "content": "Fail me"}]

        error_429 = Exception("429 RESOURCE_EXHAUSTED")
        self.mock_client_instance.models.generate_content.side_effect = error_429

        with self.assertRaises(MaxRetriesExceededError) as cm:
            self.client._make_api_call(messages, temperature=0.5)

        self.assertIn("429", str(cm.exception))
        self.assertEqual(cm.exception.attempts, 3)
        self.assertEqual(
            self.mock_client_instance.models.generate_content.call_count, 3
        )

    @patch("time.sleep", return_value=None)
    def test_make_api_call_no_retry_on_other_error(self, mock_sleep):
        messages = [{"role": "user", "content": "Fail me once"}]

        error_500 = Exception("500 Internal Server Error")
        self.mock_client_instance.models.generate_content.side_effect = error_500

        with self.assertRaises(Exception) as cm:
            self.client._make_api_call(messages, temperature=0.5)

        self.assertIn("500", str(cm.exception))
        self.assertEqual(
            self.mock_client_instance.models.generate_content.call_count, 1
        )

    def test_make_api_call_checks_rate_limiter(self):
        mock_limiter = MagicMock()
        self.client.rate_limiter = mock_limiter

        messages = [{"role": "user", "content": "Hello"}]
        mock_response = MagicMock()
        mock_response.text = "Hello"
        self.mock_client_instance.models.generate_content.return_value = mock_response

        self.client._make_api_call(messages, temperature=0.5)

        mock_limiter.wait_for_token.assert_called_once()

    def test_wait_from_google_retry_info_with_details(self):
        # Mocking the RetryCallState and Exception structure
        mock_retry_state = MagicMock(spec=RetryCallState)
        mock_exception = MagicMock()

        # Structure: exc.details = [{'@type': '...RetryInfo', 'retryDelay': '21.5s'}]
        mock_exception.details = [
            {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "21.5s"}
        ]

        mock_outcome = MagicMock()
        mock_outcome.exception.return_value = mock_exception
        mock_retry_state.outcome = mock_outcome

        wait_time = wait_from_google_retry_info(mock_retry_state)
        # Expected: 21.5s + 3.0s buffer = 24.5s
        self.assertEqual(wait_time, 24.5)

    def test_wait_from_google_retry_info_default(self):
        # Case where no retry info is present
        mock_retry_state = MagicMock(spec=RetryCallState)
        mock_exception = MagicMock()
        mock_exception.details = []  # Empty details

        mock_outcome = MagicMock()
        mock_outcome.exception.return_value = mock_exception
        mock_retry_state.outcome = mock_outcome

        wait_time = wait_from_google_retry_info(mock_retry_state)
        # Should return default 15s (no buffer applied to default)
        self.assertEqual(wait_time, 15.0)

    def test_wait_from_google_retry_info_nested_args(self):
        # Case where details are in args[0] (dict wrapper)
        mock_retry_state = MagicMock(spec=RetryCallState)
        mock_exception = Exception(
            {
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.RetryInfo",
                        "retryDelay": "10s",
                    }
                ]
            }
        )

        mock_outcome = MagicMock()
        mock_outcome.exception.return_value = mock_exception
        mock_retry_state.outcome = mock_outcome

        wait_time = wait_from_google_retry_info(mock_retry_state)
        # Expected: 10s + 3.0s buffer = 13.0s
        self.assertEqual(wait_time, 13.0)

    def test_wait_from_google_retry_info_invalid_string(self):
        mock_retry_state = MagicMock(spec=RetryCallState)
        mock_exception = MagicMock()
        mock_exception.details = [
            {
                "@type": "type.googleapis.com/google.rpc.RetryInfo",
                "retryDelay": "invalid",
            }
        ]
        mock_outcome = MagicMock()
        mock_outcome.exception.return_value = mock_exception
        mock_retry_state.outcome = mock_outcome

        # Should fallback to default because parsing fails
        self.assertEqual(wait_from_google_retry_info(mock_retry_state), 15.0)

    def test_wait_from_google_retry_info_protobuf(self):
        mock_retry_state = MagicMock(spec=RetryCallState)
        mock_exception = MagicMock()

        # Mocking a protobuf-like object
        mock_detail = MagicMock()
        mock_detail.retry_delay.seconds = 5
        mock_detail.retry_delay.nanos = 500000000  # 0.5s
        # Only has retry_delay, doesn't match dict check
        mock_exception.details = [mock_detail]

        mock_outcome = MagicMock()
        mock_outcome.exception.return_value = mock_exception
        mock_retry_state.outcome = mock_outcome

        # Expected: 5.5s + 3.0s buffer = 8.5s
        self.assertEqual(wait_from_google_retry_info(mock_retry_state), 8.5)

    def test_wait_from_google_retry_info_protobuf_error(self):
        mock_retry_state = MagicMock(spec=RetryCallState)
        mock_exception = MagicMock()

        # Mocking a protobuf-like object that raises error on property access
        class BadRetryDelay:
            @property
            def retry_delay(self):
                # This mimics the attribute existing but raising on access?
                # No, we want hasattr(detail, 'retry_delay') to be True
                # But accessing detail.retry_delay to raise? or detail.retry_delay.seconds?
                # The code: hasattr(detail, "retry_delay") -> True
                # try: float(detail.retry_delay.seconds) ...
                # So we return an object whose .seconds raises.
                return self

            @property
            def seconds(self):
                raise AttributeError("Fail")

        mock_detail = BadRetryDelay()
        mock_exception.details = [mock_detail]

        mock_outcome = MagicMock()
        mock_outcome.exception.return_value = mock_exception
        mock_retry_state.outcome = mock_outcome

        self.assertEqual(wait_from_google_retry_info(mock_retry_state), 15.0)

    def test_init_with_rate_limiter(self):
        mock_limiter = MagicMock()
        client = GeminiClient(self.model_name, self.api_key, rate_limiter=mock_limiter)
        self.assertEqual(client.rate_limiter, mock_limiter)

    def test_wait_from_google_retry_info_no_outcome(self):
        mock_retry_state = MagicMock(spec=RetryCallState)
        mock_retry_state.outcome = None
        self.assertEqual(wait_from_google_retry_info(mock_retry_state), 15.0)

        mock_retry_state.outcome = MagicMock()
        mock_retry_state.outcome.exception.return_value = None
        self.assertEqual(wait_from_google_retry_info(mock_retry_state), 15.0)

    def test_wait_from_google_retry_info_dict_structure(self):
        mock_retry_state = MagicMock(spec=RetryCallState)
        mock_exception = MagicMock()

        # Structure found in real ClientError: {'error': {'details': [...]}}
        # But ClientError.details returns this dict directly
        mock_exception.details = {
            "error": {
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.RetryInfo",
                        "retryDelay": "25s",
                    }
                ]
            }
        }

        mock_outcome = MagicMock()
        mock_outcome.exception.return_value = mock_exception
        mock_retry_state.outcome = mock_outcome

        mock_retry_state.outcome = mock_outcome

        # Expected: 25s + 3.0s buffer = 28.0s
        self.assertEqual(wait_from_google_retry_info(mock_retry_state), 28.0)

    def test_wait_from_google_retry_info_dict_structure_flat(self):
        mock_retry_state = MagicMock(spec=RetryCallState)
        mock_exception = MagicMock()

        # Structure: {'details': [...]} (hypothetical)
        mock_exception.details = {
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.RetryInfo",
                    "retryDelay": "20s",
                }
            ]
        }

        mock_outcome = MagicMock()
        mock_outcome.exception.return_value = mock_exception
        mock_retry_state.outcome = mock_outcome

        # Expected: 20s + 3.0s buffer = 23.0s
        self.assertEqual(wait_from_google_retry_info(mock_retry_state), 23.0)
