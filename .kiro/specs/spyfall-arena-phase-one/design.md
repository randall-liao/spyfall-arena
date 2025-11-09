# Design Document

## Overview

Spyfall Arena Phase One is a Python-based backend system that orchestrates autonomous Spyfall games between multiple LLM agents. The architecture follows a modular design with clear separation of concerns: configuration management, game state coordination, LLM interaction, and data persistence. The system operates entirely through configuration files and produces structured JSON logs for analysis.

The design prioritizes reproducibility, extensibility, and fault tolerance. Each component is designed to be testable in isolation while maintaining clean interfaces for integration.

## Design Patterns

This design leverages several design patterns to ensure maintainability, testability, and extensibility:

1. **State Machine Pattern**: Game state transitions (RoundState, GameState)
2. **Factory Pattern**: LLMClientFactory for creating LLM clients
3. **Strategy Pattern**: Different scoring strategies, prompt building strategies
4. **Builder Pattern**: PromptBuilder for constructing complex prompts
5. **Singleton Pattern**: Configuration management
6. **Template Method Pattern**: BaseLLMClient defines template for LLM interactions

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Main Entry Point                      │
│                      (game_runner.py)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├──> ConfigLoader
                     │
                     ├──> GameOrchestrator
                     │         │
                     │         ├──> RoleAssigner
                     │         ├──> TurnManager
                     │         ├──> VotingManager
                     │         ├──> ScoringEngine
                     │         └──> GameState
                     │
                     ├──> LLMClientFactory
                     │         └──> [OpenAI, Anthropic, etc.]
                     │
                     └──> GameLogger
                               └──> MetricsCalculator
```

### Component Layers

1. **Configuration Layer**: Handles YAML parsing, validation, and default values
2. **Orchestration Layer**: Manages game flow, state transitions, and rule enforcement
3. **LLM Integration Layer**: Abstracts different LLM providers behind a common interface
4. **Persistence Layer**: Handles logging, metrics calculation, and file output

## Components and Interfaces

### 1. Configuration Management

**Module**: `config/`

**Components**:
- `config_loader.py`: Loads and validates YAML configuration
- `config_schema.py`: Defines configuration structure and defaults
- `config_validator.py`: Validates configuration values

**Configuration Schema**:
```yaml
game:
  num_rounds: 3              # Number of rounds to play
  max_turns_per_round: 20    # Maximum Q&A turns before timeout
  random_seed: 42            # For reproducibility
  
players:
  - nickname: "Alice"
    model_provider: "openai"
    model_name: "gpt-4"
    temperature: 0.7
  - nickname: "Bob"
    model_provider: "anthropic"
    model_name: "claude-3-opus"
    temperature: 0.7
  # ... more players (4-12 total)

locations:
  - "Bank"
  - "Airport"
  - "Restaurant"
  # ... more locations

prompts:
  system_prompt_template: "path/to/system_prompt.txt"
  civilian_role_template: "path/to/civilian_role.txt"
  spy_role_template: "path/to/spy_role.txt"

logging:
  output_dir: "./logs"
  save_full_prompts: false
  log_level: "INFO"

api_keys:
  openai_api_key_env: "OPENAI_API_KEY"
  anthropic_api_key_env: "ANTHROPIC_API_KEY"
```

**Interface**:
```python
class GameConfig:
    def __init__(self, config_dict: dict)
    def get_num_rounds(self) -> int
    def get_players(self) -> List[PlayerConfig]
    def get_locations(self) -> List[str]
    def get_random_seed(self) -> int
    def validate(self) -> bool
```

### 2. Game State Management (State Machine Pattern)

**Module**: `game/game_state.py`

**Purpose**: Central state container using state machine pattern for game flow

**State Machine Design**:
```python
from enum import Enum
from typing import Optional

class GamePhase(Enum):
    """Game-level states"""
    INITIALIZING = "initializing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"

class RoundPhase(Enum):
    """Round-level states"""
    ROLE_ASSIGNMENT = "role_assignment"
    QUESTIONING = "questioning"
    VOTING = "voting"
    SPY_GUESSING = "spy_guessing"
    SCORING = "scoring"
    COMPLETED = "completed"

