import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from spyfall_arena.config.config_schema import GameConfig
from spyfall_arena.game.game_state import GameState, RoundState


class GameLogger:
    """Handles structured JSON logging for a complete game of Spyfall."""

    def __init__(self, config: GameConfig):
        self.config = config
        self.log_dir = Path(config.logging.output_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_loguru()

    def _setup_loguru(self):
        """Configures Loguru for game execution logging."""
        log_file = self.log_dir / "game_execution.log"
        logger.add(
            log_file,
            rotation="10 MB",
            level=self.config.logging.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        )

    def write_final_log(self, game_state: GameState) -> str:
        """
        Writes the complete game state to a structured JSON log file.

        Args:
            game_state: The final state of the game.

        Returns:
            The path to the written log file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_game_{game_state.game_id}.json"
        filepath = self.log_dir / filename

        log_data = self._build_log_structure(game_state)

        with open(filepath, "w") as f:
            json.dump(log_data, f, indent=2, default=str)

        logger.success(f"Game log written to: {filepath}")
        return str(filepath)

    def _build_log_structure(self, game_state: GameState) -> dict:
        """Builds the complete log structure from the game state."""
        return {
            "game_id": game_state.game_id,
            "timestamp": datetime.now().isoformat(),
            "config_snapshot": self.config.model_dump(),
            "players": [p.model_dump() for p in self.config.players],
            "rounds": [self._serialize_round(r) for r in game_state.rounds_data],
            "final_scores": game_state.player_scores,
            "status": game_state.phase.value,
        }

    def _serialize_round(self, round_state: RoundState) -> dict:
        """Serializes a RoundState object to a dictionary."""
        return {
            "round_number": round_state.round_number,
            "location": round_state.location,
            "spy": round_state.spy_nickname,
            "role_assignments": {
                p: r.__dict__ for p, r in round_state.role_assignments.items()
            },
            "turns": [t.__dict__ for t in round_state.conversation_history],
            "vote_attempts": [v.__dict__ for v in round_state.votes],
            "spy_guess": (
                round_state.spy_guess.__dict__ if round_state.spy_guess else None
            ),
            "ending_condition": round_state.ending_condition,
            "round_scores": round_state.round_scores,
        }
