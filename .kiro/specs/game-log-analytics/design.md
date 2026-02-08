# Design Document

## Overview

The game log analytics system will analyze JSON game logs from Spyfall Arena and generate comprehensive performance statistics for each LLM model. The system follows a pipeline architecture: parse logs → aggregate data → calculate statistics → generate reports. The design emphasizes modularity, testability, and extensibility to support future analytics needs.

## Architecture

The system consists of four main components organized in a pipeline:

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────┐
│ Log Parser  │───▶│ Data         │───▶│ Statistics      │───▶│ Report      │
│             │    │ Aggregator   │    │ Calculator      │    │ Generator   │
└─────────────┘    └──────────────┘    └─────────────────┘    └─────────────┘
       │                  │                     │                     │
       ▼                  ▼                     ▼                     ▼
  JSON Files        Game Records         Metric Objects         Text/JSON/CSV
```

**Design Principles:**
- **Separation of Concerns**: Each component has a single, well-defined responsibility
- **Immutability**: Parsed data structures are immutable to prevent accidental modification
- **Fail-Safe**: Errors in individual files don't stop the entire analysis
- **Extensibility**: New metrics can be added without modifying existing code

## Components and Interfaces

### 1. Log Parser

**Responsibility**: Read and parse JSON game log files into structured Python objects.

**Interface**:
```python
class LogParser:
    def parse_directory(self, directory_path: str) -> List[GameRecord]:
        """Parse all JSON files in directory, return list of game records"""
        
    def parse_file(self, file_path: str) -> Optional[GameRecord]:
        """Parse single JSON file, return GameRecord or None if error"""
```

**Key Behaviors**:
- Scans directory for `.json` files (ignores non-JSON files)
- Validates JSON structure before parsing
- Logs errors for malformed files but continues processing
- Returns empty list if directory doesn't exist or has no valid files

### 2. Data Aggregator

**Responsibility**: Group and organize game records by model for efficient statistics calculation.

**Interface**:
```python
class DataAggregator:
    def aggregate_by_model(self, games: List[GameRecord]) -> Dict[str, ModelData]:
        """Group all game data by model_name"""
        
    def aggregate_by_location(self, games: List[GameRecord]) -> Dict[str, LocationData]:
        """Group all game data by location"""
```

**Key Behaviors**:
- Creates a ModelData object for each unique model_name
- Collects all rounds where each model participated
- Separates spy rounds from civilian rounds
- Tracks all votes, turns, and scores for each model

### 3. Statistics Calculator

**Responsibility**: Calculate all performance metrics from aggregated data.

**Interface**:
```python
class StatisticsCalculator:
    def calculate_all_statistics(self, model_data: Dict[str, ModelData]) -> Dict[str, ModelStatistics]:
        """Calculate complete statistics for all models"""
        
    def calculate_model_statistics(self, data: ModelData) -> ModelStatistics:
        """Calculate statistics for a single model"""
```

**Key Behaviors**:
- Calculates win rates, averages, and percentages
- Handles division by zero gracefully (returns 0.0 or None)
- Computes derived metrics (e.g., spy survival rate)
- Validates data before calculation

### 4. Report Generator

**Responsibility**: Format statistics into human-readable or machine-readable output.

**Interface**:
```python
class ReportGenerator:
    def generate_text_report(self, statistics: Dict[str, ModelStatistics]) -> str:
        """Generate formatted text report"""
        
    def generate_json_report(self, statistics: Dict[str, ModelStatistics]) -> str:
        """Generate JSON report"""
        
    def generate_csv_report(self, statistics: Dict[str, ModelStatistics]) -> str:
        """Generate CSV report"""
```

**Key Behaviors**:
- Sorts models by win rate for text reports
- Formats percentages to 2 decimal places
- Creates leaderboards for key metrics
- Includes summary statistics across all models

## Data Models

### GameRecord
```python
@dataclass
class GameRecord:
    game_id: str
    timestamp: str
    players: List[PlayerConfig]
    rounds: List[RoundRecord]
    final_scores: Dict[str, int]
    status: str
```

### RoundRecord
```python
@dataclass
class RoundRecord:
    round_number: int
    location: str
    spy: str
    role_assignments: Dict[str, RoleAssignment]
    turns: List[TurnRecord]
    vote_attempts: List[VoteAttempt]
    spy_guess: Optional[SpyGuess]
    ending_condition: str
    round_scores: Dict[str, int]
