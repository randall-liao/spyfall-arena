from unittest.mock import MagicMock

import pytest

from config.config_schema import GameConfig, PlayerConfig
from game.game_state import Role
from game.spy_guess_manager import SpyGuessManager
from llm.llm_client_factory import LLMClientFactory
from prompts.prompt_builder import PromptBuilder


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
    builder = MagicMock(spec=PromptBuilder)
    # The spy role prompt is built with a Role object, so we need to mock it
    builder.build_role_prompt.return_value = "You are the Spy."
    return builder


@pytest.fixture
def mock_config() -> GameConfig:
    """Provides a mock GameConfig for testing."""
    return GameConfig(
        players=[
            PlayerConfig(nickname="Alice", model_name="test-model"),
            PlayerConfig(nickname="Bob", model_name="test-model"),
        ],
        locations=["Bank"],
    )


@pytest.fixture
def spy_guess_manager(
    mock_llm_factory: LLMClientFactory,
    mock_prompt_builder: PromptBuilder,
    mock_config: GameConfig,
) -> SpyGuessManager:
    """Provides a SpyGuessManager instance with mocked dependencies."""
    return SpyGuessManager(mock_llm_factory, mock_prompt_builder, mock_config)


def test_spy_guess_correct(spy_guess_manager: SpyGuessManager):
    """Tests a correct spy guess."""
    spy_guess_manager.llm_factory.create_client.return_value.generate_structured_response.return_value = {  # type: ignore
        "make_guess": True,
        "location_guess": "Bank",
    }
    guess_result = spy_guess_manager.check_spy_guess(
        "Alice", [], ["Bank", "Airport"], "Bank"
    )

    assert guess_result is not None
    assert guess_result.correct
    assert guess_result.guessed_location == "Bank"


def test_spy_guess_incorrect(spy_guess_manager: SpyGuessManager):
    """Tests an incorrect spy guess."""
    spy_guess_manager.llm_factory.create_client.return_value.generate_structured_response.return_value = {  # type: ignore
        "make_guess": True,
        "location_guess": "Airport",
    }
    guess_result = spy_guess_manager.check_spy_guess(
        "Alice", [], ["Bank", "Airport"], "Bank"
    )

    assert guess_result is not None
    assert not guess_result.correct


def test_spy_does_not_guess(spy_guess_manager: SpyGuessManager):
    """Tests the case where the spy chooses not to guess."""
    spy_guess_manager.llm_factory.create_client.return_value.generate_structured_response.return_value = {  # type: ignore
        "make_guess": False
    }
    guess_result = spy_guess_manager.check_spy_guess(
        "Alice", [], ["Bank", "Airport"], "Bank"
    )
    assert guess_result is None


def test_invalid_guess_format(spy_guess_manager: SpyGuessManager):
    """Tests that a ValueError is raised for a malformed guess response."""
    spy_guess_manager.llm_factory.create_client.return_value.generate_structured_response.return_value = {  # type: ignore
        "invalid_key": "value"
    }
    with pytest.raises(ValueError, match="LLM returned invalid spy guess format"):
        spy_guess_manager.check_spy_guess("Alice", [], ["Bank", "Airport"], "Bank")
