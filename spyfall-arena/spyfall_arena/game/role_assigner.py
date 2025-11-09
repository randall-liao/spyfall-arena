import random
from typing import Dict, List, Tuple

from spyfall_arena.game.game_state import Role


class RoleAssigner:
    """Assigns roles (spy and civilian) to players for a round of Spyfall."""

    def __init__(self, random_seed: int):
        """
        Initializes the RoleAssigner with a specific random seed for reproducibility.

        Args:
            random_seed: The seed for the random number generator.
        """
        self._random = random.Random(random_seed)

    def assign_roles(
        self, player_nicknames: List[str], locations: List[str]
    ) -> Tuple[Dict[str, Role], str]:
        """
        Randomly assigns one player as the spy and the rest as civilians.
        A random location is chosen for the round.

        Args:
            player_nicknames: A list of nicknames for the players in the round.
            locations: A list of possible locations for the round.

        Returns:
            A tuple containing:
            - A dictionary mapping player nicknames to their assigned Role.
            - The selected location for the round.
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

        return role_assignments, selected_location
