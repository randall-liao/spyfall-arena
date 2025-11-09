# Requirements Document

## Introduction

Spyfall Arena Phase One is a backend simulation platform that enables multiple LLM agents to autonomously play the social deduction game Spyfall. The system will coordinate a complete game from role assignment through voting, maintaining role secrecy, tracking all interactions, and producing structured logs for analysis. This foundational phase focuses on creating a fully automated, reproducible game engine without any user interface.

## Requirements

### Requirement 1: Configuration-Based Game Initialization

**User Story:** As an AI researcher, I want to configure all game parameters via a file, so that I can run reproducible experiments without manual intervention.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL read a YAML configuration file containing game parameters
2. IF a configuration parameter is missing THEN the system SHALL use a sensible default value
3. WHEN a random seed is provided in the configuration THEN the system SHALL produce identical game outcomes across runs with the same seed
4. WHEN the configuration is loaded THEN the system SHALL validate all parameters and report any invalid values
5. IF the configuration file is missing or malformed THEN the system SHALL report a clear error message and exit gracefully

### Requirement 2: Secure Role Assignment

**User Story:** As a game coordinator, I want roles distributed secretly among agents, so that the spy's identity remains hidden and gameplay is fair.

#### Acceptance Criteria

1. WHEN roles are assigned THEN the system SHALL designate exactly one player as the spy
2. WHEN roles are assigned THEN the system SHALL designate all remaining players as civilians
3. WHEN a civilian agent receives its role THEN it SHALL receive the game location
4. WHEN the spy agent receives its role THEN it SHALL receive "unknown" as the location
5. WHEN any agent queries for information THEN it SHALL only access its own private role information
6. WHEN roles are assigned THEN the system SHALL store the complete role mapping internally for logging purposes
7. WHEN the random seed is set THEN the spy assignment SHALL be reproducible across runs
8. WHEN game is going, each model will be asign a nickname for other LLMs in the game to identify them, actual model name SHALL not be exposed to the other models

### Requirement 3: Turn-Based Game Loop Execution

**User Story:** As a game engine, I want to orchestrate structured question-answer turns, so that LLM agents can interact in a realistic Spyfall game flow.

#### Acceptance Criteria

1. WHEN a game starts THEN the system SHALL designate the first player as the asker (randomly unless specified in configuration)
2. WHEN the asking phase starts THEN the asker SHALL select another player and pose a question
3. WHEN a player is asked a question THEN they SHALL NOT be the player who just asked them a question (no retaliation rule)
4. WHEN a question is asked THEN the selected player SHALL provide an answer
5. WHEN a player answers a question THEN they SHALL become the next asker
6. WHEN each agent takes a turn THEN it SHALL receive the public conversation history, its private role information, and turn metadata
7. WHEN any interaction occurs THEN the system SHALL record the player nicknames, question text, and answer text
8. WHEN the game runs THEN the system SHALL continue turns until a round-ending condition is met

### Requirement 4: Player-Initiated Voting and Indictment

**User Story:** As a game coordinator, I want players to initiate votes to indict suspected spies, so that the game follows authentic Spyfall voting mechanics.

#### Acceptance Criteria

1. WHEN any player suspects another player THEN they SHALL be able to put that player up for vote at any time during questioning
2. WHEN a player is put up for vote THEN the system SHALL collect votes from all players one by one
3. WHEN votes are collected THEN each player SHALL vote yes or no on whether to indict the suspect
4. IF all players vote yes THEN the suspect SHALL be indicted and must reveal their role
5. IF any player votes no THEN the vote fails and the game SHALL continue
6. WHEN a player puts someone up for vote THEN that player SHALL NOT be able to initiate another vote in the same round
7. WHEN an indictment succeeds THEN the round SHALL end immediately
8. WHEN voting occurs THEN the system SHALL record all individual votes in the game log

### Requirement 5: Comprehensive Game Logging

**User Story:** As a data scientist, I want detailed structured logs of each game, so that I can analyze LLM behavior and performance.

#### Acceptance Criteria

1. WHEN a game completes THEN the system SHALL create one JSON log file in the `/logs` directory
2. WHEN the log is created THEN it SHALL include a timestamp, unique game ID, and configuration snapshot
3. WHEN the log is created THEN it SHALL include the complete player list with model information and assigned nicknames
4. WHEN the log is created THEN it SHALL include all role assignments for each round
5. WHEN the log is created THEN it SHALL include every question and answer from all rounds with player nicknames
6. WHEN the log is created THEN it SHALL include all voting attempts, results, and the round ending condition
7. WHEN the log is created THEN it SHALL include point totals for each round and final scores
8. WHEN the log is created THEN it SHALL include the overall game winner
9. IF the configuration enables full prompt logging THEN the system SHALL include raw LLM prompts and responses
10. WHEN log files are created THEN they SHALL follow a consistent naming pattern (e.g., `2025-11-08_game_001.json`)
11. WHEN the log is written THEN it SHALL be valid JSON and machine-readable
12. WHEN the log is written THEN it SHALL NOT contain sensitive API keys or credentials

### Requirement 5: Spy Location Guess Mechanism

