# Requirements Document

## Introduction

This document specifies the requirements for a game log analytics system that analyzes JSON game logs from the Spyfall Arena project and generates comprehensive statistics about model performance. The system will parse all game logs in the `./logs` folder and produce aggregated metrics showing how different LLM models perform across various game scenarios.

## Glossary

- **Log_Analyzer**: The system component that reads and parses game log files
- **Statistics_Generator**: The component that computes performance metrics from parsed game data
- **Model**: An LLM (Large Language Model) identified by its model_name (e.g., "x-ai/grok-4.1-fast:free")
- **Game_Log**: A JSON file containing complete game data including rounds, players, votes, and scores
- **Performance_Metric**: A quantitative measure of how well a model performs (e.g., win rate, spy detection accuracy)
- **Report_Generator**: The component that formats and outputs statistics in human-readable format

## Requirements

### Requirement 1: Parse Game Logs

**User Story:** As a researcher, I want to parse all game log files in the logs directory, so that I can extract game data for analysis.

#### Acceptance Criteria

1. WHEN the Log_Analyzer is invoked, THE System SHALL scan the logs directory for all JSON files
2. WHEN a JSON file is found, THE Log_Analyzer SHALL parse it and extract game data
3. IF a JSON file is malformed or cannot be parsed, THEN THE System SHALL log the error and continue processing other files
4. WHEN parsing is complete, THE Log_Analyzer SHALL return a collection of parsed game records
5. THE Log_Analyzer SHALL extract player information including nickname, model_name, provider, and temperature
6. THE Log_Analyzer SHALL extract round information including spy identity, location, votes, and scores

### Requirement 2: Aggregate Model Performance Data

**User Story:** As a researcher, I want to aggregate performance data by model, so that I can compare how different models perform.

#### Acceptance Criteria

1. WHEN game data is processed, THE Statistics_Generator SHALL group results by model_name
2. THE Statistics_Generator SHALL calculate total games played per model
3. THE Statistics_Generator SHALL calculate total rounds played per model
4. THE Statistics_Generator SHALL track how many times each model was assigned the spy role
5. THE Statistics_Generator SHALL track how many times each model was assigned a civilian role
6. THE Statistics_Generator SHALL calculate average scores per model across all games

### Requirement 3: Calculate Win Rate Statistics

**User Story:** As a researcher, I want to see win rates for each model, so that I can identify which models are most successful.

#### Acceptance Criteria

1. THE Statistics_Generator SHALL calculate overall win rate (games won / games played) per model
2. THE Statistics_Generator SHALL calculate spy win rate (rounds won as spy / rounds played as spy) per model
3. THE Statistics_Generator SHALL calculate civilian win rate (rounds won as civilian / rounds played as civilian) per model
4. WHEN a model has not played any games, THE System SHALL report zero win rate
5. THE Statistics_Generator SHALL calculate the percentage of games where the model achieved the highest score

### Requirement 4: Calculate Voting Behavior Statistics

**User Story:** As a researcher, I want to analyze voting behavior, so that I can understand how models make decisions about identifying spies.

#### Acceptance Criteria

