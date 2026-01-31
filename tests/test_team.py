"""Tests for the Team class."""

from vibegame.team import Team
from vibegame.world.territory import Territory


class TestTeam:
    """Tests for Team class."""

    def test_create_team_with_defaults(self) -> None:
        """Test creating a team with default values."""
        team = Team(name="Test", color=(255, 0, 0))

        assert team.name == "Test"
        assert team.color == (255, 0, 0)
        assert team.is_player is False
        assert team.resources == 100.0
        assert team.happiness == 50.0
        assert team.military_power == 25.0
        assert team.territories == []

    def test_create_player_team(self) -> None:
        """Test creating a player-controlled team."""
        team = Team(name="Player", color=(0, 0, 255), is_player=True)

        assert team.is_player is True

    def test_custom_stats(self) -> None:
        """Test creating a team with custom stats."""
        team = Team(
            name="Custom",
            color=(0, 255, 0),
            resources=200.0,
            happiness=75.0,
            military_power=50.0,
        )

        assert team.resources == 200.0
        assert team.happiness == 75.0
        assert team.military_power == 50.0

    def test_default_stat_priorities(self) -> None:
        """Test that default stat priorities are set."""
        team = Team(name="Test", color=(255, 0, 0))

        assert "military" in team.stat_priorities
        assert "resources" in team.stat_priorities
        assert "happiness" in team.stat_priorities

    def test_custom_stat_priorities(self) -> None:
        """Test setting custom stat priorities."""
        priorities = {"military": 0.8, "resources": 0.1, "happiness": 0.1}
        team = Team(name="Test", color=(255, 0, 0), stat_priorities=priorities)

        assert team.stat_priorities["military"] == 0.8

    def test_territory_count(self) -> None:
        """Test territory count property."""
        team = Team(name="Test", color=(255, 0, 0))
        assert team.territory_count == 0

        territory = Territory(id=0, grid_x=0, grid_y=0)
        team.add_territory(territory)
        assert team.territory_count == 1

    def test_add_territory(self) -> None:
        """Test adding a territory to a team."""
        team = Team(name="Test", color=(255, 0, 0))
        territory = Territory(id=0, grid_x=0, grid_y=0)

        team.add_territory(territory)

        assert territory in team.territories
        assert territory.owner is team

    def test_add_territory_twice(self) -> None:
        """Test that adding the same territory twice doesn't duplicate."""
        team = Team(name="Test", color=(255, 0, 0))
        territory = Territory(id=0, grid_x=0, grid_y=0)

        team.add_territory(territory)
        team.add_territory(territory)

        assert len(team.territories) == 1

    def test_remove_territory(self) -> None:
        """Test removing a territory from a team."""
        team = Team(name="Test", color=(255, 0, 0))
        territory = Territory(id=0, grid_x=0, grid_y=0)

        team.add_territory(territory)
        team.remove_territory(territory)

        assert territory not in team.territories
        assert territory.owner is None

    def test_is_eliminated_with_territories(self) -> None:
        """Test is_eliminated returns False when team has territories."""
        team = Team(name="Test", color=(255, 0, 0))
        territory = Territory(id=0, grid_x=0, grid_y=0)
        team.add_territory(territory)

        assert team.is_eliminated() is False

    def test_is_eliminated_without_territories(self) -> None:
        """Test is_eliminated returns True when team has no territories."""
        team = Team(name="Test", color=(255, 0, 0))

        assert team.is_eliminated() is True
