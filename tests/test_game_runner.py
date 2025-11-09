from unittest.mock import MagicMock, patch

import pytest

import game_runner


@patch("game_runner.GameLogger")
@patch("game_runner.GameOrchestrator")
@patch("game_runner.ConfigLoader")
@patch("argparse.ArgumentParser.parse_args")
def test_main_success(
    mock_parse_args, mock_config_loader, mock_orchestrator, mock_logger
):
    """Tests the successful execution of the main function."""
    mock_parse_args.return_value.config_file = "config.yaml"

    game_runner.main()

    mock_config_loader.load_config.assert_called_once_with("config.yaml")
    mock_orchestrator.assert_called_once()
    mock_logger.assert_called_once()
    mock_orchestrator.return_value.run_game.assert_called_once()
    mock_logger.return_value.write_final_log.assert_called_once()


@patch(
    "game_runner.ConfigLoader.load_config",
    side_effect=FileNotFoundError("File not found"),
)
@patch("argparse.ArgumentParser.parse_args")
def test_main_file_not_found(mock_parse_args, mock_load_config):
    """Tests that a FileNotFoundError is handled correctly."""
    mock_parse_args.return_value.config_file = "non_existent.yaml"
    game_runner.main()
    # We just need to ensure the program doesn't crash. The error message is printed to stdout.


@patch("game_runner.ConfigLoader.load_config", side_effect=ValueError("Invalid config"))
@patch("argparse.ArgumentParser.parse_args")
def test_main_value_error(mock_parse_args, mock_load_config):
    """Tests that a ValueError is handled correctly."""
    mock_parse_args.return_value.config_file = "invalid.yaml"
    game_runner.main()
    # We just need to ensure the program doesn't crash. The error message is printed to stdout.