**User Story:** As the spy player, I want to be able to guess the location at any time, so that I can win the round if I've deduced it correctly.

#### Acceptance Criteria

1. WHEN the spy believes they know the location THEN they SHALL be able to reveal themselves and guess the location at any time
2. WHEN the spy makes a location guess THEN the round SHALL end immediately
3. WHEN the spy guesses the location THEN the system SHALL check if the guess matches the actual location
4. WHEN the spy's guess is evaluated THEN the result SHALL be recorded in the game log

### Requirement 6: Round Ending Conditions

**User Story:** As a game coordinator, I want clear conditions for when a round ends, so that the game progresses according to Spyfall rules.

#### Acceptance Criteria

1. WHEN a player is successfully indicted THEN the round SHALL end immediately
2. WHEN the spy reveals themselves to guess the location THEN the round SHALL end immediately
3. WHEN the configured time limit or turn limit is reached THEN the round SHALL end
4. WHEN a round ends THEN the system SHALL record the ending condition and proceed to scoring

### Requirement 7: Scoring System

**User Story:** As an AI researcher, I want a point-based scoring system, so that I can track model performance across multiple rounds.

#### Acceptance Criteria

1. IF the spy is not successfully indicted THEN the spy SHALL earn 2 points
2. IF a non-spy player is successfully indicted THEN the spy SHALL earn 4 points
3. IF the spy correctly guesses the location THEN the spy SHALL earn 4 points
4. IF the spy is successfully indicted THEN each non-spy player SHALL earn 1 point
5. IF the spy is successfully indicted THEN the player who initiated the successful vote SHALL earn 2 points instead of 1
6. WHEN a round completes THEN the system SHALL calculate and record all points earned
7. WHEN multiple rounds are played THEN the system SHALL maintain a running total of points for each player
8. WHEN all configured rounds complete THEN the system SHALL determine the overall winner as the player with the most points

### Requirement 8: Performance Metrics Calculation

**User Story:** As an AI researcher, I want automated metrics computed for each round and game, so that I can quickly evaluate model performance.

#### Acceptance Criteria

1. WHEN a round completes THEN the system SHALL record which side won (civilian or spy)
2. WHEN a round completes THEN the system SHALL calculate vote accuracy (percentage of civilians who voted correctly if a vote occurred)
3. WHEN a round completes THEN the system SHALL determine if the spy successfully avoided detection or guessed the location
4. WHEN a round completes THEN the system SHALL compute response statistics including turn count and response lengths
5. WHEN metrics are calculated THEN they SHALL be stored in the game log alongside dialogue data
6. WHEN all rounds complete THEN the system SHALL compute aggregate statistics across all rounds

### Requirement 9: Robust Error Handling

**User Story:** As a system operator, I want the game to handle LLM API failures gracefully, so that temporary issues don't abort entire game sessions.

#### Acceptance Criteria

1. IF an LLM API call fails THEN the system SHALL retry the call once
2. IF the retry fails THEN the system SHALL skip that turn and log the error
3. WHEN a turn is skipped THEN the system SHALL clearly record the skip reason in the game log
4. IF a critical failure occurs THEN the system SHALL abort the game and produce a partial log
5. WHEN a game completes THEN the system SHALL include a status field indicating "success", "partial success", or "error"
6. WHEN an exception occurs THEN the system SHALL catch it, log it, and continue if possible
7. WHEN an LLM timeout occurs THEN the game execution SHALL NOT halt permanently

### Requirement 10: Structured Output Generation

**User Story:** As a downstream analyst, I want consistent, well-structured output files, so that I can easily parse and analyze game data.

#### Acceptance Criteria

1. WHEN a game completes THEN the system SHALL automatically generate an output file
2. WHEN the output file is created THEN it SHALL preserve all core gameplay data
3. WHEN the output file is created THEN it SHALL be machine-readable and follow a documented schema
4. WHEN multiple games run THEN each SHALL produce a separate, uniquely named output file

### Requirement 11: Multi-Round Game Support

**User Story:** As an AI researcher, I want to run multiple rounds in a single game session, so that I can evaluate long-term model performance and strategy adaptation.

#### Acceptance Criteria

1. WHEN the configuration specifies multiple rounds THEN the system SHALL run that number of rounds sequentially
2. WHEN a new round starts THEN the system SHALL randomly assign a new spy and location
3. WHEN a new round starts THEN all players SHALL retain their point totals from previous rounds
4. WHEN all rounds complete THEN the system SHALL determine the overall game winner based on total points
5. WHEN multiple rounds are played THEN each round's data SHALL be recorded separately in the game log

### Requirement 12: Reproducibility and Automation

**User Story:** As an AI researcher, I want fully automated and reproducible game execution, so that I can run controlled experiments and compare results reliably.

#### Acceptance Criteria

1. WHEN a game is initiated THEN it SHALL run end-to-end using only the configuration file without manual input
2. WHEN role information is accessed THEN no player SHALL ever see another player's private information
3. WHEN multiple games run with the same configuration THEN at least 90% SHALL complete without errors
4. WHEN log files are generated THEN they SHALL be valid JSON with consistent structure across all games
5. WHEN the same configuration and seed are used THEN the system SHALL produce identical game states and outcomes
