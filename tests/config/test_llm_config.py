import pytest
from pydantic import ValidationError
from config.config_schema import LLMConfig, GameConfig, PlayerConfig


def test_llm_config_defaults():
    """Test LLMConfig default values."""
    config = LLMConfig()
    assert config.max_retries == 2
    assert config.retry_min_wait == 1.0
    assert config.retry_max_wait == 10.0


def test_llm_config_valid_values():
    """Test LLMConfig with valid custom values."""
    config = LLMConfig(max_retries=5, retry_min_wait=2.0, retry_max_wait=20.0)
    assert config.max_retries == 5
    assert config.retry_min_wait == 2.0
    assert config.retry_max_wait == 20.0


def test_llm_config_max_retries_bounds():
    """Test validation for max_retries bounds."""
    # Test lower bound
    with pytest.raises(ValidationError):
        LLMConfig(max_retries=-1)

    # Test upper bound
    with pytest.raises(ValidationError):
        LLMConfig(max_retries=11)


def test_llm_config_retry_min_wait_bounds():
    """Test validation for retry_min_wait bounds."""
    # Test lower bound
    with pytest.raises(ValidationError):
        LLMConfig(retry_min_wait=0.05)

    # Test upper bound
    with pytest.raises(ValidationError):
        LLMConfig(retry_min_wait=61.0)


def test_llm_config_retry_max_wait_bounds():
    """Test validation for retry_max_wait bounds."""
    # Test lower bound
    with pytest.raises(ValidationError):
        LLMConfig(retry_max_wait=0.5)

    # Test upper bound
    with pytest.raises(ValidationError):
        LLMConfig(retry_max_wait=301.0)


def test_game_config_with_llm_field():
    """Test GameConfig accepts llm field."""
    # Create minimal valid game config
    game_config = GameConfig(
        players=[
            PlayerConfig(nickname="p1", model_name="m1"),
            PlayerConfig(nickname="p2", model_name="m2"),
        ],
        locations=["loc1"],
        llm=LLMConfig(max_retries=3),
    )
    assert game_config.llm.max_retries == 3


def test_game_config_default_llm_field():
    """Test GameConfig uses default LLMConfig when not specified."""
    game_config = GameConfig(
        players=[
            PlayerConfig(nickname="p1", model_name="m1"),
            PlayerConfig(nickname="p2", model_name="m2"),
        ],
        locations=["loc1"],
    )
    assert game_config.llm.max_retries == 2
