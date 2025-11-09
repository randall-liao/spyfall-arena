from typing import List, Optional

from pydantic import BaseModel, ValidationError

from game.game_state import Role, SpyGuess
from llm.llm_client_factory import LLMClientFactory
from prompts.prompt_builder import PromptBuilder


class SpyGuessResponse(BaseModel):
    make_guess: bool
    location_guess: Optional[str] = None


from config.config_schema import GameConfig
class SpyGuessManager:
    """Manages the spy's attempt to guess the location."""

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
        """
        Asks the spy if they want to guess the location and processes the guess.

        Returns:
            A SpyGuess object if the spy makes a guess, otherwise None.

        Raises:
            ValueError: If the LLM provides an invalid response.
        """
        prompt = self.prompt_builder.build_spy_guess_prompt(
            conversation_history, available_locations
        )
        system_prompt = self.prompt_builder.build_system_prompt()
        # The role prompt for the spy is generic and doesn't need the Role object
        role_prompt = self.prompt_builder.build_role_prompt(Role(is_spy=True, location=None))

        player_config = next(p for p in self.config.players if p.nickname == spy_nickname)
        llm_client = self.llm_factory.create_client(
            model_name=player_config.model_name,
            api_key="",  # API key should be handled by the client
            temperature=player_config.temperature,
        )
        structured_response = llm_client.generate_structured_response(
            system_prompt,
            f"{role_prompt}\n{prompt}",
            response_schema={"type": "json_object"},
        )

        try:
            response = SpyGuessResponse(**structured_response)
            if response.make_guess and response.location_guess:
                is_correct = response.location_guess == actual_location
                return SpyGuess(
                    spy_nickname=spy_nickname,
                    guessed_location=response.location_guess,
                    actual_location=actual_location,
                    correct=is_correct,
                )
            return None
        except ValidationError as e:
            raise ValueError(f"LLM returned invalid spy guess format: {e}") from e
