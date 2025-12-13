# System Patterns

## Architecture
The project follows a modular **Source Layout** (`src/`) architecture.

### Directory Structure
-   `src/config`: Configuration loading (`config.yaml`), validation (Pydantic), and API key management (`ApiKeyManager`).
-   `src/game`: Core business logic.
    -   `GameRunner`: Orchestrates the game loop.
    -   `GameState`: Manages the state (players, roles, turns).
    -   `VoteManager`: Handles voting logic.
-   `src/llm`: Abstraction layer for LLM providers.
    -   `LLMClient`: Base interface.
    -   `OpenAIClient`: Adapter for OpenRouter/OpenAI.
    -   `GeminiClient`: Adapter for Google Gemini.
    -   `LLMClientFactory`: Instantiates the correct client based on model name.
-   `src/game_logging`: Custom logging module (renamed from `logging` to avoid stdlib conflict). Uses `loguru` for structured JSON output.
-   `src/prompts`: Manages prompt templates and construction.

## Key Technical Decisions

### 1. Configuration-Driven
Everything is defined in `config.yaml`. The application reads this at startup to instantiate the `GameState`.
**Pattern**: `ConfigLoader` reads YAML -> Pydantic Models -> Application Configuration.

### 2. Modularity & Dependency Injection
Components are designed to be testable in isolation.
**Pattern**: `LLMClient` is injected into Player objects, allowing easy mocking for tests.

### 3. Error Handling & logging
-   **Loguru**: Used for all logging. Console gets user-friendly output; Files get machine-readable JSON.
-   **Namespace Protection**: The logging module is explicitly named `game_logging`.

### 4. API Key Management
**Pattern**: Priority Chain.
1.  System Keyring (`keyring` library, service: `spyfall-arena`).
2.  `apikeys.yaml` (fallback, discouraged).
This keeps secrets out of the codebase and environment variables (mostly).

## Critical Implementation Paths
1.  **Game Loop**: `GameRunner` -> `GameState` -> `Player` -> `LLMClient` -> API.
2.  **Prompt Engineering**: Converting game state into effective prompts for the LLM is crucial for performance.
