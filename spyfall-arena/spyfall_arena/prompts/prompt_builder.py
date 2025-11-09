from pathlib import Path
from typing import List

from spyfall_arena.config.config_schema import GameConfig
from spyfall_arena.game.game_state import Role, Turn


class PromptBuilder:
    """Constructs prompts for the LLM agents based on templates and game state."""

    def __init__(self, config: GameConfig):
        self.config = config
        self.system_prompt = ""
        self.civilian_template = ""
        self.spy_template = ""

    def load_templates(self):
        """Loads the prompt templates from the files specified in the config."""
        try:
            self.system_prompt = self._read_template(
                Path(self.config.prompts.system_prompt_template)
            )
            self.civilian_template = self._read_template(
                Path(self.config.prompts.civilian_role_template)
            )
            self.spy_template = self._read_template(
                Path(self.config.prompts.spy_role_template)
            )
        except FileNotFoundError as e:
            raise RuntimeError(f"Could not load prompt templates: {e}") from e

    @staticmethod
    def _read_template(filepath: Path) -> str:
        """Reads a template file and returns its content."""
        return filepath.read_text()

    def build_system_prompt(self) -> str:
        """Builds the system prompt."""
        return self.system_prompt

    def build_role_prompt(self, role: Role) -> str:
        """Builds the role-specific prompt."""
        if role.is_spy:
            return self.spy_template
        else:
            return self.civilian_template.replace("{{ location }}", role.location or "")

    @staticmethod
    def _format_conversation_history(history: List[Turn]) -> str:
        """Formats the conversation history into a readable string."""
        if not history:
            return "The conversation has not started yet."

        formatted_history = "\n".join(
            f"Turn {turn.turn_number}: {turn.asker_nickname} asked {turn.answerer_nickname}: '{turn.question}'\n"
            f"  {turn.answerer_nickname} answered: '{turn.answer}'"
            for turn in history
        )
        return f"Conversation History:\n{formatted_history}"

    def build_question_prompt(
        self,
        conversation_history: List[Turn],
        valid_targets: List[str],
    ) -> str:
        """Builds the prompt for asking a question."""
        history_str = self._format_conversation_history(conversation_history)
        targets_str = ", ".join(valid_targets)
        return (
            f"{history_str}\n\n"
            f"It is your turn to ask a question.\n"
            f"Choose one of the following players to question: {targets_str}.\n"
            f"Your response must be in the following JSON format:\n"
            f'{{"target_nickname": "player_name", "question": "your_question_here"}}'
        )

    def build_answer_prompt(
        self,
        conversation_history: List[Turn],
        question: str,
    ) -> str:
        """Builds the prompt for answering a question."""
        history_str = self._format_conversation_history(conversation_history)
        return (
            f"{history_str}\n\n"
            f"You have been asked the following question: '{question}'\n"
            f"Your response must be in the following JSON format:\n"
            f'{{"answer": "your_answer_here"}}'
        )

    def build_vote_initiation_prompt(
        self, conversation_history: List[Turn], can_vote: bool
    ) -> str:
        """Builds the prompt asking if a player wants to initiate a vote."""
        history_str = self._format_conversation_history(conversation_history)
        if not can_vote:
            return (
                f"{history_str}\n\n"
                f"You have already initiated a vote this round and cannot do so again.\n"
                f"Your response must be in the following JSON format:\n"
                f'{{"initiate_vote": false, "suspect_nickname": null}}'
            )

        return (
            f"{history_str}\n\n"
            f"Do you want to initiate a vote to accuse someone of being the spy? "
            f"If so, provide the nickname of the player you suspect.\n"
            f"Your response must be in the following JSON format:\n"
            f'{{"initiate_vote": true_or_false, "suspect_nickname": "player_name_or_null"}}'
        )

    def build_vote_decision_prompt(
        self, conversation_history: List[Turn], suspect: str
    ) -> str:
        """Builds the prompt for voting on a suspect."""
        history_str = self._format_conversation_history(conversation_history)
        return (
            f"{history_str}\n\n"
            f"{suspect} has been accused of being the spy. Do you agree?\n"
            f"Your response must be in the following JSON format:\n"
            f'{{"vote_yes": true_or_false}}'
        )

    def build_spy_guess_prompt(
        self, conversation_history: List[Turn], available_locations: List[str]
    ) -> str:
        """Builds the prompt for the spy to guess the location."""
        history_str = self._format_conversation_history(conversation_history)
        locations_str = ", ".join(available_locations)
        return (
            f"{history_str}\n\n"
            f"As the spy, you can choose to guess the location. "
            f"If you are correct, you win. If you are wrong, you lose.\n"
            f"Do you want to guess the location now? If so, choose from the list of available locations.\n"
            f"Available locations: {locations_str}\n"
            f"Your response must be in the following JSON format:\n"
            f'{{"make_guess": true_or_false, "location_guess": "location_name_or_null"}}'
        )
