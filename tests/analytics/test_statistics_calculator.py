import pytest

from analytics.models import (ModelData, RoleAssignment, RoundRecord, SpyGuess,
                              VoteAttempt, VoteRecord)
from analytics.statistics_calculator import StatisticsCalculator


@pytest.fixture
def calculator():
    return StatisticsCalculator()


def test_calculate_all_statistics(calculator):
    data_map = {
        "gpt-4": ModelData(model_name="gpt-4", total_games=1),
        "claude-3": ModelData(model_name="claude-3", total_games=1),
    }
    stats_map = calculator.calculate_all_statistics(data_map)
    assert len(stats_map) == 2
    assert "gpt-4" in stats_map
    assert "claude-3" in stats_map


def test_calculate_model_statistics_basic(calculator):
    data = ModelData(model_name="gpt-4", total_games=2, games_won=1, total_rounds=2)
    data.all_scores = [5, 0]

    stats = calculator.calculate_model_statistics(data)

    assert stats.model_name == "gpt-4"
    assert stats.total_games == 2
    assert stats.total_rounds == 2
    assert stats.overall_win_rate == 0.5
    assert stats.average_score_per_round == 2.5
    assert stats.max_score == 5
    assert stats.min_score == 0
    assert stats.average_score_per_game == 2.5
    # score_std_dev should be calculated as len > 1
    assert stats.score_std_dev > 0


def test_calculate_single_score(calculator):
    data = ModelData(model_name="gpt-4", total_games=1, total_rounds=1)
    data.all_scores = [5]

    stats = calculator.calculate_model_statistics(data)
    assert stats.score_std_dev == 0.0


def test_calculate_win_rates(calculator):
    # Round 1: Spy wins by guessing location
    spy_round = RoundRecord(
        round_number=1,
        location="Beach",
        spy="gpt-4",
        role_assignments={"gpt-4": RoleAssignment(is_spy=True, location=None)},
        turns=[],
        vote_attempts=[],
        spy_guess=SpyGuess(
            spy_nickname="gpt-4",
            guessed_location="Beach",
            actual_location="Beach",
            correct=True,
            timestamp="",
        ),
        ending_condition="spy_guess",
        round_scores={"gpt-4": 5},
    )

    # Round 2: Civilian wins (Spy voted out)
    civilian_round = RoundRecord(
        round_number=2,
        location="Bank",
        spy="Other",
        role_assignments={"gpt-4": RoleAssignment(is_spy=False, location="Bank")},
        turns=[],
        vote_attempts=[
            VoteAttempt(
                initiator="gpt-4", suspect="Other", votes={}, passed=True, timestamp=""
            )
        ],
        spy_guess=None,
        ending_condition="vote",
        round_scores={"gpt-4": 1},
    )

    data = ModelData(
        model_name="gpt-4",
        total_games=1,
        games_won=0,
        total_rounds=2,
        spy_rounds=[spy_round],
        civilian_rounds=[civilian_round],
        spy_scores=[5],
        civilian_scores=[1]
    )

    stats = calculator.calculate_model_statistics(data)

    assert stats.spy_rounds_count == 1
    assert stats.civilian_rounds_count == 1

    # Spy round: Spy won. So Spy Win Rate = 1/1 = 1.0
    assert stats.spy_win_rate == 1.0
    assert stats.average_spy_score == 5.0

    # Civilian round: Spy voted out (suspect="Other", spy="Other"). Civilians won.
    # So Civilian Win Rate = 1/1 = 1.0
    assert stats.civilian_win_rate == 1.0
    assert stats.average_civilian_score == 1.0