@dataclass
class GameState:
    game_id: str
    config: GameConfig
    phase: GamePhase
    current_round: int
    rounds_data: List[RoundState]
    player_scores: Dict[str, int]  # nickname -> total points
    errors: List[GameError]
    
    def transition_to(self, new_phase: GamePhase) -> bool:
        """Validates and executes state transition"""
        if self._is_valid_transition(self.phase, new_phase):
            self.phase = new_phase
            return True
        return False
    
    def _is_valid_transition(self, from_phase: GamePhase, to_phase: GamePhase) -> bool:
        """Defines valid state transitions"""
        valid_transitions = {
            GamePhase.INITIALIZING: [GamePhase.IN_PROGRESS, GamePhase.ERROR],
            GamePhase.IN_PROGRESS: [GamePhase.COMPLETED, GamePhase.ERROR],
            GamePhase.COMPLETED: [],
            GamePhase.ERROR: []
        }
        return to_phase in valid_transitions.get(from_phase, [])
    
@dataclass
class RoundState:
    round_number: int
    phase: RoundPhase
    location: str
    spy_nickname: str
    role_assignments: Dict[str, Role]  # nickname -> Role
    conversation_history: List[Turn]
    votes: List[VoteAttempt]
    spy_guess: Optional[SpyGuess]
    ending_condition: Optional[EndingCondition]
    round_scores: Dict[str, int]
    current_asker: Optional[str]
    previous_asker: Optional[str]
    players_who_voted: Set[str]  # Track who initiated votes
    
    def transition_to(self, new_phase: RoundPhase) -> bool:
        """Validates and executes state transition"""
        if self._is_valid_transition(self.phase, new_phase):
            self.phase = new_phase
            return True
        return False
    
    def _is_valid_transition(self, from_phase: RoundPhase, to_phase: RoundPhase) -> bool:
        """Defines valid state transitions"""
        valid_transitions = {
            RoundPhase.ROLE_ASSIGNMENT: [RoundPhase.QUESTIONING],
            RoundPhase.QUESTIONING: [RoundPhase.VOTING, RoundPhase.SPY_GUESSING, RoundPhase.SCORING],
            RoundPhase.VOTING: [RoundPhase.QUESTIONING, RoundPhase.SCORING],
            RoundPhase.SPY_GUESSING: [RoundPhase.SCORING],
            RoundPhase.SCORING: [RoundPhase.COMPLETED],
            RoundPhase.COMPLETED: []
        }
        return to_phase in valid_transitions.get(from_phase, [])
    
@dataclass
class Turn:
    turn_number: int
    asker_nickname: str
    answerer_nickname: str
    question: str
    answer: str
    timestamp: datetime
```

### 3. Role Assignment System

**Module**: `game/role_assigner.py`

**Purpose**: Randomly assign spy and location while maintaining secrecy

**Interface**:
```python
class RoleAssigner:
    def __init__(self, random_seed: int)
    
    def assign_roles(
        self, 
        player_nicknames: List[str], 
        locations: List[str]
    ) -> Tuple[Dict[str, Role], str]:
        """
        Returns: (role_assignments, selected_location)
        role_assignments: {nickname: Role(is_spy, location)}
        """
```

**Role Data Structure**:
```python
@dataclass
class Role:
    is_spy: bool
    location: Optional[str]  # None for spy, actual location for civilians
```

### 4. Game Orchestrator

**Module**: `game/orchestrator.py`

**Purpose**: Main game loop coordinator

**Interface**:
```python
class GameOrchestrator:
    def __init__(
        self, 
        config: GameConfig,
        llm_factory: LLMClientFactory,
        logger: GameLogger
    )
    
    def run_game(self) -> GameState:
        """Runs complete multi-round game"""
        
    def run_round(self, round_num: int) -> RoundState:
        """Runs a single round"""
        
    def _check_ending_conditions(self) -> Optional[EndingCondition]:
        """Checks if round should end"""
