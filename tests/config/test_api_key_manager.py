import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from config.api_key_manager import ApiKeyManager


class TestApiKeyManager(unittest.TestCase):
    def setUp(self):
        # Reset the singleton instance before each test
        ApiKeyManager._instance = None
        ApiKeyManager._api_key = None
        ApiKeyManager._key_loaded = False

    @patch("keyring.get_password")
    def test_get_api_key_from_keyring(self, mock_get_password):
        """Test that the API key is correctly retrieved from the keyring."""
        mock_get_password.return_value = "keyring-api-key"

        manager = ApiKeyManager()
        api_key = manager.get_api_key()

        self.assertEqual(api_key, "keyring-api-key")
        mock_get_password.assert_called_once_with("spyfall-arena", "openrouter_api_key")

    @patch("keyring.get_password", side_effect=Exception("Keyring error"))
    @patch("pathlib.Path.is_file", return_value=True)
    @patch(
        "builtins.open",
        new_callable=unittest.mock.mock_open,
        read_data='openrouter_api_key: "config-api-key"',
    )
    def test_get_api_key_from_config_fallback(
        self, mock_open, mock_is_file, mock_get_password
    ):
        """Test that the API key is retrieved from the config file when keyring fails."""
        with self.assertWarns(UserWarning) as cm:
            manager = ApiKeyManager()
            api_key = manager.get_api_key()

            self.assertEqual(api_key, "config-api-key")
            self.assertIn("Could not access system keyring", str(cm.warnings[0].message))
            self.assertIn(
                "Loading API key from `apikeys.yaml`", str(cm.warnings[1].message)
            )

    @patch("keyring.get_password", return_value=None)
    @patch("pathlib.Path.is_file", return_value=False)
    def test_get_api_key_not_found(self, mock_is_file, mock_get_password):
        """Test that a ValueError is raised when the API key is not found."""
        manager = ApiKeyManager()
        with self.assertRaises(ValueError) as context:
            manager.get_api_key()

        self.assertIn("OpenRouter API key not found", str(context.exception))

    def test_api_key_is_loaded_only_once(self):
        """Test that the API key is loaded only once and cached."""
        with patch("keyring.get_password", return_value="api-key") as mock_get_password:
            manager = ApiKeyManager()
            manager.get_api_key()  # First call, should load the key
            manager.get_api_key()  # Second call, should use the cached key

            mock_get_password.assert_called_once()
