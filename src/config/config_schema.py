from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field, conint, constr, field_validator


class LLMProvider(str, Enum):
    OPEN_ROUTER = "OPEN_ROUTER"
    GOOGLE_AI_STUDIO = "GOOGLE_AI_STUDIO"


class ReasoningConfig(BaseModel):
    """
    Configuration for OpenRouter reasoning tokens (thinking tokens).

    Attributes:
        effort: reasoning effort level (e.g. "high", "medium", "low").
        max_tokens: maximum number of tokens to use for reasoning.
        exclude: whether to exclude reasoning tokens from the response.
        enabled: whether to enable reasoning (inferred if effort/max_tokens set).
    """
    effort: Optional[str] = None
    max_tokens: Optional[int] = None
    exclude: Optional[bool] = None
    enabled: Optional[bool] = None


class PlayerConfig(BaseModel):
    nickname: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)
    provider: LLMProvider = Field(default=LLMProvider.OPEN_ROUTER)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    reasoning: Optional[ReasoningConfig] = None


class GameRulesConfig(BaseModel):
    num_rounds: int = Field(default=3, gt=0)
    max_turns_per_round: int = Field(default=20, gt=0)
    random_seed: Optional[int] = 42


class PromptsConfig(BaseModel):
    system_prompt_template: str = "prompts/templates/system_prompt.txt"
    civilian_role_template: str = "prompts/templates/civilian_role.txt"
    spy_role_template: str = "prompts/templates/spy_role.txt"


class LoggingConfig(BaseModel):
    output_dir: str = "logs"
    save_full_prompts: bool = False
    log_level: str = "INFO"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        upper_value = value.upper()
        if upper_value not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return upper_value


class RateLimitConfig(BaseModel):
    enabled: bool = True
    requests_per_minute: int = Field(default=15, gt=0)
    burst_limit: int = Field(default=5, gt=0)


class LLMConfig(BaseModel):
    max_retries: int = Field(default=2, ge=0, le=10)
    retry_min_wait: float = Field(default=1.0, ge=0.1, le=60.0)
    retry_max_wait: float = Field(default=10.0, ge=1.0, le=300.0)


class GameConfig(BaseModel):
    game: GameRulesConfig = Field(default_factory=GameRulesConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    players: List[PlayerConfig] = Field(..., min_length=2, max_length=12)
    locations: List[str] = Field(..., min_length=1)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @field_validator("players")
    @classmethod
    def unique_nicknames(cls, players: List[PlayerConfig]) -> List[PlayerConfig]:
        nicknames = [p.nickname for p in players]
        if len(nicknames) != len(set(nicknames)):
            raise ValueError("Player nicknames must be unique")
        return players

    @field_validator("locations")
    @classmethod
    def unique_locations(cls, locations: List[str]) -> List[str]:
        if len(locations) != len(set(locations)):
            raise ValueError("Locations must be unique")
        return locations
