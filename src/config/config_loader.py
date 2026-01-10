from pathlib import Path

import yaml
from loguru import logger
from pydantic import ValidationError

from config.config_schema import GameConfig


class ConfigLoader:
    """
    Handles loading and validation of game configuration.

    Implements 'Req 1: Configuration Management (via File)', ensuring
    the system can be initialized with reproducible settings from a YAML/JSON file.
    """

    @staticmethod
    def load_config(config_path: Path) -> GameConfig:
        """
        Parses and validates the configuration file.

        Uses Pydantic for schema validation to ensure all required parameters
        (Req 1) are present and correct before game start.
        """
        logger.info(f"Loading configuration from {config_path}")
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
