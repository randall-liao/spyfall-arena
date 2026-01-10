import pytest
from hypothesis import given, strategies as st
from unittest.mock import MagicMock
from game.game_state import RoundState, Role, VoteAttempt, Turn, SpyGuess, GameState
from game_logging.metrics_calculator import (
    calculate_round_metrics,
    calculate_game_metrics,
)


# Property 1: Round outcome determination
@given(winner_is_spy=st.booleans(), spy_guessed=st.booleans())
def test_round_outcome_property(winner_is_spy, spy_guessed):
    # Construct a round state consistent with these flags
    rs = MagicMock(spec=RoundState)
    rs.spy_nickname = "Spy"
    rs.role_assignments = {"Spy": Role(True, None), "Civ": Role(False, "Loc")}
    rs.votes = []
    rs.conversation_history = []

    if spy_guessed:
        rs.spy_guess = SpyGuess("Spy", "Loc", "Loc", True)
    else:
        rs.spy_guess = None

    if not spy_guessed:
        if winner_is_spy:
            # Time out or failed vote
            rs.votes = []
        else:
            # Civilians win (successful vote)
            # Must imply successful vote on Spy
            rs.votes = [VoteAttempt("Civ", "Spy", {"Civ": True}, True)]

    # If spy_guessed is true, spy always wins.
    # If spy_guessed is false, winner depends on whether we set up a spy win or civilian win.

    metrics = calculate_round_metrics(rs)

    if spy_guessed:
        assert metrics.winner_side == "spy"
        assert metrics.spy_guessed_correctly is True
    elif not winner_is_spy:
        # We set it up so civilians win
        assert metrics.winner_side == "civilians"
        assert metrics.spy_caught is True
    else:
        # We set it up so spy wins (time out)
        assert metrics.winner_side == "spy"


# Property 2: Vote accuracy calculation
@given(
    num_civilians=st.integers(min_value=1, max_value=10),
    yes_votes=st.integers(min_value=0, max_value=10),
)
def test_vote_accuracy_property(num_civilians, yes_votes):
    # Ensure yes_votes <= num_civilians
    yes_votes = min(yes_votes, num_civilians)

    rs = MagicMock(spec=RoundState)
    rs.spy_nickname = "Spy"

    # Create civilians
    roles = {"Spy": Role(True, None)}
    votes_dict = {}

    for i in range(num_civilians):
        name = f"Civ{i}"
        roles[name] = Role(False, "Loc")
        if i < yes_votes:
            votes_dict[name] = True
        else:
            votes_dict[name] = False

    rs.role_assignments = roles

    # Successful vote needed for accuracy to be calc
    rs.votes = [VoteAttempt("Civ0", "Spy", votes_dict, True)]
    rs.spy_guess = None
    rs.conversation_history = []

    metrics = calculate_round_metrics(rs)

    expected_accuracy = yes_votes / num_civilians
    assert metrics.vote_accuracy == pytest.approx(expected_accuracy)
    assert 0.0 <= metrics.vote_accuracy <= 1.0


# Property 3: Response statistics calculation
@given(questions=st.lists(st.text()), answers=st.lists(st.text()))
def test_response_stats_property(questions, answers):
    # Truncate to shorter length to match pairs
    min_len = min(len(questions), len(answers))
    questions = questions[:min_len]
    answers = answers[:min_len]

    rs = MagicMock(spec=RoundState)
    rs.spy_nickname = "Spy"
    rs.votes = []
    rs.spy_guess = None
    rs.role_assignments = {}

    history = []
    for i, (q, a) in enumerate(zip(questions, answers)):
        history.append(Turn(i, "A", "B", q, a))

    rs.conversation_history = history

    metrics = calculate_round_metrics(rs)

    assert metrics.total_turns == min_len
    if min_len > 0:
        assert metrics.avg_question_length >= 0
        assert metrics.avg_answer_length >= 0
    else:
        assert metrics.avg_question_length == 0
        assert metrics.avg_answer_length == 0


# Property 4: Aggregate metrics calculation
@given(
    rounds=st.lists(st.tuples(st.booleans(), st.booleans()), min_size=1, max_size=20)
)
def test_game_metrics_property(rounds):
    # rounds list contains tuples of (winner_is_spy, spy_guessed)
    # mirroring test_round_outcome_property logic

    gs = MagicMock(spec=GameState)
    rounds_data = []

    spy_wins_count = 0
    civ_wins_count = 0

    for winner_is_spy, spy_guessed in rounds:
        rs = MagicMock(spec=RoundState)
        rs.spy_nickname = "S"
        rs.role_assignments = {"S": Role(True, None), "C": Role(False, "Loc")}
        rs.votes = []
        rs.conversation_history = [
            Turn(1, "A", "B", "Q", "A")
        ]  # 1 turn per round for simplicity

        if spy_guessed:
            rs.spy_guess = SpyGuess("S", "Loc", "Loc", True)
            spy_wins_count += 1
        else:
            rs.spy_guess = None
            if winner_is_spy:
                # Time out -> Spy wins
                spy_wins_count += 1
            else:
                # Civilians win
                rs.votes = [VoteAttempt("C", "S", {"C": True}, True)]
                civ_wins_count += 1

        rounds_data.append(rs)

    gs.rounds_data = rounds_data

    # Mock scores to match
    # Spy gets 10 points for a win, Civs get 1 point?
    # Let's just mock scores loosely to check overall_winner logic separately logic or
    # we can just trust the metrics calculator relies on gs.player_scores which we set.

    # For this property test, we focus on spy_wins + civ_wins = total_rounds
    # And consistency of whatever scores we provide.

    gs.player_scores = {"S": spy_wins_count * 10, "C": civ_wins_count * 10}

    metrics = calculate_game_metrics(gs)  # Assuming this is imported or available

    assert metrics.spy_wins == spy_wins_count
    assert metrics.civilian_wins == civ_wins_count
    assert metrics.spy_wins + metrics.civilian_wins == len(rounds)

    if spy_wins_count > civ_wins_count:
        assert metrics.overall_winner == "S"
    elif civ_wins_count > spy_wins_count:
        assert metrics.overall_winner == "C"
    # Tie breaking is specific, but if counts are equal here scores are equal
    elif spy_wins_count == civ_wins_count and spy_wins_count > 0:
        # "C" comes before "S" alphabetically
        assert metrics.overall_winner == "C"
