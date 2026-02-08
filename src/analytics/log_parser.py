import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from analytics.models import (GameRecord, PlayerConfig, RoleAssignment,
                              RoundRecord, SpyGuess, TurnRecord, VoteAttempt)


class LogParser:
    """Parses game logs into structured GameRecord objects."""

    def parse_directory(self, directory_path: str) -> List[GameRecord]:
        """Parse all JSON files in directory, return list of game records."""
        game_records = []
        path = Path(directory_path)

        if not path.exists() or not path.is_dir():
            logger.warning(f"Directory not found: {directory_path}")
            return []

        for file_path in path.glob("*.json"):
            record = self.parse_file(str(file_path))
            if record:
                game_records.append(record)

        return game_records

    def parse_file(self, file_path: str) -> Optional[GameRecord]:
        """Parse single JSON file, return GameRecord or None if error."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._parse_game_data(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return None

    def parse_json_string(self, json_str: str) -> Optional[GameRecord]:
        """Parse JSON string directly (useful for testing)."""
        try:
            data = json.loads(json_str)
            return self._parse_game_data(data)
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON string")
            return None
        except Exception as e:
            logger.error(f"Error processing JSON string: {e}")
            return None

    def _parse_game_data(self, data: Dict[str, Any]) -> Optional[GameRecord]:
        """Internal method to convert dictionary to GameRecord."""
        try:
            # Validate required top-level fields
            required_fields = [
                "game_id",
                "timestamp",
                "players",
                "rounds",
                "final_scores",
                "status",
            ]
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return None

            # Parse players
            players = []
            for p_data in data.get("players", []):
                players.append(
                    PlayerConfig(
                        nickname=p_data["nickname"],
                        model_name=p_data["model_name"],
                        provider=p_data.get("provider", "OPEN_ROUTER"),
                        temperature=p_data.get("temperature", 0.7),
                        reasoning=p_data.get("reasoning"),
                    )
                )

            # Parse rounds
            rounds = []
            for r_data in data.get("rounds", []):
                rounds.append(self._parse_round(r_data))

            return GameRecord(
                game_id=data["game_id"],
                timestamp=data["timestamp"],
                players=players,
                rounds=rounds,
                final_scores=data["final_scores"],
                status=data["status"],
            )
        except Exception as e:
            logger.error(f"Error converting data to GameRecord: {e}")
            return None

    def _parse_round(self, data: Dict[str, Any]) -> RoundRecord:
        """Parse round data."""
        # Parse role assignments
        role_assignments = {}
        for nickname, role_data in data.get("role_assignments", {}).items():
            role_assignments[nickname] = RoleAssignment(
                is_spy=role_data["is_spy"], location=role_data.get("location")
            )

        # Parse turns
        turns = []
        for t_data in data.get("turns", []):
            turns.append(
                TurnRecord(
                    turn_number=t_data["turn_number"],
                    asker_nickname=t_data["asker_nickname"],
                    answerer_nickname=t_data["answerer_nickname"],
                    question=t_data["question"],
                    answer=t_data["answer"],
                    timestamp=t_data["timestamp"],
                )
            )

        # Parse vote attempts
        vote_attempts = []
        for v_data in data.get("vote_attempts", []):
            vote_attempts.append(
                VoteAttempt(
                    initiator=v_data["initiator"],
                    suspect=v_data["suspect"],
                    votes=v_data["votes"],
                    passed=v_data["passed"],
                    timestamp=v_data["timestamp"],
                )
            )

        # Parse spy guess
        spy_guess = None
        if data.get("spy_guess"):
            sg_data = data["spy_guess"]
            spy_guess = SpyGuess(
                spy_nickname=sg_data["spy_nickname"],
                guessed_location=sg_data["guessed_location"],
                actual_location=sg_data["actual_location"],
                correct=sg_data["correct"],
                timestamp=sg_data["timestamp"],
            )

        return RoundRecord(
            round_number=data["round_number"],
            location=data["location"],
            spy=data["spy"],
            role_assignments=role_assignments,
            turns=turns,
            vote_attempts=vote_attempts,
            spy_guess=spy_guess,
            ending_condition=data["ending_condition"],
            round_scores=data["round_scores"],
        )
