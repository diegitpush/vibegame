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

# Alliance border color - bright cyan/turquoise to stand out
ALLIANCE_BORDER_COLOR = (0, 255, 200)


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
        self._render_map(game_map, teams, selected_territory)
        self._render_stats_panel(
            teams, current_turn, current_team_index, stat_scale_suffix
        )

    def _render_map(
        self,
        game_map: GameMap,
        teams: list[Team],
        selected_territory: Territory | None = None,
    ) -> None:
        """Render the territory map with alliance borders."""
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

        # Draw alliance borders on top (thicker lines between allied territories)
        self._render_alliance_borders(game_map, teams)

    def _render_alliance_borders(self, game_map: GameMap, teams: list[Team]) -> None:
        """Render special borders between allied teams' territories."""
        territory_size = self.layout.territory_size
        offset_x = self.layout.map_offset_x
        offset_y = self.layout.map_offset_y
        border_width = max(3, territory_size // 12)  # Thicker border for visibility

        # Track which edges we've already drawn to avoid duplicates
        drawn_edges: set[tuple[int, int]] = set()

        for territory in game_map.territories.values():
            if territory.owner is None:
                continue

            x = offset_x + territory.grid_x * territory_size
            y = offset_y + territory.grid_y * territory_size

            # Check each neighbor for alliance relationship
            for neighbor in game_map.get_neighbors(territory.id):
                if neighbor.owner is None:
                    continue

                # Check if these two teams are allied
                if not territory.owner.is_allied_with(neighbor.owner):
                    continue

                # Create a unique edge identifier (smaller id first)
                edge_id = (
                    min(territory.id, neighbor.id),
                    max(territory.id, neighbor.id),
                )
                if edge_id in drawn_edges:
                    continue
                drawn_edges.add(edge_id)

                # Draw the alliance border on the shared edge based on neighbor position
                if neighbor.grid_x > territory.grid_x:
                    # Neighbor is to the right - draw right edge of territory
                    start = (x + territory_size, y)
                    end = (x + territory_size, y + territory_size)
                elif neighbor.grid_x < territory.grid_x:
                    # Neighbor is to the left - draw left edge of territory
                    start = (x, y)
                    end = (x, y + territory_size)
                elif neighbor.grid_y > territory.grid_y:
                    # Neighbor is below - draw bottom edge of territory
                    start = (x, y + territory_size)
                    end = (x + territory_size, y + territory_size)
                else:
                    # Neighbor is above - draw top edge of territory
                    start = (x, y)
                    end = (x + territory_size, y)

                pygame.draw.line(
                    self.screen, ALLIANCE_BORDER_COLOR, start, end, border_width
                )

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

        # Calculate team block height: gap + name + 4 stats + alliance line
        # Always reserve space for alliance line to prevent overlap
        team_content_height = gap + self.layout.font_medium_size + (5 * line_height)

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

            # Show alliance info if team has any
            if team.alliances:
                alliance_y = stats_y + 4 * line_height
                ally_names = [
                    f"{ally_name}({turns})"
                    for ally_name, turns in team.alliances.items()
                ]
                alliance_str = "Allies: " + ", ".join(ally_names)
                # Truncate if too long
                max_width = panel_width - padding_x * 2
                alliance_text = self.font_small.render(
                    alliance_str, True, ALLIANCE_BORDER_COLOR
                )
                if alliance_text.get_width() > max_width:
                    # Show shortened version
                    alliance_str = f"Allies: {len(team.alliances)}"
                    alliance_text = self.font_small.render(
                        alliance_str, True, ALLIANCE_BORDER_COLOR
                    )
                self.screen.blit(alliance_text, (panel_x + padding_x, alliance_y))

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
