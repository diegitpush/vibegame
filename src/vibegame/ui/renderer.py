"""Renderer for drawing the game map and UI elements."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from vibegame.settings import (
    BLACK,
    DARK_GRAY,
    GRAY,
    TERRITORY_BORDER,
    WHITE,
)
from vibegame.ui.animation import AnimationManager
from vibegame.ui.layout import Layout

if TYPE_CHECKING:
    from vibegame.team import Team
    from vibegame.world.map import GameMap
    from vibegame.world.territory import Territory


class Renderer:
    """Handles all game rendering."""

    def __init__(self, screen: pygame.Surface, layout: Layout) -> None:
        """Initialize the renderer.

        Args:
            screen: The pygame surface to render to
            layout: Layout calculator for dynamic dimensions
        """
        self.screen = screen
        self.layout = layout
        self.animations = AnimationManager()
        self._update_fonts()

    def _update_fonts(self) -> None:
        """Update font sizes based on current layout."""
        self.font_small = pygame.font.Font(None, self.layout.font_small_size)
        self.font_medium = pygame.font.Font(None, self.layout.font_medium_size)
        self.font_large = pygame.font.Font(None, self.layout.font_large_size)

    def update_layout(self, layout: Layout) -> None:
        """Update the layout and refresh fonts.

        Args:
            layout: New layout calculator
        """
        self.layout = layout
        self._update_fonts()

    def update_animations(self, dt: float) -> None:
        """Update all active animations.

        Args:
            dt: Time elapsed since last frame in seconds
        """
        self.animations.update(dt)

    def render(
        self,
        game_map: GameMap,
        teams: list[Team],
        current_turn: int,
        current_team_index: int,
        selected_territory: Territory | None = None,
        stat_scale_suffix: str = "",
    ) -> None:
        """Render the complete game state.

        Args:
            game_map: The game map to render
            teams: List of all teams
            current_turn: Current turn number
            current_team_index: Index of the team whose turn it is
            selected_territory: Currently selected territory for player attacks
            stat_scale_suffix: Suffix to display after stat values (K, M, B, etc.)
        """
        self.screen.fill(BLACK)
        self._render_map(game_map, selected_territory)
        self._render_stats_panel(
            teams, current_turn, current_team_index, stat_scale_suffix
        )

    def _render_map(
        self, game_map: GameMap, selected_territory: Territory | None = None
    ) -> None:
        """Render the territory map."""
        territory_size = self.layout.territory_size
        offset_x = self.layout.map_offset_x
        offset_y = self.layout.map_offset_y

        for territory in game_map.territories.values():
            x = offset_x + territory.grid_x * territory_size
            y = offset_y + territory.grid_y * territory_size

            # Determine territory color (check for animation override)
            default_color = territory.owner.color if territory.owner else GRAY
            color = self.animations.get_territory_color(territory, default_color)

            # Draw territory background
            rect = pygame.Rect(x, y, territory_size, territory_size)
            pygame.draw.rect(self.screen, color, rect)

            # Draw territory border
            pygame.draw.rect(self.screen, DARK_GRAY, rect, TERRITORY_BORDER)

            # Draw selection highlight
            if territory is selected_territory:
                highlight_width = max(2, territory_size // 15)
                pygame.draw.rect(self.screen, WHITE, rect, highlight_width)

    def _render_stats_panel(
        self,
        teams: list[Team],
        current_turn: int,
        current_team_index: int,
        stat_scale_suffix: str = "",
    ) -> None:
        """Render the stats panel on the right side."""
        panel_width = self.layout.stats_panel_width
        window_width = self.layout.window_width
        window_height = self.layout.window_height

        panel_x = window_width - panel_width
        panel_rect = pygame.Rect(panel_x, 0, panel_width, window_height)
        pygame.draw.rect(self.screen, DARK_GRAY, panel_rect)

        # Use tight spacing to fit all teams with readable fonts
        gap = 2  # Minimal gap between elements
        padding_x = max(5, panel_width // 20)  # Horizontal padding only

        # Line height equals font size (no extra spacing)
        line_height = self.layout.font_small_size

        # Calculate team block height: gap + name + 4 stats
        team_content_height = gap + self.layout.font_medium_size + (4 * line_height)

        # Header height
        header_height = gap + self.layout.font_large_size + gap

        # Draw turn counter
        turn_text = self.font_large.render(f"Turn {current_turn}", True, WHITE)
        self.screen.blit(turn_text, (panel_x + padding_x, gap))

        # Draw team stats
        y_offset = header_height
        for i, team in enumerate(teams):
            if team.is_eliminated():
                continue

            # Highlight current team (includes all content)
            team_rect = pygame.Rect(
                panel_x + 2,
                y_offset,
                panel_width - 4,
                team_content_height - 2,
            )
            if i == current_team_index:
                pygame.draw.rect(self.screen, team.color, team_rect, 2)

            # Team name with indicator
            indicator = "(You)" if team.is_player else "(AI)"
            name_text = self.font_medium.render(
                f"{team.name} {indicator}", True, team.color
            )
            self.screen.blit(name_text, (panel_x + padding_x, y_offset + gap))

            # Stats (single column layout to prevent overlap)
            stats_y = y_offset + gap + self.layout.font_medium_size
            suffix = stat_scale_suffix
            stats = [
                f"Resources: {int(team.resources)}{suffix}",
                f"Happiness: {int(team.happiness)}{suffix}",
                f"Military: {int(team.military_power)}{suffix}",
                f"Territories: {team.territory_count}",
            ]
            for j, stat in enumerate(stats):
                stat_text = self.font_small.render(stat, True, WHITE)
                stat_y = stats_y + j * line_height
                self.screen.blit(stat_text, (panel_x + padding_x, stat_y))

            y_offset += team_content_height

    def render_message(self, message: str, y_position: int | None = None) -> None:
        """Render a message at the bottom of the screen.

        Args:
            message: Text to display
            y_position: Y position for the message (defaults to near bottom)
        """
        if y_position is None:
            y_position = self.layout.window_height - 30

        # Center in the map area (excluding stats panel)
        map_center_x = (self.layout.window_width - self.layout.stats_panel_width) // 2

        text = self.font_medium.render(message, True, WHITE)
        text_rect = text.get_rect(center=(map_center_x, y_position))
        padding = max(5, self.layout.font_medium_size // 4)
        bg_rect = (
            text_rect.x - padding * 2,
            text_rect.y - padding,
            text_rect.width + padding * 4,
            text_rect.height + padding * 2,
        )
        pygame.draw.rect(self.screen, BLACK, bg_rect)
        self.screen.blit(text, text_rect)
