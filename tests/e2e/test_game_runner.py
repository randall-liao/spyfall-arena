import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

# Set up logging to capture output from the game runner
logging.basicConfig(level=logging.INFO)

# Add the project root to the Python path to allow importing game_runner
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import game_runner


@patch("src.llm.openai_client.OpenAI")
def test_game_runner_integration(mock_openai_class, capsys):
    """
    Integration test for the game runner.

    This test runs the main function from game_runner.py, mocking the LLM client,
    and checks for successful execution by verifying that a log file is created.
    """
    # This mock strategy is designed to end each round quickly by initiating a vote
    # and having all players vote 'yes'.
    vote_initiate_response = json.dumps(
        {"initiate_vote": True, "suspect_nickname": "Bob"}
    )
    vote_yes_response = json.dumps({"vote_yes": True})

    # The game will make one 'initiate_vote' call, followed by 4 'vote_yes' calls per round.
    # We configure 3 rounds in config.yaml.
    responses = (
        [vote_initiate_response]
        + [vote_yes_response] * 4
        + [vote_initiate_response]
        + [vote_yes_response] * 4
        + [vote_initiate_response]
        + [vote_yes_response] * 4
    )

    # Wrap the JSON string responses in the expected OpenAI API structure.
    mock_api_responses = []
    for r in responses:
        mock_completion = MagicMock()
        mock_completion.dict.return_value = {
            "choices": [{"message": {"content": r}}]
        }
        mock_api_responses.append(mock_completion)

    # Configure the mock OpenAI client instance
    mock_openai_instance = MagicMock()
    mock_openai_instance.chat.completions.create.side_effect = mock_api_responses
    mock_openai_class.return_value = mock_openai_instance

    # Mock sys.argv to pass the config file path to the main function
    test_args = ["game_runner.py", "config.yaml"]
    with patch.object(sys, "argv", test_args):
        # Call the main function
        game_runner.main()

    # Verify that the game completed successfully
    captured = capsys.readouterr()
    assert "Game completed" in captured.out

    # Check that a log file was created
    log_dir = Path("logs")
    assert log_dir.exists()
    log_files = list(log_dir.glob("*.json"))
    assert len(log_files) > 0, "No log files found in the logs directory."
