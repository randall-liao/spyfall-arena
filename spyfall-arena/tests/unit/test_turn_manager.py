from unittest.mock import MagicMock

import pytest

from spyfall_arena.config.config_schema import GameConfig, PlayerConfig
from spyfall_arena.game.game_state import Role
from spyfall_arena.game.turn_manager import (AnswerResponse, QuestionResponse,
                                             TurnManager)
from spyfall_arena.llm.llm_client_factory import LLMClientFactory
from spyfall_arena.prompts.prompt_builder import PromptBuilder


@pytest.fixture
def mock_llm_factory() -> LLMClientFactory:
    """Mocks the LLMClientFactory and the client it creates."""
    mock_client = MagicMock()
    mock_client.generate_structured_response.side_effect = [
        {"target_nickname": "Bob", "question": "Are you a spy?"},
        {"answer": "No, I am not."},
    ]

    mock_factory = MagicMock(spec=LLMClientFactory)
    mock_factory.create_client.return_value = mock_client
    return mock_factory


@pytest.fixture
def mock_prompt_builder() -> PromptBuilder:
    """Mocks the PromptBuilder."""
    return MagicMock(spec=PromptBuilder)


@pytest.fixture
def mock_config() -> GameConfig:
    """Provides a mock GameConfig for testing."""
    return GameConfig(
        players=[
            PlayerConfig(nickname="Alice", model_name="test-model"),
            PlayerConfig(nickname="Bob", model_name="test-model"),
            PlayerConfig(nickname="Charlie", model_name="test-model"),
        ],
        locations=["Bank"],
    )


@pytest.fixture
def turn_manager(
    mock_llm_factory: LLMClientFactory,
    mock_prompt_builder: PromptBuilder,
    mock_config: GameConfig,
) -> TurnManager:
    """Provides a TurnManager instance with mocked dependencies."""
    return TurnManager(mock_llm_factory, mock_prompt_builder, mock_config)


@pytest.fixture
def player_roles() -> dict[str, Role]:
    return {
        "Alice": Role(is_spy=True, location=None),
        "Bob": Role(is_spy=False, location="Bank"),
        "Charlie": Role(is_spy=False, location="Bank"),
    }


def test_execute_turn_success(turn_manager: TurnManager, player_roles: dict[str, Role]):
    """Tests the successful execution of a single turn."""
    turn = turn_manager.execute_turn(
        current_asker="Alice",
        player_roles=player_roles,
        conversation_history=[],
        player_nicknames=["Alice", "Bob", "Charlie"],
    )

    assert turn.asker_nickname == "Alice"
    assert turn.answerer_nickname == "Bob"
    assert turn.question == "Are you a spy?"
    assert turn.answer == "No, I am not."
    assert turn.turn_number == 1

    # Verify that the correct prompts were built and the LLM was called
    assert turn_manager.prompt_builder.build_question_prompt.called  # type: ignore
    assert turn_manager.prompt_builder.build_answer_prompt.called  # type: ignore
    assert turn_manager.llm_factory.create_client.call_count == 2  # type: ignore


def test_invalid_question_format(
    turn_manager: TurnManager, player_roles: dict[str, Role]
):
    """Tests that a ValueError is raised for a malformed question from the LLM."""
    turn_manager.llm_factory.create_client.return_value.generate_structured_response.side_effect = [  # type: ignore
        {"invalid_key": "value"},  # Malformed question
    ]

    with pytest.raises(ValueError, match="LLM returned invalid question format"):
        turn_manager.execute_turn(
            "Alice", player_roles, [], ["Alice", "Bob", "Charlie"]
        )


def test_invalid_answer_format(
    turn_manager: TurnManager, player_roles: dict[str, Role]
):
    """Tests that a ValueError is raised for a malformed answer from the LLM."""
    turn_manager.llm_factory.create_client.return_value.generate_structured_response.side_effect = [  # type: ignore
        {"target_nickname": "Bob", "question": "Are you a spy?"},
        {"invalid_key": "value"},  # Malformed answer
    ]

    with pytest.raises(ValueError, match="LLM returned invalid answer format"):
        turn_manager.execute_turn(
            "Alice", player_roles, [], ["Alice", "Bob", "Charlie"]
        )


def test_invalid_target_from_llm(
    turn_manager: TurnManager, player_roles: dict[str, Role]
):
    """Tests that a ValueError is raised if the LLM selects an invalid target."""
    turn_manager.llm_factory.create_client.return_value.generate_structured_response.side_effect = [  # type: ignore
        {"target_nickname": "Alice", "question": "Why did you pick me?"},
    ]

    with pytest.raises(ValueError, match="Invalid target selected by LLM"):
        turn_manager.execute_turn(
            "Alice", player_roles, [], ["Alice", "Bob", "Charlie"]
        )


def test_get_next_asker(turn_manager: TurnManager):
    """Tests that the next asker is correctly identified."""
    assert turn_manager.get_next_asker("Bob") == "Bob"


def test_get_valid_targets(turn_manager: TurnManager):
    """Tests the logic for determining valid targets for questioning."""
    players = ["Alice", "Bob", "Charlie", "David"]

    # Alice is asking, no previous asker
    targets1 = turn_manager.get_valid_targets("Alice", None, players)
    assert targets1 == ["Bob", "Charlie", "David"]

    # Bob is asking, Alice was the previous asker
    targets2 = turn_manager.get_valid_targets("Bob", "Alice", players)
    assert targets2 == ["Charlie", "David"]