1. THE Statistics_Generator SHALL calculate voting accuracy (correct spy votes / total votes) per model
2. THE Statistics_Generator SHALL track how often each model initiates votes
3. THE Statistics_Generator SHALL track how often each model is voted as a suspect
4. THE Statistics_Generator SHALL calculate the percentage of votes where the model voted correctly for the spy
5. THE Statistics_Generator SHALL track vote agreement rate (how often a model's vote matches the majority)

### Requirement 5: Calculate Spy Performance Metrics

**User Story:** As a researcher, I want to see how well models perform as spies, so that I can evaluate their deception capabilities.

#### Acceptance Criteria

1. THE Statistics_Generator SHALL calculate spy survival rate (rounds survived without being voted out / total spy rounds) per model
2. THE Statistics_Generator SHALL calculate average score achieved when playing as spy per model
3. THE Statistics_Generator SHALL track successful location guesses made by spies per model
4. THE Statistics_Generator SHALL calculate the average number of turns survived before being voted out when playing as spy
5. WHEN a model has never played as spy, THE System SHALL indicate this in the statistics

### Requirement 6: Calculate Civilian Performance Metrics

**User Story:** As a researcher, I want to see how well models perform as civilians, so that I can evaluate their spy detection capabilities.

#### Acceptance Criteria

1. THE Statistics_Generator SHALL calculate civilian success rate (rounds where spy was correctly identified / total civilian rounds) per model
2. THE Statistics_Generator SHALL calculate average score achieved when playing as civilian per model
3. THE Statistics_Generator SHALL track how often the model correctly voted for the actual spy when playing as civilian
4. THE Statistics_Generator SHALL calculate average number of turns played per round when playing as civilian
5. WHEN a model has never played as civilian, THE System SHALL indicate this in the statistics

### Requirement 7: Generate Summary Report

**User Story:** As a researcher, I want to see a formatted summary report, so that I can quickly understand model performance.

#### Acceptance Criteria

1. THE Report_Generator SHALL produce a text-based summary report containing all calculated statistics
2. THE Report_Generator SHALL organize statistics by model in a clear, readable format
3. THE Report_Generator SHALL include a summary section showing overall statistics across all models
4. THE Report_Generator SHALL sort models by overall win rate in descending order
5. THE Report_Generator SHALL include metadata such as total games analyzed and date range of logs
6. THE Report_Generator SHALL display percentages with two decimal places for readability

### Requirement 8: Export Statistics to Structured Format

**User Story:** As a researcher, I want to export statistics to JSON or CSV format, so that I can perform further analysis in other tools.

#### Acceptance Criteria

1. THE System SHALL support exporting statistics to JSON format
2. THE System SHALL support exporting statistics to CSV format
3. WHEN exporting to JSON, THE System SHALL preserve all calculated metrics in a structured format
4. WHEN exporting to CSV, THE System SHALL create a tabular format with one row per model
5. THE System SHALL allow the user to specify the output file path for exports

### Requirement 9: Handle Edge Cases and Data Quality

**User Story:** As a researcher, I want the system to handle incomplete or unusual data gracefully, so that analysis is robust.

#### Acceptance Criteria

1. WHEN a game log has missing fields, THE System SHALL use default values and log a warning
2. WHEN a game has zero rounds, THE System SHALL skip it and log a warning
3. WHEN calculating percentages with zero denominators, THE System SHALL return 0.0 or indicate "N/A"
4. THE System SHALL handle games with different numbers of players correctly
5. THE System SHALL handle games with different numbers of rounds correctly

### Requirement 10: Calculate Round Ending Statistics

**User Story:** As a researcher, I want to see how rounds typically end for each model, so that I can understand their strategic tendencies.

#### Acceptance Criteria

1. THE Statistics_Generator SHALL track the frequency of each ending condition (vote, spy_guess, timeout) per model
2. THE Statistics_Generator SHALL calculate the percentage of rounds ending by successful spy vote per model
3. THE Statistics_Generator SHALL calculate the percentage of rounds ending by spy location guess per model
4. THE Statistics_Generator SHALL calculate the percentage of rounds ending by timeout per model
5. THE Statistics_Generator SHALL track successful vs unsuccessful spy location guesses per model
6. THE Statistics_Generator SHALL calculate spy guess accuracy (correct guesses / total guesses) per model

### Requirement 11: Calculate Turn-Based Engagement Metrics

**User Story:** As a researcher, I want to analyze turn patterns, so that I can understand model activity levels.

#### Acceptance Criteria

1. THE Statistics_Generator SHALL calculate average number of turns per round per model
2. THE Statistics_Generator SHALL track total questions asked by each model across all games
3. THE Statistics_Generator SHALL track total questions answered by each model across all games
4. THE Statistics_Generator SHALL calculate the ratio of questions asked to questions answered per model
5. WHEN turn data is not available in a log, THE System SHALL skip turn-based metrics for that game

### Requirement 12: Calculate Vote Initiation Statistics

**User Story:** As a researcher, I want to see vote initiation patterns, so that I can understand which models are more aggressive.

#### Acceptance Criteria

1. THE Statistics_Generator SHALL track how many times each model initiated a vote
2. THE Statistics_Generator SHALL calculate vote initiation success rate (successful votes / total initiated) per model
3. THE Statistics_Generator SHALL track how many times each model was the suspect in a vote
4. THE Statistics_Generator SHALL calculate how often each model votes "yes" vs "no" when not the suspect
5. THE Statistics_Generator SHALL track the average round number when each model initiates their first vote

### Requirement 13: Calculate Location-Based Performance

**User Story:** As a researcher, I want to see if certain locations affect model performance, so that I can identify location-specific patterns.

#### Acceptance Criteria

1. THE Statistics_Generator SHALL track win rates per location per model
2. THE Statistics_Generator SHALL calculate spy win rate per location per model
3. THE Statistics_Generator SHALL calculate civilian win rate per location per model
4. THE Statistics_Generator SHALL track how often spies successfully guess each location
5. THE Statistics_Generator SHALL identify which locations have the highest spy success rates overall

### Requirement 14: Calculate Comparative Rankings

**User Story:** As a researcher, I want to see models ranked by various metrics, so that I can quickly identify top performers.

#### Acceptance Criteria

1. THE Report_Generator SHALL create a leaderboard ranking models by overall win rate
2. THE Report_Generator SHALL create a leaderboard ranking models by spy win rate
3. THE Report_Generator SHALL create a leaderboard ranking models by civilian win rate
4. THE Report_Generator SHALL create a leaderboard ranking models by voting accuracy
5. THE Report_Generator SHALL create a leaderboard ranking models by average score per game

### Requirement 15: Calculate Score Distribution Statistics

**User Story:** As a researcher, I want to see score distributions, so that I can understand performance consistency.

#### Acceptance Criteria

1. THE Statistics_Generator SHALL calculate average score per round per model
2. THE Statistics_Generator SHALL calculate minimum and maximum scores achieved per model
3. THE Statistics_Generator SHALL calculate score standard deviation per model
4. THE Statistics_Generator SHALL track the distribution of scores (0, 1, 2, 4 points) per model
5. THE Statistics_Generator SHALL calculate what percentage of rounds each model scores 0 points

### Requirement 16: Provide Command-Line Interface

**User Story:** As a researcher, I want to run the analysis from the command line, so that I can easily integrate it into my workflow.

#### Acceptance Criteria

1. THE System SHALL provide a command-line script that can be executed from the project root
2. THE System SHALL accept a logs directory path as a command-line argument
3. THE System SHALL accept an output format option (text, json, csv) as a command-line argument
4. THE System SHALL accept an output file path as an optional command-line argument
5. WHEN no arguments are provided, THE System SHALL use sensible defaults (./logs directory, text format, stdout)
6. THE System SHALL display a help message when invoked with --help flag
