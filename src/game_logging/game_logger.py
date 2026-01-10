import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from loguru import logger

from config.config_schema import GameConfig
from game.game_state import GameState, RoundState
from game_logging.metrics_calculator import calculate_game_metrics, calculate_round_metrics


class GameLogger:
    """
    Handles structured JSON logging for game sessions.

    Implements 'Req 5: Logging and Data Recording' and 'Req 8: Output Specification'.
    Ensures that a full trace of the game (turns, votes, roles) is preserved for analysis.
    """

    def __init__(self, config: GameConfig):
        self.config = config
        self.log_dir = Path(config.logging.output_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def setup_file_logging(self):
        """
        Configures the Loguru sink for file-based logging.

        Separates application execution logs (INFO/DEBUG) from the structured game data JSON.
        """
        log_file = self.log_dir / "game_execution.log"
        logger.add(
            log_file,
            rotation="10 MB",
            level=self.config.logging.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        )

    def write_final_log(self, game_state: GameState) -> str:
        """
        Serializes and writes the complete game state to a JSON file.

        The output schema conforms to 'Req 5 Acceptance Criteria', containing:
        - Metadata & Config Snapshot
        - Hidden Role Assignments
        - Turn-by-turn Dialogue
        - Voting Records
        - Calculated Metrics (Req 6)
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
        """
        Aggregates game data and metrics into the final log structure.
        """
        game_metrics = calculate_game_metrics(game_state)
        
        return {
            "game_id": game_state.game_id,
            "timestamp": datetime.now().isoformat(),
            "config_snapshot": self.config.model_dump(),
            "players": [p.model_dump() for p in self.config.players],
            "rounds": [self._serialize_round(r) for r in game_state.rounds_data],
            "final_scores": game_state.player_scores,
            "status": game_state.phase.value,
            "game_metrics": asdict(game_metrics),
        }

    def _serialize_round(self, round_state: RoundState) -> dict:
        """
        Helper to serialize RoundState, including nested objects like Turns and Votes.
        """
        round_metrics = calculate_round_metrics(round_state)
        
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
            "metrics": asdict(round_metrics),
        }
