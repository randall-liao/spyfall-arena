import sys
from unittest.mock import MagicMock, patch

from game_logging.console_setup import setup_console_logging


def test_setup_console_logging_calls() -> None:
    """Verifies that setup_console_logging calls remove and add on the logger."""
    with patch("game_logging.console_setup.logger") as mock_logger:
        setup_console_logging("DEBUG")

        mock_logger.remove.assert_called_once()
        mock_logger.add.assert_called_once()

        # Verify the sink is sys.stderr and level is correct
        args, kwargs = mock_logger.add.call_args
        assert args[0] == sys.stderr
        assert kwargs["level"] == "DEBUG"
        assert "format" in kwargs

def test_setup_console_logging_default() -> None:
    """Verifies default log level is INFO (or whatever is passed, actually defaults to INFO in args usually)."""
    # The function has a default arg "INFO"
    with patch("game_logging.console_setup.logger") as mock_logger:
        setup_console_logging()

        mock_logger.add.assert_called_once()
        args, kwargs = mock_logger.add.call_args
        assert kwargs["level"] == "INFO"
