from dataclasses import asdict, is_dataclass
from unittest.mock import MagicMock

import pytest

from game.game_state import (GameState, Role, RoundState, SpyGuess, Turn,
                             VoteAttempt)
from game_logging.metrics_calculator import (GameMetrics, RoundMetrics,
                                             calculate_game_metrics,
                                             calculate_round_metrics)

# ... existing tests ...
# (Repasting everything is annoying, I should have used replace or append if I could, but I'll paste the whole new content with additions)


# Task 1.2: Unit tests for RoundMetrics dataclass
def test_round_metrics_is_dataclass():
    assert is_dataclass(RoundMetrics)


def test_round_metrics_instantiation():
    metrics = RoundMetrics(
        winner_side="spy",
        spy_caught=False,
        spy_guessed_correctly=True,
        total_turns=10,
        vote_accuracy=0.25,
        avg_question_length=15.5,
        avg_answer_length=20.2,
    )
    assert metrics.winner_side == "spy"
    assert metrics.spy_caught is False
    assert metrics.spy_guessed_correctly is True
    assert metrics.total_turns == 10
    assert metrics.vote_accuracy == 0.25
    assert metrics.avg_question_length == 15.5
    assert metrics.avg_answer_length == 20.2


def test_round_metrics_optional_fields():
    # vote_accuracy can be None if no vote happened
    metrics = RoundMetrics(
        winner_side="spy",
        spy_caught=False,
        spy_guessed_correctly=True,
        total_turns=10,
        vote_accuracy=None,
        avg_question_length=15.5,
        avg_answer_length=20.2,
    )
    assert metrics.vote_accuracy is None


def test_round_metrics_serialization():
    metrics = RoundMetrics(
        winner_side="civilians",
        spy_caught=True,
        spy_guessed_correctly=False,
        total_turns=5,
        vote_accuracy=1.0,
        avg_question_length=10.0,
        avg_answer_length=10.0,
    )
    data = asdict(metrics)
    assert data["winner_side"] == "civilians"
    assert data["spy_caught"] is True
    assert data["vote_accuracy"] == 1.0


# Task 1.3: Unit tests for GameMetrics dataclass
def test_game_metrics_is_dataclass():
    assert is_dataclass(GameMetrics)


def test_game_metrics_instantiation():
    metrics = GameMetrics(
        spy_wins=2, civilian_wins=1, avg_turns_per_round=8.5, overall_winner="Alice"
    )
    assert metrics.spy_wins == 2
    assert metrics.civilian_wins == 1
    assert metrics.avg_turns_per_round == 8.5
    assert metrics.overall_winner == "Alice"


def test_game_metrics_serialization():
    metrics = GameMetrics(
        spy_wins=2, civilian_wins=1, avg_turns_per_round=8.5, overall_winner="Alice"
    )
    data = asdict(metrics)
    assert data["spy_wins"] == 2
    assert data["civilian_wins"] == 1
    assert data["overall_winner"] == "Alice"


# Task 3.1: Winner determination
def test_calculate_round_metrics_spy_wins_time_limit():
    rs = MagicMock(spec=RoundState)
    rs.spy_nickname = "SpyPlayer"
    rs.spy_guess = None
    rs.votes = []  # No successful votes
    rs.conversation_history = []

    metrics = calculate_round_metrics(rs)
    assert metrics.winner_side == "spy"
    assert metrics.spy_caught is False
    assert metrics.spy_guessed_correctly is False


def test_calculate_round_metrics_spy_wins_wrong_vote():
    rs = MagicMock(spec=RoundState)
    rs.spy_nickname = "SpyPlayer"
    rs.spy_guess = None

    # Successful vote on innocent
    successful_vote = VoteAttempt(
        initiator="Alice", suspect="Bob", votes={}, passed=True
    )
    rs.votes = [successful_vote]
    rs.conversation_history = []
    rs.role_assignments = {
        "SpyPlayer": Role(is_spy=True, location=None),
        "Alice": Role(is_spy=False, location="Loc"),
        "Bob": Role(is_spy=False, location="Loc"),
    }

    metrics = calculate_round_metrics(rs)
    assert metrics.winner_side == "spy"
    assert metrics.spy_caught is False  # Spy wasn't caught, innocent was


def test_calculate_round_metrics_spy_wins_location_guess():
    rs = MagicMock(spec=RoundState)
    rs.spy_nickname = "SpyPlayer"
    rs.votes = []

    # Spy guessed correctly
    rs.spy_guess = SpyGuess(
        spy_nickname="SpyPlayer",
        guessed_location="Loc",
        actual_location="Loc",
        correct=True,
    )
    rs.conversation_history = []

    metrics = calculate_round_metrics(rs)
    assert metrics.winner_side == "spy"
    assert metrics.spy_caught is False
    assert metrics.spy_guessed_correctly is True


def test_calculate_round_metrics_civilians_win():
    rs = MagicMock(spec=RoundState)
    rs.spy_nickname = "SpyPlayer"
    rs.spy_guess = None

    # Successful vote on Spy
    successful_vote = VoteAttempt(
        initiator="Alice", suspect="SpyPlayer", votes={}, passed=True
    )
    rs.votes = [successful_vote]
    rs.conversation_history = []
    rs.role_assignments = {
        "SpyPlayer": Role(is_spy=True, location=None),
        "Alice": Role(is_spy=False, location="Loc"),
        "Bob": Role(is_spy=False, location="Loc"),
    }

    metrics = calculate_round_metrics(rs)
    assert metrics.winner_side == "civilians"
    assert metrics.spy_caught is True
    assert metrics.spy_guessed_correctly is False


