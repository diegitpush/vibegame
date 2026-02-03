"""Tests for the NegotiateAction and alliance functionality."""

from vibegame.actions.negotiate import (
    AcceptAllianceAction,
    DeclineAllianceAction,
    NegotiateAction,
)
from vibegame.team import Team
from vibegame.world.map import GameMap


class TestAllianceFormation:
    """Tests for alliance formation mechanics."""

    def test_form_alliance_costs_happiness(self) -> None:
        """Test that forming an alliance costs 1/3 of each team's happiness."""
        team1 = Team(name="Team1", color=(255, 0, 0), happiness=90)
        team2 = Team(name="Team2", color=(0, 255, 0), happiness=60)

        team1.form_alliance(team2, duration=15)

        # Each team should lose 1/3 of their happiness
        assert team1.happiness == 60  # 90 - 30
        assert team2.happiness == 40  # 60 - 20

    def test_form_alliance_sets_duration(self) -> None:
        """Test that alliance is set with correct duration on both sides."""
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))

        team1.form_alliance(team2, duration=15)

        assert team1.alliances["Team2"] == 15
        assert team2.alliances["Team1"] == 15

    def test_is_allied_with(self) -> None:
        """Test the is_allied_with method."""
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))
        team3 = Team(name="Team3", color=(0, 0, 255))

        team1.form_alliance(team2, duration=10)

        assert team1.is_allied_with(team2) is True
        assert team2.is_allied_with(team1) is True
        assert team1.is_allied_with(team3) is False


class TestAllianceTicking:
    """Tests for alliance duration countdown."""

    def test_tick_decrements_turns(self) -> None:
        """Test that ticking decrements alliance turns."""
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))

        team1.form_alliance(team2, duration=5)

        team1.tick_alliances()

        assert team1.alliances["Team2"] == 4

    def test_tick_removes_expired_alliance(self) -> None:
        """Test that alliance is removed when it expires."""
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))

        team1.form_alliance(team2, duration=1)

        expired = team1.tick_alliances()

        assert "Team2" in expired
        assert "Team2" not in team1.alliances
        assert team1.is_allied_with(team2) is False

    def test_tick_returns_expired_names(self) -> None:
        """Test that tick_alliances returns list of expired team names."""
        team1 = Team(name="Team1", color=(255, 0, 0))

        team1.alliances["Team2"] = 1  # Will expire
        team1.alliances["Team3"] = 5  # Will not expire

        expired = team1.tick_alliances()

        assert expired == ["Team2"]
        assert "Team3" in team1.alliances


class TestNegotiateAction:
    """Tests for the NegotiateAction class."""

    def test_negotiate_requires_min_shared_borders(self) -> None:
        """Test that negotiation requires minimum shared borders."""
        game_map = GameMap(cols=10, rows=8)
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))

        # Give teams territories that don't share enough borders
        t1 = game_map.get_territory_at(0, 0)
        t2 = game_map.get_territory_at(9, 7)
        assert t1 is not None and t2 is not None

        team1.add_territory(t1)
        team2.add_territory(t2)

        action = NegotiateAction(team1, team2, game_map)

        assert action.is_valid() is False

    def test_negotiate_with_enough_borders(self) -> None:
        """Test that negotiation is valid with enough shared borders."""
        game_map = GameMap(cols=10, rows=8)
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))

        # Give team1 three adjacent territories
        t00 = game_map.get_territory_at(0, 0)
        t10 = game_map.get_territory_at(1, 0)
        t20 = game_map.get_territory_at(2, 0)
        assert t00 and t10 and t20

        team1.add_territory(t00)
        team1.add_territory(t10)
        team1.add_territory(t20)

        # Give team2 three territories that share borders with team1
        t01 = game_map.get_territory_at(0, 1)
        t11 = game_map.get_territory_at(1, 1)
        t21 = game_map.get_territory_at(2, 1)
        assert t01 and t11 and t21

        team2.add_territory(t01)
        team2.add_territory(t11)
        team2.add_territory(t21)

        action = NegotiateAction(team1, team2, game_map)

        # Should have 3 shared borders
        assert action.count_shared_borders() == 3
        assert action.is_valid() is True

    def test_negotiate_creates_pending_offer(self) -> None:
        """Test that execute creates a pending offer."""
        game_map = GameMap(cols=10, rows=8)
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))

        # Set up territories with enough shared borders
        for x in range(3):
            t_upper = game_map.get_territory_at(x, 0)
            t_lower = game_map.get_territory_at(x, 1)
            assert t_upper and t_lower
            team1.add_territory(t_upper)
            team2.add_territory(t_lower)

        action = NegotiateAction(team1, team2, game_map)
        result = action.execute()

        assert result.success is True
        assert team2.has_pending_offer_from(team1) is True

    def test_cannot_negotiate_with_ally(self) -> None:
        """Test that you cannot negotiate with an existing ally."""
        game_map = GameMap(cols=10, rows=8)
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))

        # Set up alliance
        team1.form_alliance(team2)

        # Set up territories
        for x in range(3):
            t_upper = game_map.get_territory_at(x, 0)
            t_lower = game_map.get_territory_at(x, 1)
            assert t_upper and t_lower
            team1.add_territory(t_upper)
            team2.add_territory(t_lower)

        action = NegotiateAction(team1, team2, game_map)

        assert action.is_valid() is False


class TestAcceptAllianceAction:
    """Tests for accepting alliance offers."""

    def test_accept_alliance_forms_alliance(self) -> None:
        """Test that accepting an offer forms an alliance."""
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))

        # Simulate pending offer
        team2.add_pending_offer_from(team1)

        action = AcceptAllianceAction(team2, team1)
        result = action.execute()

        assert result.success is True
        assert team1.is_allied_with(team2) is True
        assert team2.is_allied_with(team1) is True
        assert team2.has_pending_offer_from(team1) is False

    def test_accept_requires_pending_offer(self) -> None:
        """Test that you can only accept existing offers."""
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))

        action = AcceptAllianceAction(team2, team1)

        assert action.is_valid() is False


class TestDeclineAllianceAction:
    """Tests for declining alliance offers."""

    def test_decline_clears_offer(self) -> None:
        """Test that declining clears the pending offer."""
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))

        # Simulate pending offer
        team2.add_pending_offer_from(team1)

        action = DeclineAllianceAction(team2, team1)
        result = action.execute()

        assert result.success is True
        assert team2.has_pending_offer_from(team1) is False
        assert team1.is_allied_with(team2) is False

    def test_decline_requires_pending_offer(self) -> None:
        """Test that you can only decline existing offers."""
        team1 = Team(name="Team1", color=(255, 0, 0))
        team2 = Team(name="Team2", color=(0, 255, 0))

        action = DeclineAllianceAction(team2, team1)

        assert action.is_valid() is False


class TestAllianceBlocksAttacks:
    """Tests for alliance preventing attacks."""

    def test_cannot_attack_ally(self) -> None:
        """Test that attacking an allied team is invalid."""
        from vibegame.actions.attack import AttackAction
        from vibegame.world.territory import Territory

        attacker = Team(name="Attacker", color=(255, 0, 0))
        defender = Team(name="Defender", color=(0, 255, 0))

        # Form alliance
        attacker.form_alliance(defender, duration=10)

        # Set up adjacent territories
        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)
        defender.add_territory(to_territory)

        action = AttackAction(attacker, defender, from_territory, to_territory)

        assert action.is_valid() is False
