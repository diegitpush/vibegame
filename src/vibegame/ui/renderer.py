"""Renderer for drawing the game map and UI elements."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from vibegame.settings import (
    BLACK,
    DARK_GRAY,
    GRAY,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    STATS_PANEL_WIDTH,
    TERRITORY_BORDER,
    TERRITORY_SIZE,
    WHITE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)

if TYPE_CHECKING:
    from vibegame.team import Team
    from vibegame.world.map import GameMap
    from vibegame.world.territory import Territory


class Renderer:
    """Handles all game rendering."""

    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the renderer.

        Args:
            screen: The pygame surface to render to
        """
        self.screen = screen
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 36)

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
        for territory in game_map.territories.values():
            x = MAP_OFFSET_X + territory.grid_x * TERRITORY_SIZE
            y = MAP_OFFSET_Y + territory.grid_y * TERRITORY_SIZE

            # Determine territory color
            color = territory.owner.color if territory.owner else GRAY

            # Draw territory background
            rect = pygame.Rect(x, y, TERRITORY_SIZE, TERRITORY_SIZE)
            pygame.draw.rect(self.screen, color, rect)

            # Draw territory border
            pygame.draw.rect(self.screen, DARK_GRAY, rect, TERRITORY_BORDER)

            # Draw selection highlight
            if territory is selected_territory:
                pygame.draw.rect(self.screen, WHITE, rect, 4)

    def _render_stats_panel(
        self,
        teams: list[Team],
        current_turn: int,
        current_team_index: int,
        stat_scale_suffix: str = "",
    ) -> None:
        """Render the stats panel on the right side."""
        panel_x = WINDOW_WIDTH - STATS_PANEL_WIDTH
        panel_rect = pygame.Rect(panel_x, 0, STATS_PANEL_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, DARK_GRAY, panel_rect)

        # Draw turn counter
        turn_text = self.font_large.render(f"Turn {current_turn}", True, WHITE)
        self.screen.blit(turn_text, (panel_x + 10, 10))

        # Draw team stats
        y_offset = 50
        for i, team in enumerate(teams):
            if team.is_eliminated():
                continue

            # Highlight current team
            team_rect = pygame.Rect(
                panel_x + 5, y_offset - 5, STATS_PANEL_WIDTH - 10, 80
            )
            if i == current_team_index:
                pygame.draw.rect(self.screen, team.color, team_rect, 2)

            # Team name with indicator
            indicator = "(You)" if team.is_player else "(AI)"
            name_text = self.font_medium.render(
                f"{team.name} {indicator}", True, team.color
            )
            self.screen.blit(name_text, (panel_x + 10, y_offset))

            # Stats (single column layout to prevent overlap)
            stats_y = y_offset + 22
            line_height = 13
            suffix = stat_scale_suffix
            stats = [
                f"Resources: {team.resources:.0f}{suffix}",
                f"Happiness: {team.happiness:.0f}{suffix}",
                f"Military: {team.military_power:.0f}{suffix}",
                f"Territories: {team.territory_count}",
            ]
            for j, stat in enumerate(stats):
                stat_text = self.font_small.render(stat, True, WHITE)
                self.screen.blit(stat_text, (panel_x + 10, stats_y + j * line_height))

            y_offset += 80

    def render_message(self, message: str, y_position: int = 550) -> None:
        """Render a message at the bottom of the screen.

        Args:
            message: Text to display
            y_position: Y position for the message
        """
        text = self.font_medium.render(message, True, WHITE)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, y_position))
        bg_rect = (
            text_rect.x - 10,
            text_rect.y - 5,
            text_rect.width + 20,
            text_rect.height + 10,
        )
        pygame.draw.rect(self.screen, BLACK, bg_rect)
        self.screen.blit(text, text_rect)
