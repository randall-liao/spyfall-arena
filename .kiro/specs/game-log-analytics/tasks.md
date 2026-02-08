# Implementation Plan: Game Log Analytics

## Overview

This implementation plan breaks down the game log analytics system into discrete, incremental tasks. Each task builds on previous work, with testing integrated throughout to catch errors early. The implementation follows a bottom-up approach: data models → parsing → aggregation → calculation → reporting → CLI.

## Tasks

- [ ] 1. Set up project structure and data models
  - Create `src/analytics/` directory and `__init__.py`
  - Define data models in `src/analytics/models.py` (GameRecord, RoundRecord, ModelData, ModelStatistics)
  - Add type hints and dataclass decorators
  - _Requirements: 1.1, 1.2, 2.1_

- [ ]* 1.1 Write unit tests for data models
  - Test dataclass instantiation and field validation
  - Test optional fields with None values
  - _Requirements: 1.1, 1.2_

- [ ] 2. Implement log parser
  - [ ] 2.1 Create `src/analytics/log_parser.py` with LogParser class
    - Implement `parse_file()` method to parse single JSON file
    - Implement `parse_directory()` method to scan and parse all JSON files
    - Add error handling for malformed JSON and missing fields
    - Use loguru for logging errors
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [ ]* 2.2 Write unit tests for log parser
    - Test parsing valid game logs
    - Test handling malformed JSON
    - Test handling missing required fields
    - Test parsing directory with multiple files
    - Test ignoring non-JSON files
    - _Requirements: 1.1, 1.2, 1.3, 9.1_

  - [ ]* 2.3 Write property test for parse-serialize round trip
    - **Property 1: Parse then serialize preserves structure**
    - **Validates: Requirements 1.2, 1.4**

- [ ] 3. Checkpoint - Ensure parser tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement data aggregator
  - [ ] 4.1 Create `src/analytics/data_aggregator.py` with DataAggregator class
    - Implement `aggregate_by_model()` method to group game data by model_name
    - Separate spy rounds from civilian rounds
    - Collect votes, turns, and scores for each model
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 4.2 Write unit tests for data aggregator
    - Test aggregating single model across multiple games
    - Test aggregating multiple different models
    - Test separating spy vs civilian rounds
    - Test handling empty game list
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 4.3 Write property test for statistics component sums
    - **Property 2: Statistics sum to totals**
    - **Validates: Requirements 2.3, 2.4, 2.5**

- [ ] 5. Implement statistics calculator - basic metrics
  - [ ] 5.1 Create `src/analytics/statistics_calculator.py` with StatisticsCalculator class
    - Implement `calculate_model_statistics()` for single model
    - Calculate basic counts (total_games, total_rounds, spy_rounds_count, civilian_rounds_count)
    - Calculate win rates (overall, spy, civilian)
    - Calculate average scores and score distribution
    - Handle division by zero (return 0.0)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 15.1, 15.2, 15.3, 15.4, 15.5_

  - [ ]* 5.2 Write unit tests for basic statistics
    - Test win rate calculations
    - Test average score calculations
    - Test score distribution
    - Test handling zero games/rounds
    - Test division by zero returns 0.0
    - _Requirements: 3.1, 3.2, 3.3, 15.1, 15.2, 15.3, 15.4_

  - [ ]* 5.3 Write property tests for win rates and percentages
    - **Property 3: Win rates are bounded**
    - **Property 7: Percentage calculations are bounded**
    - **Validates: Requirements 3.1, 3.2, 3.3, 4.1, 5.1, 6.1, 12.4**

- [ ] 6. Implement statistics calculator - voting metrics
  - [ ] 6.1 Add voting statistics to StatisticsCalculator
    - Calculate voting accuracy
    - Track votes initiated and success rate
    - Track times suspected
    - Calculate yes vote percentage
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ]* 6.2 Write unit tests for voting statistics
    - Test voting accuracy calculation
    - Test vote initiation tracking
    - Test times suspected tracking
    - Test yes/no vote percentage
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 12.1, 12.2, 12.3, 12.4_

  - [ ]* 6.3 Write property test for vote count constraints
    - **Property 5: Vote counts are consistent**
    - **Validates: Requirements 12.1, 12.2**

- [ ] 7. Implement statistics calculator - spy and civilian metrics
  - [ ] 7.1 Add spy performance metrics to StatisticsCalculator
    - Calculate spy survival rate
    - Calculate spy guess accuracy
    - Track successful and total spy guesses
    - Calculate average spy score
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [ ] 7.2 Add civilian performance metrics to StatisticsCalculator
    - Calculate civilian success rate
    - Calculate average civilian score
    - Track correct spy votes
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 7.3 Write unit tests for spy and civilian metrics
    - Test spy survival rate
    - Test spy guess accuracy
    - Test civilian success rate
    - Test handling zero spy/civilian rounds
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2, 10.6_

  - [ ]* 7.4 Write property test for spy guess accuracy formula
    - **Property 6: Spy guess accuracy is valid**
    - **Validates: Requirements 10.6**