```

### ModelData
```python
@dataclass
class ModelData:
    model_name: str
    total_games: int
    total_rounds: int
    spy_rounds: List[RoundRecord]
    civilian_rounds: List[RoundRecord]
    all_scores: List[int]
    votes_cast: List[VoteRecord]
    votes_received: List[VoteRecord]
    turns_as_asker: List[TurnRecord]
    turns_as_answerer: List[TurnRecord]
```

### ModelStatistics
```python
@dataclass
class ModelStatistics:
    model_name: str
    
    # Basic counts
    total_games: int
    total_rounds: int
    spy_rounds_count: int
    civilian_rounds_count: int
    
    # Win rates
    overall_win_rate: float
    spy_win_rate: float
    civilian_win_rate: float
    
    # Scoring
    average_score_per_round: float
    average_score_per_game: float
    min_score: int
    max_score: int
    score_std_dev: float
    score_distribution: Dict[int, int]  # score -> count
    
    # Voting
    voting_accuracy: float
    votes_initiated: int
    vote_initiation_success_rate: float
    times_suspected: int
    yes_vote_percentage: float
    
    # Spy performance
    spy_survival_rate: float
    spy_guess_accuracy: float
    successful_spy_guesses: int
    total_spy_guesses: int
    average_spy_score: float
    
    # Civilian performance
    civilian_success_rate: float
    average_civilian_score: float
    correct_spy_votes: int
    total_civilian_votes: int
    
    # Turn engagement
    questions_asked: int
    questions_answered: int
    average_turns_per_round: float
    
    # Round endings
    rounds_ended_by_vote: int
    rounds_ended_by_spy_guess: int
    rounds_ended_by_timeout: int
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Parse then serialize preserves structure

*For any* valid GameRecord object, serializing to JSON then parsing back should produce an equivalent GameRecord.

**Validates: Requirements 1.2, 1.4**

### Property 2: Statistics sum to totals

*For any* ModelStatistics object, the sum of spy_rounds_count and civilian_rounds_count should equal total_rounds.

**Validates: Requirements 2.3, 2.4, 2.5**

### Property 3: Win rates are bounded

*For any* calculated win rate (overall, spy, or civilian), the value should be between 0.0 and 1.0 inclusive.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 4: Score distribution sums correctly

*For any* ModelStatistics object, the sum of all values in score_distribution should equal the total number of rounds played.

**Validates: Requirements 15.4**

### Property 5: Vote counts are consistent

