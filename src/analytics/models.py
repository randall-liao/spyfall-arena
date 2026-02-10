from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PlayerConfig:
    nickname: str
    model_name: str
    provider: str = "OPEN_ROUTER"
    temperature: float = 0.7
    reasoning: Optional[Dict[str, Any]] = None


@dataclass
class RoleAssignment:
    is_spy: bool
    location: Optional[str]


@dataclass
class TurnRecord:
    turn_number: int
    asker_nickname: str
    answerer_nickname: str
    question: str
    answer: str
    timestamp: str


@dataclass
class VoteAttempt:
    initiator: str
    suspect: str
    votes: Dict[str, bool]
    passed: bool
    timestamp: str


@dataclass
class SpyGuess:
    spy_nickname: str
    guessed_location: str
    actual_location: str
    correct: bool
    timestamp: str


@dataclass
class RoundRecord:
    round_number: int
    location: str
    spy: str
    role_assignments: Dict[str, RoleAssignment]
    turns: List[TurnRecord]
    vote_attempts: List[VoteAttempt]
    spy_guess: Optional[SpyGuess]
    ending_condition: str
    round_scores: Dict[str, int]


@dataclass
class GameRecord:
    game_id: str
    timestamp: str
    players: List[PlayerConfig]
    rounds: List[RoundRecord]
    final_scores: Dict[str, int]
    status: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        import dataclasses

        return dataclasses.asdict(self)


@dataclass
class VoteRecord:
    game_id: str
    round_number: int
    voter: str
    suspect: str
    vote: bool  # True for yes (guilty), False for no
    correct: bool  # True if the vote aligned with the actual spy status (Vote yes on spy, vote no on civilian)


@dataclass
class ModelData:
    model_name: str
    total_games: int = 0
    games_won: int = 0  # Added to track overall game wins
    total_rounds: int = 0
    spy_rounds: List[RoundRecord] = field(default_factory=list)
    civilian_rounds: List[RoundRecord] = field(default_factory=list)
    all_scores: List[int] = field(default_factory=list)
    spy_scores: List[int] = field(default_factory=list)
    civilian_scores: List[int] = field(default_factory=list)
    votes_cast: List[VoteRecord] = field(default_factory=list)
    votes_received: List[VoteRecord] = field(default_factory=list)
    turns_as_asker: List[TurnRecord] = field(default_factory=list)
    turns_as_answerer: List[TurnRecord] = field(default_factory=list)


@dataclass
class ModelStatistics:
    model_name: str

    # Basic counts
    total_games: int = 0
    total_rounds: int = 0
    spy_rounds_count: int = 0
    civilian_rounds_count: int = 0

    # Win rates
    overall_win_rate: float = 0.0
    spy_win_rate: float = 0.0
    civilian_win_rate: float = 0.0

    # Scoring
    average_score_per_round: float = 0.0
    average_score_per_game: float = 0.0
    min_score: int = 0
    max_score: int = 0
    score_std_dev: float = 0.0
    score_distribution: Dict[int, int] = field(default_factory=dict)

    # Voting
    voting_accuracy: float = 0.0
    votes_initiated: int = 0
    vote_initiation_success_rate: float = 0.0
    times_suspected: int = 0
    yes_vote_percentage: float = 0.0

    # Spy performance
    spy_survival_rate: float = 0.0
    spy_guess_accuracy: float = 0.0
    successful_spy_guesses: int = 0
    total_spy_guesses: int = 0
    average_spy_score: float = 0.0

    # Civilian performance
    civilian_success_rate: float = 0.0
    average_civilian_score: float = 0.0
    correct_spy_votes: int = 0
    total_civilian_votes: int = 0

    # Turn engagement
    questions_asked: int = 0
    questions_answered: int = 0
    average_turns_per_round: float = 0.0

    # Round endings
    rounds_ended_by_vote: int = 0
    rounds_ended_by_spy_guess: int = 0
    rounds_ended_by_timeout: int = 0