```

**Game Flow**:
1. Initialize game state
2. For each round:
   - Assign roles and location
   - Run turn loop until ending condition
   - Process final scoring
   - Log round results
3. Calculate final scores and winner
4. Generate complete game log

### 5. Turn Manager

**Module**: `game/turn_manager.py`

**Purpose**: Manages question-answer flow and turn rotation

**Interface**:
```python
class TurnManager:
    def __init__(self, llm_factory: LLMClientFactory)
    
    def execute_turn(
        self,
        game_state: GameState,
        round_state: RoundState,
        current_asker: str
    ) -> Turn:
        """
        Executes one Q&A turn:
        1. Asker selects target and asks question
        2. Target answers
        3. Returns Turn object
        """
        
    def get_next_asker(
        self,
        current_answerer: str,
        previous_asker: str
    ) -> str:
        """
        Returns next asker (the person who just answered)
        Enforces no-retaliation rule
        """
        
    def get_valid_targets(
        self,
        asker: str,
        previous_asker: Optional[str]
    ) -> List[str]:
        """Returns list of players asker can question"""
```

### 6. Voting Manager

**Module**: `game/voting_manager.py`

**Purpose**: Handles player-initiated votes and indictments

**Interface**:
```python
class VotingManager:
    def __init__(self, llm_factory: LLMClientFactory)
    
    def check_for_vote_initiation(
        self,
        game_state: GameState,
        round_state: RoundState,
        current_player: str
    ) -> Optional[str]:
        """
        Asks current player if they want to initiate a vote
        Returns: suspect_nickname or None
        """
        
    def conduct_vote(
        self,
        game_state: GameState,
        round_state: RoundState,
        initiator: str,
        suspect: str
    ) -> VoteAttempt:
        """
        Collects votes from all players
        Returns: VoteAttempt with results
        """
        
@dataclass
class VoteAttempt:
    initiator: str
    suspect: str
    votes: Dict[str, bool]  # nickname -> yes/no
    passed: bool  # True if unanimous yes
    timestamp: datetime
```

### 7. Spy Guess Manager

**Module**: `game/spy_guess_manager.py`

**Purpose**: Handles spy's location guess attempts

**Interface**:
```python
class SpyGuessManager:
    def __init__(self, llm_factory: LLMClientFactory)
    
    def check_spy_guess(
        self,
        game_state: GameState,
        round_state: RoundState
    ) -> Optional[SpyGuess]:
        """
        Asks spy if they want to guess location
        Returns: SpyGuess or None
        """
        
@dataclass
class SpyGuess:
    spy_nickname: str
    guessed_location: str
    actual_location: str
    correct: bool
    timestamp: datetime
```

### 8. Scoring Engine

**Module**: `game/scoring_engine.py`

**Purpose**: Calculates points based on round outcomes

**Interface**:
```python
class ScoringEngine:
    def calculate_round_scores(
        self,
        round_state: RoundState
    ) -> Dict[str, int]:
        """
        Calculates points for each player based on:
        - Spy not indicted: spy gets 2 points
        - Wrong person indicted: spy gets 4 points
        - Spy guessed correctly: spy gets 4 points
        - Spy indicted: civilians get 1 point each
        - Vote initiator gets 2 points (if successful)
        """
```

### 9. LLM Client Factory and Abstraction (Factory + Template Method Patterns)

**Module**: `llm/`

**Components**:
- `llm_client_factory.py`: Creates LLM client (Factory Pattern)
- `base_client.py`: Abstract base class (Template Method Pattern)
- `openrouter_client.py`: OpenRouter implementation

**Interface**:
```python
from abc import ABC, abstractmethod
from typing import Optional
import httpx
from loguru import logger

