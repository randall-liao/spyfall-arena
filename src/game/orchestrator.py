import uuid
from typing import List

from config.config_schema import GameConfig
from game.game_state import (GamePhase, GameState, RoundPhase,
                                           RoundState)
from game.role_assigner import RoleAssigner
from game.scoring_engine import ScoringEngine
from game.spy_guess_manager import SpyGuessManager
from game.turn_manager import TurnManager
from game.voting_manager import VotingManager
from llm.llm_client_factory import LLMClientFactory
from prompts.prompt_builder import PromptBuilder


class GameOrchestrator:
    """Orchestrates the execution of a complete game of Spyfall."""

    def __init__(self, config: GameConfig):
        self.config = config
        self.llm_factory = LLMClientFactory()
        self.prompt_builder = PromptBuilder(config)
        self.prompt_builder.load_templates()
        self.role_assigner = RoleAssigner(config.game.random_seed or 42)
        self.turn_manager = TurnManager(self.llm_factory, self.prompt_builder, config)
        self.voting_manager = VotingManager(self.llm_factory, self.prompt_builder, config)
        self.spy_guess_manager = SpyGuessManager(
            self.llm_factory, self.prompt_builder, config
        )
        self.scoring_engine = ScoringEngine()

    def run_game(self) -> GameState:
        """Runs a complete game of Spyfall from start to finish."""
        game_state = GameState(
            game_id=f"game_{uuid.uuid4().hex[:8]}",
            phase=GamePhase.INITIALIZING,
        )
        game_state.transition_to(GamePhase.IN_PROGRESS)

        player_nicknames = [p.nickname for p in self.config.players]
        game_state.player_scores = {nickname: 0 for nickname in player_nicknames}

        for i in range(self.config.game.num_rounds):
            round_state = self.run_round(
                i + 1, player_nicknames, list(self.config.locations)
            )
            game_state.rounds_data.append(round_state)

            # Update total scores
            for nickname, score in round_state.round_scores.items():
                game_state.player_scores[nickname] += score

        game_state.transition_to(GamePhase.COMPLETED)
        return game_state

    def run_round(
        self, round_number: int, player_nicknames: List[str], locations: List[str]
    ) -> RoundState:
        """Runs a single round of Spyfall."""
        roles, location = self.role_assigner.assign_roles(player_nicknames, locations)
        spy_nickname = next(p for p, r in roles.items() if r.is_spy)

        round_state = RoundState(
            round_number=round_number,
            phase=RoundPhase.ROLE_ASSIGNMENT,
            location=location,
            spy_nickname=spy_nickname,
            role_assignments=roles,
        )
        round_state.transition_to(RoundPhase.QUESTIONING)

        current_asker = player_nicknames[0]
        previous_asker = None

        for turn_num in range(self.config.game.max_turns_per_round):
            try:
                # Check for spy guess
                if round_state.spy_nickname == current_asker:
                    spy_guess = self.spy_guess_manager.check_spy_guess(
                        spy_nickname,
                        round_state.conversation_history,
                        locations,
                        location,
                    )
                    if spy_guess:
                        round_state.spy_guess = spy_guess
                        round_state.ending_condition = "spy_guess"
                        break

                # Check for vote initiation
                suspect = self.voting_manager.check_for_vote_initiation(
                    current_asker,
                    roles,
                    round_state.conversation_history,
                    round_state.players_who_voted,
                )
                if suspect:
                    vote_attempt = self.voting_manager.conduct_vote(
                        current_asker, suspect, roles, round_state.conversation_history
                    )
                    round_state.votes.append(vote_attempt)
                    round_state.players_who_voted.add(current_asker)
                    if vote_attempt.passed:
                        round_state.ending_condition = "vote"
                        break

                # Execute a regular turn
                turn = self.turn_manager.execute_turn(
                    current_asker,
                    roles,
                    round_state.conversation_history,
                    player_nicknames,
                    previous_asker,
                )
                round_state.conversation_history.append(turn)

                previous_asker = current_asker
                current_asker = self.turn_manager.get_next_asker(turn.answerer_nickname)
            except (ValueError, ConnectionError) as e:
                # In a real application, you would log this error
                print(f"Error during turn {turn_num + 1}: {e}")
                # For simplicity, we'll just end the round on any error.
                round_state.ending_condition = "error"
                break

        if not round_state.ending_condition:
            round_state.ending_condition = "turn_limit_reached"

        round_state.transition_to(RoundPhase.SCORING)
        round_state.round_scores = self.scoring_engine.calculate_round_scores(
            round_state
        )
        round_state.transition_to(RoundPhase.COMPLETED)

        return round_state
