from pathlib import Path
from typing import Optional

import keyring
import yaml
from loguru import logger


class ApiKeyManager:
    """Singleton for secure API key retrieval (keyring-first, YAML fallback).

    Supports PRD Section 4.2 multi-provider requirement. Keys are cached
    after first load to avoid repeated I/O.
    """

    _instance = None
    _api_key: Optional[str] = None
    _key_loaded: bool = False
    _google_api_key: Optional[str] = None
    _google_key_loaded: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_api_key(self) -> str:
        """Return OpenRouter API key; raise ValueError if unavailable."""
        if not self._key_loaded:
            self._load_api_key()
            self._key_loaded = True

        if self._api_key is None:
            raise ValueError(
                "OpenRouter API key not found. Please set it up in the system keyring or `apikeys.yaml`."
            )

        return self._api_key

    def get_google_api_key(self) -> str:
        """Return Google API key; raise ValueError if unavailable."""
        if not self._google_key_loaded:
            self._load_google_api_key()
            self._google_key_loaded = True

        if self._google_api_key is None:
            raise ValueError(
                "Google API key not found. Please set it up in the system keyring or `apikeys.yaml`."
            )

        return self._google_api_key

    def _load_api_key(self) -> None:
        """Loads the OpenRouter API key from the supported sources."""
        # Try to get the key from the system keyring first
        try:
            logger.debug("Attempting to load API key from system keyring.")
            key = keyring.get_password("spyfall-arena", "openrouter_api_key")
            if key:
                self._api_key = key
                logger.info("API key loaded successfully from system keyring.")
                return
        except Exception as e:
            logger.warning(
                f"Could not access system keyring. Falling back to config file. Error: {e}"
            )

        # Fallback to `apikeys.yaml`
        config_path = Path(__file__).resolve().parents[2] / "apikeys.yaml"
        if config_path.is_file():
            try:
                logger.debug(f"Attempting to load API key from {config_path}")
                with open(config_path, "r") as f:
                    config_data = yaml.safe_load(f)
                    key = config_data.get("openrouter_api_key")
                    if key and key != "your-open-router-api-key-goes-here":
                        self._api_key = key
                        logger.warning(
                            "Loading API key from `apikeys.yaml`. "
                            "This is not recommended for production. "
                            "Use a secure credential manager instead."
                        )
                        return
            except (yaml.YAMLError, IOError) as e:
                logger.warning(f"Error reading `apikeys.yaml`: {e}")

        # If we reach here, the key was not found
        self._api_key = None

    def _load_google_api_key(self) -> None:
        """Loads the Google API key from the supported sources."""
        # Try to get the key from the system keyring first
        try:
            logger.debug("Attempting to load Google API key from system keyring.")
            key = keyring.get_password("spyfall-arena", "google_api_key")
            if key:
                self._google_api_key = key
                logger.info("Google API key loaded successfully from system keyring.")
                return
        except Exception as e:
            logger.warning(
                f"Could not access system keyring. Falling back to config file. Error: {e}"
            )

        # Fallback to `apikeys.yaml`
        config_path = Path(__file__).resolve().parents[2] / "apikeys.yaml"
        if config_path.is_file():
            try:
                logger.debug(f"Attempting to load Google API key from {config_path}")
                with open(config_path, "r") as f:
                    config_data = yaml.safe_load(f)
                    key = config_data.get("google_api_key")
                    if key and key != "your-google-api-key-goes-here":
                        self._google_api_key = key
                        logger.warning(
                            "Loading Google API key from `apikeys.yaml`. "
                            "This is not recommended for production. "
                            "Use a secure credential manager instead."
                        )
                        return
            except (yaml.YAMLError, IOError) as e:
                logger.warning(f"Error reading `apikeys.yaml`: {e}")

        # If we reach here, the key was not found
        self._google_api_key = None
