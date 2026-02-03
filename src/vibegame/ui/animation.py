"""Animation system for visual feedback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vibegame.world.territory import Territory

# RGB tuple type
Color = tuple[int, int, int]


def lerp_color(color1: Color, color2: Color, t: float) -> Color:
    """Linearly interpolate between two colors.

    Args:
        color1: Starting color (RGB tuple)
        color2: Ending color (RGB tuple)
        t: Interpolation factor (0.0 to 1.0)

    Returns:
        Interpolated color
    """
    t = max(0.0, min(1.0, t))
    return (
        int(color1[0] + (color2[0] - color1[0]) * t),
        int(color1[1] + (color2[1] - color1[1]) * t),
        int(color1[2] + (color2[2] - color1[2]) * t),
    )


@dataclass
class TerritoryAnimation:
    """Animation for a territory capture attempt."""

    territory: Territory
    original_color: Color  # Color before attack
    attacker_color: Color  # Attacking team's color
    success: bool  # Whether the attack succeeded
    progress: float = 0.0  # 0.0 to 1.0
    duration: float = 0.4  # Total animation duration in seconds

    def get_current_color(self) -> Color:
        """Get the current display color based on animation progress.

        Animation phases:
        - 0.0 to 0.5: Transition toward attacker color
        - 0.5 to 1.0:
            - Success: Continue to attacker color (new owner)
            - Failure: Return to original color
        """
        if self.progress <= 0.5:
            # First half: transition toward attacker color
            t = self.progress * 2  # 0 to 1 over first half
            return lerp_color(self.original_color, self.attacker_color, t)
        else:
            # Second half
            t = (self.progress - 0.5) * 2  # 0 to 1 over second half
            if self.success:
                # Stay at attacker color (already transitioned)
                return self.attacker_color
            else:
                # Return to original color
                return lerp_color(self.attacker_color, self.original_color, t)

    def update(self, dt: float) -> bool:
        """Update animation progress.

        Args:
            dt: Time elapsed since last update in seconds

        Returns:
            True if animation is still running, False if complete
        """
        self.progress += dt / self.duration
        if self.progress >= 1.0:
            self.progress = 1.0
            return False
        return True

    @property
    def is_complete(self) -> bool:
        """Check if the animation has finished."""
        return self.progress >= 1.0


class AnimationManager:
    """Manages all active territory animations."""

    def __init__(self) -> None:
        """Initialize the animation manager."""
        self._animations: dict[int, TerritoryAnimation] = {}

    def start_attack_animation(
        self,
        territory: Territory,
        original_color: Color,
        attacker_color: Color,
        success: bool,
    ) -> None:
        """Start an animation for a territory attack.

        Args:
            territory: The territory being attacked
            original_color: Color of the territory before attack
            attacker_color: Color of the attacking team
            success: Whether the attack succeeded
        """
        self._animations[territory.id] = TerritoryAnimation(
            territory=territory,
            original_color=original_color,
            attacker_color=attacker_color,
            success=success,
        )

    def update(self, dt: float) -> None:
        """Update all animations.

        Args:
            dt: Time elapsed since last update in seconds
        """
        completed = []
        for territory_id, animation in self._animations.items():
            if not animation.update(dt):
                completed.append(territory_id)

        for territory_id in completed:
            del self._animations[territory_id]

    def get_territory_color(self, territory: Territory, default_color: Color) -> Color:
        """Get the current display color for a territory.

        Args:
            territory: The territory to get color for
            default_color: Color to use if no animation is active

        Returns:
            The color to display for this territory
        """
        if territory.id in self._animations:
            return self._animations[territory.id].get_current_color()
        return default_color

    def has_animation(self, territory: Territory) -> bool:
        """Check if a territory has an active animation."""
        return territory.id in self._animations

    def clear(self) -> None:
        """Clear all animations."""
        self._animations.clear()
