# 🕹️ Phase One — Foundational Arena (Backend-Only)

**Goal:**
Run a complete Spyfall game between multiple LLM agents, fully automated, using a configuration file to define settings.
At the end of each game, produce a structured JSON log that records all actions, reasoning, and results.

---

## 1. Configuration Management (via File)

**Purpose:**
Allow the system to initialize and run without manual input.
The configuration defines every parameter required for gameplay and model setup.

**Product Requirements:**

* The system must read a YAML or JSON configuration file at startup.
* If parameters are missing, use sensible defaults.
* All runs are reproducible with a fixed random seed.
* No runtime CLI overrides are needed for MVP.

---

## 2. Role Assignment System

**Purpose:**
Distribute roles among LLM agents while maintaining secrecy.

**Requirements:**

* Exactly **one spy** per game.
* The remaining players are **civilians**.
* Civilians receive the same **location**; the spy gets “unknown.”
* Each agent must only have access to its private information.
* The system must store the hidden roles internally for logging.

**Acceptance Criteria:**

* Randomly assign one spy with a reproducible random seed.
* Confirm roles are hidden from other players.
* Log assignments (internally, not visible to players).

---

## 3. Game Loop and Turn-Based Interaction

**Purpose:**
Simulate Spyfall gameplay through structured turns of questions and answers.

**Turn Structure:**

1. **Asking Phase** – Player A chooses another player and asks a question.
2. **Answering Phase** – Player B responds.
3. **Rotation** – Next player becomes the asker.
4. Repeat for a configurable number of rounds (e.g., 5 rounds).

**Requirements:**

* Each turn must include:

  * Who asked (player ID/model name)
  * Who answered
  * The exact question and answer text
* Players receive:

  * Public conversation so far
  * Their private role/location
  * Turn metadata (whose turn, round number)
* The system should ensure that:

  * The spy has enough ambiguity to bluff effectively.
  * Civilians base questions on the shared location.

**Acceptance Criteria:**

* The game completes all rounds without external input.
* Every LLM participates in at least one Q/A turn.
* Responses are recorded in a structured format.

---

## 4. Voting and Win Condition Logic

**Purpose:**
Determine the winner through a collective voting process.

**Requirements:**

* After all rounds:

  * Each player votes for who they believe is the spy.
* Votes are collected simultaneously (no influence between votes).
* Majority vote determines outcome:

  * If majority votes for the actual spy → civilians win.
  * If spy avoids detection → spy wins.
* Optional (stretch goal): spy may guess the location to steal victory.

**Acceptance Criteria:**

* Every player submits a valid vote.
* Votes are visible in the final log.
* Correct determination of winner (civilian or spy).

---

## 5. Logging and Data Recording

**Purpose:**
Maintain a transparent, analyzable record of every game interaction.

**Requirements:**

* Log file per game in the output directory (`/logs`).
* Log must contain:

  * Metadata: timestamp, game ID, config snapshot.
  * Player list and model info.
  * Role assignments (hidden from LLMs but recorded).
  * Every round’s question and answer.
  * Voting results and final winner.
* Optionally include:

  * Raw LLM prompts/responses (if `save_full_prompts` = true).

**Acceptance Criteria:**

* Each game produces one valid JSON file.
* Log files are named consistently (e.g., `2025-11-08_game_001.json`).
* All required fields are present and readable.
* No sensitive API data is written.

---

## 6. Evaluation and Metrics

**Purpose:**
Provide structured metrics to analyze performance.

**MVP Metrics:**

* **Win Rate** — which side won (civilian/spy).
* **Vote Accuracy** — how many civilians voted correctly.
* **Spy Deception Success** — if spy avoided being caught.
* **Response Statistics** — number and length of turns.

**Optional Extensions for Later Phases:**

* Spy guess accuracy (location guess).
* Consistency score using judge model.
* Deception likelihood analysis.

**Acceptance Criteria:**

* Metrics are computed at the end of each game.
* Results are stored alongside the dialogue log.
* Fields clearly indicate who won and why.

---

## 7. Error Handling & Stability

**Purpose:**
Ensure smooth game execution even if an LLM API call fails.

**Requirements:**

* Retry once or skip turn if LLM call fails.
* Clearly log any skipped turns or errors.
* Continue the game unless critical failure occurs.
* Produce a summary status (“success” / “partial success” / “error”).

**Acceptance Criteria:**

* Game execution never halts mid-turn due to LLM timeout.
* All exceptions are caught and logged.

---

## 8. Output Specification

**Purpose:**
Define expected product output for downstream analysis.

**Acceptance Criteria:**

* Output file is automatically generated upon completion.
* All core gameplay data is preserved and machine-readable.

---

## 9. Phase One Success Definition

| Success Criterion        | Description                                                |
| ------------------------ | ---------------------------------------------------------- |
| **Automation**           | Game runs end-to-end using only the config file.           |
| **Role Integrity**       | No player ever sees another player’s private info.         |
| **Game Completion Rate** | 90%+ of runs complete without errors.                      |
| **Log Quality**          | JSON outputs are valid and structured consistently.        |
| **Reproducibility**      | Same config seed yields identical game state and outcomes. |
