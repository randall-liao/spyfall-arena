import pytest

from analytics.models import (GameRecord, ModelData, ModelStatistics,
                              PlayerConfig, RoleAssignment, RoundRecord,
                              SpyGuess, TurnRecord, VoteAttempt)


def test_player_config_instantiation():
    player = PlayerConfig(nickname="Alice", model_name="gpt-4")
    assert player.nickname == "Alice"
    assert player.model_name == "gpt-4"
    assert player.provider == "OPEN_ROUTER"  # default
    assert player.temperature == 0.7  # default
    assert player.reasoning is None


def test_role_assignment_instantiation():
    role = RoleAssignment(is_spy=True, location=None)
    assert role.is_spy
    assert role.location is None


def test_turn_record_instantiation():
    turn = TurnRecord(
        turn_number=1,
        asker_nickname="Alice",
        answerer_nickname="Bob",
        question="Where are we?",
        answer="Somewhere.",
        timestamp="2024-01-01T12:00:00",
    )
    assert turn.turn_number == 1
    assert turn.asker_nickname == "Alice"


def test_vote_attempt_instantiation():
    vote = VoteAttempt(
        initiator="Alice",
        suspect="Bob",
        votes={"Alice": True, "Bob": False},
        passed=False,
        timestamp="2024-01-01T12:05:00",
    )
    assert vote.initiator == "Alice"
    assert not vote.passed
    assert vote.votes["Alice"] is True


def test_spy_guess_instantiation():
    guess = SpyGuess(
        spy_nickname="Bob",
        guessed_location="Beach",
        actual_location="Beach",
        correct=True,
        timestamp="2024-01-01T12:10:00",
    )
    assert guess.spy_nickname == "Bob"
    assert guess.correct


def test_round_record_instantiation():
    round_rec = RoundRecord(
        round_number=1,
        location="Beach",
        spy="Bob",
        role_assignments={"Bob": RoleAssignment(is_spy=True, location=None)},
        turns=[],
        vote_attempts=[],
        spy_guess=None,
        ending_condition="spy_guess",
        round_scores={"Alice": 0, "Bob": 5},
    )
    assert round_rec.round_number == 1
    assert round_rec.spy == "Bob"
    assert round_rec.spy_guess is None


def test_game_record_instantiation():
    game = GameRecord(
        game_id="game_1",
        timestamp="2024-01-01T12:00:00",
        players=[PlayerConfig(nickname="Alice", model_name="gpt-4")],
        rounds=[],
        final_scores={"Alice": 0},
        status="completed",
    )
    assert game.game_id == "game_1"
    assert len(game.players) == 1

    # Test to_dict method (simple check, recursive dict conversion isn't automatic with asdict unless configured properly but dataclasses.asdict works recursively)
    game_dict = game.to_dict()
    assert game_dict["game_id"] == "game_1"
    assert game_dict["players"][0]["nickname"] == "Alice"


def test_model_statistics_defaults():
    stats = ModelStatistics(model_name="gpt-4")
    assert stats.total_games == 0
    assert stats.overall_win_rate == 0.0
    assert stats.score_distribution == {}
