"""Tests for the AIController class."""

from vibegame.ai.controller import AIController
from vibegame.team import Team
from vibegame.world.map import GameMap


class TestAIController:
    """Tests for AIController class."""

    def test_create_controller(self) -> None:
        """Test creating an AI controller."""
        game_map = GameMap(cols=5, rows=5)
        team = Team(name="AI Team", color=(255, 0, 0))

        controller = AIController(team, game_map)

        assert controller.team is team
        assert controller.game_map is game_map

    def test_stat_priorities(self) -> None:
        """Test accessing stat priorities through controller."""
        game_map = GameMap(cols=5, rows=5)
        team = Team(
            name="AI Team",
            color=(255, 0, 0),
            stat_priorities={"military": 0.9, "resources": 0.05, "happiness": 0.05},
        )

        controller = AIController(team, game_map)

        assert controller.stat_priorities["military"] == 0.9

    def test_evaluate_targets_no_borders(self) -> None:
        """Test evaluating targets when no borders are shared."""
        game_map = GameMap(cols=10, rows=8)
        ai_team = Team(name="AI", color=(255, 0, 0))
        other_team = Team(name="Other", color=(0, 255, 0))

        # Give teams territories that don't border each other
        t1 = game_map.get_territory_at(0, 0)
        t2 = game_map.get_territory_at(9, 7)
        assert t1 is not None and t2 is not None

        ai_team.add_territory(t1)
        other_team.add_territory(t2)

        controller = AIController(ai_team, game_map)
        targets = controller.evaluate_targets([ai_team, other_team])

        # Other team is not adjacent, so not a valid target
        assert other_team not in targets

    def test_evaluate_targets_with_borders(self) -> None:
        """Test evaluating targets when borders are shared."""
        game_map = GameMap(cols=10, rows=8)
        ai_team = Team(name="AI", color=(255, 0, 0))
        other_team = Team(name="Other", color=(0, 255, 0))

        # Give teams adjacent territories
        t1 = game_map.get_territory_at(0, 0)
        t2 = game_map.get_territory_at(1, 0)  # Adjacent to t1
        assert t1 is not None and t2 is not None

        ai_team.add_territory(t1)
        other_team.add_territory(t2)

        controller = AIController(ai_team, game_map)
        targets = controller.evaluate_targets([ai_team, other_team])

        assert other_team in targets

    def test_evaluate_targets_excludes_self(self) -> None:
        """Test that team doesn't target itself."""
        game_map = GameMap(cols=5, rows=5)
        ai_team = Team(name="AI", color=(255, 0, 0))
        t1 = game_map.get_territory_at(0, 0)
        assert t1 is not None
        ai_team.add_territory(t1)

        controller = AIController(ai_team, game_map)
        targets = controller.evaluate_targets([ai_team])

        assert ai_team not in targets

    def test_evaluate_targets_excludes_eliminated(self) -> None:
        """Test that eliminated teams are not targets."""
        game_map = GameMap(cols=5, rows=5)
        ai_team = Team(name="AI", color=(255, 0, 0))
        eliminated_team = Team(name="Eliminated", color=(0, 255, 0))

        # AI has territory, eliminated team has none
        t1 = game_map.get_territory_at(0, 0)
        assert t1 is not None
        ai_team.add_territory(t1)

        controller = AIController(ai_team, game_map)
        targets = controller.evaluate_targets([ai_team, eliminated_team])

        assert eliminated_team not in targets

    def test_get_attackable_territories(self) -> None:
        """Test getting attackable territory pairs."""
        game_map = GameMap(cols=5, rows=5)
        ai_team = Team(name="AI", color=(255, 0, 0))
        enemy_team = Team(name="Enemy", color=(0, 255, 0))

        # AI owns (0,0), enemy owns (1,0)
        t00 = game_map.get_territory_at(0, 0)
        t10 = game_map.get_territory_at(1, 0)
        assert t00 is not None and t10 is not None

        ai_team.add_territory(t00)
        enemy_team.add_territory(t10)

        controller = AIController(ai_team, game_map)
        attackable = controller.get_attackable_territories(enemy_team)

        assert (t00.id, t10.id) in attackable

    def test_decide_action_captures_empty_territory(self) -> None:
        """Test that AI captures adjacent empty territories."""
        game_map = GameMap(cols=5, rows=5)
        ai_team = Team(name="AI", color=(255, 0, 0))
        t1 = game_map.get_territory_at(0, 0)
        assert t1 is not None
        ai_team.add_territory(t1)

        controller = AIController(ai_team, game_map)
        action = controller.decide_action([ai_team])

        # AI should try to capture adjacent empty territory
        assert action is not None
        assert action.name == "Attack"

    def test_decide_action_returns_none_when_surrounded(self) -> None:
        """Test that AI returns None when no expansion possible."""
        game_map = GameMap(cols=2, rows=2)
        ai_team = Team(name="AI", color=(255, 0, 0))

        # Give AI all territories so no expansion possible
        for territory in game_map.territories.values():
            ai_team.add_territory(territory)

        controller = AIController(ai_team, game_map)
        action = controller.decide_action([ai_team])

        # No empty territories or enemies to attack
        assert action is None
