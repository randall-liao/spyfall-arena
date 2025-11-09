# 🕵️‍♂️ Spyfall Arena — Product Requirements Document (PRD)

## 1. Product Overview

**Product Vision:**
Spyfall Arena is a simulation platform that allows multiple large language models (LLMs) to autonomously play the social deduction game *Spyfall*. The system coordinates turns, tracks dialogue, determines outcomes, and evaluates each model’s reasoning, deception, and deduction capabilities.

**Core Objective:**
To systematically evaluate and compare how different LLMs perform in dynamic, multi-agent interaction environments that require *social reasoning, question interpretation, and bluffing.*

**Product Type:**
Research / evaluation tool (backend-only; no user-facing UI in the MVP).

---

## 2. Target Users and Use Cases

### 2.1 Target Users

| User Type                       | Primary Goal                                                                                          |
| ------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **AI Researchers / Developers** | Benchmark and compare reasoning and deception abilities of different LLMs in structured social games. |
| **Prompt Engineers**            | Experiment with prompt design for deception detection, role-playing, and multi-agent consistency.     |
| **Data Scientists**             | Collect conversation data for analysis on strategy, linguistic deception, and reasoning quality.      |

### 2.2 Core Use Cases

1. **Model Benchmarking**

   * Run tournaments among different LLMs (e.g., GPT-4 vs. Claude 3 vs. Mistral).
   * Observe win rates, deception success, and logic consistency.

2. **Behavioral Analysis**

   * Examine linguistic cues used in deception or suspicion.
   * Identify differences in reasoning strategies across models.

3. **Prompt and Agent Experimentation**

   * Modify personality traits or system prompts to observe behavior variation.

4. **Data Collection for Research**

   * Generate structured dialogue datasets labeled with role, suspicion, and round outcomes.

---

## 3. Product Scope and Phases

### Phase 1 — **Foundational Arena (MVP)**

**Goal:** Fully automated Spyfall gameplay between LLM agents without a UI.

**Key Features:**

* Role assignment (spy vs civilians)
* Turn-based question-answer sequence
* Voting and win condition logic
* Logging of full conversation and results
* Configuration via file or CLI arguments

**Output:** JSON or structured log of each game with roles, dialogue, and results.

---

### Phase 2 — **Comparative Arena**

**Goal:** Enable large-scale experimentation and evaluation.

**Key Features:**

* Tournament mode (run multiple games automatically)
* Configurable model pool and parameters
* Scoring metrics (win rate, reasoning quality, deception success)
* Automatic aggregation and summary reports
* Optional evaluation via “Judge LLM” (e.g., to rate logical consistency)

---

### Phase 3 — **Analytical Arena**

**Goal:** Enable behavioral and cognitive insights.

**Key Features:**

* Capture hidden reasoning traces (private “thoughts” per model)
* Correlate reasoning vs public output
* Support variable difficulty and personalities
* Statistical and linguistic analysis exports (CSV/JSON)
* Visualization hooks (to be integrated later if UI added)

---

## 4. Core Product Features (Phase 1 Focus)

### 4.1 Game Simulation

* **Objective:** Simulate one complete round of Spyfall.

* **Actors:** Multiple LLM agents, each playing as one player.

* **Core Loop:**

  1. Assign roles randomly (1 spy, rest civilians).
  2. Civilians share a location; the spy doesn’t know it.
  3. Each player asks another player one question.
  4. Each answer is publicly visible.
  5. After several rounds, all players vote who they think the spy is.
  6. The spy wins if not discovered (or if they correctly guess the location).

* **End Condition:**

  * Civilians win if spy is correctly identified.
  * Spy wins if guessed location correctly or avoided detection.

---

### 4.2 LLM Player Management

* Each “player” corresponds to one LLM instance.

* Each player:

  * Receives context (public dialogue + their private role info).
  * Responds with a *question*, *answer*, or *vote*.
  * Follows a consistent persona (defined by prompt template).

* Must support multiple models from different providers (e.g., OpenAI, Anthropic).

---

### 4.3 Configuration

* Game parameters configurable via YAML or JSON:

  * Number of players
  * Model selection per player
  * List of locations
  * Number of rounds
  * Random seed
  * Temperature and API parameters

* Must allow running with different configurations easily (e.g., from CLI).

---

### 4.4 Logging & Storage

* Store **full trace** of each game:

  * Player roles and model names
  * Each question and answer pair
  * Voting decisions
  * Final result and winner
* Data format: JSON
* Support optional summary statistics per run.

---

### 4.5 Evaluation and Metrics (MVP)

* **Win Rate** — how often a model wins as spy or civilian.
* **Suspicion Rate** — how often a model is voted as spy when innocent.
* **Bluff Success Rate** — spy’s success frequency.
* **Token/Response Stats** — average length and token usage.

---

## 5. Product Success Criteria

| Goal                         | Metric                                                       |
| ---------------------------- | ------------------------------------------------------------ |
| **Game Completion**          | 95% of simulated games run to completion without failure.    |
| **Reproducibility**          | Given same seed and parameters, same results should occur.   |
| **Data Quality**             | All logs capture consistent, structured fields for analysis. |
| **Model Comparison Clarity** | Each game clearly maps outcomes to model identifiers.        |
| **Experiment Scalability**   | Arena can run 50+ games in sequence automatically.           |

---

## 6. Product Constraints

| Constraint                 | Description                                                                                  |
| -------------------------- | -------------------------------------------------------------------------------------------- |
| **No frontend**            | All outputs are logged or printed via CLI.                                                   |
| **Limited API rate**       | Must handle LLM API quotas; include backoff/retry logic (future non-functional requirement). |
| **No manual intervention** | LLMs act fully autonomously within the rules.                                                |
| **Transparency**           | Each model sees only what its role allows (no shared hidden state).                          |
| **Extensibility**          | Easy to add new models or modify rules later.                                                |

---

## 7. Future Product Extensions (beyond MVP)

| Extension                    | Description                                                       |
| ---------------------------- | ----------------------------------------------------------------- |
| **Judge LLM Evaluation**     | Add referee model to score reasoning consistency or plausibility. |
| **Meta-Agent Analysis**      | Simulate human-like personality traits.                           |
| **Cross-Game Analytics**     | Aggregate multi-game statistics automatically.                    |
| **Human-in-the-Loop Mode**   | Let a human replace one player to observe LLM behavior.           |
| **Web Dashboard (optional)** | Future visualization tool for results and replays.                |

---

## 8. Product Deliverables

* Product Configuration Specification (YAML schema)
* Game Log Schema (JSON format)
* LLM Role Prompt Specifications
* Metric Definitions Document
