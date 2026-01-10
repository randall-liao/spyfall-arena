from typing import List, Optional

from loguru import logger
from pydantic import BaseModel, ValidationError

from config.config_schema import GameConfig
from game.game_state import Role, SpyGuess
from llm.llm_client_factory import LLMClientFactory
from prompts.prompt_builder import PromptBuilder


class SpyGuessResponse(BaseModel):
    make_guess: bool
    location_guess: Optional[str] = None


class SpyGuessManager:
    """Handles spy location guess per game-rules.md (Spy guessing the location).

    At any time, the spy may reveal themselves and guess the location.
    A correct guess ends the round with spy victory (4 pts).
    """

    def __init__(
        self,
        llm_factory: LLMClientFactory,
        prompt_builder: PromptBuilder,
        config: GameConfig,
    ):
        self.llm_factory = llm_factory
        self.prompt_builder = prompt_builder
        self.config = config

    def check_spy_guess(
        self,
        spy_nickname: str,
        conversation_history: List,
        available_locations: List[str],
        actual_location: str,
    ) -> Optional[SpyGuess]:
        """Prompt the spy LLM to decide whether to guess; return SpyGuess if so."""
        prompt = self.prompt_builder.build_spy_guess_prompt(
            conversation_history, available_locations
        )
        system_prompt = self.prompt_builder.build_system_prompt()
        # The role prompt for the spy is generic and doesn't need the Role object
        role_prompt = self.prompt_builder.build_role_prompt(
            Role(is_spy=True, location=None)
        )

        player_config = next(
            p for p in self.config.players if p.nickname == spy_nickname
        )
        reasoning = (
            player_config.reasoning.model_dump() if player_config.reasoning else None
        )
        llm_client = self.llm_factory.create_client(
            model_name=player_config.model_name,
            provider=player_config.provider,
            temperature=player_config.temperature,
            reasoning_config=reasoning,
        )
        structured_response = llm_client.generate_structured_response(
            system_prompt,
            f"{role_prompt}\n{prompt}",
            response_schema={"type": "json_object"},
        )

        try:
            response = SpyGuessResponse(**structured_response)
            if response.make_guess and response.location_guess:
                logger.info(
                    f"Spy {spy_nickname} guesses location: {response.location_guess}"
                )
                is_correct = response.location_guess == actual_location
                logger.info(
                    f"Spy guess result: {'Correct' if is_correct else 'Incorrect'}"
                )
                return SpyGuess(
                    spy_nickname=spy_nickname,
                    guessed_location=response.location_guess,
                    actual_location=actual_location,
                    correct=is_correct,
                )
            return None
        except ValidationError as e:
            raise ValueError(f"LLM returned invalid spy guess format: {e}") from e
