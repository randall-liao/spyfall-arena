import unittest
from unittest.mock import MagicMock, patch

from config.api_key_manager import ApiKeyManager


class TestApiKeyManager(unittest.TestCase):
    def setUp(self):
        # Reset the singleton instance before each test
        ApiKeyManager._instance = None
        self.manager = ApiKeyManager()

    def test_get_api_key_success(self):
        """Test retrieving the OpenRouter API key when it's already loaded."""
        self.manager._api_key = "test-key"
        self.manager._key_loaded = True
        self.assertEqual(self.manager.get_api_key(), "test-key")

    @patch("config.api_key_manager.keyring.get_password")
    def test_get_api_key_from_keyring(self, mock_get_password):
        """Test retrieving the OpenRouter API key from keyring."""
        mock_get_password.return_value = "keyring-key"
        self.assertEqual(self.manager.get_api_key(), "keyring-key")
        mock_get_password.assert_called_with("spyfall-arena", "openrouter_api_key")

    def test_get_api_key_not_found(self):
        """Test when OpenRouter API key is not found."""
        with patch("config.api_key_manager.keyring.get_password", return_value=None):
            # Also mock path check to ensure it doesn't find file
            with patch("pathlib.Path.is_file", return_value=False):
                with self.assertRaises(ValueError):
                    self.manager.get_api_key()

    def test_get_google_api_key_success(self):
        """Test retrieving the Google API key when it's already loaded."""
        self.manager._google_api_key = "test-google-key"
        self.manager._google_key_loaded = True
        self.assertEqual(self.manager.get_google_api_key(), "test-google-key")

    @patch("config.api_key_manager.keyring.get_password")
    def test_get_google_api_key_from_keyring(self, mock_get_password):
        """Test retrieving the Google API key from keyring."""
        mock_get_password.return_value = "keyring-google-key"
        self.assertEqual(self.manager.get_google_api_key(), "keyring-google-key")
        mock_get_password.assert_called_with("spyfall-arena", "google_api_key")

    @patch("config.api_key_manager.keyring.get_password")
    def test_get_google_api_key_from_file(self, mock_get_password):
        """Test retrieving the Google API key from apikeys.yaml."""
        mock_get_password.return_value = None

        mock_yaml_data = {"google_api_key": "yaml-google-key"}

        with patch("builtins.open", unittest.mock.mock_open(read_data="")):
            with patch("yaml.safe_load", return_value=mock_yaml_data):
                with patch("pathlib.Path.is_file", return_value=True):
                    self.assertEqual(self.manager.get_google_api_key(), "yaml-google-key")

    @patch("config.api_key_manager.logger")
    @patch("keyring.get_password", side_effect=Exception("Keyring error"))
    @patch("pathlib.Path.is_file", return_value=True)
    @patch(
        "builtins.open",
        new_callable=unittest.mock.mock_open,
        read_data='openrouter_api_key: "config-api-key"',
    )
    def test_get_api_key_from_config_fallback(
        self, mock_open, mock_is_file, mock_get_password, mock_logger
    ):
        """Test that the API key is retrieved from the config file when keyring fails."""
        manager = ApiKeyManager()
        api_key = manager.get_api_key()

        self.assertEqual(api_key, "config-api-key")

        # Check for the expected warning logs
        warnings = [call.args[0] for call in mock_logger.warning.call_args_list]
        self.assertTrue(any("Could not access system keyring" in w for w in warnings))
        self.assertTrue(
            any("Loading API key from `apikeys.yaml`" in w for w in warnings)
        )

    @patch("keyring.get_password", return_value=None)
    @patch("pathlib.Path.is_file", return_value=False)
    def test_get_api_key_not_found_ensure_error(self, mock_is_file, mock_get_password):
        """Test that a ValueError is raised when the API key is not found."""
        manager = ApiKeyManager()
        with self.assertRaises(ValueError) as context:
            manager.get_api_key()

        self.assertIn("OpenRouter API key not found", str(context.exception))

    def test_get_google_api_key_not_found(self):
        """Test when Google API key is not found."""
        with patch("config.api_key_manager.keyring.get_password", return_value=None):
            with patch("pathlib.Path.is_file", return_value=False):
                with self.assertRaises(ValueError):
                    self.manager.get_google_api_key()
