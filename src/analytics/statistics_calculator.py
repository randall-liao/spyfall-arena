import statistics
from collections import Counter
from typing import Dict, List, Optional

from analytics.models import ModelData, ModelStatistics, RoundRecord


class StatisticsCalculator:
    """Calculates performance statistics from aggregated model data."""

    def calculate_all_statistics(
        self, model_data_map: Dict[str, ModelData]
    ) -> Dict[str, ModelStatistics]:
        """Calculate statistics for all models."""
        stats_map = {}
        for model_name, data in model_data_map.items():
            stats_map[model_name] = self.calculate_model_statistics(data)
        return stats_map

    def calculate_model_statistics(self, data: ModelData) -> ModelStatistics:
        """Calculate statistics for a single model."""
        stats = ModelStatistics(model_name=data.model_name)

        # Basic counts
        stats.total_games = data.total_games
        stats.total_rounds = data.total_rounds
        stats.spy_rounds_count = len(data.spy_rounds)
        stats.civilian_rounds_count = len(data.civilian_rounds)

        # Win Rates
        if stats.total_games > 0:
            stats.overall_win_rate = data.games_won / stats.total_games
        else:
            stats.overall_win_rate = 0.0

        # Spy Win Rate
        spy_wins = 0
        spy_rounds_survived = 0
        successful_spy_guesses = 0
        total_spy_guesses = 0

        for round_rec in data.spy_rounds:
            # Win check
            if self._did_spy_win(round_rec):
                spy_wins += 1

            # Survival check
            if self._did_spy_survive(round_rec):
                spy_rounds_survived += 1

            # Spy Guess check
            if round_rec.spy_guess:
                total_spy_guesses += 1
                if round_rec.spy_guess.correct:
                    successful_spy_guesses += 1

        if stats.spy_rounds_count > 0:
            stats.spy_win_rate = spy_wins / stats.spy_rounds_count
            stats.spy_survival_rate = spy_rounds_survived / stats.spy_rounds_count
            stats.average_spy_score = sum(data.spy_scores) / stats.spy_rounds_count
        else:
            stats.spy_win_rate = 0.0
            stats.spy_survival_rate = 0.0
            stats.average_spy_score = 0.0

        stats.successful_spy_guesses = successful_spy_guesses
        stats.total_spy_guesses = total_spy_guesses
        if total_spy_guesses > 0:
            stats.spy_guess_accuracy = successful_spy_guesses / total_spy_guesses
        else:
            stats.spy_guess_accuracy = 0.0

        # Civilian Win Rate
        civilian_wins = 0

        for round_rec in data.civilian_rounds:
            # Civilians win if Spy did NOT win
            if not self._did_spy_win(round_rec):
                civilian_wins += 1

        if stats.civilian_rounds_count > 0:
            stats.civilian_win_rate = civilian_wins / stats.civilian_rounds_count
            stats.civilian_success_rate = stats.civilian_win_rate  # Same metric
            stats.average_civilian_score = (
                sum(data.civilian_scores) / stats.civilian_rounds_count
            )
        else:
            stats.civilian_win_rate = 0.0
            stats.civilian_success_rate = 0.0
            stats.average_civilian_score = 0.0

        # Scores
        if data.all_scores:
            stats.average_score_per_round = statistics.mean(data.all_scores)
            stats.min_score = min(data.all_scores)
            stats.max_score = max(data.all_scores)
            if len(data.all_scores) > 1:
                stats.score_std_dev = statistics.stdev(data.all_scores)
            else:
                stats.score_std_dev = 0.0

            stats.score_distribution = dict(Counter(data.all_scores))

            # Average score per game
            if stats.total_games > 0:
                stats.average_score_per_game = sum(data.all_scores) / stats.total_games

        # Voting Statistics
        total_votes_cast = len(data.votes_cast)
        correct_votes = sum(1 for v in data.votes_cast if v.correct)

        if total_votes_cast > 0:
            stats.voting_accuracy = correct_votes / total_votes_cast
            stats.yes_vote_percentage = (
                sum(1 for v in data.votes_cast if v.vote) / total_votes_cast
            )
        else:
            stats.voting_accuracy = 0.0
            stats.yes_vote_percentage = 0.0

        stats.correct_spy_votes = (
            correct_votes  # Assuming all votes are about finding spy?
        )
        # Actually correct_votes includes NO votes on Civilians.
        # Requirement 6.3: "track how often the model correctly voted for the actual spy when playing as civilian"
        # This implies "Yes" vote on Spy.
        # My `VoteRecord.correct` logic:
        # If suspect is spy, Vote=True -> Correct.
        # If suspect is civilian, Vote=False -> Correct.
        # Req 6.3 is specific about "correctly voted for the actual spy".
        # I'll calculate `correct_spy_votes` as votes where suspect was spy AND vote was Yes.

        correct_spy_votes = 0
        total_civilian_votes = 0

        for vote_rec in data.votes_cast:
            # We need to know if I was civilian when I voted?
            # Or just check if the vote was "Yes" on a Spy.
            # `VoteRecord` has `correct`. If `correct` is True AND `vote` is True, then suspect must be Spy.
            # (Because if suspect was Civilian, correct vote is False).
            if vote_rec.vote and vote_rec.correct:
                correct_spy_votes += 1

            # Check if I was civilian?
            # `VoteRecord` has game_id and round_number. I can lookup role but it's expensive.
            # But `votes_cast` contains all votes.
            # Usually "correct spy votes" implies identifying the spy.
            pass

        stats.correct_spy_votes = correct_spy_votes
        stats.total_civilian_votes = (
            total_votes_cast  # Approximate? Or iterate rounds to be precise?
        )
        # Let's count votes cast while being civilian.
        # We can iterate civilian_rounds and sum votes cast by me.

        votes_as_civilian = 0
        for round_rec in data.civilian_rounds:
            for vote_attempt in round_rec.vote_attempts:
                if data.model_name in vote_attempt.votes:
                    votes_as_civilian += 1
        stats.total_civilian_votes = votes_as_civilian

        # Votes Initiated
        votes_initiated = 0
        successful_initiations = 0
        all_rounds = data.spy_rounds + data.civilian_rounds
        for round_rec in all_rounds:
            for vote_attempt in round_rec.vote_attempts:
                if vote_attempt.initiator == data.model_name:
                    votes_initiated += 1
                    if vote_attempt.passed:
                        successful_initiations += 1

        stats.votes_initiated = votes_initiated
        if votes_initiated > 0:
            stats.vote_initiation_success_rate = (
                successful_initiations / votes_initiated
            )
        else:
            stats.vote_initiation_success_rate = 0.0

        stats.times_suspected = len(data.votes_received)

        # Turn Engagement
        stats.questions_asked = len(data.turns_as_asker)
        stats.questions_answered = len(data.turns_as_answerer)
        if stats.total_rounds > 0:
            # Total turns involved
            total_turns = stats.questions_asked + stats.questions_answered
            # Note: If a model asks and answers in same turn (impossible?), it counts twice.
            # Actually `TurnRecord` has distinct asker and answerer.
            stats.average_turns_per_round = total_turns / stats.total_rounds
        else:
            stats.average_turns_per_round = 0.0

        # Round Endings
        for round_rec in all_rounds:
            if round_rec.ending_condition == "vote":
                stats.rounds_ended_by_vote += 1
            elif round_rec.ending_condition == "spy_guess":
                stats.rounds_ended_by_spy_guess += 1
            elif round_rec.ending_condition == "timeout":
                stats.rounds_ended_by_timeout += 1

        return stats

    def _did_spy_win(self, round_rec: RoundRecord) -> bool:
        """Determine if the spy won the round."""
        if round_rec.ending_condition == "spy_guess":
            return round_rec.spy_guess.correct if round_rec.spy_guess else False
        elif round_rec.ending_condition == "vote":
            # Find the passed vote
            passed_vote = next(
                (v for v in reversed(round_rec.vote_attempts) if v.passed), None
            )
            if passed_vote:
                # Spy wins if the person voted out (suspect) is NOT the spy
                return passed_vote.suspect != round_rec.spy
            else:
                # Should not happen if ending_condition is vote
                return False
        elif round_rec.ending_condition == "timeout":
            # Assuming Spy wins on timeout (Civilians failed to identify)
            return True
        else:
            return False

    def _did_spy_survive(self, round_rec: RoundRecord) -> bool:
        """Determine if the spy survived the round (was not voted out)."""
        if round_rec.ending_condition == "vote":
            passed_vote = next(
                (v for v in reversed(round_rec.vote_attempts) if v.passed), None
            )
            if passed_vote:
                # Spy died if they were the suspect
                return passed_vote.suspect != round_rec.spy
            else:
                return True  # No vote passed, spy survived
        else:
            # In other endings (spy_guess, timeout), spy is not voted out
            return True
