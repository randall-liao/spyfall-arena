# Project Brief: Spyfall Arena

## Overview
Spyfall Arena is a Python-based backend system designed to simulate games of Spyfall between multiple Large Language Models (LLMs). The project aims to evaluate how different LLMs perform in reasoning, deception, and deduction under dynamic multi-agent interactions.

## Core Goals
1.  **Simulation Engine**: Create a robust, automated environment for playing Spyfall.
2.  **LLM Evaluation**: Benchmark model performance in social deduction tasks (reasoning, bluffing).
3.  **Modularity**: Ensure the system is highly configurable via YAML (models, game parameters).
4.  **Observability**: Produce structured JSON logs for every match to enable analysis.

## Key Requirements
-   **Backend Only**: No frontend components.
-   **Configuration**: Centralized `config.yaml` for all settings.
-   **Logging**: Comprehensive JSON logging for game events (questions, answers, votes).
-   **Testing**: High unit test coverage (target 100%, min 90%) with mocked external calls.
-   **Security**: Secure API key management via system keyring (with YAML fallback).

## Scope
-   **Phase 1 (Current)**: Foundational Arena (MVP) - Core game engine, single-game simulation.
-   **Phase 2**: Comparative Arena - Tournament automation, aggregate metrics.
-   **Phase 3**: Analytical Arena - Advanced behavioral and cognitive analysis.
