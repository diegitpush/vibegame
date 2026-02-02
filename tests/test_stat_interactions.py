"""Tests for stat interaction methods."""

from vibegame.team import Team


class TestResourceGrowth:
    """Tests for apply_resource_growth method."""

    def test_resource_growth_scales_with_territory_ratio(self) -> None:
        """Resource growth should equal happiness * (territories / total)."""
        team = Team(name="Test", color=(0, 0, 0), resources=100.0, happiness=50.0)
        team.territories = [object() for _ in range(40)]  # type: ignore[list-item]

        # 50 happiness * (40 / 80 territories) = 50 * 0.5 = 25
        gained = team.apply_resource_growth(total_territories=80)

        assert gained == 25.0
        assert team.resources == 125.0

    def test_resource_growth_full_map_control(self) -> None:
        """Owning all territories gives full happiness as resources."""
        team = Team(name="Test", color=(0, 0, 0), resources=100.0, happiness=80.0)
        team.territories = [object() for _ in range(80)]  # type: ignore[list-item]

        # 80 happiness * (80 / 80) = 80
        gained = team.apply_resource_growth(total_territories=80)

        assert gained == 80.0
        assert team.resources == 180.0

    def test_resource_growth_no_territories(self) -> None:
        """No territories means no resource growth."""
        team = Team(name="Test", color=(0, 0, 0), resources=100.0, happiness=50.0)
        # No territories

        gained = team.apply_resource_growth(total_territories=80)

        assert gained == 0.0
        assert team.resources == 100.0

    def test_resource_growth_zero_total_territories(self) -> None:
        """Zero total territories should return 0 to avoid division by zero."""
        team = Team(name="Test", color=(0, 0, 0), resources=100.0, happiness=50.0)

        gained = team.apply_resource_growth(total_territories=0)

        assert gained == 0.0
        assert team.resources == 100.0


class TestHappinessDecay:
    """Tests for apply_happiness_decay method."""

    def test_happiness_decay_default(self) -> None:
        """Happiness should decay by default rate (10%)."""
        team = Team(name="Test", color=(0, 0, 0), happiness=50.0)

        team.apply_happiness_decay()

        assert team.happiness == 45.0  # 50 * 0.90

    def test_happiness_decay_custom_rate(self) -> None:
        """Happiness should decay by specified rate."""
        team = Team(name="Test", color=(0, 0, 0), happiness=50.0)

        team.apply_happiness_decay(0.20)  # 20% decay

        assert team.happiness == 40.0  # 50 * 0.80

    def test_happiness_decay_clamps_at_zero(self) -> None:
        """Happiness should not go below 0."""
        team = Team(name="Test", color=(0, 0, 0), happiness=10.0)

        team.apply_happiness_decay(1.5)  # Rate > 1.0 would go negative

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
