from typing import Dict, List, Optional, Set

from loguru import logger
from pydantic import BaseModel, ValidationError

from game.game_state import Role, VoteAttempt
from llm.llm_client_factory import LLMClientFactory
from prompts.prompt_builder import PromptBuilder


class VoteInitiationResponse(BaseModel):
    initiate_vote: bool
    suspect_nickname: Optional[str] = None


class VoteDecisionResponse(BaseModel):
    vote_yes: bool


from config.config_schema import GameConfig


class VotingManager:
    """
    Manages the voting process for a Spyfall round.

    Implements 'Req 4: Voting and Win Condition Logic'.
    Handles both the initiation of votes by players and the collective voting process.
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

    def check_for_vote_initiation(
        self,
        current_player: str,
        player_roles: Dict[str, Role],
        conversation_history: List,
        players_who_voted: Set[str],
    ) -> Optional[str]:
        """
        Determines if the current player wishes to accuse another player of being the Spy.

        This check happens before a player's turn (Req 3, Turn Structure).
        A player who has already initiated a vote in the current round may be restricted
        (logic handled by `players_who_voted` check).

        Returns:
             The suspect's nickname if a vote is triggered, otherwise None.
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
            response = VoteInitiationResponse(**structured_response)
            if response.initiate_vote and response.suspect_nickname:
                logger.info(
                    f"Vote initiated by {current_player} against {response.suspect_nickname}"
                )
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
        Executes the collective voting process (Req 4).

        Iterates through all players to collect their votes on the accused suspect.
        In Spyfall, a unanimous decision (often excluding the accused/accuser,
        but implementation here checks for unanimous agreement) is usually required.

        Logic:
        1. Queries each player for a "yes/no" vote.
        2. Aggregates results.
        3. Determines if the vote passed based on unanimity.

        Returns:
            A VoteAttempt object containing individual votes and the final result.
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
                response = VoteDecisionResponse(**structured_response)
                votes[nickname] = response.vote_yes
            except (ValidationError, KeyError):
                # Fail-safe: default to 'no' to prevent game crash on single LLM failure.
                votes[nickname] = False

        passed = all(votes.values())
        logger.info(f"Vote result: {'Passed' if passed else 'Failed'} (Votes: {votes})")
        return VoteAttempt(
            initiator=initiator, suspect=suspect, votes=votes, passed=passed
        )
