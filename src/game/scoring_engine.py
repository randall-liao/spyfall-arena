from typing import Dict

from loguru import logger

from game.game_state import RoundState, VoteAttempt


class ScoringEngine:
    """Calculates round scores per game-rules.md (Scoring and who wins).

    - Spy: 4 pts for correct location guess or civilian misidentification
    - Spy: 2 pts if not caught and no correct guess
    - Civilians: 1 pt each for catching spy, 2 pts for vote initiator
    """

    def calculate_round_scores(self, round_state: RoundState) -> Dict[str, int]:
        """Return nickname-to-points mapping for the completed round."""
        logger.debug(f"Calculating scores for Round {round_state.round_number}")
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

        logger.debug(f"Round scores: {scores}")
        return scores
