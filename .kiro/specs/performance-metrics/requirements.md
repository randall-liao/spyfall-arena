# Requirements Document

## Introduction

This spec implements performance metrics calculation for Spyfall Arena Phase One. The MetricsCalculator component computes round-level and game-level statistics that enable researchers to analyze model performance.

## Glossary

- **Metrics_Calculator**: Component responsible for computing performance metrics from game and round data
- **Round_Metrics**: Statistics computed for a single round of gameplay
- **Game_Metrics**: Aggregate statistics computed across all rounds in a game
- **Vote_Accuracy**: Percentage of civilians who voted correctly to identify the spy

## Requirements

### Requirement 1: Round Metrics Calculation

**User Story:** As an AI researcher, I want automated metrics computed for each round, so that I can quickly evaluate model performance without manual analysis.

#### Acceptance Criteria

1. WHEN a round completes THEN the Metrics_Calculator SHALL compute which side won (civilian or spy)
2. WHEN a round completes with a vote THEN the Metrics_Calculator SHALL calculate vote accuracy as the percentage of civilians who voted correctly
3. WHEN a round completes THEN the Metrics_Calculator SHALL determine if the spy successfully avoided detection or correctly guessed the location
4. WHEN a round completes THEN the Metrics_Calculator SHALL compute response statistics including total turn count
5. WHEN a round completes THEN the Metrics_Calculator SHALL compute average question length and average answer length
6. WHEN a round has no turns THEN the Metrics_Calculator SHALL return 0.0 for average lengths
7. WHEN a round has no votes THEN the Metrics_Calculator SHALL return None for vote accuracy

### Requirement 2: Game Metrics Calculation

**User Story:** As an AI researcher, I want aggregate metrics computed across all rounds, so that I can evaluate overall game performance.

#### Acceptance Criteria

1. WHEN all rounds complete THEN the Metrics_Calculator SHALL compute aggregate statistics across all rounds
2. WHEN aggregate metrics are computed THEN they SHALL include total spy wins and total civilian wins
3. WHEN aggregate metrics are computed THEN they SHALL include average turns per round
4. WHEN aggregate metrics are computed THEN they SHALL determine the overall winner based on final scores
5. WHEN scores are tied THEN the Metrics_Calculator SHALL select the first player alphabetically as winner

### Requirement 3: Metrics Integration with Logging

**User Story:** As a data scientist, I want metrics included in game logs, so that I can analyze performance alongside dialogue data.

#### Acceptance Criteria

1. WHEN metrics are calculated THEN they SHALL be stored in the game log alongside dialogue data
2. WHEN the log is created THEN it SHALL include round metrics for each round
3. WHEN the log is created THEN it SHALL include aggregate game metrics
