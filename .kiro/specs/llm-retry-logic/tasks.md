# Implementation Plan: LLM Retry Logic

## Overview

This plan implements configurable LLM retry logic using TDD. Tests are written first for each component, then implementation follows.

## Tasks

- [x] 1. Add tenacity dependency
  - [x] 1.1 Update pyproject.toml
    - Add `tenacity = "^8.2.0"` to dependencies
    - Run `poetry install` to install
    - _Requirements: 3.2_

- [x] 2. Implement LLMConfig schema (TDD)
  - [x] 2.1 Write tests for LLMConfig validation
    - Test default values (max_retries=2, retry_min_wait=1.0, retry_max_wait=10.0)
    - Test valid values within bounds
    - Test validation errors for out-of-bounds values
    - Test max_retries bounds (0-10)
    - Test retry_min_wait bounds (0.1-60.0)
    - Test retry_max_wait bounds (1.0-300.0)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [x] 2.2 Write tests for GameConfig with llm field
    - Test GameConfig accepts llm field
    - Test GameConfig uses default LLMConfig when not specified
    - _Requirements: 1.1_

  - [x] 2.3 Implement LLMConfig class
    - Add LLMConfig to config_schema.py
    - Add llm field to GameConfig
    - Run tests to verify they pass
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [x] 3. Checkpoint - Verify config schema
  - Run config tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Update OpenAIClient with retry (TDD)
  - [x] 4.1 Write tests for OpenAIClient max_retries parameter
    - Test __init__ accepts max_retries parameter
    - Test max_retries is passed to OpenAI SDK client
    - Test default max_retries value
    - _Requirements: 2.1, 2.2_

  - [x] 4.2 Implement OpenAIClient retry parameter
    - Add max_retries parameter to __init__
    - Pass max_retries to OpenAI() constructor
    - Run tests to verify they pass
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 5. Update GeminiClient with retry (TDD)
  - [x] 5.1 Write tests for GeminiClient retry parameters
    - Test __init__ accepts max_retries, retry_min_wait, retry_max_wait
    - Test default values for retry parameters
    - _Requirements: 3.1_

  - [x] 5.2 Write tests for GeminiClient retry behavior
    - Mock API to raise ServiceUnavailable
    - Verify retry is attempted
    - Mock API to raise ResourceExhausted
    - Verify retry is attempted
    - Test error is raised after max retries exhausted
    - _Requirements: 3.2, 3.3, 3.4, 3.5_

  - [x] 5.3 Implement GeminiClient retry logic
    - Add retry parameters to __init__
    - Refactor _make_api_call to use tenacity decorator
    - Create _make_api_call_impl for actual API call
    - Configure tenacity with retry settings
    - Run tests to verify they pass
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 6. Checkpoint - Verify client retry
  - Run all client tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Update LLMClientFactory (TDD)
  - [x] 7.1 Write tests for factory with LLMConfig
    - Test factory accepts llm_config parameter
    - Test factory uses default LLMConfig when not provided
    - _Requirements: 4.1, 4.4_

  - [x] 7.2 Write tests for factory passing retry config
    - Test OpenAI client receives max_retries from config
    - Test Gemini client receives all retry settings from config
    - _Requirements: 4.2, 4.3_

  - [x] 7.3 Implement factory LLMConfig integration
    - Add llm_config parameter to __init__
    - Pass retry settings when creating OpenAI client
    - Pass retry settings when creating Gemini client
    - Run tests to verify they pass
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 8. Update config.yaml with llm section
  - [x] 8.1 Add llm section to config.yaml
    - Add example llm section with default values
    - Add comments explaining each parameter
    - _Requirements: 1.1_

- [x] 9. Final checkpoint - All retry tests
  - Run complete LLM test suite
  - Verify all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Follow TDD: Write tests first (Red), implement to pass (Green), refactor
- OpenAI SDK has built-in retry - we just configure it
- Gemini client uses tenacity for equivalent behavior
- All tasks are required for comprehensive testing
- Each task references specific requirements for traceability
