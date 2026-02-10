from typing import Dict, List, Optional

from loguru import logger

from analytics.models import (GameRecord, ModelData, PlayerConfig, RoundRecord,
                              VoteRecord)


class DataAggregator:
    """Aggregates game data by model."""

    def aggregate_by_model(self, games: List[GameRecord]) -> Dict[str, ModelData]:
        """Group all game data by model_name."""
        model_data_map: Dict[str, ModelData] = {}

        for game in games:
            # Map nickname to model name for this game
            # Assuming nicknames are unique per game as per config schema
            # We strip whitespace to be robust against log inconsistencies
            nickname_to_model: Dict[str, str] = {}
            for player in game.players:
                clean_nick = player.nickname.strip()
                nickname_to_model[clean_nick] = player.model_name
                if player.model_name not in model_data_map:
                    model_data_map[player.model_name] = ModelData(
                        model_name=player.model_name
                    )

            # Increment total games for each participating model
            for model_name in set(nickname_to_model.values()):
                model_data_map[model_name].total_games += 1

            for round_rec in game.rounds:
                self._process_round(
                    round_rec, game.game_id, nickname_to_model, model_data_map
                )

            # Determine game winners based on final scores
            if game.final_scores:
                max_score = max(game.final_scores.values())
                winners = [
                    nick
                    for nick, score in game.final_scores.items()
                    if score == max_score
                ]

                # Identify winning models (use set to avoid double counting if multiple players of same model win)
                winning_models = set()
                for winner_nick in winners:
                    if winner_nick in nickname_to_model:
                        winning_models.add(nickname_to_model[winner_nick])

                for winner_model in winning_models:
                    model_data_map[winner_model].games_won += 1

        return model_data_map

    def _process_round(
        self,
        round_rec: RoundRecord,
        game_id: str,
        nickname_to_model: Dict[str, str],
        model_data_map: Dict[str, ModelData],
    ):
        """Process a single round and update model data."""

        # Determine spy
        spy_nickname = round_rec.spy

        # Iterate over all players in this round (from role assignments)
        for nickname, role_assignment in round_rec.role_assignments.items():
            clean_nick = nickname.strip()
            if clean_nick not in nickname_to_model:
                continue  # Should not happen if data is consistent

            model_name = nickname_to_model[clean_nick]
            model_data = model_data_map[model_name]

            model_data.total_rounds += 1

            if role_assignment.is_spy:
                model_data.spy_rounds.append(round_rec)
            else:
                model_data.civilian_rounds.append(round_rec)

            # Collect score
            score = round_rec.round_scores.get(nickname, 0)
            model_data.all_scores.append(score)

        # Process Turns
        for turn in round_rec.turns:
            clean_asker = turn.asker_nickname.strip()
            if clean_asker in nickname_to_model:
                asker_model = nickname_to_model[clean_asker]
                model_data_map[asker_model].turns_as_asker.append(turn)

            clean_answerer = turn.answerer_nickname.strip()
            if clean_answerer in nickname_to_model:
                answerer_model = nickname_to_model[clean_answerer]
                model_data_map[answerer_model].turns_as_answerer.append(turn)

        # Process Votes
        for vote_attempt in round_rec.vote_attempts:
            voter_nicknames = vote_attempt.votes.keys()
            for voter_nick in voter_nicknames:
                clean_voter = voter_nick.strip()
                if clean_voter not in nickname_to_model:
                    continue

                voter_model = nickname_to_model[clean_voter]
                vote_val = vote_attempt.votes[voter_nick]

                # Determine correctness
                # If suspect was spy, YES is correct, NO is incorrect.
                # If suspect was civilian, YES is incorrect, NO is correct.
                suspect_is_spy = vote_attempt.suspect == spy_nickname

                # Wait, if I am the suspect, does my vote count towards correctness?
                # Usually suspect cannot vote or their vote doesn't count in Spyfall?
                # But in the data structure, they might have a vote recorded.
                # Assuming standard rules: usually you don't vote on yourself or it doesn't matter.
                # But let's define correctness simply: matching the truth.

                is_correct = False
                if suspect_is_spy:
                    is_correct = vote_val  # True (Yes) is correct
                else:
                    is_correct = not vote_val  # False (No) is correct

                vote_record = VoteRecord(
                    game_id=game_id,
                    round_number=round_rec.round_number,
                    voter=voter_nick,
                    suspect=vote_attempt.suspect,
                    vote=vote_val,
                    correct=is_correct,
                )

                model_data_map[voter_model].votes_cast.append(vote_record)

                # Also track received votes (being suspected)
                clean_suspect = vote_attempt.suspect.strip()
                if clean_suspect in nickname_to_model:
                    suspect_model = nickname_to_model[clean_suspect]
                    # We are iterating per voter, so this would add duplicates if we add it here for every voter.
                    # We should add "votes received" maybe once per vote attempt?
                    # But `votes_received` is List[VoteRecord].
                    # If `VoteRecord` represents a single vote cast by someone, then `votes_received` for a model
                    # should be the list of votes cast AGAINST them.

                    if clean_suspect == clean_voter:
                        # Self-vote?
                        pass

                    if nickname_to_model.get(clean_suspect) == suspect_model:
                        # This vote is against suspect_model
                        # We can store the same VoteRecord object in the suspect's received list
                        model_data_map[suspect_model].votes_received.append(vote_record)
