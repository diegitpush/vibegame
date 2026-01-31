"""Tests for the GameMap class."""

from vibegame.team import Team
from vibegame.world.map import GameMap


class TestGameMap:
    """Tests for GameMap class."""

    def test_create_map(self) -> None:
        """Test creating a map with given dimensions."""
        game_map = GameMap(cols=10, rows=8)

        assert game_map.cols == 10
        assert game_map.rows == 8
        assert game_map.total_territories == 80

    def test_get_territory(self) -> None:
        """Test getting a territory by ID."""
        game_map = GameMap(cols=5, rows=5)

        territory = game_map.get_territory(0)
        assert territory is not None
        assert territory.id == 0

        territory = game_map.get_territory(12)
        assert territory is not None
        assert territory.id == 12

        territory = game_map.get_territory(999)
        assert territory is None

    def test_get_territory_at(self) -> None:
        """Test getting a territory by grid coordinates."""
        game_map = GameMap(cols=5, rows=5)

        territory = game_map.get_territory_at(0, 0)
        assert territory is not None
        assert territory.id == 0

        territory = game_map.get_territory_at(2, 3)
        assert territory is not None
        assert territory.id == 17  # 3 * 5 + 2

        territory = game_map.get_territory_at(10, 10)
        assert territory is None


class TestMapNeighbors:
    """Tests for map neighbor relationships."""

    def test_corner_neighbors(self) -> None:
        """Test that corner territories have 2 neighbors."""
        game_map = GameMap(cols=5, rows=5)

        # Top-left corner (0,0)
        territory = game_map.get_territory_at(0, 0)
        assert territory is not None
        neighbors = game_map.get_neighbors(territory.id)
        assert len(neighbors) == 2

        # Bottom-right corner (4,4)
        territory = game_map.get_territory_at(4, 4)
        assert territory is not None
        neighbors = game_map.get_neighbors(territory.id)
        assert len(neighbors) == 2

    def test_edge_neighbors(self) -> None:
        """Test that edge territories have 3 neighbors."""
        game_map = GameMap(cols=5, rows=5)

        # Top edge (2,0)
        territory = game_map.get_territory_at(2, 0)
        assert territory is not None
        neighbors = game_map.get_neighbors(territory.id)
        assert len(neighbors) == 3

    def test_center_neighbors(self) -> None:
        """Test that center territories have 4 neighbors."""
        game_map = GameMap(cols=5, rows=5)

        # Center (2,2)
        territory = game_map.get_territory_at(2, 2)
        assert territory is not None
        neighbors = game_map.get_neighbors(territory.id)
        assert len(neighbors) == 4

    def test_neighbor_correctness(self) -> None:
        """Test that neighbors are correctly identified."""
        game_map = GameMap(cols=5, rows=5)

        # Territory at (2,2) should have neighbors at (1,2), (3,2), (2,1), (2,3)
        center = game_map.get_territory_at(2, 2)
        assert center is not None
        neighbors = game_map.get_neighbors(center.id)
        neighbor_positions = [(n.grid_x, n.grid_y) for n in neighbors]

        assert (1, 2) in neighbor_positions  # Left
        assert (3, 2) in neighbor_positions  # Right
        assert (2, 1) in neighbor_positions  # Up
        assert (2, 3) in neighbor_positions  # Down


class TestMapTeams:
    """Tests for team-related map functionality."""

    def test_get_team_territories(self) -> None:
        """Test getting all territories owned by a team."""
        game_map = GameMap(cols=5, rows=5)
        team = Team(name="Test", color=(255, 0, 0))

        # Initially no territories
        assert game_map.get_team_territories(team) == []

        # Add some territories
        t1 = game_map.get_territory_at(0, 0)
        t2 = game_map.get_territory_at(1, 0)
        assert t1 is not None and t2 is not None

        team.add_territory(t1)
        team.add_territory(t2)

        territories = game_map.get_team_territories(team)
        assert len(territories) == 2
        assert t1 in territories
        assert t2 in territories

    def test_get_border_territories(self) -> None:
        """Test getting border territories."""
        game_map = GameMap(cols=5, rows=5)
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))

        # Team1 owns (0,0), (1,0), (0,1)
        t00 = game_map.get_territory_at(0, 0)
        t10 = game_map.get_territory_at(1, 0)
        t01 = game_map.get_territory_at(0, 1)
        assert t00 is not None and t10 is not None and t01 is not None

        team1.add_territory(t00)
        team1.add_territory(t10)
        team1.add_territory(t01)

        # Team2 owns (2,0)
        t20 = game_map.get_territory_at(2, 0)
        assert t20 is not None
        team2.add_territory(t20)

        # Team1 border territories should include (1,0) which borders Team2
        border = game_map.get_border_territories(team1)
        assert t10 in border

    def test_assign_clustered_start(self) -> None:
        """Test assigning clustered starting territories."""
        game_map = GameMap(cols=10, rows=8)
        teams = [
            Team(name="Team1", color=(255, 0, 0)),
            Team(name="Team2", color=(0, 255, 0)),
        ]

        game_map.assign_clustered_start(teams, territories_per_team=5)

        # Each team should have 5 territories
        assert teams[0].territory_count == 5
        assert teams[1].territory_count == 5

        # Territories should be clustered (all adjacent to at least one other)
        for team in teams:
            for territory in team.territories:
                # Verify territories were assigned to the correct team
                assert territory.owner is team
