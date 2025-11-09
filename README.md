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

This project requires an API key from [OpenRouter](https://openrouter.ai/).

#### Recommended: Using a Credential Manager

The most secure way to store your API key is using your system's credential manager.

1.  **Store the key:**
    Use the `keyring` command-line tool (installed with the project dependencies) to store your key.

    ```bash
    keyring set spyfall-arena openrouter_api_key
    ```

    When prompted, paste your OpenRouter API key.

2.  **Verify the key:**
    ```bash
    keyring get spyfall-arena openrouter_api_key
    ```

#### Fallback: Using a YAML File (Not Recommended)

If you cannot use a credential manager, you can use the `apikeys.yaml` file as a fallback.

1.  **Create the file:**
    Rename the `apikeys.yaml.example` file to `apikeys.yaml`.

2.  **Add your key:**
    Open `apikeys.yaml` and replace the placeholder with your actual OpenRouter API key.

    ```yaml
    openrouter_api_key: "your-open-router-api-key-goes-here"
    ```

    A warning will be displayed every time you run the application to remind you that this method is insecure.

### 4. Running the Application

To run a game, you need to provide a configuration file.

```bash
python game_runner.py config.yaml
```

You can customize the game by editing `config.yaml` or creating your own configuration files.

### 5. Running Tests

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