# Task 3.2: Vote accuracy
def test_calculate_round_metrics_vote_accuracy():
    rs = MagicMock(spec=RoundState)
    rs.spy_nickname = "SpyPlayer"
    rs.conversation_history = []

    vote = VoteAttempt(
        initiator="Alice",
        suspect="SpyPlayer",
        votes={
            "Alice": True,
            "Bob": True,
            "Charlie": False,
            "SpyPlayer": False,
        },  # Charlie is Civ, but voted No
        passed=True,
    )
    rs.votes = [vote]
    rs.role_assignments = {
        "Alice": Role(is_spy=False, location="Loc"),
        "Bob": Role(is_spy=False, location="Loc"),
        "Charlie": Role(is_spy=False, location="Loc"),
        "SpyPlayer": Role(is_spy=True, location=None),
    }

    metrics = calculate_round_metrics(rs)
    # Civilians: Alice, Bob, Charlie (3).
    # Voted Yes: Alice, Bob (2).
    # Accuracy: 2/3
    assert metrics.vote_accuracy == pytest.approx(2 / 3)


def test_calculate_round_metrics_no_successful_vote():
    rs = MagicMock(spec=RoundState)
    rs.spy_nickname = "SpyPlayer"
    rs.votes = [
        VoteAttempt(initiator="A", suspect="B", votes={}, passed=False)
    ]  # Failed vote
    rs.conversation_history = []

    metrics = calculate_round_metrics(rs)
    assert metrics.vote_accuracy is None


# Task 3.3: Response statistics
def test_calculate_round_metrics_response_stats():
    rs = MagicMock(spec=RoundState)
    rs.spy_nickname = "SpyPlayer"
    rs.votes = []
    rs.spy_guess = None

    t1 = Turn(
        turn_number=1,
        asker_nickname="A",
        answerer_nickname="B",
        question="QQQ",
        answer="AAA",
    )  # 3, 3
    t2 = Turn(
        turn_number=2,
        asker_nickname="B",
        answerer_nickname="A",
        question="Q",
        answer="AAAAA",
    )  # 1, 5

    rs.conversation_history = [t1, t2]

    metrics = calculate_round_metrics(rs)
    assert metrics.total_turns == 2
    assert metrics.avg_question_length == 2.0
    assert metrics.avg_answer_length == 4.0


def test_calculate_round_metrics_empty_stats():
    rs = MagicMock(spec=RoundState)
    rs.spy_nickname = "SpyPlayer"
    rs.votes = []
    rs.spy_guess = None
    rs.conversation_history = []

    metrics = calculate_round_metrics(rs)
    assert metrics.total_turns == 0
    assert metrics.avg_question_length == 0.0
    assert metrics.avg_answer_length == 0.0


# Task 6.1: Win counting
def test_calculate_game_metrics_wins():
    # Need to mock game state with multiple rounds
    gs = MagicMock(spec=GameState)

    # Spy win (time out)
    r1 = MagicMock(spec=RoundState)
    r1.spy_nickname = "S"
    r1.spy_guess = None
    r1.votes = []
    r1.conversation_history = []
    r1.role_assignments = {"S": Role(True, None), "C": Role(False, "Loc")}

    # Civilians win
    r2 = MagicMock(spec=RoundState)
    r2.spy_nickname = "S"
    r2.votes = [VoteAttempt("C", "S", {}, True)]
    r2.spy_guess = None
    r2.conversation_history = []
    r2.role_assignments = {"S": Role(True, None), "C": Role(False, "Loc")}

    # Spy win (guess)
    r3 = MagicMock(spec=RoundState)
    r3.spy_nickname = "S"
    r3.votes = []
    r3.spy_guess = SpyGuess("S", "Loc", "Loc", True)
    r3.conversation_history = []
    r3.role_assignments = {"S": Role(True, None), "C": Role(False, "Loc")}

    gs.rounds_data = [r1, r2, r3]
    gs.player_scores = {"S": 10, "C": 5}

    metrics = calculate_game_metrics(gs)

    # 2 Spy wins, 1 Civ win
    assert metrics.spy_wins == 2
    assert metrics.civilian_wins == 1


# Task 6.2: Average turns
def test_calculate_game_metrics_avg_turns():
    gs = MagicMock(spec=GameState)

    r1 = MagicMock(spec=RoundState)
    r1.conversation_history = [Turn(1, "", "", "", "")]  # 1 turn
    # Need to set other fields to avoid crash
    r1.spy_nickname = "S"
    r1.votes = []
    r1.spy_guess = None
    r1.role_assignments = {"S": Role(True, None)}

    r2 = MagicMock(spec=RoundState)
    r2.conversation_history = [
        Turn(1, "", "", "", ""),
        Turn(2, "", "", "", ""),
    ]  # 2 turns
    r2.spy_nickname = "S"
    r2.votes = []
    r2.spy_guess = None
    r2.role_assignments = {"S": Role(True, None)}

    gs.rounds_data = [r1, r2]
    gs.player_scores = {"S": 0}

    metrics = calculate_game_metrics(gs)

    # Total turns = 3. Count = 2. Avg = 1.5
    assert metrics.avg_turns_per_round == 1.5


# Task 6.3: Overall winner
def test_calculate_game_metrics_winner():
    gs = MagicMock(spec=GameState)
    gs.rounds_data = []  # No rounds needed for score check
    gs.player_scores = {"Alice": 10, "Bob": 5}

    metrics = calculate_game_metrics(gs)
    assert metrics.overall_winner == "Alice"


def test_calculate_game_metrics_winner_tie():
    gs = MagicMock(spec=GameState)
    gs.rounds_data = []
    gs.player_scores = {"Charlie": 10, "Bob": 10}

    metrics = calculate_game_metrics(gs)
    # Tie broken alphabetically? "Bob" < "Charlie"
    assert metrics.overall_winner == "Bob"
