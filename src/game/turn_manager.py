import json
from typing import Dict, List, Optional

from loguru import logger
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
    """
    Manages the question-and-answer flow for a single turn in Spyfall.

    Encapsulates the logic defined in 'Req 3: Game Loop and Turn-Based Interaction',
    specifically the Asking Phase and Answering Phase.
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

    def execute_turn(
        self,
        current_asker: str,
        player_roles: Dict[str, Role],
        conversation_history: List[Turn],
        player_nicknames: List[str],
        previous_asker: Optional[str] = None,
    ) -> Turn:
        """
        Executes a complete Q&A interaction between two players.

        Handles:
        1. Context assembly for the 'Asker' (Req 3 Asking Phase).
        2. LLM generation and validation of the question.
        3. Context assembly for the 'Answerer' (Req 3 Answering Phase).
        4. LLM generation and validation of the answer.

        Raises:
            ValueError: If the LLM generates output that violates the schema or game rules.
        """
        logger.info(f"Turn execution started. Asker: {current_asker}")
        asker_role = player_roles[current_asker]

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
        asker_reasoning = (
            asker_config.reasoning.model_dump() if asker_config.reasoning else None
        )
        asker_llm_client = self.llm_factory.create_client(
            model_name=asker_config.model_name,
            provider=asker_config.provider,
            temperature=asker_config.temperature,
            reasoning_config=asker_reasoning,
        )

        # Enforce structured JSON output to ensure reliable parsing of the target and question.
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
            logger.debug(
                f"Player {current_asker} asks {target_nickname}: {question_text}"
            )
        except ValidationError as e:
            raise ValueError(f"LLM returned invalid question format: {e}") from e

        logger.info(f"Target {target_nickname} answering...")
        answerer_role = player_roles[target_nickname]
        answer_prompt = self.prompt_builder.build_answer_prompt(
            conversation_history, question_text
        )
        role_prompt = self.prompt_builder.build_role_prompt(answerer_role)

        answerer_config = next(
            p for p in self.config.players if p.nickname == target_nickname
        )
        answerer_reasoning = (
            answerer_config.reasoning.model_dump() if answerer_config.reasoning else None
        )
        answerer_llm_client = self.llm_factory.create_client(
            model_name=answerer_config.model_name,
            provider=answerer_config.provider,
            temperature=answerer_config.temperature,
            reasoning_config=answerer_reasoning,
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

        return Turn(
            turn_number=len(conversation_history) + 1,
            asker_nickname=current_asker,
            answerer_nickname=target_nickname,
            question=question_text,
            answer=answer_text,
        )

    def get_next_asker(self, current_answerer: str) -> str:
        """
        Determines the next asker based on game rules (Req 3, Rotation).
        The player who answered becomes the next asker.
        """
        return current_answerer

    def get_valid_targets(
        self,
        current_asker: str,
        previous_asker: Optional[str],
        player_nicknames: List[str],
    ) -> List[str]:
        """
        Calculates valid question targets.

        Enforces the rule that a player cannot ask themselves or the player
        who immediately preceded them (preventing infinite loops between two players).
        """
        invalid_targets = {current_asker, previous_asker}
        return [p for p in player_nicknames if p not in invalid_targets]
