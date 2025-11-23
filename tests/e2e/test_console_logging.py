import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import game_runner

@pytest.fixture
def mock_openai():
    with patch("llm.openai_client.OpenAI") as mock_class, \
         patch("config.api_key_manager.keyring.get_password", return_value="fake_key"):

        mock_instance = MagicMock()

        # Setup a sequence of responses that allows the game to proceed through a round
        # 1. Vote initiation (Yes, suspect Bob) -> Ends round immediately
        vote_initiate_response = json.dumps(
            {"initiate_vote": True, "suspect_nickname": "Bob"}
        )
        vote_yes_response = json.dumps({"vote_yes": True})

        # 3 rounds * (1 initiation + 4 votes)
        responses = [vote_initiate_response] + [vote_yes_response] * 4
        responses = responses * 3

        mock_api_responses = []
        for r in responses:
            mock_completion = MagicMock()
            mock_completion.dict.return_value = {
                "choices": [{"message": {"content": r}}]
            }
            mock_api_responses.append(mock_completion)

        mock_instance.chat.completions.create.side_effect = mock_api_responses
        mock_class.return_value = mock_instance
        yield mock_class

def test_console_logging_debug(mock_openai, capsys):
    """Verifies that DEBUG logs are emitted when --log-level DEBUG is set."""
    test_args = ["game_runner.py", "config.yaml", "--log-level", "DEBUG"]

    with patch.object(sys, "argv", test_args):
        try:
            game_runner.main()
        except Exception:
            pass

    captured = capsys.readouterr()
    stderr = captured.err

    # Verify DEBUG level logs appear
    assert "DEBUG" in stderr
    # Verify specific debug messages from components
    assert "Generating structured response" in stderr  # From BaseLLMClient
    assert "Raw LLM structured response" in stderr # DEBUG from BaseLLMClient

    # Verify INFO logs
    assert "Starting Game" in stderr

def test_console_logging_error_suppression(mock_openai, capsys):
    """Verifies that INFO logs are suppressed when --log-level ERROR is set."""
    test_args = ["game_runner.py", "config.yaml", "--log-level", "ERROR"]

    with patch.object(sys, "argv", test_args):
        try:
            game_runner.main()
        except Exception:
            pass

    captured = capsys.readouterr()
    stderr = captured.err

    # Verify INFO logs are ABSENT
    assert "Starting Game" not in stderr
    assert "Starting Round" not in stderr

    # Verify DEBUG logs are ABSENT
    assert "DEBUG" not in stderr
