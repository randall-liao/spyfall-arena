from typing import List, Optional

from pydantic import BaseModel, Field, conint, constr, field_validator


class PlayerConfig(BaseModel):
    nickname: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


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


class GameConfig(BaseModel):
    game: GameRulesConfig = Field(default_factory=GameRulesConfig)
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
