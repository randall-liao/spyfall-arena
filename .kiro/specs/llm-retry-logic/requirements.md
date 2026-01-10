# Requirements Document

## Introduction

This spec implements configurable LLM retry logic for Spyfall Arena. The retry mechanism ensures temporary API failures don't cause unnecessary turn skips, with settings configurable via the YAML config file.

## Glossary

- **LLM_Config**: Configuration section for LLM API behavior including retry settings
- **Retryable_Error**: Errors that should trigger automatic retry (connection errors, timeouts, rate limits, server errors)
- **Exponential_Backoff**: Retry strategy where wait time increases exponentially between attempts

## Requirements

### Requirement 1: LLM Configuration Schema

**User Story:** As a system operator, I want to configure LLM retry behavior via the config file, so that I can tune settings for different environments.

#### Acceptance Criteria

1. WHEN the configuration is loaded THEN it SHALL accept an optional `llm` section with retry settings
2. WHEN `llm.max_retries` is specified THEN it SHALL be validated as an integer between 0 and 10
3. WHEN `llm.max_retries` is not specified THEN it SHALL default to 2
4. WHEN `llm.retry_min_wait` is specified THEN it SHALL be validated as a float between 0.1 and 60.0 seconds
5. WHEN `llm.retry_min_wait` is not specified THEN it SHALL default to 1.0 seconds
6. WHEN `llm.retry_max_wait` is specified THEN it SHALL be validated as a float between 1.0 and 300.0 seconds
7. WHEN `llm.retry_max_wait` is not specified THEN it SHALL default to 10.0 seconds

### Requirement 2: OpenAI Client Retry

**User Story:** As a system operator, I want the OpenAI client to automatically retry failed API calls, so that temporary issues don't cause turn failures.

#### Acceptance Criteria

1. WHEN the OpenAI_Client is initialized THEN it SHALL accept a max_retries parameter
2. WHEN the OpenAI_Client is initialized THEN it SHALL pass max_retries to the OpenAI SDK
3. WHEN an API call encounters a retryable error THEN the SDK SHALL automatically retry with exponential backoff
4. WHEN all retries are exhausted THEN the client SHALL raise the error for the orchestrator to handle

### Requirement 3: Gemini Client Retry

**User Story:** As a system operator, I want the Gemini client to have equivalent retry behavior, so that all LLM providers handle failures consistently.

#### Acceptance Criteria

1. WHEN the Gemini_Client is initialized THEN it SHALL accept max_retries, retry_min_wait, and retry_max_wait parameters
2. WHEN the Gemini_Client makes an API call THEN it SHALL use tenacity for retry logic
3. WHEN a ServiceUnavailable or ResourceExhausted error occurs THEN the client SHALL retry with exponential backoff
4. WHEN retry wait times are configured THEN the client SHALL use retry_min_wait and retry_max_wait for backoff bounds
5. WHEN all retries are exhausted THEN the client SHALL raise the error for the orchestrator to handle

### Requirement 4: LLM Client Factory Integration

**User Story:** As a developer, I want the factory to pass retry config to clients, so that configuration flows through the system correctly.

#### Acceptance Criteria

1. WHEN the LLMClientFactory is initialized THEN it SHALL accept an optional LLMConfig parameter
2. WHEN creating an OpenAI client THEN the factory SHALL pass max_retries from config
3. WHEN creating a Gemini client THEN the factory SHALL pass all retry settings from config
4. WHEN LLMConfig is not provided THEN the factory SHALL use default values
