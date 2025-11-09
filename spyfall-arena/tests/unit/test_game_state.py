import pytest

from spyfall_arena.game.game_state import (GamePhase, GameState, Role,
                                           RoundPhase, RoundState)


@pytest.fixture
def initial_game_state() -> GameState:
    """Provides a GameState in the INITIALIZING phase."""
    return GameState(game_id="test_game", phase=GamePhase.INITIALIZING)


@pytest.fixture
def initial_round_state() -> RoundState:
    """Provides a RoundState in the ROLE_ASSIGNMENT phase."""
    return RoundState(
        round_number=1,
        phase=RoundPhase.ROLE_ASSIGNMENT,
        location="Bank",
        spy_nickname="Alice",
        role_assignments={"Alice": Role(is_spy=True, location=None)},
    )


class TestGameStateTransitions:
    def test_initializing_to_in_progress(self, initial_game_state: GameState):
        assert initial_game_state.transition_to(GamePhase.IN_PROGRESS)
        assert initial_game_state.phase == GamePhase.IN_PROGRESS

    def test_initializing_to_error(self, initial_game_state: GameState):
        assert initial_game_state.transition_to(GamePhase.ERROR)
        assert initial_game_state.phase == GamePhase.ERROR

    def test_in_progress_to_completed(self):
        state = GameState(game_id="test", phase=GamePhase.IN_PROGRESS)
        assert state.transition_to(GamePhase.COMPLETED)
        assert state.phase == GamePhase.COMPLETED

    def test_in_progress_to_error(self):
        state = GameState(game_id="test", phase=GamePhase.IN_PROGRESS)
        assert state.transition_to(GamePhase.ERROR)
        assert state.phase == GamePhase.ERROR

    def test_invalid_transition_from_initializing(self, initial_game_state: GameState):
        assert not initial_game_state.transition_to(GamePhase.COMPLETED)
        assert initial_game_state.phase == GamePhase.INITIALIZING

    def test_invalid_transition_from_completed(self):
        state = GameState(game_id="test", phase=GamePhase.COMPLETED)
        assert not state.transition_to(GamePhase.IN_PROGRESS)
        assert state.phase == GamePhase.COMPLETED


class TestRoundStateTransitions:
    def test_role_assignment_to_questioning(self, initial_round_state: RoundState):
        assert initial_round_state.transition_to(RoundPhase.QUESTIONING)
        assert initial_round_state.phase == RoundPhase.QUESTIONING

    def test_questioning_to_voting(self):
        state = RoundState(
            round_number=1,
            phase=RoundPhase.QUESTIONING,
            location="L",
            spy_nickname="S",
            role_assignments={},
        )
        assert state.transition_to(RoundPhase.VOTING)
        assert state.phase == RoundPhase.VOTING

    def test_questioning_to_spy_guessing(self):
        state = RoundState(
            round_number=1,
            phase=RoundPhase.QUESTIONING,
            location="L",
            spy_nickname="S",
            role_assignments={},
        )
        assert state.transition_to(RoundPhase.SPY_GUESSING)
        assert state.phase == RoundPhase.SPY_GUESSING

    def test_questioning_to_scoring(self):
        state = RoundState(
            round_number=1,
            phase=RoundPhase.QUESTIONING,
            location="L",
            spy_nickname="S",
            role_assignments={},
        )
        assert state.transition_to(RoundPhase.SCORING)
        assert state.phase == RoundPhase.SCORING

    def test_voting_to_questioning(self):
        state = RoundState(
            round_number=1,
            phase=RoundPhase.VOTING,
            location="L",
            spy_nickname="S",
            role_assignments={},
        )
        assert state.transition_to(RoundPhase.QUESTIONING)
        assert state.phase == RoundPhase.QUESTIONING

    def test_voting_to_scoring(self):
        state = RoundState(
            round_number=1,
            phase=RoundPhase.VOTING,
            location="L",
            spy_nickname="S",
            role_assignments={},
        )
        assert state.transition_to(RoundPhase.SCORING)
        assert state.phase == RoundPhase.SCORING

    def test_spy_guessing_to_scoring(self):
        state = RoundState(
            round_number=1,
            phase=RoundPhase.SPY_GUESSING,
            location="L",
            spy_nickname="S",
            role_assignments={},
        )
        assert state.transition_to(RoundPhase.SCORING)
        assert state.phase == RoundPhase.SCORING

    def test_scoring_to_completed(self):
        state = RoundState(
            round_number=1,
            phase=RoundPhase.SCORING,
            location="L",
            spy_nickname="S",
            role_assignments={},
        )
        assert state.transition_to(RoundPhase.COMPLETED)
        assert state.phase == RoundPhase.COMPLETED

    def test_invalid_transition_from_role_assignment(
        self, initial_round_state: RoundState
    ):
        assert not initial_round_state.transition_to(RoundPhase.VOTING)
        assert initial_round_state.phase == RoundPhase.ROLE_ASSIGNMENT

    def test_invalid_transition_from_completed(self):
        state = RoundState(
            round_number=1,
            phase=RoundPhase.COMPLETED,
            location="L",
            spy_nickname="S",
            role_assignments={},
        )
        assert not state.transition_to(RoundPhase.QUESTIONING)
        assert state.phase == RoundPhase.COMPLETED
