"""Tests for stat interaction methods."""

from unittest.mock import patch

from vibegame.team import Team


class TestResourceGrowth:
    """Tests for apply_resource_growth method."""

    def test_resource_growth_from_territories(self) -> None:
        """Resource growth should include territory-based component."""
        team = Team(name="Test", color=(0, 0, 0), resources=100.0)
        # Add mock territories
        team.territories = [object() for _ in range(5)]  # type: ignore[list-item]

        # With random returning 0.9, base = int(5 * 0.9) = 4
        with patch("vibegame.team.random.random", return_value=0.9):
            gained = team.apply_resource_growth()

        # 5 territories * 0.9 = 4 (truncated) + 50 happiness * 0.9 = 45 = 49 total
        assert gained == 49
        assert team.resources == 149.0

    def test_resource_growth_from_happiness(self) -> None:
        """Resource growth should include happiness-based component."""
        team = Team(name="Test", color=(0, 0, 0), resources=100.0, happiness=80.0)

        # With random returning 0.5: base = int(0 * 0.5) = 0, bonus = int(80 * 0.5) = 40
        with patch("vibegame.team.random.random", return_value=0.5):
            gained = team.apply_resource_growth()

        assert gained == 40
        assert team.resources == 140.0

    def test_resource_growth_truncates(self) -> None:
        """Resource growth should use int() truncation."""
        team = Team(name="Test", color=(0, 0, 0), resources=100.0, happiness=33.0)
        team.territories = [object() for _ in range(3)]  # type: ignore[list-item]

        # With random returning 0.7: base = int(3 * 0.7) = 2, bonus = int(33 * 0.7) = 23
        with patch("vibegame.team.random.random", return_value=0.7):
            gained = team.apply_resource_growth()

        assert gained == 25  # 2 + 23
        assert team.resources == 125.0


class TestHappinessDecay:
    """Tests for apply_happiness_decay method."""

    def test_happiness_decay_default(self) -> None:
        """Happiness should decay by default amount (5)."""
        team = Team(name="Test", color=(0, 0, 0), happiness=50.0)

        team.apply_happiness_decay()

        assert team.happiness == 45.0

    def test_happiness_decay_custom_amount(self) -> None:
        """Happiness should decay by specified amount."""
        team = Team(name="Test", color=(0, 0, 0), happiness=50.0)

        team.apply_happiness_decay(10.0)

        assert team.happiness == 40.0

    def test_happiness_decay_clamps_at_zero(self) -> None:
        """Happiness should not go below 0."""
        team = Team(name="Test", color=(0, 0, 0), happiness=3.0)

        team.apply_happiness_decay(5.0)

        assert team.happiness == 0.0


class TestSpendOnHappiness:
    """Tests for spend_on_happiness method."""

    def test_spend_on_happiness_success(self) -> None:
        """Spending should convert resources to happiness 1:1."""
        team = Team(name="Test", color=(0, 0, 0), resources=100.0, happiness=50.0)

        result = team.spend_on_happiness(10.0)

        assert result is True
        assert team.resources == 90.0
        assert team.happiness == 60.0

    def test_spend_on_happiness_insufficient(self) -> None:
        """Spending should fail if not enough resources."""
        team = Team(name="Test", color=(0, 0, 0), resources=5.0, happiness=50.0)

        result = team.spend_on_happiness(10.0)

        assert result is False
        assert team.resources == 5.0
        assert team.happiness == 50.0

    def test_spend_on_happiness_exact_amount(self) -> None:
        """Spending should work when resources exactly match."""
        team = Team(name="Test", color=(0, 0, 0), resources=10.0, happiness=50.0)

        result = team.spend_on_happiness(10.0)

        assert result is True
        assert team.resources == 0.0
        assert team.happiness == 60.0


class TestSpendOnMilitary:
    """Tests for spend_on_military method."""

    def test_spend_on_military_success(self) -> None:
        """Spending should convert resources to military 1:1."""
        team = Team(name="Test", color=(0, 0, 0), resources=100.0, military_power=25.0)

        result = team.spend_on_military(10.0)

        assert result is True
        assert team.resources == 90.0
        assert team.military_power == 35.0

    def test_spend_on_military_insufficient(self) -> None:
        """Spending should fail if not enough resources."""
        team = Team(name="Test", color=(0, 0, 0), resources=5.0, military_power=25.0)

        result = team.spend_on_military(10.0)

        assert result is False
        assert team.resources == 5.0
        assert team.military_power == 25.0

    def test_spend_on_military_exact_amount(self) -> None:
        """Spending should work when resources exactly match."""
        team = Team(name="Test", color=(0, 0, 0), resources=10.0, military_power=25.0)

        result = team.spend_on_military(10.0)

        assert result is True
        assert team.resources == 0.0
        assert team.military_power == 35.0
