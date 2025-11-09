from unittest.mock import MagicMock, patch

import pytest

from spyfall_arena.config.config_schema import GameConfig
from spyfall_arena.game.game_state import Role, SpyGuess, Turn, VoteAttempt
from spyfall_arena.game.orchestrator import GameOrchestrator


from spyfall_arena.config.config_schema import GameConfig, GameRulesConfig, PlayerConfig

@pytest.fixture
def mock_config() -> GameConfig:
    """Provides a mock GameConfig for testing."""
    return GameConfig(
        game=GameRulesConfig(num_rounds=1, max_turns_per_round=2),
        players=[
            PlayerConfig(nickname="Alice", model_name="test"),
            PlayerConfig(nickname="Bob", model_name="test"),
        ],
        locations=["Bank", "Airport"],
    )


@pytest.fixture
@patch("spyfall_arena.game.orchestrator.SpyGuessManager")
@patch("spyfall_arena.game.orchestrator.VotingManager")
@patch("spyfall_arena.game.orchestrator.TurnManager")
@patch("spyfall_arena.game.orchestrator.RoleAssigner")
@patch("spyfall_arena.game.orchestrator.ScoringEngine")
@patch("spyfall_arena.game.orchestrator.PromptBuilder")
@patch("spyfall_arena.game.orchestrator.LLMClientFactory")
def orchestrator(
    MockLLMFactory,
    MockPromptBuilder,
    MockScoringEngine,
    MockRoleAssigner,
    MockTurnManager,
    MockVotingManager,
    MockSpyGuessManager,
    mock_config,
) -> GameOrchestrator:
    """Provides a GameOrchestrator with all dependencies mocked."""
    # Mock the return values of the managers
    MockRoleAssigner.return_value.assign_roles.return_value = (
        {
            "Alice": Role(is_spy=True, location=None),
            "Bob": Role(is_spy=False, location="Bank"),
        },
        "Bank",
    )
    MockTurnManager.return_value.execute_turn.return_value = Turn(
        1, "Alice", "Bob", "q", "a"
    )
    MockVotingManager.return_value.check_for_vote_initiation.return_value = None
    MockSpyGuessManager.return_value.check_spy_guess.return_value = None
    MockScoringEngine.return_value.calculate_round_scores.return_value = {
        "Alice": 2,
        "Bob": 0,
    }

    return GameOrchestrator(mock_config)


def test_run_game(orchestrator: GameOrchestrator):
    """Tests the execution of a full game."""
    game_state = orchestrator.run_game()

    assert game_state.phase.value == "completed"
    assert len(game_state.rounds_data) == 1
    assert game_state.player_scores == {"Alice": 2, "Bob": 0}


def test_run_round_turn_limit(orchestrator: GameOrchestrator):
    """Tests that a round ends when the turn limit is reached."""
    round_state = orchestrator.run_round(1, ["Alice", "Bob"], ["Bank"])

    assert round_state.ending_condition == "turn_limit_reached"
    assert len(round_state.conversation_history) == 2
    assert orchestrator.turn_manager.execute_turn.call_count == 2  # type: ignore
    assert round_state.round_scores == {"Alice": 2, "Bob": 0}


def test_run_round_spy_guess_wins(orchestrator: GameOrchestrator):
    """Tests that a round ends correctly when the spy guesses the location."""
    orchestrator.spy_guess_manager.check_spy_guess.return_value = SpyGuess(  # type: ignore
        "Alice", "Bank", "Bank", True
    )
    round_state = orchestrator.run_round(1, ["Alice", "Bob"], ["Bank"])

    assert round_state.ending_condition == "spy_guess"
    assert len(round_state.conversation_history) == 0  # Game ends on the first turn


def test_run_round_vote_ends_game(orchestrator: GameOrchestrator):
    """Tests that a round ends correctly when a vote succeeds."""
    orchestrator.voting_manager.check_for_vote_initiation.return_value = "Bob"  # type: ignore
    orchestrator.voting_manager.conduct_vote.return_value = VoteAttempt(  # type: ignore
        "Alice", "Bob", {}, passed=True
    )
    round_state = orchestrator.run_round(1, ["Alice", "Bob"], ["Bank"])

    assert round_state.ending_condition == "vote"
    assert len(round_state.conversation_history) == 0


def test_run_round_error_handling(orchestrator: GameOrchestrator):
    """Tests that the orchestrator handles exceptions from managers."""
    orchestrator.turn_manager.execute_turn.side_effect = ValueError("Test error")  # type: ignore
    round_state = orchestrator.run_round(1, ["Alice", "Bob"], ["Bank"])

    assert round_state.ending_condition == "error"