class BaseLLMClient(ABC):
    """Template Method Pattern: Defines skeleton of LLM interaction"""
    
    def __init__(self, model_name: str, api_key: str, temperature: float = 0.7):
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Hook method: Validate configuration"""
        pass
    
    @abstractmethod
    def _make_api_call(
        self,
        messages: list,
        temperature: float,
        response_format: Optional[dict] = None
    ) -> dict:
        """Hook method: Make actual API call"""
        pass
    
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        """Template method: Orchestrates response generation"""
        temp = temperature if temperature is not None else self.temperature
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self._make_api_call(messages, temp)
            return self._extract_text(response)
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
    
    def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict,
        temperature: Optional[float] = None
    ) -> dict:
        """Template method: Orchestrates structured response generation"""
        temp = temperature if temperature is not None else self.temperature
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self._make_api_call(messages, temp, response_schema)
            return self._extract_structured_data(response)
        except Exception as e:
            logger.error(f"LLM structured API call failed: {e}")
            raise
    
    @abstractmethod
    def _extract_text(self, response: dict) -> str:
        """Hook method: Extract text from API response"""
        pass
    
    @abstractmethod
    def _extract_structured_data(self, response: dict) -> dict:
        """Hook method: Extract structured data from API response"""
        pass


class OpenRouterClient(BaseLLMClient):
    """OpenRouter implementation"""
    
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def _validate_config(self) -> None:
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        if not self.model_name:
            raise ValueError("Model name is required")
    
    def _make_api_call(
        self,
        messages: list,
        temperature: float,
        response_format: Optional[dict] = None
    ) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(self.BASE_URL, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    def _extract_text(self, response: dict) -> str:
        return response["choices"][0]["message"]["content"]
    
    def _extract_structured_data(self, response: dict) -> dict:
        import json
        content = response["choices"][0]["message"]["content"]
        return json.loads(content)


class LLMClientFactory:
    """Factory Pattern: Creates appropriate LLM client"""
    
    _instance = None  # Singleton
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def create_client(
        self,
        model_name: str,
        api_key: str,
        temperature: float = 0.7
    ) -> BaseLLMClient:
        """Factory method to create OpenRouter client"""
        logger.info(f"Creating LLM client for model: {model_name}")
        return OpenRouterClient(model_name, api_key, temperature)
```

### 10. Prompt Builder

**Module**: `prompts/prompt_builder.py`

**Purpose**: Constructs prompts for different game actions

**Interface**:
```python
class PromptBuilder:
    def __init__(self, config: GameConfig)
    
    def build_role_prompt(self, role: Role) -> str:
        """Builds initial role assignment prompt"""
        
    def build_question_prompt(
        self,
        role: Role,
        conversation_history: List[Turn],
        valid_targets: List[str],
        round_metadata: dict
    ) -> str:
        """Builds prompt for asking a question"""
        
    def build_answer_prompt(
        self,
        role: Role,
        conversation_history: List[Turn],
        question: str,
        round_metadata: dict
    ) -> str:
        """Builds prompt for answering a question"""
        
    def build_vote_initiation_prompt(
        self,
        role: Role,
        conversation_history: List[Turn],
        can_vote: bool
    ) -> str:
        """Builds prompt asking if player wants to initiate vote"""
        
    def build_vote_decision_prompt(
        self,
        role: Role,
        conversation_history: List[Turn],
        suspect: str
    ) -> str:
        """Builds prompt for voting yes/no on suspect"""
        
    def build_spy_guess_prompt(
        self,
        conversation_history: List[Turn],
        available_locations: List[str]
    ) -> str:
        """Builds prompt for spy to guess location"""
```

### 11. Game Logger

**Module**: `logging/game_logger.py`

**Purpose**: Writes structured game logs using Loguru

**Interface**:
```python
from loguru import logger
from pathlib import Path
import json
from datetime import datetime

class GameLogger:
    """Simple logger for game events and JSON output"""
    
    def __init__(self, config: GameConfig):
        self.config = config
        self.log_dir = Path(config.logging.output_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_loguru()
    
    def _setup_loguru(self):
        """Configure Loguru for game logging"""
        log_file = self.log_dir / "game_execution.log"
        logger.add(
            log_file,
            rotation="10 MB",
            level=self.config.logging.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
    
    def write_final_log(self, game_state: GameState) -> str:
        """Writes complete JSON log file, returns filepath"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_game_{game_state.game_id}.json"
        filepath = self.log_dir / filename
        
        log_data = self._build_log_structure(game_state)
        
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
        
        logger.success(f"Game log written to: {filepath}")
        return str(filepath)
    
    def _build_log_structure(self, game_state: GameState) -> dict:
        """Builds complete log structure from game state"""
        return {
            "game_id": game_state.game_id,
            "timestamp": datetime.now().isoformat(),
            "config_snapshot": self._serialize_config(game_state.config),
            "rounds": [self._serialize_round(r) for r in game_state.rounds_data],
            "final_scores": game_state.player_scores,
            "status": game_state.phase.value
        }
