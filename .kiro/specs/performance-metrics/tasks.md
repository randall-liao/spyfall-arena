# Implementation Plan: Performance Metrics

## Overview

This plan implements the MetricsCalculator component using TDD (Test-Driven Development). Tests are written first, then implementation follows to make tests pass.

## Tasks

- [x] 1. Create test file and data model tests (TDD - Red Phase)
  - [x] 1.1 Create test file structure
    - Create `tests/game_logging/test_metrics_calculator.py`
    - Create `tests/game_logging/test_metrics_properties.py`
    - Add necessary imports and test fixtures
    - _Requirements: 1.1, 2.1_

  - [x] 1.2 Write unit tests for RoundMetrics dataclass
    - Test dataclass instantiation with all fields
    - Test default values and optional fields
    - Test serialization to dict with asdict()
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 1.3 Write unit tests for GameMetrics dataclass
    - Test dataclass instantiation with all fields
    - Test serialization to dict with asdict()
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. Implement data models (TDD - Green Phase)
  - [x] 2.1 Create metrics_calculator.py with dataclasses
    - Create `src/game_logging/metrics_calculator.py`
    - Implement RoundMetrics dataclass
    - Implement GameMetrics dataclass
    - Run tests to verify they pass
    - _Requirements: 1.1, 2.1_

- [x] 3. Write tests for calculate_round_metrics (TDD - Red Phase)
  - [x] 3.1 Write unit tests for winner determination
    - Test spy wins when not caught (turn limit reached)
    - Test spy wins when wrong person indicted
    - Test spy wins when correctly guesses location
    - Test civilians win when spy is caught
    - _Requirements: 1.1, 1.3_

  - [x] 3.2 Write unit tests for vote accuracy
    - Test vote accuracy with all civilians voting correctly
    - Test vote accuracy with mixed votes
    - Test vote accuracy returns None when no successful vote
    - _Requirements: 1.2_

  - [x] 3.3 Write unit tests for response statistics
    - Test total_turns equals conversation history length
    - Test avg_question_length calculation
    - Test avg_answer_length calculation
    - Test returns 0.0 for averages when no turns
    - _Requirements: 1.4, 1.5, 1.6_

  - [x] 3.4 Write property test for round outcome determination
    - **Property 1: Round outcome determination**
    - Use Hypothesis to generate random RoundState
    - Verify winner_side and spy_caught are consistent
    - **Validates: Requirements 1.1, 1.3**

  - [x] 3.5 Write property test for vote accuracy
    - **Property 2: Vote accuracy calculation**
    - Generate rounds with various vote configurations
    - Verify vote_accuracy is in range [0.0, 1.0] or None
    - **Validates: Requirements 1.2**

  - [x] 3.6 Write property test for response statistics
    - **Property 3: Response statistics calculation**
    - Generate rounds with various turn counts
    - Verify total_turns matches list length
    - Verify averages are non-negative
    - **Validates: Requirements 1.4, 1.5**

- [x] 4. Implement calculate_round_metrics (TDD - Green Phase)
  - [x] 4.1 Implement winner determination logic
    - Determine winner_side based on ending condition
    - Set spy_caught flag based on successful indictment
    - Set spy_guessed_correctly based on spy guess result
    - _Requirements: 1.1, 1.3_

  - [x] 4.2 Implement vote accuracy calculation
    - Find successful vote attempt (if any)
    - Count civilians who voted yes on spy
    - Calculate percentage, return None if no successful vote
    - _Requirements: 1.2, 1.7_

  - [x] 4.3 Implement response statistics calculation
    - Count total turns from conversation history
    - Calculate average question and answer lengths
    - Handle edge case of empty conversation history
    - _Requirements: 1.4, 1.5, 1.6_

- [x] 5. Checkpoint - Verify round metrics
  - Run all round metrics tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Write tests for calculate_game_metrics (TDD - Red Phase)
  - [x] 6.1 Write unit tests for win counting
    - Test spy_wins and civilian_wins sum to total rounds
    - Test correct counting with mixed outcomes
    - _Requirements: 2.2_

  - [x] 6.2 Write unit tests for average turns
    - Test avg_turns_per_round calculation
    - Test with varying turn counts per round
    - _Requirements: 2.3_

  - [x] 6.3 Write unit tests for overall winner
    - Test winner is player with highest score
    - Test alphabetical tiebreaker
    - _Requirements: 2.4, 2.5_

  - [x] 6.4 Write property test for aggregate metrics
    - **Property 4: Aggregate metrics calculation**
    - Generate multi-round games with Hypothesis
    - Verify spy_wins + civilian_wins = total_rounds
    - Verify overall_winner has highest score
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [x] 7. Implement calculate_game_metrics (TDD - Green Phase)
  - [x] 7.1 Implement win counting
    - Count rounds where winner_side is "spy" or "civilians"
    - _Requirements: 2.2_

  - [x] 7.2 Implement average turns calculation
    - Sum total_turns from all round metrics
    - Divide by number of rounds
    - _Requirements: 2.3_

  - [x] 7.3 Implement overall winner determination
    - Find player with highest score
    - Use alphabetical order for tiebreaker
    - _Requirements: 2.4, 2.5_

- [x] 8. Checkpoint - Verify game metrics
  - Run all game metrics tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Integrate metrics into GameLogger (TDD)
  - [x] 9.1 Write tests for GameLogger metrics integration
    - Test log output includes round metrics
    - Test log output includes game_metrics field
    - Test _serialize_round_with_metrics helper
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 9.2 Update GameLogger implementation
    - Add MetricsCalculator instance
    - Update _build_log_structure to compute metrics
    - Add _serialize_round_with_metrics helper
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 9.3 Export MetricsCalculator from module
    - Update `src/game_logging/__init__.py`
    - _Requirements: 3.1_

- [x] 10. Final checkpoint - All metrics tests
  - Run complete metrics test suite
  - Verify all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Follow TDD: Write tests first (Red), implement to pass (Green), refactor
- Property tests use Hypothesis library for random input generation
- All tasks are required for comprehensive testing
- Each task references specific requirements for traceability
