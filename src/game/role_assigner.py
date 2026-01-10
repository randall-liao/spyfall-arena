import random
from typing import Dict, List, Tuple

from loguru import logger

from game.game_state import Role


class RoleAssigner:
    """Assigns spy/civilian roles per PRD Section 2 (Role Assignment System).

    Uses seeded random for reproducibility (PRD Section 9 success criterion).
    """

    def __init__(self, random_seed: int):
        self._random = random.Random(random_seed)

    def assign_roles(
        self, player_nicknames: List[str], locations: List[str]
    ) -> Tuple[Dict[str, Role], str]:
        """Assign one spy and the rest as civilians, selecting a location."""
        if not player_nicknames:
            raise ValueError("Player list cannot be empty.")
        if not locations:
            raise ValueError("Location list cannot be empty.")

        selected_location = self._random.choice(locations)
        spy_nickname = self._random.choice(player_nicknames)

        role_assignments: Dict[str, Role] = {}
        for nickname in player_nicknames:
            if nickname == spy_nickname:
                role_assignments[nickname] = Role(is_spy=True, location=None)
            else:
                role_assignments[nickname] = Role(
                    is_spy=False, location=selected_location
                )

        logger.info(
            f"Assigned roles. Spy: {spy_nickname}, Location: {selected_location}"
        )
        return role_assignments, selected_location
