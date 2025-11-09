import json
from typing import Dict, List, Optional

from pydantic import BaseModel, ValidationError

from game.game_state import Role, Turn
from llm.llm_client_factory import LLMClientFactory
from prompts.prompt_builder import PromptBuilder


class QuestionResponse(BaseModel):
    target_nickname: str
    question: str


class AnswerResponse(BaseModel):
    answer: str


from config.config_schema import GameConfig
class TurnManager:
    """Manages the question-and-answer flow for a single turn in Spyfall."""

    def __init__(
        self,
        llm_factory: LLMClientFactory,
        prompt_builder: PromptBuilder,
        config: GameConfig,
    ):
        self.llm_factory = llm_factory
        self.prompt_builder = prompt_builder
        self.config = config

    def execute_turn(
        self,
        current_asker: str,
        player_roles: Dict[str, Role],
        conversation_history: List[Turn],
        player_nicknames: List[str],
        previous_asker: Optional[str] = None,
    ) -> Turn:
        """
        Executes a single question-and-answer turn.

        Args:
            current_asker: The nickname of the player asking the question.
            player_roles: A dictionary mapping player nicknames to their roles.
            conversation_history: The history of the conversation so far.
            player_nicknames: A list of all player nicknames.
            previous_asker: The nickname of the player who asked the previous question.

        Returns:
            A Turn object representing the completed turn.

        Raises:
            ValueError: If the LLM provides an invalid response.
        """
        asker_role = player_roles[current_asker]

        # 1. Asker asks a question
        valid_targets = self.get_valid_targets(
            current_asker, previous_asker, player_nicknames
        )
        question_prompt = self.prompt_builder.build_question_prompt(
            conversation_history, valid_targets
        )
        system_prompt = self.prompt_builder.build_system_prompt()
        role_prompt = self.prompt_builder.build_role_prompt(asker_role)

        asker_config = next(
            p for p in self.config.players if p.nickname == current_asker
        )
        asker_llm_client = self.llm_factory.create_client(
            model_name=asker_config.model_name,
            api_key="",  # API key should be handled by the client
            temperature=asker_config.temperature,
        )

        structured_question = asker_llm_client.generate_structured_response(
            system_prompt,
            f"{role_prompt}\n{question_prompt}",
            response_schema={"type": "json_object"},
        )

        try:
            question_data = QuestionResponse(**structured_question)
            if question_data.target_nickname not in valid_targets:
                raise ValueError(
                    f"Invalid target selected by LLM: {question_data.target_nickname}"
                )

            target_nickname = question_data.target_nickname
            question_text = question_data.question
        except ValidationError as e:
            raise ValueError(f"LLM returned invalid question format: {e}") from e

        # 2. Target answers the question
        answerer_role = player_roles[target_nickname]
        answer_prompt = self.prompt_builder.build_answer_prompt(
            conversation_history, question_text
        )
        role_prompt = self.prompt_builder.build_role_prompt(answerer_role)

        answerer_config = next(
            p for p in self.config.players if p.nickname == target_nickname
        )
        answerer_llm_client = self.llm_factory.create_client(
            model_name=answerer_config.model_name,
            api_key="",  # API key should be handled by the client
            temperature=answerer_config.temperature,
        )
        structured_answer = answerer_llm_client.generate_structured_response(
            system_prompt,
            f"{role_prompt}\n{answer_prompt}",
            response_schema={"type": "json_object"},
        )

        try:
            answer_data = AnswerResponse(**structured_answer)
            answer_text = answer_data.answer
        except ValidationError as e:
            raise ValueError(f"LLM returned invalid answer format: {e}") from e

        # 3. Create and return the Turn object
        return Turn(
            turn_number=len(conversation_history) + 1,
            asker_nickname=current_asker,
            answerer_nickname=target_nickname,
            question=question_text,
            answer=answer_text,
        )

    def get_next_asker(self, current_answerer: str) -> str:
        """
        Determines the next asker. In Spyfall, the person who just answered becomes the next asker.
        """
        return current_answerer

    def get_valid_targets(
        self,
        current_asker: str,
        previous_asker: Optional[str],
        player_nicknames: List[str],
    ) -> List[str]:
        """
        Gets the list of valid players for the current asker to question.
        A player cannot question themselves or the person who just questioned them.
        """
        invalid_targets = {current_asker, previous_asker}
        return [p for p in player_nicknames if p not in invalid_targets]
