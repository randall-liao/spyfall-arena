# Implementation Plan

- [ ] 1. Set up project structure and dependencies
  - Initialize Poetry project with Python 3.10+
  - Configure pyproject.toml with all dependencies (pyyaml, pydantic, loguru, httpx, pytest, pytest-cov, mypy, black, isort)
  - Create directory structure for spyfall_arena package
  - Set up .env.example file with OPENROUTER_API_KEY placeholder
  - Configure .gitignore to exclude .env, logs/, and other sensitive files
  - Create pytest.ini with 100% coverage requirement
  - Create mypy.ini for type checking configuration
  - _Requirements: 1.1, 9.1, 12.1_

- [ ] 2. Implement configuration management
  - [ ] 2.1 Create configuration data models
    - Define Pydantic models for GameConfig, PlayerConfig, LoggingConfig
    - Implement validation rules for all configuration fields
    - Define default values for optional parameters
    - Write unit tests for configuration models (all validation branches)
    - _Requirements: 1.1, 1.2, 1.4_

  - [ ] 2.2 Implement configuration loader
    - Create ConfigLoader class to read YAML files
    - Implement error handling for missing/malformed config files
    - Add environment variable loading with python-dotenv
    - Implement Singleton pattern for config management
    - Write unit tests for config loading (success and error cases)
    - _Requirements: 1.1, 1.2, 1.5_

- [ ] 3. Implement game state management with state machine pattern
  - [ ] 3.1 Create state enums and data classes
    - Define GamePhase and RoundPhase enums
    - Create GameState dataclass with state transition methods
    - Create RoundState dataclass with state transition methods
    - Define Turn, Role, VoteAttempt, SpyGuess, GameError dataclasses
    - _Requirements: 2.6, 3.7, 4.8, 5.1, 5.4, 5.5, 5.6, 5.7_

  - [ ] 3.2 Implement state transition logic
    - Implement transition_to() method for GameState
    - Implement transition_to() method for RoundState
    - Define valid state transition rules
    - Write unit tests for all valid transitions
    - Write unit tests for all invalid transitions (should fail)
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 4. Implement LLM client with Factory and Template Method patterns
  - [ ] 4.1 Create base LLM client interface
    - Define BaseLLMClient abstract class with Template Method pattern
    - Implement generate_response() template method
    - Implement generate_structured_response() template method
    - Define abstract hook methods (_make_api_call, _extract_text, etc.)
    - _Requirements: 9.1_

  - [ ] 4.2 Implement OpenRouter client
    - Create OpenRouterClient class extending BaseLLMClient
    - Implement _make_api_call() using httpx
    - Implement response parsing methods
    - Add retry logic with exponential backoff
    - Write unit tests with mocked API responses
    - Write unit tests for error handling (timeouts, invalid responses)
    - _Requirements: 9.1, 9.2, 9.6, 9.7_

  - [ ] 4.3 Implement LLM client factory
    - Create LLMClientFactory with Singleton pattern
    - Implement create_client() factory method
    - Add API key validation
    - Write unit tests for client creation
    - _Requirements: 9.1_

- [ ] 5. Implement role assignment system
  - [ ] 5.1 Create RoleAssigner class
    - Implement assign_roles() method with random seed support
    - Ensure exactly one spy is assigned per round
    - Implement location assignment (civilians get location, spy gets None)
    - Write unit tests for reproducibility with same seed
    - Write unit tests for role distribution correctness
    - Write unit tests for edge cases (minimum/maximum players)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.7, 11.2_

- [ ] 6. Implement prompt building system
  - [ ] 6.1 Create prompt templates
    - Write system_prompt.txt template
    - Write civilian_role.txt template
    - Write spy_role.txt template
    - Define template variables and placeholders
    - _Requirements: 3.5_

  - [ ] 6.2 Implement PromptBuilder class
    - Create PromptBuilder with Builder pattern
    - Implement build_role_prompt() method
    - Implement build_question_prompt() method
    - Implement build_answer_prompt() method
    - Implement build_vote_initiation_prompt() method
    - Implement build_vote_decision_prompt() method
    - Implement build_spy_guess_prompt() method
    - Write unit tests for all prompt building methods
    - Write unit tests for variable substitution
    - _Requirements: 3.5, 3.6_

- [ ] 7. Implement turn management system
  - [ ] 7.1 Create TurnManager class
    - Implement execute_turn() method for Q&A flow
    - Implement get_next_asker() method with turn rotation
    - Implement get_valid_targets() method enforcing no-retaliation rule
    - Integrate with LLM client for question and answer generation
    - Write unit tests for no-retaliation rule enforcement
    - Write unit tests for valid target selection
    - Write unit tests for turn rotation logic
    - Write unit tests for edge cases (2 players, many players)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.7_

- [ ] 8. Implement voting system
  - [ ] 8.1 Create VotingManager class
    - Implement check_for_vote_initiation() method
    - Implement conduct_vote() method for collecting votes
    - Enforce unanimous voting requirement
    - Track players who have initiated votes (one per round)
    - Integrate with LLM client for vote decisions
    - Write unit tests for unanimous vote requirement
    - Write unit tests for one-vote-per-player rule
    - Write unit tests for all voting outcomes
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

