from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from config.config_schema import (
    GameConfig,
    GameRulesConfig,
    LoggingConfig,
    PlayerConfig,
)
from game.game_state import GamePhase, GameState, RoundPhase, RoundState
from game_logging.game_logger import GameLogger
from game_logging.metrics_calculator import GameMetrics, RoundMetrics


@pytest.fixture
def mock_config() -> GameConfig:
    """Returns a mock GameConfig object for testing."""
    return GameConfig(
        game=GameRulesConfig(),
        players=[
            PlayerConfig(nickname="Alice", model_name="claude-3-opus-20240229"),
            PlayerConfig(nickname="Bob", model_name="claude-3-sonnet-20240229"),
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
    round_state.conversation_history.append(
        MagicMock(nickname="Alice", utterance="...")
    )
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
        logger_instance = GameLogger(config=mock_config)
        logger_instance.setup_file_logging()
        mock_logger_add.assert_called_once()
        args, kwargs = mock_logger_add.call_args
        assert args[0] == Path(mock_config.logging.output_dir) / "game_execution.log"
        assert kwargs["level"] == "INFO"


def test_metrics_integration_in_log(
    mock_config: GameConfig, mock_game_state: GameState, tmp_path: Path
):
    """Tests that metrics are calculated and included in the log."""
    mock_config.logging.output_dir = str(tmp_path)
    logger_instance = GameLogger(config=mock_config)

    # Needs to ensure Mocks in mock_game_state have enough data for metrics calculator
    # The fixture mock_game_state has MagicMocks which might fail when attributes are accessed

    # Let's inspect mock_game_state fixture usage.
    # It creates a RoundState with mocked role assignments.
    # We might need to make it more concrete for metrics calculator to not crash or just mock the calculator methods.

    # However, this test is an integration test for GameLogger using real MetricsCalculator?
    # Or should we mock MetricsCalculator?
    # The task says "Integrate metrics into GameLogger".

    # If we want to test that GameLogger CALLS metrics calculator and puts result in JSON:
    with (
        patch("game_logging.game_logger.calculate_game_metrics") as mock_calc_game,
        patch("game_logging.game_logger.calculate_round_metrics") as mock_calc_round,
        patch("builtins.open", mock_open()),
        patch("json.dump") as mock_json_dump,
    ):
        # Return real dataclasses so asdict() works
        mock_game_metrics = GameMetrics(
            spy_wins=1,
            civilian_wins=0,
            avg_turns_per_round=10.0,
            overall_winner="Alice",
        )
        mock_calc_game.return_value = mock_game_metrics

        mock_round_metrics = RoundMetrics(
            winner_side="spy",
            spy_caught=False,
            spy_guessed_correctly=True,
            total_turns=10,
            vote_accuracy=None,
            avg_question_length=5.0,
            avg_answer_length=5.0,
        )
        mock_calc_round.return_value = mock_round_metrics

        logger_instance.write_final_log(game_state=mock_game_state)

        args, _ = mock_json_dump.call_args
        written_data = args[0]

        assert "game_metrics" in written_data
        assert written_data["game_metrics"]["spy_wins"] == 1

        assert "metrics" in written_data["rounds"][0]
        assert written_data["rounds"][0]["metrics"]["winner_side"] == "spy"

        mock_calc_game.assert_called_once()
        mock_calc_round.assert_called()
