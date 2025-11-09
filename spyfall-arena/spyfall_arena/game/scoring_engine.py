from typing import Dict

from spyfall_arena.game.game_state import RoundState, VoteAttempt


class ScoringEngine:
    """Calculates player scores based on the outcome of a Spyfall round."""

    def calculate_round_scores(self, round_state: RoundState) -> Dict[str, int]:
        """
        Calculates the scores for all players for a completed round.

        Args:
            round_state: The state of the round that has just finished.

        Returns:
            A dictionary mapping player nicknames to the points they earned in the round.
        """
        scores: Dict[str, int] = {
            nickname: 0 for nickname in round_state.role_assignments
        }
        spy_nickname = round_state.spy_nickname
        civilians = [p for p in round_state.role_assignments if p != spy_nickname]

        successful_vote: VoteAttempt | None = None
        for vote in round_state.votes:
            if vote.passed:
                successful_vote = vote
                break

        if round_state.spy_guess and round_state.spy_guess.correct:
            # Spy guessed the location correctly
            scores[spy_nickname] = 4
        elif successful_vote:
            if successful_vote.suspect == spy_nickname:
                # Spy was correctly identified
                for civilian in civilians:
                    scores[civilian] = 1
                if successful_vote.initiator in civilians:
                    scores[successful_vote.initiator] = 2  # Initiator gets a bonus
            else:
                # Civilians voted out the wrong person
                scores[spy_nickname] = 4
        else:
            # Spy was not caught, and didn't guess the location
            scores[spy_nickname] = 2

        return scores
