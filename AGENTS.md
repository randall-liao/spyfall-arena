# Agent Instructions for Spyfall Arena

This document provides guidance for AI development agents working on the Spyfall Arena project.

## Project Overview

**Spyfall Arena** is a Python-based backend system for simulating games of Spyfall between multiple Large Language Models (LLMs). The project is designed to be highly modular, configurable, and observable.

-   **Backend Only:** This is a pure backend project with no frontend components.
-   **Configuration:** Game parameters, player models, and locations are all defined in a central YAML configuration file (`config.yaml`).
-   **Logging:** The system produces structured JSON logs for each game, capturing all signficant events.

## Development Conventions

### Code Style and Quality

To maintain code quality and consistency, the following tools are used. Before submitting any changes, ensure your code adheres to these standards by running:

-   **Formatting:** `poetry run black .`
-   **Import Sorting:** `poetry run isort .`
-   **Static Typing:** `poetry run mypy .`

### Project Structure

The project follows a `src` layout. All Python source code is located in the `./src` directory.

-   `src/config`: Configuration loading, validation, and API key management.
-   `src/game`: Core game logic, including the orchestrator, state machine, and managers for turns, voting, and scoring.
-   `src/llm`: LLM client implementation and factory.
-   `src/logging`: Game logging and output.
-   `src/prompts`: Prompt templates and the prompt builder.

### Import Style

Python modules within the `src` directory should use relative imports from the `src` root. For example, to import the `GameState` class from `src/game/game_state.py`, use the following syntax:

```python
from game.game_state import GameState
```

Do **not** prefix the import with `src`, like `from src.game.game_state...`.

## Testing

The project has a comprehensive suite of unit tests. The testing philosophy is as follows:

-   **Unit Tests Only:** The focus is on unit tests that isolate and verify the behavior of individual components. Do not write end-to-end or integration tests.
-   **Mocking:** External services and API calls must be mocked.
-   **Coverage:** The goal is 100% line coverage, with a minimum acceptance of 90%.
-   **File Naming:** Test files must be named to match the corresponding source file. For example, the tests for `src/game/game_state.py` should be in `tests/game/test_game_state.py`.

The test directory (`./tests`) mirrors the source directory (`./src`). To run the tests and generate a coverage report, use the following command:

```bash
poetry run pytest
```

## Running the Application

The application is run from the project's root directory. You must provide the path to a valid configuration file.

```bash
python game_runner.py <path_to_config.yaml>
```
