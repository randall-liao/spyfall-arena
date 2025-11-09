import pytest
from pydantic import ValidationError

from spyfall_arena.config.config_schema import (GameConfig, LoggingConfig,
                                                PlayerConfig)


def test_valid_config():
    """Tests that a valid configuration is parsed correctly."""
    config_data = {
        "game": {"num_rounds": 5},
        "players": [
            {"nickname": "Alice", "model_name": "gpt-4"},
            {"nickname": "Bob", "model_name": "claude-3"},
        ],
        "locations": ["Bank", "Airport"],
    }
    config = GameConfig(**config_data)
    assert config.game.num_rounds == 5
    assert config.game.random_seed == 42  # Default value
    assert len(config.players) == 2
    assert config.players[0].nickname == "Alice"
    assert config.logging.log_level == "INFO"  # Default value


def test_default_game_config():
    """Tests that default values are used when the 'game' section is missing."""
    config_data = {
        "players": [
            {"nickname": "A", "model_name": "m1"},
            {"nickname": "B", "model_name": "m2"},
        ],
        "locations": ["L1"],
    }
    config = GameConfig(**config_data)
    assert config.game.num_rounds == 3
    assert config.game.max_turns_per_round == 20


def test_invalid_player_count():
    """Tests that an error is raised for an invalid number of players."""
    # Test for too few players
    with pytest.raises(ValidationError):
        GameConfig(players=[{"nickname": "A", "model_name": "m1"}], locations=["L1"])

    # Test for too many players
    players = [{"nickname": f"p{i}", "model_name": "m"} for i in range(13)]
    with pytest.raises(ValidationError):
        GameConfig(players=players, locations=["L1"])


def test_duplicate_nicknames():
    """Tests that an error is raised for duplicate player nicknames."""
    with pytest.raises(ValidationError) as excinfo:
        GameConfig(
            players=[
                {"nickname": "Alice", "model_name": "m1"},
                {"nickname": "Alice", "model_name": "m2"},
            ],
            locations=["L1"],
        )
    assert "Player nicknames must be unique" in str(excinfo.value)


def test_duplicate_locations():
    """Tests that an error is raised for duplicate locations."""
    with pytest.raises(ValidationError) as excinfo:
        GameConfig(
            players=[
                {"nickname": "A", "model_name": "m1"},
                {"nickname": "B", "model_name": "m2"},
            ],
            locations=["Bank", "Bank"],
        )
    assert "Locations must be unique" in str(excinfo.value)


def test_invalid_temperature():
    """Tests that an error is raised for an invalid player temperature."""
    with pytest.raises(ValidationError):
        PlayerConfig(nickname="A", model_name="m1", temperature=-0.5)
    with pytest.raises(ValidationError):
        PlayerConfig(nickname="A", model_name="m1", temperature=2.1)


def test_invalid_log_level():
    """Tests that an error is raised for an invalid log level."""
    with pytest.raises(ValidationError) as excinfo:
        LoggingConfig(log_level="INVALID_LEVEL")
    assert "log_level must be one of" in str(excinfo.value)


def test_log_level_case_insensitivity():
    """Tests that the log level validation is case-insensitive."""
    config = LoggingConfig(log_level="debug")
    assert config.log_level == "DEBUG"
