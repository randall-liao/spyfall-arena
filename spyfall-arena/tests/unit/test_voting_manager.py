from unittest.mock import MagicMock

import pytest

from spyfall_arena.config.config_schema import GameConfig, PlayerConfig
from spyfall_arena.game.game_state import Role
from spyfall_arena.game.voting_manager import VotingManager
from spyfall_arena.llm.llm_client_factory import LLMClientFactory
from spyfall_arena.prompts.prompt_builder import PromptBuilder


@pytest.fixture
def mock_llm_factory() -> LLMClientFactory:
    """Mocks the LLMClientFactory and the client it creates."""
    mock_client = MagicMock()
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
def voting_manager(
    mock_llm_factory: LLMClientFactory,
    mock_prompt_builder: PromptBuilder,
    mock_config: GameConfig,
) -> VotingManager:
    """Provides a VotingManager instance with mocked dependencies."""
    return VotingManager(mock_llm_factory, mock_prompt_builder, mock_config)


@pytest.fixture
def player_roles() -> dict[str, Role]:
    return {
        "Alice": Role(is_spy=True, location=None),
        "Bob": Role(is_spy=False, location="Bank"),
        "Charlie": Role(is_spy=False, location="Bank"),
    }


def test_vote_initiation_yes(
    voting_manager: VotingManager, player_roles: dict[str, Role]
):
    """Tests that a suspect's nickname is returned when a vote is initiated."""
    voting_manager.llm_factory.create_client.return_value.generate_structured_response.return_value = {  # type: ignore
        "initiate_vote": True,
        "suspect_nickname": "Bob",
    }
    suspect = voting_manager.check_for_vote_initiation("Alice", player_roles, [], set())
    assert suspect == "Bob"


def test_vote_initiation_no(
    voting_manager: VotingManager, player_roles: dict[str, Role]
):
    """Tests that None is returned when a vote is not initiated."""
    voting_manager.llm_factory.create_client.return_value.generate_structured_response.return_value = {  # type: ignore
        "initiate_vote": False
    }
    suspect = voting_manager.check_for_vote_initiation("Alice", player_roles, [], set())
    assert suspect is None


def test_cannot_initiate_vote_twice(
    voting_manager: VotingManager, player_roles: dict[str, Role]
):
    """Tests that a player who has already voted cannot initiate another vote."""
    voting_manager.llm_factory.create_client.return_value.generate_structured_response.return_value = {  # type: ignore
        "initiate_vote": False
    }
    voting_manager.check_for_vote_initiation("Alice", player_roles, [], {"Alice"})
    # Verify that the prompt builder was called with can_vote=False
    voting_manager.prompt_builder.build_vote_initiation_prompt.assert_called_with(  # type: ignore
        [], False
    )


def test_conduct_vote_unanimous_yes(
    voting_manager: VotingManager, player_roles: dict[str, Role]
):
    """Tests a successful vote where all players vote yes."""
    voting_manager.llm_factory.create_client.return_value.generate_structured_response.return_value = {  # type: ignore
        "vote_yes": True
    }
    vote_attempt = voting_manager.conduct_vote("Alice", "Bob", player_roles, [])
    assert vote_attempt.passed
    assert vote_attempt.votes == {"Alice": True, "Bob": True, "Charlie": True}


def test_conduct_vote_not_unanimous(
    voting_manager: VotingManager, player_roles: dict[str, Role]
):
    """Tests a failed vote where not all players vote yes."""
    # Simulate one 'no' vote
    mock_client = voting_manager.llm_factory.create_client.return_value  # type: ignore
    mock_client.generate_structured_response.side_effect = [  # type: ignore
        {"vote_yes": True},
        {"vote_yes": False},  # Bob votes no
        {"vote_yes": True},
    ]
    vote_attempt = voting_manager.conduct_vote("Alice", "Bob", player_roles, [])
    assert not vote_attempt.passed
    assert vote_attempt.votes == {"Alice": True, "Bob": False, "Charlie": True}


def test_conduct_vote_llm_failure(
    voting_manager: VotingManager, player_roles: dict[str, Role]
):
    """Tests that a failed LLM response is treated as a 'no' vote."""
    mock_client = voting_manager.llm_factory.create_client.return_value  # type: ignore
    mock_client.generate_structured_response.side_effect = [  # type: ignore
        {"vote_yes": True},
        {"invalid_key": "value"},  # Bob's vote fails
        {"vote_yes": True},
    ]
    vote_attempt = voting_manager.conduct_vote("Alice", "Bob", player_roles, [])
    assert not vote_attempt.passed
    assert vote_attempt.votes["Bob"] is False


def test_invalid_initiation_format(
    voting_manager: VotingManager, player_roles: dict[str, Role]
):
    """Tests that a ValueError is raised for a malformed initiation response."""
    voting_manager.llm_factory.create_client.return_value.generate_structured_response.return_value = {  # type: ignore
        "invalid_key": "value"
    }
    with pytest.raises(ValueError, match="LLM returned invalid vote initiation format"):
        voting_manager.check_for_vote_initiation("Alice", player_roles, [], set())
