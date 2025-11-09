import pytest

from game.game_state import (Role, RoundPhase, RoundState,
                                           SpyGuess, VoteAttempt)
from game.scoring_engine import ScoringEngine


@pytest.fixture
def scoring_engine() -> ScoringEngine:
    return ScoringEngine()


@pytest.fixture
def base_round_state() -> RoundState:
    """A base RoundState for testing, representing a 3-player game."""
    return RoundState(
        round_number=1,
        phase=RoundPhase.COMPLETED,
        location="Bank",
        spy_nickname="Alice",
        role_assignments={
            "Alice": Role(is_spy=True, location=None),
            "Bob": Role(is_spy=False, location="Bank"),
            "Charlie": Role(is_spy=False, location="Bank"),
        },
    )


def test_spy_wins_by_correct_guess(
    scoring_engine: ScoringEngine, base_round_state: RoundState
):
    """Spy guesses the location correctly: Spy gets 4 points."""
    base_round_state.spy_guess = SpyGuess(
        spy_nickname="Alice",
        guessed_location="Bank",
        actual_location="Bank",
        correct=True,
    )
    scores = scoring_engine.calculate_round_scores(base_round_state)
    assert scores == {"Alice": 4, "Bob": 0, "Charlie": 0}


def test_civilians_win_by_voting_out_spy(
    scoring_engine: ScoringEngine, base_round_state: RoundState
):
    """Civilians vote out the spy: Civilians get 1 point, initiator gets 2."""
    base_round_state.votes.append(
        VoteAttempt(
            initiator="Bob",
            suspect="Alice",
            votes={"Alice": True, "Bob": True, "Charlie": True},
            passed=True,
        )
    )
    scores = scoring_engine.calculate_round_scores(base_round_state)
    assert scores == {"Alice": 0, "Bob": 2, "Charlie": 1}


def test_spy_wins_when_civilians_vote_out_wrong_person(
    scoring_engine: ScoringEngine, base_round_state: RoundState
):
    """Civilians vote out a civilian: Spy gets 4 points."""
    base_round_state.votes.append(
        VoteAttempt(
            initiator="Charlie",
            suspect="Bob",
            votes={"Alice": True, "Bob": True, "Charlie": True},
            passed=True,
        )
    )
    scores = scoring_engine.calculate_round_scores(base_round_state)
    assert scores == {"Alice": 4, "Bob": 0, "Charlie": 0}


def test_spy_wins_by_surviving(
    scoring_engine: ScoringEngine, base_round_state: RoundState
):
    """The round ends without the spy being caught: Spy gets 2 points."""
    scores = scoring_engine.calculate_round_scores(base_round_state)
    assert scores == {"Alice": 2, "Bob": 0, "Charlie": 0}
