"""Tests for the animation module."""

import pytest

from vibegame.ui.animation import (
    AnimationManager,
    TerritoryAnimation,
    lerp_color,
)
from vibegame.world.territory import Territory


class TestLerpColor:
    """Tests for color interpolation."""

    def test_lerp_at_zero(self) -> None:
        """At t=0, should return color1."""
        color1 = (0, 0, 0)
        color2 = (255, 255, 255)
        assert lerp_color(color1, color2, 0.0) == (0, 0, 0)

    def test_lerp_at_one(self) -> None:
        """At t=1, should return color2."""
        color1 = (0, 0, 0)
        color2 = (255, 255, 255)
        assert lerp_color(color1, color2, 1.0) == (255, 255, 255)

    def test_lerp_at_half(self) -> None:
        """At t=0.5, should return midpoint color."""
        color1 = (0, 0, 0)
        color2 = (100, 200, 50)
        result = lerp_color(color1, color2, 0.5)
        assert result == (50, 100, 25)

    def test_lerp_clamps_t(self) -> None:
        """Should clamp t values outside 0-1 range."""
        color1 = (0, 0, 0)
        color2 = (100, 100, 100)
        # t < 0 should act like t = 0
        assert lerp_color(color1, color2, -0.5) == (0, 0, 0)
        # t > 1 should act like t = 1
        assert lerp_color(color1, color2, 1.5) == (100, 100, 100)


class TestTerritoryAnimation:
    """Tests for TerritoryAnimation."""

    @pytest.fixture
    def territory(self) -> Territory:
        """Create a test territory."""
        return Territory(1, 0, 0)

    def test_animation_initial_state(self, territory: Territory) -> None:
        """Animation should start at progress 0."""
        anim = TerritoryAnimation(
            territory=territory,
            original_color=(100, 100, 100),
            attacker_color=(200, 200, 200),
            success=True,
        )
        assert anim.progress == 0.0
        assert not anim.is_complete

    def test_animation_update_increments_progress(self, territory: Territory) -> None:
        """Update should increment progress based on dt and duration."""
        anim = TerritoryAnimation(
            territory=territory,
            original_color=(100, 100, 100),
            attacker_color=(200, 200, 200),
            success=True,
            duration=0.4,
        )
        # Update by half the duration
        running = anim.update(0.2)
        assert running is True
        assert anim.progress == pytest.approx(0.5, rel=0.01)

    def test_animation_completes(self, territory: Territory) -> None:
        """Animation should complete when progress reaches 1.0."""
        anim = TerritoryAnimation(
            territory=territory,
            original_color=(100, 100, 100),
            attacker_color=(200, 200, 200),
            success=True,
            duration=0.4,
        )
        # Update past the duration
        running = anim.update(0.5)
        assert running is False
        assert anim.is_complete
        assert anim.progress == 1.0

    def test_successful_attack_color_at_start(self, territory: Territory) -> None:
        """At start, color should be original."""
        anim = TerritoryAnimation(
            territory=territory,
            original_color=(0, 0, 0),
            attacker_color=(100, 100, 100),
            success=True,
        )
        assert anim.get_current_color() == (0, 0, 0)

    def test_successful_attack_color_at_midpoint(self, territory: Territory) -> None:
        """At midpoint, color should be attacker color."""
        anim = TerritoryAnimation(
            territory=territory,
            original_color=(0, 0, 0),
            attacker_color=(100, 100, 100),
            success=True,
        )
        anim.progress = 0.5
        assert anim.get_current_color() == (100, 100, 100)

    def test_successful_attack_color_at_end(self, territory: Territory) -> None:
        """At end of successful attack, color should remain attacker color."""
        anim = TerritoryAnimation(
            territory=territory,
            original_color=(0, 0, 0),
            attacker_color=(100, 100, 100),
            success=True,
        )
        anim.progress = 1.0
        assert anim.get_current_color() == (100, 100, 100)

    def test_failed_attack_color_at_end(self, territory: Territory) -> None:
        """At end of failed attack, color should return to original."""
        anim = TerritoryAnimation(
            territory=territory,
            original_color=(50, 50, 50),
            attacker_color=(200, 200, 200),
            success=False,
        )
        anim.progress = 1.0
        assert anim.get_current_color() == (50, 50, 50)


class TestAnimationManager:
    """Tests for AnimationManager."""

    @pytest.fixture
    def manager(self) -> AnimationManager:
        """Create a test animation manager."""
        return AnimationManager()

    @pytest.fixture
    def territory(self) -> Territory:
        """Create a test territory."""
        return Territory(1, 0, 0)

    def test_start_animation(
        self, manager: AnimationManager, territory: Territory
    ) -> None:
        """Should track animations for territories."""
        manager.start_attack_animation(
            territory=territory,
            original_color=(100, 100, 100),
            attacker_color=(200, 200, 200),
            success=True,
        )
        assert manager.has_animation(territory)

    def test_get_territory_color_with_animation(
        self, manager: AnimationManager, territory: Territory
    ) -> None:
        """Should return animated color when animation is active."""
        manager.start_attack_animation(
            territory=territory,
            original_color=(0, 0, 0),
            attacker_color=(100, 100, 100),
            success=True,
        )
        # At progress 0, should return original color
        color = manager.get_territory_color(territory, (255, 255, 255))
        assert color == (0, 0, 0)

    def test_get_territory_color_without_animation(
        self, manager: AnimationManager, territory: Territory
    ) -> None:
        """Should return default color when no animation."""
        color = manager.get_territory_color(territory, (255, 255, 255))
        assert color == (255, 255, 255)

    def test_update_removes_completed_animations(
        self, manager: AnimationManager, territory: Territory
    ) -> None:
        """Should remove completed animations after update."""
        manager.start_attack_animation(
            territory=territory,
            original_color=(100, 100, 100),
            attacker_color=(200, 200, 200),
            success=True,
        )
        # Update past animation duration
        manager.update(1.0)
        assert not manager.has_animation(territory)

    def test_clear_removes_all_animations(
        self, manager: AnimationManager, territory: Territory
    ) -> None:
        """Clear should remove all animations."""
        manager.start_attack_animation(
            territory=territory,
            original_color=(100, 100, 100),
            attacker_color=(200, 200, 200),
            success=True,
        )
        manager.clear()
        assert not manager.has_animation(territory)
