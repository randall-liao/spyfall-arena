
from dataclasses import dataclass
from typing import Optional
from game.game_state import RoundState, GameState

@dataclass
class RoundMetrics:
    """Per-round metrics per PRD Section 6 (Evaluation and Metrics MVP)."""
    winner_side: str  # "spy" or "civilians"
    spy_caught: bool
    spy_guessed_correctly: bool
    total_turns: int
    vote_accuracy: Optional[float]  # None if no vote successfully concluded
    avg_question_length: float
    avg_answer_length: float

@dataclass
class GameMetrics:
    """Aggregate game metrics for multi-round analysis."""
    spy_wins: int
    civilian_wins: int
    avg_turns_per_round: float
    overall_winner: str

def calculate_round_metrics(round_state: RoundState) -> RoundMetrics:
    """Compute win condition, vote accuracy, and response stats for a round."""
    # Initialize outcome flags
    winner_side = "spy"
    spy_caught = False
    spy_guessed_correctly = False

    # Determine winner and outcome details
    if round_state.spy_guess and round_state.spy_guess.correct:
        # Spy guessed location correctly -> Spy wins
        spy_guessed_correctly = True
        winner_side = "spy"
    else:
        # Check for successful vote
        successful_vote = next((v for v in round_state.votes if v.passed), None)
        if successful_vote:
            if successful_vote.suspect == round_state.spy_nickname:
                # Civilians caught spy -> Civilians win
                winner_side = "civilians"
                spy_caught = True
            else:
                # Civilians voted out wrong person -> Spy wins
                winner_side = "spy"
        else:
            # No successful vote and no correct guess (time limit usually) -> Spy wins
            winner_side = "spy"

    # Calculate vote accuracy
    vote_accuracy: Optional[float] = None
    successful_vote = next((v for v in round_state.votes if v.passed), None)
    
    if successful_vote:
        # Identify civilians
        civilians = [p for p in round_state.role_assignments if p != round_state.spy_nickname]
        total_civilians = len(civilians)
        
        if total_civilians > 0:
            # Count civilians who voted YES
            civilians_voted_yes = 0
            for civ in civilians:
                if successful_vote.votes.get(civ, False):
                    civilians_voted_yes += 1
            vote_accuracy = civilians_voted_yes / total_civilians if total_civilians > 0 else 0.0

    # Calculate response statistics
    total_turns = len(round_state.conversation_history)
    avg_question_length = 0.0
    avg_answer_length = 0.0
    
    if total_turns > 0:
        total_q_len = sum(len(t.question) for t in round_state.conversation_history)
        total_a_len = sum(len(t.answer) for t in round_state.conversation_history)
        avg_question_length = total_q_len / total_turns
        avg_answer_length = total_a_len / total_turns

    return RoundMetrics(
        winner_side=winner_side,
        spy_caught=spy_caught,
        spy_guessed_correctly=spy_guessed_correctly,
        total_turns=total_turns,
        vote_accuracy=vote_accuracy,
        avg_question_length=avg_question_length,
        avg_answer_length=avg_answer_length
    )

def calculate_game_metrics(game_state: GameState) -> GameMetrics:
    """Aggregate round metrics into overall game statistics."""
    spy_wins = 0
    civilian_wins = 0
    total_turns = 0
    num_rounds = len(game_state.rounds_data)
    
    for round_state in game_state.rounds_data:
        # Reuse calculate_round_metrics to determine the winner based on state
        round_metrics = calculate_round_metrics(round_state)
        
        if round_metrics.winner_side == "spy":
            spy_wins += 1
        elif round_metrics.winner_side == "civilians":
            civilian_wins += 1
            
        total_turns += round_metrics.total_turns

    avg_turns_per_round = total_turns / num_rounds if num_rounds > 0 else 0.0

    # Determine overall winner
    overall_winner = ""
    if game_state.player_scores:
        # Sort by score (descending), then name (ascending)
        sorted_players = sorted(
            game_state.player_scores.items(),
            key=lambda item: (-item[1], item[0])
        )
        if sorted_players:
            overall_winner = sorted_players[0][0]

    return GameMetrics(
        spy_wins=spy_wins,
        civilian_wins=civilian_wins,
        avg_turns_per_round=avg_turns_per_round,
        overall_winner=overall_winner
    )
