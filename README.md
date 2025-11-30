# 🕵️‍♂️ Spyfall Arena

**Spyfall Arena** is a platform where multiple large language models (LLMs) autonomously play the social deduction game **Spyfall**.
It aims to evaluate how different LLMs perform in reasoning, deception, and deduction under dynamic multi-agent interactions.

---

## 🎯 Project Highlights

- 🧠 Multi-agent environment for reasoning and bluffing
- 🎮 Automated Spyfall gameplay simulation
- 📊 Model performance and deception benchmarking
- 📁 Fully backend (no frontend)
- 🧩 Configurable via YAML file
- 📄 JSON logs for every match (questions, answers, votes, results)

---

## 🛠️ Setup and Usage

### 1. Prerequisites

- [Python](https://www.python.org/downloads/) (version 3.12 or higher)
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management
- [Git Credential Manager](https://github.com/git-ecosystem/git-credential-manager) for secure API key storage

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/spyfall-arena.git
    cd spyfall-arena
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    poetry install
    ```

### 3. API Key Configuration

This project supports LLM providers via API keys.
*   **OpenRouter** (for OpenAI, Anthropic, etc.)
*   **Google Gemini** (for Gemini models)

#### Recommended: Using a Credential Manager

The most secure way to store your API keys is using your system's credential manager.

1.  **Store the OpenRouter key:**
    ```bash
    keyring set spyfall-arena openrouter_api_key
    ```
    When prompted, paste your OpenRouter API key.

2.  **Store the Google Gemini key:**
    ```bash
    keyring set spyfall-arena google_api_key
    ```
    When prompted, paste your Google API key.

3.  **Verify the keys:**
    ```bash
    keyring get spyfall-arena openrouter_api_key
    keyring get spyfall-arena google_api_key
    ```

#### Fallback: Using a YAML File (Not Recommended)

If you cannot use a credential manager, you can use the `apikeys.yaml` file as a fallback.

1.  **Create the file:**
    Rename the `apikeys.yaml.example` file to `apikeys.yaml`.

2.  **Add your keys:**
    Open `apikeys.yaml` and replace the placeholders with your actual API keys.

    ```yaml
    openrouter_api_key: "your-open-router-api-key-goes-here"
    google_api_key: "your-google-api-key-goes-here"
    ```

    A warning will be displayed every time you run the application to remind you that this method is insecure.

### 4. Configuration

The project uses a YAML configuration file (e.g., `config.yaml`) to define game settings.

#### Supported Models

*   **OpenRouter**: Use standard model names (e.g., `openai/gpt-4`).
*   **Google Gemini**: Use model names starting with `gemini` (e.g., `gemini-2.5-flash`).

The application automatically selects the correct provider based on the model name in the configuration file.

```yaml
llm:
  model: "gemini-2.5-flash" # or "openai/gpt-4o"
  temperature: 0.7
```

### 5. Running the Application

To run a game, you need to provide a configuration file.

```bash
python game_runner.py config.yaml
```

You can control the console logging verbosity with the `--log-level` flag (default: INFO).
Available levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`.

```bash
# Run with detailed debug logs
python game_runner.py config.yaml --log-level DEBUG
```

You can customize the game by editing `config.yaml` or creating your own configuration files.

### 6. Running Tests

The project has a comprehensive test suite. To run the tests and see the coverage report:

```bash
poetry run pytest
```

---

## 🚀 Project Phases

### **Phase 1 – Foundational Arena (MVP)**
> Build the core game engine and single-game simulation.

- [x] Define game rules and structure (Spy vs Civilians)
- [x] Role assignment logic
- [x] Turn-based Q/A flow
- [x] Voting and win condition
- [x] YAML config file for setup
- [x] Structured JSON logging
- [ ] Basic evaluation metrics (win rate, suspicion rate)

---

### **Phase 2 – Comparative Arena**
> Expand to large-scale experimentation and evaluation.

- [ ] Tournament automation (multiple games)
- [ ] Configurable model pool and parameters
- [ ] Aggregate metrics and summary reports
- [ ] Optional “Judge LLM” for reasoning evaluation

---

### **Phase 3 – Analytical Arena**
> Enable advanced behavioral and cognitive analysis.

- [ ] Capture hidden reasoning traces
- [ ] Compare internal reasoning vs public responses
- [ ] Support different personality prompts
- [ ] Export datasets for linguistic and statistical study

---

## 🧭 Current Status

> ✅ **Phase 1 in progress**
> Building the foundational backend and refining role-based LLM interactions.

---

**Spyfall Arena**
*Exploring how machines reason, bluff, and deduce — one game at a time.*
