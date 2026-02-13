# Agent Instructions for Spyfall Arena

This document provides guidance for AI development agents working on the Spyfall Arena project.

## Project Overview

**Spyfall Arena** is a Python-based backend system (Python 3.12+) for simulating games of Spyfall between multiple Large Language Models (LLMs). The project is designed to be highly modular, configurable, and observable.

-   **Backend Only:** This is a pure backend project with no frontend components.
-   **Configuration:** Game parameters, player models, and locations are all defined in a central YAML configuration file (`config.yaml`).
-   **Logging:** The system produces structured JSON logs for each game, capturing all signficant events.
-   **Analytics:** A dedicated analytics module processes logs to generate performance metrics and reports.

## Development Conventions

### Code Style and Quality

To maintain code quality and consistency, we use **Ruff** for formatting and linting. Before submitting any changes, ensure your code adheres to these standards by running:

-   **Formatting:** `poetry run ruff format .`
-   **Linting:** `poetry run ruff check . --fix`
-   **Static Typing:** `poetry run mypy .`

### Project Structure

The project follows a `src` layout. All Python source code is located in the `./src` directory.

-   `src/analytics`: Log parsing, data aggregation, and report generation.
-   `src/config`: Configuration loading, validation, and API key management.
-   `src/game`: Core game logic, including the orchestrator, state machine, and managers for turns, voting, and scoring.
-   `src/game_logging`: Game logging, console setup, and metrics calculation.
-   `src/llm`: LLM client implementation and factory.
-   `src/prompts`: Prompt templates and the prompt builder.

### Import Style

Python modules within the `src` directory should use relative imports from the `src` root. For example, to import the `GameState` class from `src/game/game_state.py`, use the following syntax:

```python
from game.game_state import GameState
```

Do **not** prefix the import with `src`, like `from src.game.game_state...`.

## Testing

The project has a comprehensive suite of unit and end-to-end tests.

-   **Testing Framework:** We use `pytest` with `pytest-cov`.
-   **Test Types:** While the focus is on unit tests, end-to-end tests (in `tests/e2e`) are used to verify full game flows.
-   **Mocking:** External services and API calls must be mocked in unit tests.
-   **Coverage:** The project aims for high test coverage. The build will fail if coverage drops below **90%**.
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

To run analytics on generated logs:

```bash
python analyze_logs.py
```
