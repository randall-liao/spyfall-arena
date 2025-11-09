# Spyfall Arena

Spyfall Arena is a Python-based backend system that orchestrates autonomous Spyfall games between multiple LLM agents.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/spyfall-arena.git
    cd spyfall-arena
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    poetry install
    ```

## Configuration

The game is configured using a YAML file. An example configuration is provided in `config.yaml`.

-   `game`: Contains general game settings.
    -   `num_rounds`: The number of rounds to play.
    -   `max_turns_per_round`: The maximum number of question-answer turns before a round ends.
    -   `random_seed`: A seed for the random number generator to ensure reproducibility.
-   `players`: A list of the players in the game.
    -   `nickname`: A unique name for the player.
    -   `model_name`: The name of the LLM to use for this player (e.g., `openai/gpt-4`).
    -   `temperature`: The temperature to use for the LLM's responses.
-   `locations`: A list of possible locations for the game.
-   `prompts`: Paths to the prompt template files.
-   `logging`: Configuration for the game logs.
    -   `output_dir`: The directory where the JSON log files will be saved.
    -   `save_full_prompts`: Whether to include the full LLM prompts in the log.
    -   `log_level`: The logging level for the text-based log file.

## Usage

To run a game, use the `game_runner.py` script and provide the path to your configuration file:

```bash
poetry run python game_runner.py config.yaml
```

The game will run to completion, and a JSON log file will be created in the directory specified in the configuration.

## Development

To set up the development environment, install the development dependencies:

```bash
poetry install --with dev
```

### Running Tests

To run the unit tests:

```bash
poetry run pytest
```

To run the tests with coverage:

```bash
poetry run pytest --cov=spyfall_arena
```