- [ ] 9. Implement spy guess mechanism
  - [ ] 9.1 Create SpyGuessManager class
    - Implement check_spy_guess() method
    - Integrate with LLM client for spy's location guess
    - Validate guess against actual location
    - Write unit tests for correct and incorrect guesses
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 10. Implement scoring system
  - [ ] 10.1 Create ScoringEngine class
    - Implement calculate_round_scores() method
    - Implement spy not indicted scoring (2 points)
    - Implement wrong person indicted scoring (4 points to spy)
    - Implement spy correct guess scoring (4 points to spy)
    - Implement spy indicted scoring (1 point to civilians, 2 to initiator)
    - Write unit tests for all scoring scenarios
    - Write unit tests for point accumulation across rounds
    - Write unit tests for winner determination
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_

- [ ] 11. Implement game orchestrator
  - [ ] 11.1 Create GameOrchestrator class
    - Implement run_game() method for multi-round games
    - Implement run_round() method for single round execution
    - Integrate RoleAssigner for role assignment phase
    - Integrate TurnManager for questioning phase
    - Integrate VotingManager for vote handling
    - Integrate SpyGuessManager for spy guess handling
    - Integrate ScoringEngine for scoring phase
    - Implement _check_ending_conditions() method
    - Implement state transitions using state machine
    - Write integration tests for complete game flow
    - Write integration tests for all ending conditions
    - _Requirements: 3.8, 6.1, 6.2, 6.3, 6.4, 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 12. Implement logging and metrics
  - [ ] 12.1 Set up Loguru configuration
    - Configure Loguru in GameLogger.__init__()
    - Set up log file rotation and retention
    - Configure log levels from config
    - Write unit tests for Loguru setup
    - _Requirements: 5.1, 5.8, 5.10_

  - [ ] 12.2 Implement GameLogger class
    - Implement write_final_log() method
    - Implement _build_log_structure() method
    - Implement _serialize_config() helper method
    - Implement _serialize_round() helper method
    - Ensure JSON output follows documented schema
    - Write unit tests for log structure generation
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12, 10.1, 10.2, 10.3, 10.4_

  - [ ] 12.3 Implement MetricsCalculator class
    - Implement calculate_round_metrics() method
    - Implement calculate_game_metrics() method
    - Calculate win rates, vote accuracy, response statistics
    - Write unit tests for all metric calculations
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ] 13. Implement error handling
  - [ ] 13.1 Add error handling to LLM client
    - Implement retry logic with exponential backoff
    - Handle API timeouts and failures
    - Log errors using Loguru
    - Write unit tests for all error scenarios
    - _Requirements: 9.1, 9.2, 9.6, 9.7_

  - [ ] 13.2 Add error handling to game orchestrator
    - Catch and log LLM failures during turns
    - Skip turns on repeated failures
    - Continue game when possible
    - Produce partial logs on critical failures
    - Set appropriate game status (success/partial success/error)
    - Write integration tests for error recovery
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ] 14. Create main entry point
  - [ ] 14.1 Implement game_runner.py
    - Create main() function to load config
    - Initialize GameOrchestrator with dependencies
    - Run game and handle exceptions
    - Write final log on completion
    - Add command-line argument parsing (optional config path)
    - Write integration test for end-to-end execution
    - _Requirements: 12.1, 12.2, 12.4, 12.5_

- [ ] 15. Create example configuration and documentation
  - [ ] 15.1 Create example config.yaml
    - Include all required configuration sections
    - Add comments explaining each parameter
    - Provide sensible defaults
    - Include multiple player configurations
    - _Requirements: 1.1, 1.2_

  - [ ] 15.2 Create .env.example
    - Document OPENROUTER_API_KEY variable
    - Add usage instructions
    - _Requirements: 1.1_

  - [ ] 15.3 Update README.md
    - Add installation instructions using Poetry
    - Document configuration options
    - Provide usage examples
    - Explain log output format
    - Add development setup instructions
    - _Requirements: 12.1_

- [ ] 16. Achieve 100% test coverage
  - [ ] 16.1 Run coverage report and identify gaps
    - Execute pytest with coverage
    - Generate HTML coverage report
    - Identify uncovered lines
    - _Requirements: 12.3_

  - [ ] 16.2 Write additional tests for uncovered code
    - Add tests for edge cases
    - Add tests for error paths
    - Add tests for all branches
    - Verify 100% coverage achieved
    - _Requirements: 12.3, 12.4_

- [ ] 17. Final integration and validation
  - [ ] 17.1 Run complete game with real LLM API
    - Set up OpenRouter API key
    - Run game with multiple models
    - Verify log output is correct
    - Validate metrics calculation
    - _Requirements: 12.1, 12.5_

  - [ ] 17.2 Validate reproducibility
    - Run same config with same seed multiple times
    - Verify identical outcomes
    - Document any non-deterministic behavior
    - _Requirements: 1.3, 12.5_

  - [ ] 17.3 Code quality checks
    - Run mypy for type checking
    - Run black for code formatting
    - Run isort for import sorting
    - Fix any issues found
    - _Requirements: 12.1_
