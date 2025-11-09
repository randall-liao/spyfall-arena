from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from config.config_schema import GameConfig, PromptsConfig
from game.game_state import Role, Turn
from prompts.prompt_builder import PromptBuilder


@pytest.fixture
def mock_config(tmp_path: Path) -> GameConfig:
    """Mocks the GameConfig and creates dummy template files."""
    # Create dummy template files
    (tmp_path / "prompts").mkdir()
    (tmp_path / "prompts" / "system.txt").write_text("System prompt")
    (tmp_path / "prompts" / "civilian.txt").write_text(
        "You are a civilian at {{ location }}."
    )
    (tmp_path / "prompts" / "spy.txt").write_text("You are the spy.")

    # Mock config to point to the dummy files
    mock_prompts = PromptsConfig(
        system_prompt_template=str(tmp_path / "prompts" / "system.txt"),
        civilian_role_template=str(tmp_path / "prompts" / "civilian.txt"),
        spy_role_template=str(tmp_path / "prompts" / "spy.txt"),
    )

    config = MagicMock(spec=GameConfig)
    config.prompts = mock_prompts
    return config


@pytest.fixture
def prompt_builder(mock_config: GameConfig) -> PromptBuilder:
    """Provides a PromptBuilder instance with mocked templates."""
    builder = PromptBuilder(mock_config)
    builder.load_templates()
    return builder


def test_template_loading(prompt_builder: PromptBuilder):
    """Tests that the templates are loaded correctly."""
    assert prompt_builder.system_prompt == "System prompt"
    assert prompt_builder.civilian_template == "You are a civilian at {{ location }}."
    assert prompt_builder.spy_template == "You are the spy."


def test_read_template(tmp_path: Path):
    """Tests the _read_template method directly."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")
    content = PromptBuilder._read_template(test_file)
    assert content == "Test content"


def test_template_loading_file_not_found():
    """Tests that a RuntimeError is raised if a template file is not found."""
    mock_prompts = MagicMock(spec=PromptsConfig)
    mock_prompts.system_prompt_template = "non_existent.txt"

    config = MagicMock(spec=GameConfig)
    config.prompts = mock_prompts

    builder = PromptBuilder(config)
    with pytest.raises(RuntimeError):
        builder.load_templates()


def test_build_role_prompt(prompt_builder: PromptBuilder):
    """Tests the construction of role-specific prompts."""
    spy_role = Role(is_spy=True, location=None)
    civilian_role = Role(is_spy=False, location="Bank")

    assert prompt_builder.build_role_prompt(spy_role) == "You are the spy."
    assert (
        prompt_builder.build_role_prompt(civilian_role) == "You are a civilian at Bank."
    )


def test_build_question_prompt(prompt_builder: PromptBuilder):
    """Tests the construction of the question prompt."""
    history = [Turn(1, "A", "B", "q", "a")]
    prompt = prompt_builder.build_question_prompt(history, ["C", "D"])
    assert "Turn 1: A asked B" in prompt
    assert "Choose one of the following players to question: C, D" in prompt
    assert '"target_nickname": "player_name"' in prompt


def test_build_answer_prompt(prompt_builder: PromptBuilder):
    """Tests the construction of the answer prompt."""
    history = [Turn(1, "A", "B", "q", "a")]
    prompt = prompt_builder.build_answer_prompt(history, "Are you the spy?")
    assert "You have been asked the following question: 'Are you the spy?'" in prompt
    assert '"answer": "your_answer_here"' in prompt


def test_build_vote_initiation_prompt(prompt_builder: PromptBuilder):
    """Tests the vote initiation prompt for both possible cases."""
    prompt_can_vote = prompt_builder.build_vote_initiation_prompt([], True)
    assert "Do you want to initiate a vote" in prompt_can_vote
    assert '"initiate_vote": true_or_false' in prompt_can_vote

    prompt_cannot_vote = prompt_builder.build_vote_initiation_prompt([], False)
    assert "You have already initiated a vote" in prompt_cannot_vote
    assert '"initiate_vote": false' in prompt_cannot_vote


def test_build_vote_decision_prompt(prompt_builder: PromptBuilder):
    """Tests the construction of the vote decision prompt."""
    prompt = prompt_builder.build_vote_decision_prompt([], "Charlie")
    assert "Charlie has been accused of being the spy." in prompt
    assert '"vote_yes": true_or_false' in prompt


def test_build_spy_guess_prompt(prompt_builder: PromptBuilder):
    """Tests the construction of the spy guess prompt."""
    prompt = prompt_builder.build_spy_guess_prompt([], ["Bank", "Airport"])
    assert "Available locations: Bank, Airport" in prompt
    assert '"make_guess": true_or_false' in prompt


def test_empty_conversation_history(prompt_builder: PromptBuilder):
    """Tests that the history is formatted correctly when it is empty."""
    prompt = prompt_builder.build_question_prompt([], ["C", "D"])
    assert "The conversation has not started yet." in prompt
