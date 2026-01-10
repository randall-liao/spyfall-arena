import argparse
from pathlib import Path

from config.config_loader import ConfigLoader
from game.orchestrator import GameOrchestrator
from game_logging.console_setup import setup_console_logging
from game_logging.game_logger import GameLogger


def main():
    """
    Main entry point for the Spyfall Arena application.

    Orchestrates the startup sequence:
    1. Parse CLI arguments (Req 1).
    2. Initialize logging (Req 5).
    3. Load configuration (Req 1).
    4. Start the Game Orchestrator (Req 4.1).
    5. Save results (Req 8).
    """
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

    setup_console_logging(args.log_level)

    try:
        config = ConfigLoader.load_config(args.config_file)

        logger = GameLogger(config)
        logger.setup_file_logging()
        orchestrator = GameOrchestrator(config)

        game_state = orchestrator.run_game()

        logger.write_final_log(game_state)

        print(f"Game completed. Log file written to {config.logging.output_dir}")

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
