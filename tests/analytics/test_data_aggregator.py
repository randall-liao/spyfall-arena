import pytest

from analytics.data_aggregator import DataAggregator
from analytics.models import (GameRecord, PlayerConfig, RoleAssignment,
                              RoundRecord, SpyGuess, TurnRecord, VoteAttempt)


@pytest.fixture
def sample_game():
    return GameRecord(
        game_id="game_1",
        timestamp="2024-01-01T12:00:00",
        players=[
            PlayerConfig(nickname="Alice", model_name="gpt-4"),
            PlayerConfig(nickname="Bob", model_name="claude-3"),
        ],
        rounds=[
            RoundRecord(
                round_number=1,
                location="Beach",
                spy="Bob",
                role_assignments={
                    "Alice": RoleAssignment(is_spy=False, location="Beach"),
                    "Bob": RoleAssignment(is_spy=True, location=None),
                },
                turns=[],
                vote_attempts=[],
                spy_guess=None,
                ending_condition="spy_guess",
                round_scores={"Alice": 0, "Bob": 5},
            )
        ],
        final_scores={"Alice": 0, "Bob": 5},
        status="completed",
    )


def test_aggregate_single_model(sample_game):
    aggregator = DataAggregator()
    model_data = aggregator.aggregate_by_model([sample_game])

    assert "gpt-4" in model_data
    assert "claude-3" in model_data

    gpt4_data = model_data["gpt-4"]
    assert gpt4_data.total_games == 1
    assert gpt4_data.total_rounds == 1
    assert len(gpt4_data.civilian_rounds) == 1
    assert len(gpt4_data.spy_rounds) == 0
    assert gpt4_data.all_scores == [0]

    claude3_data = model_data["claude-3"]
    assert claude3_data.total_games == 1
    assert claude3_data.total_rounds == 1
    assert len(claude3_data.civilian_rounds) == 0
    assert len(claude3_data.spy_rounds) == 1
    assert claude3_data.all_scores == [5]


def test_aggregate_multiple_games(sample_game):
    aggregator = DataAggregator()
    # Duplicate game (should aggregate correctly if total_games increments)
    # Ideally should use different games, but simple duplication is enough to test increment logic
    model_data = aggregator.aggregate_by_model([sample_game, sample_game])

    gpt4_data = model_data["gpt-4"]
    assert gpt4_data.total_games == 2
    assert gpt4_data.total_rounds == 2
    assert len(gpt4_data.civilian_rounds) == 2


def test_aggregate_empty_list():
    aggregator = DataAggregator()
    model_data = aggregator.aggregate_by_model([])
    assert model_data == {}


def test_aggregate_votes():
    aggregator = DataAggregator()

    vote_attempt = VoteAttempt(
        initiator="Alice",
        suspect="Bob",
        votes={"Alice": True, "Bob": False},
        passed=False,
        timestamp="2024-01-01T12:05:00",
    )

    game = GameRecord(
        game_id="game_1",
        timestamp="2024-01-01T12:00:00",
        players=[
            PlayerConfig(nickname="Alice", model_name="gpt-4"),
            PlayerConfig(nickname="Bob", model_name="claude-3"),
        ],
        rounds=[
            RoundRecord(
                round_number=1,
                location="Beach",
                spy="Bob",
                role_assignments={
                    "Alice": RoleAssignment(is_spy=False, location="Beach"),
                    "Bob": RoleAssignment(is_spy=True, location=None),
                },
                turns=[],
                vote_attempts=[vote_attempt],
                spy_guess=None,
                ending_condition="vote",
                round_scores={"Alice": 0, "Bob": 0},
            )
        ],
        final_scores={"Alice": 0, "Bob": 0},
        status="completed",
    )

    model_data = aggregator.aggregate_by_model([game])

    gpt4_data = model_data["gpt-4"]
    claude3_data = model_data["claude-3"]

    assert len(gpt4_data.votes_cast) == 1  # Alice voted
    assert len(claude3_data.votes_cast) == 1  # Bob voted

    # Alice voted True on Bob (spy), so correct=True (if logic holds: Spy is guilty)
    # Wait, in Spyfall, you vote to accuse. If accused is Spy, vote Yes is correct.
    assert gpt4_data.votes_cast[0].vote is True
    assert gpt4_data.votes_cast[0].correct is True  # Bob is Spy

    # Bob voted False on Bob (spy), so correct=False? Or is it strategic?
    # Bob (Spy) voting No on himself is correct self-preservation, but objectively "Is Bob Spy?" -> Yes.
    # The logic in DataAggregator is:
    # suspect_is_spy = True
    # is_correct = vote_val (False) -> False
    # So Bob's vote is marked incorrect because he voted No on a Spy. This is fine for now as raw data.
    assert claude3_data.votes_cast[0].vote is False
    assert claude3_data.votes_cast[0].correct is False

    # Check votes received
    # Bob was suspected by Alice (VoteRecord for Alice targeting Bob)
    # And by Bob (VoteRecord for Bob targeting Bob)
    assert len(claude3_data.votes_received) == 2

    # Alice was not suspected
    assert len(gpt4_data.votes_received) == 0


