from pathlib import Path

import yaml
from loguru import logger
from pydantic import ValidationError

from config.config_schema import GameConfig


class ConfigLoader:
    """Load and validate game config per PRD Section 1 (Configuration Management)."""

    @staticmethod
    def load_config(config_path: Path) -> GameConfig:
        """Parse YAML file and return validated GameConfig."""
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