```

### 12. Metrics Calculator

**Module**: `logging/metrics_calculator.py`

**Purpose**: Computes performance metrics

**Interface**:
```python
class MetricsCalculator:
    def calculate_round_metrics(
        self,
        round_state: RoundState
    ) -> RoundMetrics:
        """Calculates metrics for a single round"""
        
    def calculate_game_metrics(
        self,
        game_state: GameState
    ) -> GameMetrics:
        """Calculates aggregate metrics across all rounds"""
        
@dataclass
class RoundMetrics:
    winner_side: str  # "spy" or "civilians"
    ending_condition: str
    total_turns: int
    vote_attempts: int
    spy_caught: bool
    spy_guessed_correctly: Optional[bool]
    avg_question_length: float
    avg_answer_length: float
    
@dataclass
class GameMetrics:
    total_rounds: int
    spy_wins: int
    civilian_wins: int
    final_scores: Dict[str, int]
    overall_winner: str
    avg_turns_per_round: float
    total_vote_attempts: int
```

## Data Models

### Complete JSON Log Schema

```json
{
  "game_id": "game_20251108_001",
  "timestamp": "2025-11-08T14:30:00Z",
  "config_snapshot": { },
  "players": [
    {
      "nickname": "Alice",
      "model_provider": "openai",
      "model_name": "gpt-4"
    }
  ],
  "rounds": [
    {
      "round_number": 1,
      "location": "Bank",
      "spy": "Alice",
      "role_assignments": {
        "Alice": {"is_spy": true, "location": null},
        "Bob": {"is_spy": false, "location": "Bank"}
      },
      "turns": [
        {
          "turn_number": 1,
          "asker": "Alice",
          "answerer": "Bob",
          "question": "Is this a place where money is involved?",
          "answer": "Yes, definitely.",
          "timestamp": "2025-11-08T14:31:00Z"
        }
      ],
      "vote_attempts": [
        {
          "initiator": "Bob",
          "suspect": "Alice",
          "votes": {"Bob": true, "Charlie": true, "Alice": false},
          "passed": false,
          "timestamp": "2025-11-08T14:35:00Z"
        }
      ],
      "spy_guess": null,
      "ending_condition": "successful_indictment",
      "round_scores": {
        "Alice": 0,
        "Bob": 2,
        "Charlie": 1
      },
      "metrics": { }
    }
  ],
  "final_scores": {
    "Alice": 4,
    "Bob": 6,
    "Charlie": 3
  },
  "overall_winner": "Bob",
  "game_metrics": { },
  "status": "success"
}
```

## Error Handling

### Error Handling Strategy

1. **LLM API Failures**:
   - Implement exponential backoff retry (1 retry)
   - If retry fails, skip turn and log error
   - Continue game unless critical failure

2. **Invalid LLM Responses**:
   - Validate structured responses against schema
   - If invalid, retry with clarification prompt
   - If still invalid, use default/skip action

3. **Configuration Errors**:
   - Validate on load, fail fast with clear error messages
   - Don't start game with invalid config

4. **File I/O Errors**:
   - Ensure log directory exists, create if needed
   - Handle write failures gracefully
   - Produce partial logs if game aborts

**Error Logging**:
```python
@dataclass
class GameError:
    error_type: str
    message: str
    player_nickname: Optional[str]
    turn_number: Optional[int]
    timestamp: datetime
    recovered: bool
```

## Testing Strategy (100% Line Coverage Requirement)

**Coverage Tool**: pytest-cov with strict 100% line coverage enforcement

**Test Configuration** (pytest.ini):
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=spyfall_arena
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=100
    -v
```

### Unit Tests (100% Coverage)

