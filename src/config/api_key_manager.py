import warnings
from pathlib import Path
from typing import Optional

import keyring
import yaml


class ApiKeyManager:
    """A singleton class to manage the OpenRouter API key."""

    _instance = None
    _api_key: Optional[str] = None
    _key_loaded: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_api_key(self) -> str:
        """
        Retrieves the OpenRouter API key.

        The key is loaded only once and stored in memory. The loading order is:
        1. System keyring (recommended)
        2. `apikeys.yaml` file (fallback with a warning)

        Returns:
            The OpenRouter API key.

        Raises:
            ValueError: If the API key cannot be found in any of the sources.
        """
        if not self._key_loaded:
            self._load_api_key()
            self._key_loaded = True

        if self._api_key is None:
            raise ValueError(
                "OpenRouter API key not found. Please set it up in the system keyring or `apikeys.yaml`."
            )

        return self._api_key

    def _load_api_key(self) -> None:
        """Loads the API key from the supported sources."""
        # Try to get the key from the system keyring first
        try:
            key = keyring.get_password("spyfall-arena", "openrouter_api_key")
            if key:
                self._api_key = key
                return
        except Exception as e:
            warnings.warn(f"Could not access system keyring. Falling back to config file. Error: {e}")

        # Fallback to `apikeys.yaml`
        config_path = Path(__file__).resolve().parents[2] / "apikeys.yaml"
        if config_path.is_file():
            try:
                with open(config_path, "r") as f:
                    config_data = yaml.safe_load(f)
                    key = config_data.get("openrouter_api_key")
                    if key and key != "your-open-router-api-key-goes-here":
                        self._api_key = key
                        warnings.warn(
                            "Loading API key from `apikeys.yaml`. "
                            "This is not recommended for production. "
                            "Use a secure credential manager instead."
                        )
                        return
            except (yaml.YAMLError, IOError) as e:
                warnings.warn(f"Error reading `apikeys.yaml`: {e}")

        # If we reach here, the key was not found
        self._api_key = None
