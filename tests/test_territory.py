"""Tests for the Territory class."""

from vibegame.team import Team
from vibegame.world.territory import Territory


class TestTerritory:
    """Tests for Territory class."""

    def test_create_territory(self) -> None:
        """Test creating a basic territory."""
        territory = Territory(id=0, grid_x=5, grid_y=3)

        assert territory.id == 0
        assert territory.grid_x == 5
        assert territory.grid_y == 3
        assert territory.owner is None
        assert territory.neighbor_ids == []

    def test_position_property(self) -> None:
        """Test the position property."""
        territory = Territory(id=0, grid_x=5, grid_y=3)

        assert territory.position == (5, 3)

    def test_is_adjacent_to(self) -> None:
        """Test checking adjacency between territories."""
        territory1 = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        territory2 = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])
        territory3 = Territory(id=2, grid_x=2, grid_y=0, neighbor_ids=[1])

        assert territory1.is_adjacent_to(territory2) is True
        assert territory2.is_adjacent_to(territory1) is True
        assert territory1.is_adjacent_to(territory3) is False

    def test_is_owned(self) -> None:
        """Test checking if territory has an owner."""
        territory = Territory(id=0, grid_x=0, grid_y=0)
        assert territory.is_owned() is False

        team = Team(name="Test", color=(255, 0, 0))
        territory.owner = team
        assert territory.is_owned() is True

    def test_is_owned_by(self) -> None:
        """Test checking if territory is owned by a specific team."""
        territory = Territory(id=0, grid_x=0, grid_y=0)
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))

        territory.owner = team1

        assert territory.is_owned_by(team1) is True
        assert territory.is_owned_by(team2) is False


class TestTerritoryNeighbors:
    """Tests for territory neighbor relationships."""

    def test_neighbors_with_ids(self) -> None:
        """Test setting neighbor IDs."""
        territory = Territory(id=5, grid_x=1, grid_y=1, neighbor_ids=[0, 1, 6, 10])

        assert 0 in territory.neighbor_ids
        assert 1 in territory.neighbor_ids
        assert 6 in territory.neighbor_ids
        assert 10 in territory.neighbor_ids
        assert 5 not in territory.neighbor_ids  # Not its own neighbor