- [ ] 8. Implement statistics calculator - turn and round ending metrics
  - [ ] 8.1 Add turn engagement metrics to StatisticsCalculator
    - Track questions asked and answered
    - Calculate average turns per round
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ] 8.2 Add round ending statistics to StatisticsCalculator
    - Track rounds ended by vote, spy_guess, timeout
    - Calculate ending condition percentages
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 8.3 Implement `calculate_all_statistics()` method
    - Iterate over all models in aggregated data
    - Call `calculate_model_statistics()` for each
    - Return dictionary of ModelStatistics
    - _Requirements: 2.1, 2.2_

  - [ ]* 8.4 Write unit tests for turn and round ending metrics
    - Test questions asked/answered tracking
    - Test average turns calculation
    - Test round ending condition tracking
    - Test handling missing turn data
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 10.1, 10.2, 10.3_

  - [ ]* 8.5 Write property tests for empty input and score distribution
    - **Property 4: Score distribution sums correctly**
    - **Property 8: Empty input produces empty output**
    - **Validates: Requirements 15.4, 9.2**

- [ ] 9. Checkpoint - Ensure statistics calculator tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement report generator - text format
  - [ ] 10.1 Create `src/analytics/report_generator.py` with ReportGenerator class
    - Implement `generate_text_report()` method
    - Sort models by win rate descending
    - Format percentages to 2 decimal places
    - Include summary statistics
    - Create leaderboards for key metrics
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 14.1, 14.2, 14.3, 14.4, 14.5_

  - [ ]* 10.2 Write unit tests for text report generation
    - Test report formatting
    - Test model sorting by win rate
    - Test percentage formatting
    - Test leaderboard generation
    - Test handling empty statistics
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 14.1, 14.2, 14.3, 14.4_

- [ ] 11. Implement report generator - JSON and CSV formats
  - [ ] 11.1 Add JSON report generation to ReportGenerator
    - Implement `generate_json_report()` method
    - Serialize ModelStatistics to JSON
    - Ensure all metrics included
    - _Requirements: 8.1, 8.3_

  - [ ] 11.2 Add CSV report generation to ReportGenerator
    - Implement `generate_csv_report()` method
    - Create header row with all metric names
    - Create one row per model
    - Format as valid CSV
    - _Requirements: 8.2, 8.4_

  - [ ]* 11.3 Write unit tests for JSON and CSV reports
    - Test JSON report is valid and parseable
    - Test JSON includes all statistics
    - Test CSV has correct headers
    - Test CSV has one row per model
    - Test CSV is parseable
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 11.4 Write property test for report determinism
    - **Property 10: Report generation is deterministic**
    - **Validates: Requirements 7.1, 7.2, 8.3**

- [ ] 12. Implement command-line interface
  - [ ] 12.1 Create `analyze_logs.py` CLI script
    - Use argparse for command-line arguments
    - Accept --logs-dir argument (default: ./logs)
    - Accept --format argument (text, json, csv, default: text)
    - Accept --output argument (optional file path, default: stdout)
    - Implement --help flag
    - Wire together all components: parse → aggregate → calculate → report
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6_

  - [ ]* 12.2 Write unit tests for CLI argument parsing
    - Test default arguments
    - Test custom logs directory
    - Test output format selection
    - Test output file specification
    - Test help message
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6_

- [ ] 13. Create E2E test with sample log
  - [ ] 13.1 Create `tests/e2e/sample_log.json` with known test data
    - Include 2 different models
    - Include 2 rounds with different ending conditions
    - Include known, predictable outcomes
    - Include turn data in at least one round
    - _Requirements: All_

  - [ ] 13.2 Create `tests/e2e/test_analytics_e2e.py`
    - Implement `test_full_pipeline_with_sample_log()`
    - Test complete pipeline: parse → aggregate → calculate → report
    - Validate all statistics match expected values from sample log
    - Test all three report formats (text, JSON, CSV)
    - Implement `test_e2e_parse_directory_with_sample()`
    - _Requirements: All_

- [ ] 14. Final checkpoint - Run all tests and verify 100% coverage
  - Run `poetry run pytest` to execute all tests
  - Run `poetry run pytest --cov=src/analytics --cov-report=html` to check coverage
  - Verify 100% line coverage achieved
  - Fix any failing tests or coverage gaps
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Add location-based performance metrics (optional enhancement)
  - [ ] 15.1 Add `aggregate_by_location()` method to DataAggregator
    - Group rounds by location
    - Track wins/losses per location per model
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [ ] 15.2 Add location statistics to StatisticsCalculator
    - Calculate win rates per location
    - Identify best/worst locations for each model
    - _Requirements: 13.1, 13.2, 13.3_

  - [ ]* 15.3 Write unit tests for location-based metrics
    - Test location aggregation
    - Test location-specific win rates
    - _Requirements: 13.1, 13.2, 13.3_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- E2E test validates the complete pipeline with real data
- 100% line coverage is required for all production code
