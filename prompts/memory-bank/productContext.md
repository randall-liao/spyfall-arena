# Product Context

## Why This Project Exists
Evaluating Large Language Models (LLMs) often relies on static benchmarks. Spyfall Arena provides a dynamic, social environment to test "softer" but critical capabilities:
-   **Reasoning**: Inferring roles from subtle clues.
-   **Deception**: Generating plausible lies as the Spy.
-   **Deduction**: Identifying the Spy based on inconsistencies.
-   **Multi-Agent Interaction**: Operating within a group context with varying goals.

## The Problem
Standard benchmarks don't capture how models handle prolonged, state-dependent social interactions involving hidden information and deception. Spyfall Arena fills this gap by automating the game of Spyfall.

## User Experience
The primary "user" is a researcher or developer running simulations.
-   **Input**: The user defines the experiment in `config.yaml` (e.g., "Run a game with 3 GPT-4 agents and 1 Gemini agent at the 'Beach' location").
-   **Execution**: The user runs `python game_runner.py config.yaml`.
-   **Output**: The system prints a summary to the console and generates a detailed JSON log file containing the entire game transcript and metadata for analysis.

## Key Features
-   **Automated Gameplay**: No human intervention required during the game.
-   **Role Assignment**: Random distribution of "Spy" and "Civilian" roles.
-   **Turn Management**: Orchestrated Q&A cycles.
-   **Voting Mechanism**: Automated voting logic to determine the winner.
-   **Provider Agnostic**: Supports multiple LLM providers (OpenRouter, Google Gemini).