def test_calculate_win_rates_loss(calculator):
    # Round 1: Spy loses by guessing wrong location
    spy_round = RoundRecord(
        round_number=1,
        location="Beach",
        spy="gpt-4",
        role_assignments={"gpt-4": RoleAssignment(is_spy=True, location=None)},
        turns=[],
        vote_attempts=[],
        spy_guess=SpyGuess(
            spy_nickname="gpt-4",
            guessed_location="Wrong",
            actual_location="Beach",
            correct=False,
            timestamp="",
        ),
        ending_condition="spy_guess",
        round_scores={},
    )

    # Round 2: Civilian loses (Spy wins by timeout)
    civilian_round = RoundRecord(
        round_number=2,
        location="Bank",
        spy="Other",
        role_assignments={"gpt-4": RoleAssignment(is_spy=False, location="Bank")},
        turns=[],
        vote_attempts=[],
        spy_guess=None,
        ending_condition="timeout",
        round_scores={},
    )

    data = ModelData(
        model_name="gpt-4",
        total_games=1,
        games_won=0,
        total_rounds=2,
        spy_rounds=[spy_round],
        civilian_rounds=[civilian_round],
    )

    stats = calculator.calculate_model_statistics(data)

    assert stats.spy_win_rate == 0.0
    assert stats.civilian_win_rate == 0.0


def test_empty_stats(calculator):
    data = ModelData(model_name="gpt-4")
    stats = calculator.calculate_model_statistics(data)

    assert stats.total_games == 0
    assert stats.overall_win_rate == 0.0
    assert stats.spy_win_rate == 0.0
    assert stats.civilian_win_rate == 0.0
    assert stats.average_score_per_round == 0.0


def test_unknown_ending_condition(calculator):
    round_rec = RoundRecord(
        round_number=1,
        location="Beach",
        spy="gpt-4",
        role_assignments={"gpt-4": RoleAssignment(is_spy=True, location=None)},
        turns=[],
        vote_attempts=[],
        spy_guess=None,
        ending_condition="unknown",
        round_scores={},
    )
    data = ModelData(model_name="gpt-4", total_games=1, spy_rounds=[round_rec])
    # _did_spy_win should return False for unknown condition
    stats = calculator.calculate_model_statistics(data)
    assert stats.spy_win_rate == 0.0


def test_vote_ending_without_passed_vote(calculator):
    # Should be theoretically impossible if data is consistent, but testing edge case
    round_rec = RoundRecord(
        round_number=1,
        location="Beach",
        spy="gpt-4",
        role_assignments={"gpt-4": RoleAssignment(is_spy=True, location=None)},
        turns=[],
        vote_attempts=[],  # No vote attempts
        spy_guess=None,
        ending_condition="vote",
        round_scores={},
    )
    data = ModelData(model_name="gpt-4", total_games=1, spy_rounds=[round_rec])
    # _did_spy_win should return False
    stats = calculator.calculate_model_statistics(data)
    assert stats.spy_win_rate == 0.0


def test_spy_survival_rate(calculator):
    # Spy round 1: Survived (ending condition spy_guess)
    r1 = RoundRecord(
        round_number=1,
        location="Beach",
        spy="gpt-4",
        role_assignments={"gpt-4": RoleAssignment(is_spy=True, location=None)},
        turns=[],
        vote_attempts=[],
        spy_guess=SpyGuess(
            spy_nickname="gpt-4",
            guessed_location="Beach",
            actual_location="Beach",
            correct=True,
            timestamp="",
        ),
        ending_condition="spy_guess",
        round_scores={},
    )

    # Spy round 2: Survived (timeout)
    r2 = RoundRecord(
        round_number=2,
        location="Bank",
        spy="gpt-4",
        role_assignments={"gpt-4": RoleAssignment(is_spy=True, location=None)},
        turns=[],
        vote_attempts=[],
        spy_guess=None,
        ending_condition="timeout",
        round_scores={},
    )

    # Spy round 3: Died (voted out)
    r3 = RoundRecord(
        round_number=3,
        location="Casino",
        spy="gpt-4",
        role_assignments={"gpt-4": RoleAssignment(is_spy=True, location=None)},
        turns=[],
        vote_attempts=[
            VoteAttempt(
                initiator="Other", suspect="gpt-4", votes={}, passed=True, timestamp=""
            )
        ],
        spy_guess=None,
        ending_condition="vote",
        round_scores={},
    )

    data = ModelData(model_name="gpt-4", total_rounds=3, spy_rounds=[r1, r2, r3])

    stats = calculator.calculate_model_statistics(data)
    assert stats.spy_rounds_count == 3
    # Survived r1 and r2. Died in r3.
    # Wait, r1: spy_guess means spy survived voting phase.
    assert stats.spy_survival_rate == 2 / 3


