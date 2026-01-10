import random
from typing import Dict, List, Tuple

from loguru import logger

from game.game_state import Role


class RoleAssigner:
    """
    Manages role distribution and location selection for a Spyfall round.

    Implements 'Req 2: Role Assignment System', ensuring:
    - Exactly one spy per game.
    - Deterministic assignments via a random seed (Req 2 Acceptance Criteria).
    """

    def __init__(self, random_seed: int):
        self._random = random.Random(random_seed)

    def assign_roles(
        self, player_nicknames: List[str], locations: List[str]
    ) -> Tuple[Dict[str, Role], str]:
        """
        Assigns roles to players and selects a location.

        Algorithm:
        1. Selects a random location from the provided list.
        2. Selects a random player to be the Spy.
        3. Assigns 'Spy' role (location=None) to the selected player.
        4. Assigns 'Civilian' role (location=selected_location) to all others.

        Returns:
            A tuple of (Role Mapping, Selected Location).
        """
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
