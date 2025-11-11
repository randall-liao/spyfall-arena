from pathlib import Path
from unittest.mock import MagicMock, patch

from config.config_loader import ConfigLoader
from game.game_state import GamePhase
from game.orchestrator import GameOrchestrator


def test_e2e_game_flow_spy_wins_by_guessing():
    """
    Tests a full E2E game flow where the spy wins by guessing the location.
    With a random seed of 42, the test is deterministic:
    - Players: Alice, Bob, Charlie
    - Spy: Alice
    - Location: 'Test Location 3'
    - First Turn: Alice
    """
    config_loader = ConfigLoader()
    config = config_loader.load_config(Path("tests/e2e/test_config.yaml"))

    mock_llm_client = MagicMock()
    mock_llm_client.generate_structured_response.return_value = {
        "make_guess": True,
        "location_guess": "Test Location 3",
    }

    with patch(
        "llm.llm_client_factory.LLMClientFactory.create_client",
        return_value=mock_llm_client,
    ):
        orchestrator = GameOrchestrator(config)
        final_game_state = orchestrator.run_game()

    # Assertions
    assert final_game_state.phase == GamePhase.COMPLETED
    assert len(final_game_state.rounds_data) == 1

    round_state = final_game_state.rounds_data[0]
    assert round_state.spy_nickname == "Alice"
    assert round_state.location == "Test Location 3"
    assert round_state.ending_condition == "spy_guess"
    assert round_state.spy_guess is not None
    assert round_state.spy_guess.correct is True

    assert final_game_state.player_scores == {"Alice": 4, "Bob": 0, "Charlie": 0}
    mock_llm_client.generate_structured_response.assert_called_once()


def test_e2e_game_flow_civilians_win_by_voting():
    """
    Tests a full E2E game flow where civilians win by correctly voting out the spy.
    - Spy: Alice
    - Scenario: After one turn, Bob initiates a vote for Alice, and it passes.
    """
    config_loader = ConfigLoader()
    config = config_loader.load_config(Path("tests/e2e/test_config.yaml"))

    mock_llm_client = MagicMock()
    mock_llm_client.generate_structured_response.side_effect = [
        # Turn 1: Alice (Spy) asks Bob
        {"make_guess": False},
        {"initiate_vote": False, "suspect_nickname": None},
        {"target_nickname": "Bob", "question": "What are you looking at?"},
        {"answer": "Just admiring the architecture."},
        # Turn 2: Bob (Civilian) is now the asker
        {"initiate_vote": True, "suspect_nickname": "Alice"},
        # Voting Phase - unanimous vote to make it pass
        {"vote_yes": True},  # Alice's vote
        {"vote_yes": True},  # Bob's vote
        {"vote_yes": True},  # Charlie's vote
    ]

    with patch(
        "llm.llm_client_factory.LLMClientFactory.create_client",
        return_value=mock_llm_client,
    ):
        orchestrator = GameOrchestrator(config)
        final_game_state = orchestrator.run_game()

    # Assertions
    assert final_game_state.phase == GamePhase.COMPLETED
    assert len(final_game_state.rounds_data) == 1

    round_state = final_game_state.rounds_data[0]
    assert round_state.spy_nickname == "Alice"
    assert round_state.ending_condition == "vote"

    assert len(round_state.votes) == 1
    vote_attempt = round_state.votes[0]
    assert vote_attempt.initiator == "Bob"
    assert vote_attempt.suspect == "Alice"
    assert vote_attempt.passed is True
    assert vote_attempt.votes == {"Alice": True, "Bob": True, "Charlie": True}

    assert final_game_state.player_scores == {"Alice": 0, "Bob": 2, "Charlie": 1}
    assert mock_llm_client.generate_structured_response.call_count == 8
