# Design Document

## Overview

This design adds configurable retry logic to the LLM client layer. The OpenAI client leverages the SDK's built-in retry mechanism, while the Gemini client uses the tenacity library for equivalent behavior. All settings are configurable via the YAML config file.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      config.yaml                             │
│                          │                                   │
│                          ▼                                   │
│                      LLMConfig                               │
│           (max_retries, retry_min_wait, retry_max_wait)      │
│                          │                                   │
│                          ▼                                   │
│                  LLMClientFactory                            │
│                    │         │                               │
│                    ▼         ▼                               │
│            OpenAIClient   GeminiClient                       │
│           (SDK retry)    (tenacity retry)                    │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. LLMConfig Schema

**Module**: `src/config/config_schema.py`

```python
class LLMConfig(BaseModel):
    """Configuration for LLM API behavior."""
    max_retries: int = Field(default=2, ge=0, le=10)
    retry_min_wait: float = Field(default=1.0, ge=0.1, le=60.0)
    retry_max_wait: float = Field(default=10.0, ge=1.0, le=300.0)

class GameConfig(BaseModel):
    game: GameRulesConfig = Field(default_factory=GameRulesConfig)
    players: List[PlayerConfig] = Field(..., min_length=2, max_length=12)
    locations: List[str] = Field(..., min_length=1)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)  # New
```

### 2. Updated OpenAIClient

**Module**: `src/llm/openai_client.py`

```python
class OpenAIClient(BaseLLMClient):
    def __init__(
        self,
        model_name: str,
        api_key: str,
        temperature: float = 0.7,
        max_retries: int = 2,
    ):
        self.api_key = api_key
        self.max_retries = max_retries
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            max_retries=max_retries,
        )
        super().__init__(model_name, temperature)
```

### 3. Updated GeminiClient

**Module**: `src/llm/gemini_client.py`

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from google.api_core.exceptions import ServiceUnavailable, ResourceExhausted

class GeminiClient(BaseLLMClient):
    def __init__(
        self,
        model_name: str,
        api_key: str,
        temperature: float = 0.7,
        max_retries: int = 2,
        retry_min_wait: float = 1.0,
        retry_max_wait: float = 10.0,
    ):
        self.max_retries = max_retries
        self.retry_min_wait = retry_min_wait
        self.retry_max_wait = retry_max_wait
        # ... existing init code
        super().__init__(model_name, temperature)
    
    def _make_api_call(
        self, messages: list, temperature: float, response_format=None
    ) -> dict:
        """Makes API call with retry logic."""
        @retry(
            stop=stop_after_attempt(self.max_retries + 1),
            wait=wait_exponential(
                multiplier=1,
                min=self.retry_min_wait,
                max=self.retry_max_wait
            ),
            retry=retry_if_exception_type((ServiceUnavailable, ResourceExhausted)),
            reraise=True
        )
        def _call_with_retry():
            return self._make_api_call_impl(messages, temperature, response_format)
        
        return _call_with_retry()
    
    def _make_api_call_impl(
        self, messages: list, temperature: float, response_format=None
    ) -> dict:
        """Actual API call implementation."""
        # ... existing implementation
```

### 4. Updated LLMClientFactory

**Module**: `src/llm/llm_client_factory.py`

```python
from config.config_schema import LLMConfig, LLMProvider

class LLMClientFactory:
    def __init__(
        self,
        api_key_manager: ApiKeyManager,
        llm_config: LLMConfig = None
    ):
        self.api_key_manager = api_key_manager
        self.llm_config = llm_config or LLMConfig()
    
    def create_client(
        self,
        model_name: str,
        provider: LLMProvider,
        temperature: float = 0.7,
    ) -> BaseLLMClient:
        if provider == LLMProvider.OPEN_ROUTER:
            return OpenAIClient(
                model_name=model_name,
                api_key=self.api_key_manager.get_api_key(),
                temperature=temperature,
                max_retries=self.llm_config.max_retries,
            )
        elif provider == LLMProvider.GOOGLE_AI_STUDIO:
            return GeminiClient(
                model_name=model_name,
                api_key=self.api_key_manager.get_google_api_key(),
                temperature=temperature,
                max_retries=self.llm_config.max_retries,
                retry_min_wait=self.llm_config.retry_min_wait,
                retry_max_wait=self.llm_config.retry_max_wait,
            )
```

## Configuration Example

```yaml
llm:
  max_retries: 2        # Number of retry attempts (0 to disable)
  retry_min_wait: 1.0   # Minimum wait between retries (seconds)
  retry_max_wait: 10.0  # Maximum wait between retries (seconds)
```

## Error Handling

### Retryable Errors

**OpenAI SDK (automatic)**:
- Connection errors
- 408 Request Timeout
- 409 Conflict
- 429 Rate Limit
- 5xx Server Errors

**Gemini Client (tenacity)**:
- `google.api_core.exceptions.ServiceUnavailable`
- `google.api_core.exceptions.ResourceExhausted`

### Non-Retryable Errors

These errors propagate immediately:
- 400 Bad Request
- 401 Authentication Error
- 403 Permission Denied
- 404 Not Found

## Testing Strategy

### TDD Approach

1. Write tests for LLMConfig validation
2. Write tests for client retry parameters
3. Write tests for factory config passing
4. Implement to make tests pass

### Test Files

- `tests/config/test_config_schema.py` - LLMConfig validation tests
- `tests/llm/test_openai_client.py` - OpenAI retry tests
- `tests/llm/test_gemini_client.py` - Gemini retry tests
- `tests/llm/test_llm_client_factory.py` - Factory integration tests

### Dependencies

Add to `pyproject.toml`:
```toml
tenacity = "^8.2.0"
```
