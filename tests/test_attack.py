"""Tests for the AttackAction class."""

from unittest.mock import patch

import pytest

from vibegame.actions.attack import AttackAction
from vibegame.team import Team
from vibegame.world.territory import Territory


class TestAttackActionValidity:
    """Tests for attack validity checks."""

    def test_valid_attack_on_enemy_territory(self) -> None:
        """Test that attacking adjacent enemy territory is valid."""
        attacker = Team(name="Attacker", color=(255, 0, 0))
        defender = Team(name="Defender", color=(0, 255, 0))

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)
        defender.add_territory(to_territory)

        action = AttackAction(attacker, defender, from_territory, to_territory)
        assert action.is_valid() is True

    def test_valid_attack_on_empty_territory(self) -> None:
        """Test that attacking adjacent empty territory is valid."""
        attacker = Team(name="Attacker", color=(255, 0, 0))

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)

        action = AttackAction(attacker, None, from_territory, to_territory)
        assert action.is_valid() is True

    def test_invalid_attack_non_adjacent(self) -> None:
        """Test that attacking non-adjacent territory is invalid."""
        attacker = Team(name="Attacker", color=(255, 0, 0))
        defender = Team(name="Defender", color=(0, 255, 0))

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=2, grid_x=2, grid_y=0, neighbor_ids=[1])

        attacker.add_territory(from_territory)
        defender.add_territory(to_territory)

        action = AttackAction(attacker, defender, from_territory, to_territory)
        assert action.is_valid() is False

    def test_invalid_attack_own_territory(self) -> None:
        """Test that attacking own territory is invalid."""
        attacker = Team(name="Attacker", color=(255, 0, 0))

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)
        attacker.add_territory(to_territory)

        action = AttackAction(attacker, attacker, from_territory, to_territory)
        assert action.is_valid() is False

    def test_invalid_attack_from_unowned_territory(self) -> None:
        """Test that attacking from unowned territory is invalid."""
        attacker = Team(name="Attacker", color=(255, 0, 0))
        defender = Team(name="Defender", color=(0, 255, 0))

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        defender.add_territory(to_territory)

        action = AttackAction(attacker, defender, from_territory, to_territory)
        assert action.is_valid() is False

    def test_invalid_attack_wrong_target(self) -> None:
        """Test that specifying wrong target team is invalid."""
        attacker = Team(name="Attacker", color=(255, 0, 0))
        defender = Team(name="Defender", color=(0, 255, 0))
        other = Team(name="Other", color=(0, 0, 255))

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)
        defender.add_territory(to_territory)

        action = AttackAction(attacker, other, from_territory, to_territory)
        assert action.is_valid() is False


class TestAttackEmptyTerritory:
    """Tests for capturing empty territories."""

    def test_capture_empty_territory(self) -> None:
        """Test capturing an empty territory succeeds without combat."""
        attacker = Team(name="Attacker", color=(255, 0, 0), military_power=25)

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)

        action = AttackAction(attacker, None, from_territory, to_territory)
        result = action.execute()

        assert result.success is True
        assert result.territory_changed is to_territory
        assert to_territory.owner is attacker
        assert to_territory in attacker.territories
        assert attacker.military_power == 25  # No military loss

    def test_capture_empty_territory_message(self) -> None:
        """Test that capturing empty territory has correct message."""
        attacker = Team(name="Attacker", color=(255, 0, 0))

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)

        action = AttackAction(attacker, None, from_territory, to_territory)
        result = action.execute()

        assert "captured empty territory" in result.message


