from typing import Dict, List, Optional, Set

from pydantic import BaseModel, ValidationError

from spyfall_arena.game.game_state import Role, VoteAttempt
from spyfall_arena.llm.llm_client_factory import LLMClientFactory
from spyfall_arena.prompts.prompt_builder import PromptBuilder


class VoteInitiationResponse(BaseModel):
    initiate_vote: bool
    suspect_nickname: Optional[str] = None


class VoteDecisionResponse(BaseModel):
    vote_yes: bool


from spyfall_arena.config.config_schema import GameConfig
class VotingManager:
    """Manages the voting process in a round of Spyfall."""

    def __init__(
        self,
        llm_factory: LLMClientFactory,
        prompt_builder: PromptBuilder,
        config: GameConfig,
    ):
        self.llm_factory = llm_factory
        self.prompt_builder = prompt_builder
        self.config = config

    def check_for_vote_initiation(
        self,
        current_player: str,
        player_roles: Dict[str, Role],
        conversation_history: List,
        players_who_voted: Set[str],
    ) -> Optional[str]:
        """
        Asks the current player if they want to initiate a vote.

        Returns:
            The nickname of the suspected spy if a vote is initiated, otherwise None.

        Raises:
            ValueError: If the LLM provides an invalid response.
        """
        can_vote = current_player not in players_who_voted

        prompt = self.prompt_builder.build_vote_initiation_prompt(
            conversation_history, can_vote
        )
        system_prompt = self.prompt_builder.build_system_prompt()
        role_prompt = self.prompt_builder.build_role_prompt(
            player_roles[current_player]
        )

        player_config = next(
            p for p in self.config.players if p.nickname == current_player
        )
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
            response = VoteInitiationResponse(**structured_response)
            if response.initiate_vote and response.suspect_nickname:
                return response.suspect_nickname
            return None
        except ValidationError as e:
            raise ValueError(f"LLM returned invalid vote initiation format: {e}") from e

    def conduct_vote(
        self,
        initiator: str,
        suspect: str,
        player_roles: Dict[str, Role],
        conversation_history: List,
    ) -> VoteAttempt:
        """
        Conducts a vote to indict a suspected spy.

        Returns:
            A VoteAttempt object with the results of the vote.
        """
        votes: Dict[str, bool] = {}
        system_prompt = self.prompt_builder.build_system_prompt()

        for nickname, role in player_roles.items():
            prompt = self.prompt_builder.build_vote_decision_prompt(
                conversation_history, suspect
            )
            role_prompt = self.prompt_builder.build_role_prompt(role)

            player_config = next(
                p for p in self.config.players if p.nickname == nickname
            )
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
                response = VoteDecisionResponse(**structured_response)
                votes[nickname] = response.vote_yes
            except (ValidationError, KeyError):
                # If the LLM fails to vote, assume a 'no' vote to be safe
                votes[nickname] = False

        passed = all(votes.values())
        return VoteAttempt(
            initiator=initiator, suspect=suspect, votes=votes, passed=passed
        )
