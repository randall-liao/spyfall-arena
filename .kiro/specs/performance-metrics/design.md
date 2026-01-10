# Design Document

## Overview

The MetricsCalculator component computes performance metrics for Spyfall Arena games. It calculates round-level statistics (winner, vote accuracy, response lengths) and game-level aggregates (win counts, overall winner).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GameLogger                               │
│                         │                                    │
│                         ▼                                    │
│                 MetricsCalculator                            │
│                    │         │                               │
│                    ▼         ▼                               │
│            RoundMetrics   GameMetrics                        │
│                    │         │                               │
│                    └────┬────┘                               │
│                         ▼                                    │
│                  JSON Log Output                             │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Data Models

**Module**: `src/game_logging/metrics_calculator.py`

```python
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict

@dataclass
class RoundMetrics:
    """Metrics computed for a single round."""
    winner_side: str  # "spy" or "civilians"
    ending_condition: str
    total_turns: int
    vote_attempts: int
    spy_caught: bool
    spy_guessed_correctly: Optional[bool]
    vote_accuracy: Optional[float]  # 0.0-1.0, None if no votes
    avg_question_length: float
    avg_answer_length: float

@dataclass
class GameMetrics:
    """Aggregate metrics across all rounds in a game."""
    total_rounds: int
    spy_wins: int
    civilian_wins: int
    avg_turns_per_round: float
    total_vote_attempts: int
    overall_winner: str  # nickname of player with most points
```

### 2. MetricsCalculator Class

```python
class MetricsCalculator:
    """Calculates performance metrics for rounds and games."""
    
    def calculate_round_metrics(self, round_state: RoundState) -> RoundMetrics:
        """
        Calculates metrics for a completed round.
        
        Winner determination:
        - "civilians" if spy was caught (successful indictment of spy)
        - "spy" if spy avoided detection or guessed location correctly
        
        Vote accuracy:
        - Only calculated if a successful vote occurred
        - = civilians who voted yes on spy / total civilians
        - None if no successful vote
        
        Response statistics:
        - total_turns = len(conversation_history)
        - avg_question_length = mean(len(turn.question) for turn in turns)
        - avg_answer_length = mean(len(turn.answer) for turn in turns)
        - Returns 0.0 for averages if no turns
        """
        
    def calculate_game_metrics(
        self, 
        game_state: GameState,
        round_metrics: List[RoundMetrics]
    ) -> GameMetrics:
        """
        Calculates aggregate metrics across all rounds.
        
        - spy_wins = count of rounds where winner_side == "spy"
        - civilian_wins = count of rounds where winner_side == "civilians"
        - avg_turns_per_round = sum(total_turns) / total_rounds
        - overall_winner = player with highest score (alphabetically first if tied)
        """
```

### 3. Updated GameLogger

```python
class GameLogger:
    def __init__(self, config: GameConfig):
        self.config = config
        self.log_dir = Path(config.logging.output_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_calculator = MetricsCalculator()
    
    def _build_log_structure(self, game_state: GameState) -> dict:
        """Builds log structure including metrics."""
        round_metrics = [
            self.metrics_calculator.calculate_round_metrics(r)
            for r in game_state.rounds_data
        ]
        
        game_metrics = self.metrics_calculator.calculate_game_metrics(
            game_state, round_metrics
        )
        
        return {
            "game_id": game_state.game_id,
            "timestamp": datetime.now().isoformat(),
            "config_snapshot": self.config.model_dump(),
            "players": [p.model_dump() for p in self.config.players],
            "rounds": [
                self._serialize_round_with_metrics(r, m) 
                for r, m in zip(game_state.rounds_data, round_metrics)
            ],
            "final_scores": game_state.player_scores,
            "game_metrics": asdict(game_metrics),
            "status": game_state.phase.value,
        }
    
    def _serialize_round_with_metrics(
        self, round_state: RoundState, metrics: RoundMetrics
    ) -> dict:
        """Serializes round with embedded metrics."""
        base = self._serialize_round(round_state)
        base["metrics"] = asdict(metrics)
        return base
```

## Data Models

### RoundMetrics Schema

```json
{
  "winner_side": "civilians",
  "ending_condition": "successful_indictment",
  "total_turns": 8,
  "vote_attempts": 2,
  "spy_caught": true,
  "spy_guessed_correctly": null,
  "vote_accuracy": 0.75,
  "avg_question_length": 45.2,
  "avg_answer_length": 32.8
}
```

### GameMetrics Schema

```json
{
  "total_rounds": 3,
  "spy_wins": 1,
  "civilian_wins": 2,
  "avg_turns_per_round": 7.3,
  "total_vote_attempts": 5,
  "overall_winner": "Alice"
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system.*

### Property 1: Round Outcome Determination

*For any* completed round state, the MetricsCalculator SHALL correctly determine:
- `winner_side` as "spy" if spy was not caught and didn't guess wrong, or "civilians" if spy was caught
- `spy_caught` as true if and only if a successful vote indicted the actual spy

**Validates: Requirements 1.1, 1.3**

### Property 2: Vote Accuracy Calculation

*For any* round with at least one successful vote attempt against the spy, the vote accuracy SHALL equal the number of civilians who voted "yes" divided by the total number of civilians, expressed as a value between 0.0 and 1.0.

**Validates: Requirements 1.2**

### Property 3: Response Statistics Calculation

*For any* round with at least one turn:
- `total_turns` SHALL equal the length of the conversation history
- `avg_question_length` SHALL equal the mean character count of all questions
- `avg_answer_length` SHALL equal the mean character count of all answers

**Validates: Requirements 1.4, 1.5**

### Property 4: Aggregate Metrics Calculation

*For any* completed game with N rounds:
- `spy_wins + civilian_wins` SHALL equal N
- `overall_winner` SHALL be the player with the highest score in `final_scores`
- `avg_turns_per_round` SHALL equal the sum of all round turn counts divided by N

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

## Testing Strategy

### TDD Approach

Tests are written BEFORE implementation:
1. Write failing tests for each method
2. Implement minimal code to pass tests
3. Refactor while keeping tests green

### Test Files

- `tests/game_logging/test_metrics_calculator.py` - Unit tests
- `tests/game_logging/test_metrics_properties.py` - Property-based tests

### Dependencies

Add to `pyproject.toml` (dev dependencies):
```toml
hypothesis = "^6.0.0"
```