1. **Configuration Tests** (`tests/unit/test_config.py`):
   - Valid config loading (all branches)
   - Default value application
   - Validation error detection
   - Edge cases: empty config, malformed YAML
   - All validation rules

2. **Role Assignment Tests** (`tests/unit/test_role_assigner.py`):
   - Reproducibility with same seed
   - Exactly one spy per game
   - Correct location distribution
   - Edge cases: minimum/maximum players
   - All random seed scenarios

3. **State Machine Tests** (`tests/unit/test_game_state.py`):
   - All valid state transitions
   - All invalid state transitions (should fail)
   - State transition validation logic
   - Edge cases for both GamePhase and RoundPhase

4. **Turn Manager Tests** (`tests/unit/test_turn_manager.py`):
   - No-retaliation rule enforcement
   - Valid target selection (all scenarios)
   - Turn rotation logic
   - Edge cases: 2 players, many players
   - All error paths

5. **Voting Tests** (`tests/unit/test_voting_manager.py`):
   - Unanimous vote requirement
   - One vote per player per round
   - Correct indictment logic
   - All voting outcomes
   - Edge cases: all yes, all no, mixed

6. **Scoring Tests** (`tests/unit/test_scoring_engine.py`):
   - All scoring scenarios (spy wins, civilian wins)
   - Point accumulation across rounds
   - Winner determination
   - Edge cases: ties, single round
   - All point calculation branches

7. **LLM Client Tests** (`tests/unit/test_llm_client.py`):
   - Mock API responses
   - Error handling (timeouts, invalid responses)
   - Retry logic
   - All response parsing branches

8. **Prompt Builder Tests** (`tests/unit/test_prompt_builder.py`):
   - All prompt templates
   - Variable substitution
   - Edge cases: empty history, long history

### Integration Tests

1. **Complete Game Flow** (`tests/integration/test_game_flow.py`):
   - Run full game with mock LLM clients
   - Verify all components interact correctly
   - Check log output structure
   - All ending conditions

2. **Multi-Round Games** (`tests/integration/test_multi_round.py`):
   - Verify state persistence across rounds
   - Check score accumulation
   - Validate role reassignment
   - All round transitions

3. **Error Recovery** (`tests/integration/test_error_handling.py`):
   - Simulate LLM failures (all failure types)
   - Verify graceful degradation
   - Check partial log generation
   - All error recovery paths

### Test Utilities

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock

