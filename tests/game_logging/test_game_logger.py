import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from loguru import logger

from config.config_schema import GameConfig, LoggingConfig, PlayerConfig
from game.game_state import GamePhase, GameState, RoundPhase, RoundState
from game_logging.game_logger import GameLogger


@pytest.fixture
def mock_config() -> GameConfig:
    """Returns a mock GameConfig object for testing."""
    return GameConfig(
        game_rules=MagicMock(),
        players=[
            PlayerConfig(
                nickname="Alice", model_name="claude-3-opus-20240229"
            ),
            PlayerConfig(
                nickname="Bob", model_name="claude-3-sonnet-20240229"
            ),
        ],
        locations=["Beach", "Library", "Hospital"],
        logging=LoggingConfig(output_dir="/tmp/spyfall_logs", log_level="INFO"),
    )


@pytest.fixture
def mock_game_state() -> GameState:
    """Returns a mock GameState object for testing."""
    game_state = GameState(game_id="test_game_123", phase=GamePhase.COMPLETED)
    game_state.player_scores = {"Alice": 10, "Bob": 0}

    # Add a round
    round_state = RoundState(
        round_number=1,
        phase=RoundPhase.COMPLETED,
        location="Beach",
        spy_nickname="Bob",
        role_assignments={
            "Alice": MagicMock(role="Lifeguard", description="..."),
            "Bob": MagicMock(role="Spy", description="..."),
        },
    )
    round_state.conversation_history.append(MagicMock(nickname="Alice", utterance="..."))
    round_state.votes.append(MagicMock(voter="Alice", voted_for="Bob", outcome="..."))
    round_state.spy_guess = MagicMock(guesser="Bob", location="...s", is_correct=False)
    round_state.ending_condition = "Voted out"
    round_state.round_scores = {"Alice": 10, "Bob": 0}
    game_state.rounds_data.append(round_state)

    return game_state


def test_game_logger_init(mock_config: GameConfig):
    """Tests that the GameLogger initializes and creates the log directory."""
    with patch("pathlib.Path.mkdir") as mock_mkdir:
        logger = GameLogger(config=mock_config)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        assert logger.log_dir == Path(mock_config.logging.output_dir)


def test_write_final_log(
    mock_config: GameConfig, mock_game_state: GameState, tmp_path: Path
):
    """Tests writing the final game log to a JSON file."""
    # Override the log directory to use the temporary path
    mock_config.logging.output_dir = str(tmp_path)
    logger_instance = GameLogger(config=mock_config)

    # Mock the open call to inspect what's being written
    m = mock_open()
    with patch("builtins.open", m), patch("json.dump") as mock_json_dump:
        log_path = logger_instance.write_final_log(game_state=mock_game_state)

        # Verify the file path and name
        assert log_path.startswith(str(tmp_path))
        assert "game_test_game_123.json" in log_path

        # Verify that open was called correctly
        m.assert_called_once_with(Path(log_path), "w")

        # Get the actual data passed to json.dump
        args, _ = mock_json_dump.call_args
        written_data = args[0]

        # Assertions on the written data
        assert written_data["game_id"] == "test_game_123"
        assert written_data["status"] == "completed"
        assert len(written_data["rounds"]) == 1
        assert written_data["rounds"][0]["location"] == "Beach"


def test_loguru_setup(mock_config: GameConfig):
    """Tests that Loguru is configured correctly."""
    with patch("loguru.logger.add") as mock_logger_add:
        GameLogger(config=mock_config)
        mock_logger_add.assert_called_once()
        args, kwargs = mock_logger_add.call_args
        assert args[0] == Path(mock_config.logging.output_dir) / "game_execution.log"
        assert kwargs["level"] == "INFO"
