# Technical Context

## Development Setup

### Language & Runtime
-   **Python**: Version 3.12+ required.

### Dependency Management
-   **Poetry**: Used for dependency resolution and virtual environment management.
    -   `pyproject.toml`: Defines dependencies and tool configurations.
    -   `poetry.lock`: Ensures reproducible builds.

### Testing Framework
-   **Pytest**: Main test runner.
-   **Pytest-cov**: For coverage reporting.
-   **Mocks**: `unittest.mock` is heavily used to isolate components (especially LLM API calls).

### Code Quality Tools
-   **Black**: Code formatter.
-   **Isort**: Import sorter.
-   **Mypy**: Static type checker (strict mode enabled).

## Key Dependencies
-   **Pydantic** (`pydantic`): Data validation and settings management.
-   **Loguru** (`loguru`): Simplified and powerful logging.
-   **OpenAI SDK** (`openai`): Client for OpenRouter/OpenAI models.
-   **Google GenAI SDK** (`google-genai`): Client for Gemini models.
-   **PyYAML** (`pyyaml`): Parsing configuration files.
-   **Keyring** (`keyring`): Secure credential storage.

## Technical Constraints
-   **Backend Only**: No UI libraries or web frameworks (like Flask/FastAPI) are used/needed.
-   **API Limits**: dependent on the providers (OpenRouter, Google).
-   **Latency**: Game speed is limited by LLM inference time.