def test_spy_guess_accuracy(calculator):
    r1 = RoundRecord(
        round_number=1,
        location="Beach",
        spy="gpt-4",
        role_assignments={"gpt-4": RoleAssignment(is_spy=True, location=None)},
        turns=[],
        vote_attempts=[],
        spy_guess=SpyGuess(
            spy_nickname="gpt-4",
            guessed_location="Beach",
            actual_location="Beach",
            correct=True,
            timestamp="",
        ),
        ending_condition="spy_guess",
        round_scores={},
    )

    r2 = RoundRecord(
        round_number=2,
        location="Bank",
        spy="gpt-4",
        role_assignments={"gpt-4": RoleAssignment(is_spy=True, location=None)},
        turns=[],
        vote_attempts=[],
        spy_guess=SpyGuess(
            spy_nickname="gpt-4",
            guessed_location="Wrong",
            actual_location="Bank",
            correct=False,
            timestamp="",
        ),
        ending_condition="spy_guess",
        round_scores={},
    )

    r3 = RoundRecord(
        round_number=3,
        location="Casino",
        spy="gpt-4",
        role_assignments={"gpt-4": RoleAssignment(is_spy=True, location=None)},
        turns=[],
        vote_attempts=[],
        spy_guess=None,  # No guess
        ending_condition="vote",
        round_scores={},
    )

    data = ModelData(model_name="gpt-4", total_rounds=3, spy_rounds=[r1, r2, r3])

    stats = calculator.calculate_model_statistics(data)
    assert stats.total_spy_guesses == 2
    assert stats.successful_spy_guesses == 1
    assert stats.spy_guess_accuracy == 0.5


def test_voting_statistics(calculator):
    # Vote 1: Correct Yes vote on Spy
    v1 = VoteRecord(
        game_id="1",
        round_number=1,
        voter="gpt-4",
        suspect="Spy",
        vote=True,
        correct=True,
    )
    # Vote 2: Incorrect No vote on Spy
    v2 = VoteRecord(
        game_id="2",
        round_number=1,
        voter="gpt-4",
        suspect="Spy",
        vote=False,
        correct=False,
    )
    # Vote 3: Incorrect Yes vote on Civilian
    v3 = VoteRecord(
        game_id="3",
        round_number=1,
        voter="gpt-4",
        suspect="Civilian",
        vote=True,
        correct=False,
    )

    data = ModelData(model_name="gpt-4", total_rounds=3, votes_cast=[v1, v2, v3])

    # We need rounds to calculate initiated votes
    r1 = RoundRecord(
        round_number=1,
        location="Beach",
        spy="Spy",
        role_assignments={"gpt-4": RoleAssignment(is_spy=False, location="Beach")},
        turns=[],
        vote_attempts=[
            VoteAttempt(
                initiator="gpt-4",
                suspect="Spy",
                votes={"gpt-4": True},
                passed=True,
                timestamp="",
            )
        ],
        spy_guess=None,
        ending_condition="vote",
        round_scores={},
    )
    data.civilian_rounds = [r1]

    stats = calculator.calculate_model_statistics(data)

    assert stats.voting_accuracy == 1 / 3
    assert stats.yes_vote_percentage == 2 / 3
    assert stats.correct_spy_votes == 1  # Only v1 is correct Yes on Spy
    assert stats.votes_initiated == 1
    assert stats.vote_initiation_success_rate == 1.0  # passed=True
    assert stats.total_civilian_votes == 1  # In r1, gpt-4 voted once
