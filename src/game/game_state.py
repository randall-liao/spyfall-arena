from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set


class GamePhase(Enum):
    """Game-level states"""

    INITIALIZING = "initializing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class RoundPhase(Enum):
    """Round-level states"""

    ROLE_ASSIGNMENT = "role_assignment"
    QUESTIONING = "questioning"
    VOTING = "voting"
    SPY_GUESSING = "spy_guessing"
    SCORING = "scoring"
    COMPLETED = "completed"


@dataclass
class Role:
    is_spy: bool
    location: Optional[str]  # None for spy, actual location for civilians


@dataclass
class Turn:
    turn_number: int
    asker_nickname: str
    answerer_nickname: str
    question: str
    answer: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class VoteAttempt:
    initiator: str
    suspect: str
    votes: Dict[str, bool]  # nickname -> yes/no
    passed: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SpyGuess:
    spy_nickname: str
    guessed_location: str
    actual_location: str
    correct: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class GameError:
    error_type: str
    message: str
    player_nickname: Optional[str] = None
    turn_number: Optional[int] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    recovered: bool = False


@dataclass
class RoundState:
    round_number: int
    phase: RoundPhase
    location: str
    spy_nickname: str
    role_assignments: Dict[str, Role]
    conversation_history: List[Turn] = field(default_factory=list)
    votes: List[VoteAttempt] = field(default_factory=list)
    spy_guess: Optional[SpyGuess] = None
    ending_condition: Optional[str] = None
    round_scores: Dict[str, int] = field(default_factory=dict)
    current_asker: Optional[str] = None
    previous_asker: Optional[str] = None
    players_who_voted: Set[str] = field(default_factory=set)

    def transition_to(self, new_phase: RoundPhase) -> bool:
        """Validates and executes state transition"""
        if self._is_valid_transition(self.phase, new_phase):
            self.phase = new_phase
            return True
        return False

    def _is_valid_transition(
        self, from_phase: RoundPhase, to_phase: RoundPhase
    ) -> bool:
        """Defines valid state transitions"""
        valid_transitions = {
            RoundPhase.ROLE_ASSIGNMENT: [RoundPhase.QUESTIONING],
            RoundPhase.QUESTIONING: [
                RoundPhase.VOTING,
                RoundPhase.SPY_GUESSING,
                RoundPhase.SCORING,
            ],
            RoundPhase.VOTING: [RoundPhase.QUESTIONING, RoundPhase.SCORING],
            RoundPhase.SPY_GUESSING: [RoundPhase.SCORING],
            RoundPhase.SCORING: [RoundPhase.COMPLETED],
            RoundPhase.COMPLETED: [],
        }
        return to_phase in valid_transitions.get(from_phase, [])


@dataclass
class GameState:
    game_id: str
    phase: GamePhase
    current_round: int = 0
    rounds_data: List[RoundState] = field(default_factory=list)
    player_scores: Dict[str, int] = field(default_factory=dict)
    errors: List[GameError] = field(default_factory=list)

    def transition_to(self, new_phase: GamePhase) -> bool:
        """Validates and executes state transition"""
        if self._is_valid_transition(self.phase, new_phase):
            self.phase = new_phase
            return True
        return False

    def _is_valid_transition(self, from_phase: GamePhase, to_phase: GamePhase) -> bool:
        """Defines valid state transitions"""
        valid_transitions = {
            GamePhase.INITIALIZING: [GamePhase.IN_PROGRESS, GamePhase.ERROR],
            GamePhase.IN_PROGRESS: [GamePhase.COMPLETED, GamePhase.ERROR],
            GamePhase.COMPLETED: [],
            GamePhase.ERROR: [],
        }
        return to_phase in valid_transitions.get(from_phase, [])