class MockLLMClient(BaseLLMClient):
    """Mock client for testing with predefined responses"""
    
    def __init__(self, responses: list):
        self.responses = responses
        self.call_count = 0
    
    def generate_response(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response
    
    def generate_structured_response(self, system_prompt: str, user_prompt: str, response_schema: dict, temperature: float = 0.7) -> dict:
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response

@pytest.fixture
def game_config():
    """Standard test configuration"""
    return GameConfig({
        "game": {"num_rounds": 1, "max_turns_per_round": 5, "random_seed": 42},
        "players": [
            {"nickname": "Alice", "model_name": "gpt-4", "temperature": 0.7},
            {"nickname": "Bob", "model_name": "claude-3", "temperature": 0.7},
            {"nickname": "Charlie", "model_name": "gpt-3.5", "temperature": 0.7}
        ],
        "locations": ["Bank", "Airport", "Restaurant"]
    })

@pytest.fixture
def mock_llm_factory():
    """Mock LLM factory for testing"""
    factory = Mock(spec=LLMClientFactory)
    factory.create_client.return_value = MockLLMClient([
        "Bob",  # Question target
        "Is this a place with money?",  # Question
        "Yes, it is.",  # Answer
        # ... more responses
    ])
    return factory
```

### Coverage Enforcement

- CI/CD pipeline must enforce 100% coverage
- Pull requests blocked if coverage drops below 100%
- Coverage report generated for every test run
- Uncovered lines must be justified or covered

## Implementation Notes

### Technology Stack

- **Language**: Python 3.10+
- **Dependency Management**: Poetry
- **Configuration**: PyYAML
- **LLM API**: OpenRouter (unified API for multiple models)
- **Logging**: Loguru
- **Testing**: pytest with 100% line coverage requirement
- **Type Checking**: mypy
- **Code Formatting**: black, isort
- **Secret Management**: python-dotenv with .env file (gitignored)

### Project Structure

```
spyfall-arena/
├── spyfall_arena/              # Main package
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_loader.py
│   │   ├── config_schema.py
│   │   └── config_validator.py
│   ├── game/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── game_state.py
│   │   ├── role_assigner.py
│   │   ├── turn_manager.py
│   │   ├── voting_manager.py
│   │   ├── spy_guess_manager.py
│   │   └── scoring_engine.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base_client.py
│   │   ├── llm_client_factory.py
│   │   └── openrouter_client.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── prompt_builder.py
│   │   └── templates/
│   │       ├── system_prompt.txt
│   │       ├── civilian_role.txt
│   │       └── spy_role.txt
│   └── logging/
│       ├── __init__.py
│       ├── game_logger.py
│       └── metrics_calculator.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_role_assigner.py
│   │   ├── test_game_state.py
│   │   ├── test_turn_manager.py
│   │   ├── test_voting_manager.py
│   │   ├── test_scoring_engine.py
│   │   ├── test_llm_client.py
│   │   └── test_prompt_builder.py
│   └── integration/
│       ├── test_game_flow.py
│       ├── test_multi_round.py
│       └── test_error_handling.py
├── logs/                       # Generated at runtime
├── game_runner.py              # Main entry point
├── config.yaml                 # Example configuration
├── .env.example                # Example environment variables
├── .env                        # Actual env vars (gitignored)
├── .gitignore
├── pyproject.toml              # Poetry configuration
├── poetry.lock                 # Poetry lock file
├── pytest.ini                  # Pytest configuration
├── mypy.ini                    # MyPy configuration
└── README.md
```

### Dependencies (pyproject.toml)

```toml
[tool.poetry.dependencies]
python = "^3.10"
pyyaml = "^6.0"
pydantic = "^2.0"
loguru = "^0.7.0"
python-dotenv = "^1.0"
httpx = "^0.25.0"  # For OpenRouter API calls

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
pytest-cov = "^4.1"  # For coverage reporting
pytest-asyncio = "^0.21"
mypy = "^1.7"
black = "^23.0"
isort = "^5.12"
```

### Environment Variables (.env file - gitignored)

```
OPENROUTER_API_KEY=sk-or-v1-...
```

### .gitignore additions

```
.env
.env.local
*.log
logs/
```

## Performance Considerations

1. **API Rate Limiting**:
   - Implement request throttling if needed
   - Add configurable delays between turns

2. **Concurrent Requests**:
   - Phase 1: Sequential requests (simpler)
   - Future: Parallel vote collection

3. **Memory Management**:
   - Stream large logs to disk incrementally
   - Clear conversation history if it grows too large

4. **Reproducibility**:
   - Use random.seed() for all randomization
   - Document any non-deterministic behavior

## Security Considerations

1. **API Key Management**:
   - Store API keys in `.env` file (gitignored)
   - Load using python-dotenv
   - Never log API keys in any output
   - Validate keys before game start
   - Use environment variable names in config, not actual keys
   - Example `.env.example` provided for reference

2. **Input Validation**:
   - Sanitize all LLM responses
   - Validate configuration inputs with Pydantic
   - Prevent injection attacks in prompts
   - Validate all structured responses against schemas

3. **Data Privacy**:
   - Don't log sensitive information
   - Make full prompt logging optional
   - Clear guidelines for data sharing
   - Sanitize any PII from logs

4. **Git Security**:
   - `.env` file must be in `.gitignore`
   - `logs/` directory in `.gitignore`
   - No hardcoded secrets in code
   - Pre-commit hooks to prevent secret commits (future enhancement)

## Future Extensibility

Design decisions that support future phases:

1. **Modular LLM Integration**: Easy to add new providers
2. **Pluggable Scoring**: Scoring engine can be extended
3. **Flexible Prompts**: Template-based system allows experimentation
4. **Rich Logging**: Comprehensive logs support advanced analysis
5. **State Management**: Clean state objects enable replay/analysis tools