*For any* ModelStatistics object, votes_initiated should be less than or equal to total_rounds (can't initiate more votes than rounds played).

**Validates: Requirements 12.1, 12.2**

### Property 6: Spy guess accuracy is valid

*For any* ModelStatistics object, if total_spy_guesses is zero, then spy_guess_accuracy should be 0.0, otherwise it should equal successful_spy_guesses / total_spy_guesses.

**Validates: Requirements 10.6**

### Property 7: Percentage calculations are bounded

*For any* percentage metric (voting_accuracy, spy_survival_rate, etc.), the value should be between 0.0 and 1.0 inclusive.

**Validates: Requirements 4.1, 5.1, 6.1, 12.4**

### Property 8: Empty input produces empty output

*For any* empty list of GameRecords, the statistics calculator should return an empty dictionary of ModelStatistics.

**Validates: Requirements 9.2**

### Property 9: Malformed file doesn't crash parser

*For any* file with invalid JSON or missing required fields, the parser should return None and log an error without raising an exception.

**Validates: Requirements 1.3, 9.1**

### Property 10: Report generation is deterministic

*For any* ModelStatistics object, generating a report twice should produce identical output (given the same format).

**Validates: Requirements 7.1, 7.2, 8.3**

## Error Handling

### File System Errors
- **Missing directory**: Log warning, return empty results
- **Permission denied**: Log error with file path, skip file
- **Corrupted JSON**: Log error with file name, skip file, continue processing

### Data Validation Errors
- **Missing required fields**: Use default values (0 for counts, empty list for collections)
- **Invalid data types**: Log warning, skip that specific field
- **Negative scores**: Log warning, use absolute value

### Calculation Errors
- **Division by zero**: Return 0.0 for rates/percentages
- **Empty collections**: Return 0 for counts, 0.0 for averages
- **NaN or Inf results**: Replace with 0.0, log warning

### Output Errors
- **Cannot write to file**: Fall back to stdout, log error
- **Invalid output format**: Default to text format, log warning

## Testing Strategy

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage and correctness.

### Unit Tests

Unit tests verify specific examples, edge cases, and error conditions. Each component has dedicated test coverage:

#### Log Parser Tests (`test_log_parser.py`)

**Valid Input Tests:**
- `test_parse_valid_game_log`: Parse a complete, valid game log file
- `test_parse_multiple_rounds`: Parse game with multiple rounds
- `test_parse_game_with_turns`: Parse game with turn-by-turn data
- `test_parse_game_without_turns`: Parse game with empty turns list
- `test_parse_directory_multiple_files`: Parse directory with multiple valid JSON files

**Error Handling Tests:**
- `test_parse_malformed_json`: Handle file with invalid JSON syntax
- `test_parse_missing_required_fields`: Handle JSON missing required fields (game_id, rounds, etc.)
- `test_parse_invalid_data_types`: Handle fields with wrong data types
- `test_parse_nonexistent_file`: Handle file that doesn't exist
- `test_parse_nonexistent_directory`: Handle directory that doesn't exist
- `test_parse_empty_directory`: Handle directory with no JSON files
- `test_parse_directory_with_non_json_files`: Ignore non-JSON files in directory

**Edge Cases:**
- `test_parse_game_with_zero_rounds`: Handle game with empty rounds list
- `test_parse_game_with_null_values`: Handle null values in optional fields
- `test_parse_game_with_extra_fields`: Ignore extra fields not in schema

#### Data Aggregator Tests (`test_data_aggregator.py`)

**Aggregation Tests:**
- `test_aggregate_single_model`: Aggregate data for one model across multiple games
- `test_aggregate_multiple_models`: Aggregate data for multiple different models
- `test_aggregate_spy_vs_civilian_rounds`: Correctly separate spy and civilian rounds
- `test_aggregate_votes_by_model`: Collect all votes cast by and against each model
- `test_aggregate_turns_by_model`: Collect all turns where model asked or answered

**Edge Cases:**
- `test_aggregate_empty_game_list`: Handle empty list of games
- `test_aggregate_game_with_no_players`: Handle game with empty players list
- `test_aggregate_duplicate_games`: Handle duplicate game records correctly
- `test_aggregate_same_model_different_configs`: Handle same model with different temperatures

**Location Aggregation Tests:**
- `test_aggregate_by_location`: Group rounds by location
- `test_aggregate_location_performance`: Track wins/losses per location

#### Statistics Calculator Tests (`test_statistics_calculator.py`)

**Basic Calculation Tests:**
- `test_calculate_win_rates`: Calculate overall, spy, and civilian win rates
- `test_calculate_average_scores`: Calculate average scores per round and per game
- `test_calculate_score_distribution`: Build score frequency distribution
- `test_calculate_voting_accuracy`: Calculate percentage of correct spy votes
- `test_calculate_spy_survival_rate`: Calculate how often spy avoids detection

**Edge Cases:**
- `test_calculate_with_zero_games`: Handle model with no games played
- `test_calculate_with_zero_spy_rounds`: Handle model never assigned as spy
- `test_calculate_with_zero_civilian_rounds`: Handle model never assigned as civilian
- `test_calculate_with_zero_votes`: Handle model that never voted
- `test_calculate_division_by_zero`: Ensure all division by zero returns 0.0

**Specific Metric Tests:**
- `test_spy_guess_accuracy_no_guesses`: Accuracy is 0.0 when no guesses made
- `test_spy_guess_accuracy_all_correct`: Accuracy is 1.0 when all guesses correct
- `test_vote_initiation_success_rate`: Calculate successful vote initiations
- `test_score_standard_deviation`: Calculate score variance correctly

#### Report Generator Tests (`test_report_generator.py`)

**Text Report Tests:**
- `test_generate_text_report_single_model`: Format report for one model
- `test_generate_text_report_multiple_models`: Format report with multiple models
- `test_text_report_sorting`: Models sorted by win rate descending
- `test_text_report_formatting`: Percentages formatted to 2 decimal places
- `test_text_report_leaderboards`: Leaderboards included for key metrics

**JSON Report Tests:**
- `test_generate_json_report`: Valid JSON output
- `test_json_report_structure`: All statistics included in JSON
- `test_json_report_parseable`: Output can be parsed back to Python objects

**CSV Report Tests:**
- `test_generate_csv_report`: Valid CSV output
- `test_csv_report_headers`: Correct column headers
- `test_csv_report_one_row_per_model`: Each model gets one row
- `test_csv_report_parseable`: Output can be parsed by CSV reader

**Edge Cases:**
- `test_generate_report_empty_statistics`: Handle empty statistics dictionary
- `test_generate_report_single_model`: Handle single model case
- `test_generate_report_with_nan_values`: Handle NaN or None values gracefully

### Property-Based Tests

Property tests verify universal properties across all inputs using the Hypothesis library (minimum 100 iterations per test):

#### Property 1: Parse-serialize round trip
*For any* valid GameRecord object, serializing to JSON then parsing back should produce an equivalent GameRecord.

**Test Implementation:**
```python
@given(game_record=game_record_strategy())
def test_parse_serialize_roundtrip(game_record):
    json_str = json.dumps(game_record.to_dict())
    parsed = LogParser().parse_json_string(json_str)
    assert parsed == game_record
```
**Validates: Requirements 1.2, 1.4**

#### Property 2: Statistics component sums
*For any* ModelStatistics object, the sum of spy_rounds_count and civilian_rounds_count should equal total_rounds.

**Test Implementation:**
```python
@given(model_data=model_data_strategy())
def test_statistics_component_sums(model_data):
    stats = StatisticsCalculator().calculate_model_statistics(model_data)
    assert stats.spy_rounds_count + stats.civilian_rounds_count == stats.total_rounds
```
**Validates: Requirements 2.3, 2.4, 2.5**

#### Property 3: Win rate bounds
*For any* calculated win rate (overall, spy, or civilian), the value should be between 0.0 and 1.0 inclusive.

**Test Implementation:**
```python
@given(model_data=model_data_strategy())
def test_win_rate_bounds(model_data):
    stats = StatisticsCalculator().calculate_model_statistics(model_data)
    assert 0.0 <= stats.overall_win_rate <= 1.0
    assert 0.0 <= stats.spy_win_rate <= 1.0
    assert 0.0 <= stats.civilian_win_rate <= 1.0
```
**Validates: Requirements 3.1, 3.2, 3.3**

#### Property 4: Score distribution consistency
*For any* ModelStatistics object, the sum of all values in score_distribution should equal the total number of rounds played.

**Test Implementation:**
```python
@given(model_data=model_data_strategy())
def test_score_distribution_sums_to_total(model_data):
    stats = StatisticsCalculator().calculate_model_statistics(model_data)
    distribution_sum = sum(stats.score_distribution.values())
    assert distribution_sum == stats.total_rounds
```
**Validates: Requirements 15.4**

#### Property 5: Vote count constraints
*For any* ModelStatistics object, votes_initiated should be less than or equal to total_rounds (can't initiate more votes than rounds played).

**Test Implementation:**
```python
@given(model_data=model_data_strategy())
def test_vote_count_constraints(model_data):
    stats = StatisticsCalculator().calculate_model_statistics(model_data)
    assert stats.votes_initiated <= stats.total_rounds
```
**Validates: Requirements 12.1, 12.2**

#### Property 6: Spy guess accuracy formula
*For any* ModelStatistics object, if total_spy_guesses is zero, then spy_guess_accuracy should be 0.0, otherwise it should equal successful_spy_guesses / total_spy_guesses.

**Test Implementation:**
```python
@given(model_data=model_data_strategy())
def test_spy_guess_accuracy_formula(model_data):
    stats = StatisticsCalculator().calculate_model_statistics(model_data)
    if stats.total_spy_guesses == 0:
        assert stats.spy_guess_accuracy == 0.0
    else:
        expected = stats.successful_spy_guesses / stats.total_spy_guesses
        assert abs(stats.spy_guess_accuracy - expected) < 0.001
```
**Validates: Requirements 10.6**

#### Property 7: Percentage bounds
*For any* percentage metric (voting_accuracy, spy_survival_rate, etc.), the value should be between 0.0 and 1.0 inclusive.

**Test Implementation:**
```python
@given(model_data=model_data_strategy())
def test_percentage_bounds(model_data):
    stats = StatisticsCalculator().calculate_model_statistics(model_data)
    assert 0.0 <= stats.voting_accuracy <= 1.0
    assert 0.0 <= stats.spy_survival_rate <= 1.0
    assert 0.0 <= stats.civilian_success_rate <= 1.0
    assert 0.0 <= stats.yes_vote_percentage <= 1.0
```
**Validates: Requirements 4.1, 5.1, 6.1, 12.4**

#### Property 8: Empty input handling
*For any* empty list of GameRecords, the statistics calculator should return an empty dictionary of ModelStatistics.

**Test Implementation:**
```python
def test_empty_input_produces_empty_output():
    empty_games = []
    aggregated = DataAggregator().aggregate_by_model(empty_games)
    stats = StatisticsCalculator().calculate_all_statistics(aggregated)
    assert stats == {}
```
**Validates: Requirements 9.2**

#### Property 9: Error resilience
*For any* file with invalid JSON or missing required fields, the parser should return None and log an error without raising an exception.

**Test Implementation:**
```python
@given(malformed_json=malformed_json_strategy())
def test_parser_error_resilience(malformed_json):
    parser = LogParser()
    # Should not raise exception
    result = parser.parse_json_string(malformed_json)
    assert result is None
```
**Validates: Requirements 1.3, 9.1**

#### Property 10: Report determinism
*For any* ModelStatistics object, generating a report twice should produce identical output (given the same format).

**Test Implementation:**
```python
@given(statistics=model_statistics_strategy())
def test_report_determinism(statistics):
    generator = ReportGenerator()
    report1 = generator.generate_text_report(statistics)
    report2 = generator.generate_text_report(statistics)
    assert report1 == report2
```
**Validates: Requirements 7.1, 7.2, 8.3**

### Hypothesis Strategies

Custom Hypothesis strategies for generating test data:

```python
@composite
def game_record_strategy(draw):
    """Generate random but valid GameRecord objects"""
    # Implementation details...

@composite
def model_data_strategy(draw):
    """Generate random but valid ModelData objects"""
    # Implementation details...

@composite
def model_statistics_strategy(draw):
    """Generate random but valid ModelStatistics objects"""
    # Implementation details...

@composite
def malformed_json_strategy(draw):
    """Generate various types of malformed JSON"""
    # Implementation details...
```

### Test Configuration

- **Test Runner**: pytest
- **Property Testing**: Hypothesis library
- **Minimum Iterations**: 100 per property test
- **Coverage Target**: 100% line coverage (enforced)
- **Mocking**: Use pytest fixtures and unittest.mock for file system operations
- **Test Data**: Use sample game logs from `logs/` directory for E2E tests

### End-to-End Integration Test

An end-to-end test validates the entire pipeline using a sample game log file stored in the E2E test directory.

#### E2E Test: Full Pipeline with Sample Log (`tests/e2e/test_analytics_e2e.py`)

**Purpose**: Verify the complete workflow from parsing a sample log file to generating reports.

**Test Data**: A sample log file `tests/e2e/sample_log.json` will be created with known, predictable data for validation.

**Sample Log Structure:**
```json
{
  "game_id": "test_game_001",
  "timestamp": "2025-01-01T00:00:00.000000",
  "players": [
    {"nickname": "Alice", "model_name": "test-model-1", "temperature": 0.9},
    {"nickname": "Bob", "model_name": "test-model-1", "temperature": 0.9},
    {"nickname": "Charlie", "model_name": "test-model-2", "temperature": 0.7},
    {"nickname": "David", "model_name": "test-model-2", "temperature": 0.7}
  ],
  "rounds": [
    {
      "round_number": 1,
      "location": "Bank",
      "spy": "Alice",
      "role_assignments": {
        "Alice": {"is_spy": true, "location": null},
        "Bob": {"is_spy": false, "location": "Bank"},
        "Charlie": {"is_spy": false, "location": "Bank"},
        "David": {"is_spy": false, "location": "Bank"}
      },
      "turns": [
        {
          "turn_number": 1,
          "asker_nickname": "Bob",
          "answerer_nickname": "Charlie",
          "question": "Do you handle money here?",
          "answer": "Yes, that's the main purpose.",
          "timestamp": "2025-01-01T00:01:00.000000"
        }
      ],
      "vote_attempts": [
        {
          "initiator": "Bob",
          "suspect": "Alice",
          "votes": {"Alice": false, "Bob": true, "Charlie": true, "David": true},
          "passed": true,
          "timestamp": "2025-01-01T00:05:00.000000"
        }
      ],
      "spy_guess": null,
      "ending_condition": "vote",
      "round_scores": {"Alice": 0, "Bob": 2, "Charlie": 1, "David": 1}
    },
    {
      "round_number": 2,
      "location": "Hospital",
      "spy": "Charlie",
      "role_assignments": {
        "Alice": {"is_spy": false, "location": "Hospital"},
        "Bob": {"is_spy": false, "location": "Hospital"},
        "Charlie": {"is_spy": true, "location": null},
        "David": {"is_spy": false, "location": "Hospital"}
      },
      "turns": [],
      "vote_attempts": [],
      "spy_guess": {
        "spy_nickname": "Charlie",
        "guessed_location": "Hospital",
        "actual_location": "Hospital",
        "correct": true,
        "timestamp": "2025-01-01T00:10:00.000000"
      },
      "ending_condition": "spy_guess",
      "round_scores": {"Alice": 0, "Bob": 0, "Charlie": 4, "David": 0}
    }
  ],
  "final_scores": {"Alice": 0, "Bob": 2, "Charlie": 5, "David": 1},
  "status": "completed"
}
```

**Test Implementation:**
```python
import json
from pathlib import Path

def test_full_pipeline_with_sample_log():
    """
    End-to-end test using sample log file in e2e test directory.
    Tests the complete pipeline: parse → aggregate → calculate → report.
    """
    # Setup: Use sample log file
    sample_log_path = Path(__file__).parent / "sample_log.json"
    assert sample_log_path.exists(), "Sample log file must exist"
    
    # Step 1: Parse log
    parser = LogParser()
    game = parser.parse_file(str(sample_log_path))
    
    # Assertions on parsing
    assert game is not None, "Should parse sample log successfully"
    assert game.game_id == "test_game_001"
    assert len(game.rounds) == 2
    assert len(game.players) == 4
    
    # Step 2: Aggregate data
    aggregator = DataAggregator()
    model_data = aggregator.aggregate_by_model([game])
    
    # Assertions on aggregation
    assert len(model_data) == 2, "Should have 2 models (test-model-1 and test-model-2)"
    assert "test-model-1" in model_data
    assert "test-model-2" in model_data
    
    # Validate test-model-1 data (Alice and Bob)
    model1_data = model_data["test-model-1"]
    assert model1_data.total_games == 1
    assert model1_data.total_rounds == 4  # 2 players × 2 rounds
    assert len(model1_data.spy_rounds) == 1  # Alice was spy in round 1
    assert len(model1_data.civilian_rounds) == 3  # Bob in both, Alice in round 2
    
    # Validate test-model-2 data (Charlie and David)
    model2_data = model_data["test-model-2"]
    assert model2_data.total_games == 1
    assert model2_data.total_rounds == 4  # 2 players × 2 rounds
    assert len(model2_data.spy_rounds) == 1  # Charlie was spy in round 2
    assert len(model2_data.civilian_rounds) == 3  # David in both, Charlie in round 1
    
    # Step 3: Calculate statistics
    calculator = StatisticsCalculator()
    statistics = calculator.calculate_all_statistics(model_data)
    
    # Assertions on statistics
    assert len(statistics) == 2, "Should have stats for both models"
    
    # Validate test-model-1 statistics
    stats1 = statistics["test-model-1"]
    assert stats1.total_games == 1
    assert stats1.total_rounds == 4
    assert stats1.spy_rounds_count == 1
    assert stats1.civilian_rounds_count == 3
    assert 0.0 <= stats1.overall_win_rate <= 1.0
    assert 0.0 <= stats1.spy_win_rate <= 1.0
    assert 0.0 <= stats1.civilian_win_rate <= 1.0
    
    # Alice (spy) was caught, so spy_win_rate should be 0.0
    assert stats1.spy_win_rate == 0.0
    
    # Bob initiated successful vote, should have good civilian performance
    assert stats1.civilian_success_rate > 0.0
    
    # Validate test-model-2 statistics
    stats2 = statistics["test-model-2"]
    assert stats2.total_games == 1
    assert stats2.total_rounds == 4
    assert stats2.spy_rounds_count == 1
    assert stats2.civilian_rounds_count == 3
    
    # Charlie (spy) guessed correctly, so spy_win_rate should be 1.0
    assert stats2.spy_win_rate == 1.0
    assert stats2.spy_guess_accuracy == 1.0
    assert stats2.successful_spy_guesses == 1
    assert stats2.total_spy_guesses == 1
    
    # Round ending statistics
    assert stats1.rounds_ended_by_vote == 1
    assert stats1.rounds_ended_by_spy_guess == 1
    assert stats2.rounds_ended_by_vote == 1
    assert stats2.rounds_ended_by_spy_guess == 1
    
    # Step 4: Generate reports
    generator = ReportGenerator()
    
    # Test text report
    text_report = generator.generate_text_report(statistics)
    assert len(text_report) > 0, "Text report should not be empty"
    assert "test-model-1" in text_report
    assert "test-model-2" in text_report
    
    # Test JSON report
    json_report = generator.generate_json_report(statistics)
    assert len(json_report) > 0, "JSON report should not be empty"
    parsed_json = json.loads(json_report)
    assert len(parsed_json) == 2
    assert "test-model-1" in parsed_json
    assert "test-model-2" in parsed_json
    
    # Test CSV report
    csv_report = generator.generate_csv_report(statistics)
    assert len(csv_report) > 0, "CSV report should not be empty"
    csv_lines = csv_report.strip().split('\n')
    assert len(csv_lines) == 3, "CSV should have header + 2 model rows"
    
    # Validate CSV contains model names
    assert "test-model-1" in csv_report
    assert "test-model-2" in csv_report


def test_e2e_parse_directory_with_sample():
    """
    Test parsing a directory containing the sample log file.
    """
    # Setup: Use directory containing sample log
    sample_dir = Path(__file__).parent
    
    # Parse directory
    parser = LogParser()
    games = parser.parse_directory(str(sample_dir))
    
    # Should find at least the sample_log.json file
    assert len(games) >= 1, "Should parse at least the sample log"
    
    # Find the sample game
    sample_game = next((g for g in games if g.game_id == "test_game_001"), None)
    assert sample_game is not None, "Should find sample game in parsed results"
    assert len(sample_game.rounds) == 2
```

**Test Data Requirements:**

The E2E test requires:
1. A `sample_log.json` file in `tests/e2e/` directory
2. The sample log should contain:
   - 2 different models
   - 2 rounds with different ending conditions (vote and spy_guess)
   - Known, predictable outcomes for validation
   - Both successful and unsuccessful spy scenarios
   - Turn data in at least one round

**E2E Test Execution:**

```bash
# Run E2E test
poetry run pytest tests/e2e/test_analytics_e2e.py -v

# Run specific E2E test function
poetry run pytest tests/e2e/test_analytics_e2e.py::test_full_pipeline_with_sample_log -v
```

### Test Execution

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/analytics --cov-report=html

# Run only unit tests
poetry run pytest tests/analytics -k "not property"

# Run only property tests
poetry run pytest tests/analytics -k "property"

# Run specific test file
poetry run pytest tests/analytics/test_log_parser.py
```

## Implementation Notes

### Performance Considerations

- **Lazy Loading**: Don't load all files into memory at once
- **Streaming**: Process files one at a time
- **Caching**: Cache parsed results if analyzing same directory multiple times
- **Parallel Processing**: Consider using multiprocessing for large log directories (future enhancement)

### Extensibility

- **Plugin Architecture**: New metrics can be added by extending StatisticsCalculator
- **Custom Aggregators**: Support custom aggregation strategies
- **Output Formats**: Easy to add new report formats (e.g., HTML, Markdown)

### Dependencies

- **Standard Library**: json, pathlib, dataclasses, statistics, argparse
- **Testing**: pytest, hypothesis
- **Logging**: loguru (already used in project)
- **Type Checking**: mypy (already used in project)

### Command-Line Interface

```bash
# Basic usage (defaults to ./logs, text output to stdout)
python analyze_logs.py

# Specify logs directory
python analyze_logs.py --logs-dir ./my_logs

# Output to JSON file
python analyze_logs.py --format json --output stats.json

# Output to CSV file
python analyze_logs.py --format csv --output stats.csv

# Show help
python analyze_logs.py --help
```

### File Structure

```
src/
  analytics/
    __init__.py
    log_parser.py          # LogParser class
    data_aggregator.py     # DataAggregator class
    statistics_calculator.py  # StatisticsCalculator class
    report_generator.py    # ReportGenerator class
    models.py              # Data models (GameRecord, ModelStatistics, etc.)
    
analyze_logs.py            # CLI entry point

tests/
  analytics/
    test_log_parser.py
    test_data_aggregator.py
    test_statistics_calculator.py
    test_report_generator.py
    test_models.py
  e2e/
    test_analytics_e2e.py  # End-to-end integration test
    sample_log.json        # Sample game log for E2E testing
```
