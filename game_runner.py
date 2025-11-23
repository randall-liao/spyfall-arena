import argparse
from pathlib import Path

from src.config.config_loader import ConfigLoader
from src.game.orchestrator import GameOrchestrator
from src.game_logging.console_setup import setup_console_logging
from src.game_logging.game_logger import GameLogger


def main():
    """Main entry point for the Spyfall Arena game runner."""
    parser = argparse.ArgumentParser(description="Run a game of Spyfall Arena.")
    parser.add_argument(
        "config_file",
        type=Path,
        help="Path to the game configuration YAML file.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the console logging verbosity.",
    )
    args = parser.parse_args()

    # Setup console logging before anything else
    setup_console_logging(args.log_level)

    try:
        config = ConfigLoader.load_config(args.config_file)

        logger = GameLogger(config)
        orchestrator = GameOrchestrator(config)

        game_state = orchestrator.run_game()

        logger.write_final_log(game_state)

        print(f"Game completed. Log file written to {config.logging.output_dir}")

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