def test_aggregate_turns():
    aggregator = DataAggregator()
    turn = TurnRecord(
        turn_number=1,
        asker_nickname="Alice",
        answerer_nickname="Bob",
        question="Q",
        answer="A",
        timestamp="2024-01-01T12:01:00",
    )

    game = GameRecord(
        game_id="game_1",
        timestamp="2024-01-01T12:00:00",
        players=[
            PlayerConfig(nickname="Alice", model_name="gpt-4"),
            PlayerConfig(nickname="Bob", model_name="claude-3"),
        ],
        rounds=[
            RoundRecord(
                round_number=1,
                location="Beach",
                spy="Bob",
                role_assignments={
                    "Alice": RoleAssignment(is_spy=False, location="Beach"),
                    "Bob": RoleAssignment(is_spy=True, location=None),
                },
                turns=[turn],
                vote_attempts=[],
                spy_guess=None,
                ending_condition="vote",
                round_scores={"Alice": 0, "Bob": 0},
            )
        ],
        final_scores={"Alice": 0, "Bob": 0},
        status="completed",
    )

    model_data = aggregator.aggregate_by_model([game])

    assert len(model_data["gpt-4"].turns_as_asker) == 1
    assert len(model_data["claude-3"].turns_as_answerer) == 1


def test_aggregate_unknown_players():
    """Test handling of players in rounds/turns/votes that are not in the player list (inconsistent data)"""
    aggregator = DataAggregator()

    # "Unknown" player appears in turns and votes
    turn = TurnRecord(
        turn_number=1,
        asker_nickname="Unknown",
        answerer_nickname="Alice",
        question="Q",
        answer="A",
        timestamp="2024-01-01T12:01:00",
    )

    vote_attempt = VoteAttempt(
        initiator="Unknown",
        suspect="Alice",
        votes={"Unknown": True, "Alice": False},
        passed=False,
        timestamp="2024-01-01T12:05:00",
    )

    game = GameRecord(
        game_id="game_bad",
        timestamp="2024-01-01T12:00:00",
        players=[PlayerConfig(nickname="Alice", model_name="gpt-4")],
        rounds=[
            RoundRecord(
                round_number=1,
                location="Beach",
                spy="Alice",
                role_assignments={
                    "Alice": RoleAssignment(is_spy=True, location=None),
                    # Unknown player in role assignments too?
                    # If strictly testing unknown handling in specific loops:
                    "Unknown": RoleAssignment(is_spy=False, location="Beach"),
                },
                turns=[turn],
                vote_attempts=[vote_attempt],
                spy_guess=None,
                ending_condition="vote",
                round_scores={"Alice": 0},
            )
        ],
        final_scores={"Alice": 0},
        status="completed",
    )

    model_data = aggregator.aggregate_by_model([game])

    # "Unknown" should be skipped and not crash the aggregator
    assert "gpt-4" in model_data
    # Check that we didn't crash
