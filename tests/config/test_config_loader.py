from pathlib import Path

import pytest

from config.config_loader import ConfigLoader


@pytest.fixture
def valid_config_file(tmp_path: Path) -> Path:
    """Creates a valid YAML config file for testing."""
    config_content = """
    game:
      num_rounds: 2
    players:
      - nickname: "Tester1"
        model_name: "test-model"
      - nickname: "Tester2"
        model_name: "test-model"
    locations:
      - "Test Location 1"
      - "Test Location 2"
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def invalid_config_file(tmp_path: Path) -> Path:
    """Creates a config file with validation errors."""
    config_content = """
    players:
      - nickname: "SameName"
        model_name: "test-model"
      - nickname: "SameName"
        model_name: "test-model"
    locations: ["L1"]
    """
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def malformed_config_file(tmp_path: Path) -> Path:
    """Creates a malformed YAML file."""
    config_content = "unclosed_key: {"  # Invalid YAML syntax
    config_file = tmp_path / "malformed.yaml"
    config_file.write_text(config_content)
    return config_file


def test_load_config_success(valid_config_file: Path):
    """Tests that a valid config file is loaded correctly."""
    config = ConfigLoader.load_config(valid_config_file)
    assert config.game.num_rounds == 2
    assert len(config.players) == 2
    assert config.players[0].nickname == "Tester1"


def test_load_config_not_found():
    """Tests that a FileNotFoundError is raised for a missing config file."""
    with pytest.raises(FileNotFoundError):
        ConfigLoader.load_config(Path("non_existent_file.yaml"))


def test_load_config_validation_error(invalid_config_file: Path):
    """Tests that a ValueError is raised for a config with validation errors."""
    with pytest.raises(ValueError) as excinfo:
        ConfigLoader.load_config(invalid_config_file)
    assert "Configuration validation error" in str(excinfo.value)


def test_load_config_yaml_error(malformed_config_file: Path):
    """Tests that a ValueError is raised for a malformed YAML file."""
    with pytest.raises(ValueError) as excinfo:
        ConfigLoader.load_config(malformed_config_file)
    assert "Error parsing YAML file" in str(excinfo.value)


def test_load_config_not_a_dict(tmp_path: Path):
    """Tests that a ValueError is raised if the YAML is not a dictionary."""
    config_file = tmp_path / "not_a_dict.yaml"
    config_file.write_text("- item1\n- item2")
    with pytest.raises(ValueError) as excinfo:
        ConfigLoader.load_config(config_file)
    assert "YAML file is not a valid dictionary" in str(excinfo.value)