class TestCombatResolution:
    """Tests for combat mechanics."""

    def test_attacker_wins_combat(self) -> None:
        """Test that attacker wins when they roll higher."""
        attacker = Team(name="Attacker", color=(255, 0, 0), military_power=25)
        defender = Team(name="Defender", color=(0, 255, 0), military_power=25)

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)
        defender.add_territory(to_territory)

        action = AttackAction(attacker, defender, from_territory, to_territory)

        # Mock random.uniform to give attacker a higher roll
        with patch("vibegame.actions.attack.random.uniform") as mock_random:
            mock_random.side_effect = [4.0, 1.0]  # attacker rolls 4, defender rolls 1
            result = action.execute()

        assert result.success is True
        assert result.territory_changed is to_territory
        assert to_territory.owner is attacker
        assert to_territory in attacker.territories
        assert to_territory not in defender.territories

    def test_defender_wins_combat(self) -> None:
        """Test that defender wins when they roll higher."""
        attacker = Team(name="Attacker", color=(255, 0, 0), military_power=25)
        defender = Team(name="Defender", color=(0, 255, 0), military_power=25)

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)
        defender.add_territory(to_territory)

        action = AttackAction(attacker, defender, from_territory, to_territory)

        # Mock random.uniform to give defender a higher roll
        with patch("vibegame.actions.attack.random.uniform") as mock_random:
            mock_random.side_effect = [1.0, 4.0]  # attacker rolls 1, defender rolls 4
            result = action.execute()

        assert result.success is False
        assert result.territory_changed is None
        assert to_territory.owner is defender
        assert attacker.military_power == 20  # Lost 20% of military power

    def test_attacker_loses_military_on_failed_attack(self) -> None:
        """Test that attacker loses 20% of military power on defeat."""
        attacker = Team(name="Attacker", color=(255, 0, 0), military_power=100)
        defender = Team(name="Defender", color=(0, 255, 0), military_power=25)

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)
        defender.add_territory(to_territory)

        action = AttackAction(attacker, defender, from_territory, to_territory)

        with patch("vibegame.actions.attack.random.uniform") as mock_random:
            mock_random.side_effect = [0.1, 5.0]  # attacker loses badly
            action.execute()

        assert attacker.military_power == 80  # Lost 20% of military power

    def test_tie_goes_to_defender(self) -> None:
        """Test that ties favor the defender."""
        attacker = Team(name="Attacker", color=(255, 0, 0), military_power=25)
        defender = Team(name="Defender", color=(0, 255, 0), military_power=25)

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)
        defender.add_territory(to_territory)

        action = AttackAction(attacker, defender, from_territory, to_territory)

        with patch("vibegame.actions.attack.random.uniform") as mock_random:
            mock_random.side_effect = [3.0, 3.0]  # same roll
            result = action.execute()

        assert result.success is False
        assert to_territory.owner is defender


class TestCombatEdgeCases:
    """Tests for edge cases in combat."""

    def test_attacker_zero_military_power(self) -> None:
        """Test combat with zero military power for attacker."""
        attacker = Team(name="Attacker", color=(255, 0, 0), military_power=0)
        defender = Team(name="Defender", color=(0, 255, 0), military_power=25)

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)
        defender.add_territory(to_territory)

        action = AttackAction(attacker, defender, from_territory, to_territory)

        with patch("vibegame.actions.attack.random.uniform") as mock_random:
            mock_random.side_effect = [5.0, 5.0]
            result = action.execute()

        # With 0 military, attacker gets 0 * 5 = 0, defender gets 25 * 5 = 125
        assert result.success is False
        assert attacker.military_power == 0  # Can't go negative

    def test_defender_zero_military_power(self) -> None:
        """Test combat with zero military power for defender."""
        attacker = Team(name="Attacker", color=(255, 0, 0), military_power=25)
        defender = Team(name="Defender", color=(0, 255, 0), military_power=0)

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)
        defender.add_territory(to_territory)

        action = AttackAction(attacker, defender, from_territory, to_territory)

        with patch("vibegame.actions.attack.random.uniform") as mock_random:
            mock_random.side_effect = [0.1, 5.0]  # Even tiny roll beats 0
            result = action.execute()

        assert result.success is True
        assert to_territory.owner is attacker

    def test_low_military_power_still_loses_20_percent(self) -> None:
        """Test that 20% loss applies correctly to low military power."""
        attacker = Team(name="Attacker", color=(255, 0, 0), military_power=3)
        defender = Team(name="Defender", color=(0, 255, 0), military_power=100)

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)
        defender.add_territory(to_territory)

        action = AttackAction(attacker, defender, from_territory, to_territory)

        with patch("vibegame.actions.attack.random.uniform") as mock_random:
            mock_random.side_effect = [0.1, 5.0]
            action.execute()

        assert attacker.military_power == pytest.approx(2.4)  # 3 * 0.8

    def test_defender_elimination(self) -> None:
        """Test that defender with only one territory gets eliminated."""
        attacker = Team(name="Attacker", color=(255, 0, 0), military_power=25)
        defender = Team(name="Defender", color=(0, 255, 0), military_power=25)

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[1])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[0])

        attacker.add_territory(from_territory)
        defender.add_territory(to_territory)

        assert defender.is_eliminated() is False

        action = AttackAction(attacker, defender, from_territory, to_territory)

        with patch("vibegame.actions.attack.random.uniform") as mock_random:
            mock_random.side_effect = [5.0, 0.1]
            action.execute()

        assert defender.is_eliminated() is True

    def test_invalid_attack_returns_failure(self) -> None:
        """Test that invalid attack returns failure without executing."""
        attacker = Team(name="Attacker", color=(255, 0, 0), military_power=25)
        defender = Team(name="Defender", color=(0, 255, 0), military_power=25)

        from_territory = Territory(id=0, grid_x=0, grid_y=0, neighbor_ids=[])
        to_territory = Territory(id=1, grid_x=1, grid_y=0, neighbor_ids=[])

        attacker.add_territory(from_territory)
        defender.add_territory(to_territory)

        action = AttackAction(attacker, defender, from_territory, to_territory)
        result = action.execute()

        assert result.success is False
        assert "Invalid attack" in result.message
        assert to_territory.owner is defender
