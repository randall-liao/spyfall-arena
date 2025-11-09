from pathlib import Path

import yaml
from pydantic import ValidationError

from config.config_schema import GameConfig


class ConfigLoader:
    """Loads and validates the game configuration from a YAML file."""

    @staticmethod
    def load_config(config_path: Path) -> GameConfig:
        """
        Loads the configuration from a given path.

        Args:
            config_path: The path to the YAML configuration file.

        Returns:
            A validated GameConfig object.

        Raises:
            FileNotFoundError: If the config file does not exist.
            ValueError: If the config file is malformed (YAML error or validation error).
        """
        if not config_path.is_file():
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")

        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)
                if not isinstance(config_data, dict):
                    raise ValueError("YAML file is not a valid dictionary.")
                return GameConfig(**config_data)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}") from e
        except ValidationError as e:
            raise ValueError(f"Configuration validation error: {e}") from e
