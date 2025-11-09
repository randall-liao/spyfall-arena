import pytest

from spyfall_arena.game.role_assigner import RoleAssigner


@pytest.fixture
def players() -> list[str]:
    return ["Alice", "Bob", "Charlie", "David"]


@pytest.fixture
def locations() -> list[str]:
    return ["Bank", "Airport", "Restaurant", "Hospital"]


def test_reproducibility(players: list[str], locations: list[str]):
    """Tests that the same seed produces the same role assignments."""
    assigner1 = RoleAssigner(random_seed=42)
    roles1, location1 = assigner1.assign_roles(players, locations)

    assigner2 = RoleAssigner(random_seed=42)
    roles2, location2 = assigner2.assign_roles(players, locations)

    assert roles1 == roles2
    assert location1 == location2


def test_different_seeds_produce_different_results(
    players: list[str], locations: list[str]
):
    """Tests that different seeds produce different role assignments."""
    assigner1 = RoleAssigner(random_seed=42)
    roles1, location1 = assigner1.assign_roles(players, locations)

    assigner2 = RoleAssigner(random_seed=101)
    roles2, location2 = assigner2.assign_roles(players, locations)

    assert roles1 != roles2 or location1 != location2


def test_exactly_one_spy(players: list[str], locations: list[str]):
    """Tests that exactly one spy is assigned."""
    assigner = RoleAssigner(random_seed=1)
    roles, _ = assigner.assign_roles(players, locations)

    spy_count = sum(1 for role in roles.values() if role.is_spy)
    assert spy_count == 1


def test_civilians_get_correct_location(players: list[str], locations: list[str]):
    """Tests that civilians are assigned the correct location and the spy is not."""
    assigner = RoleAssigner(random_seed=2)
    roles, selected_location = assigner.assign_roles(players, locations)

    for role in roles.values():
        if role.is_spy:
            assert role.location is None
        else:
            assert role.location == selected_location


def test_empty_player_list():
    """Tests that an error is raised for an empty player list."""
    assigner = RoleAssigner(random_seed=3)
    with pytest.raises(ValueError, match="Player list cannot be empty"):
        assigner.assign_roles([], ["Bank"])


def test_empty_location_list():
    """Tests that an error is raised for an empty location list."""
    assigner = RoleAssigner(random_seed=4)
    with pytest.raises(ValueError, match="Location list cannot be empty"):
        assigner.assign_roles(["Alice"], [])
