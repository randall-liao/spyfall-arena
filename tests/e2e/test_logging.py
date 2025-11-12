import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from game.game_state import GamePhase
from game_runner import main as game_runner_main


def test_e2e_logging_from_main():
    """
    Tests that a structured JSON log is created by running the main game runner.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary config file that points to the temp log directory
        test_config_path = Path("tests/e2e/test_config.yaml")
        with open(test_config_path, "r") as f:
            config_content = f.read()

        temp_config_content = config_content.replace(
            'output_dir: "test_logs"', f'output_dir: "{temp_dir}"'
        )

        temp_config_path = Path(temp_dir) / "temp_config.yaml"
        with open(temp_config_path, "w") as f:
            f.write(temp_config_content)

        mock_llm_client = MagicMock()
        mock_llm_client.generate_structured_response.return_value = {
            "make_guess": True,
            "location_guess": "Test Location 3",
        }

        with patch("sys.argv", ["game_runner.py", str(temp_config_path)]), \
             patch("llm.llm_client_factory.LLMClientFactory.create_client", return_value=mock_llm_client):
            game_runner_main()

        # Verify that a log file was created
        log_files = list(Path(temp_dir).glob("*.json"))
        assert len(log_files) == 1
        log_file = log_files[0]

        # Verify the log content
        with open(log_file, "r") as f:
            log_data = json.load(f)

        assert log_data["status"] == GamePhase.COMPLETED.value
        assert len(log_data["rounds"]) == 1
        assert log_data["final_scores"]["Alice"] == 4
