"""Dynamic layout calculations for responsive UI."""

from vibegame.settings import (
    MAP_COLS,
    MAP_MARGIN_RATIO,
    MAP_ROWS,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    NUM_TEAMS,
    STATS_PANEL_RATIO,
)


class Layout:
    """Calculates dynamic layout dimensions based on window size."""

    def __init__(self, window_width: int, window_height: int) -> None:
        """Initialize layout with current window dimensions.

        Args:
            window_width: Current window width in pixels
            window_height: Current window height in pixels
        """
        self.window_width = max(window_width, MIN_WINDOW_WIDTH)
        self.window_height = max(window_height, MIN_WINDOW_HEIGHT)
        self._calculate()

    def _calculate(self) -> None:
        """Calculate all layout dimensions."""
        # Stats panel width based on window width
        self.stats_panel_width = int(self.window_width * STATS_PANEL_RATIO)

        # Available space for the map
        available_width = self.window_width - self.stats_panel_width
        available_height = self.window_height

        # Calculate margins
        margin_x = int(available_width * MAP_MARGIN_RATIO)
        margin_y = int(available_height * MAP_MARGIN_RATIO)

        # Calculate territory size to fit the map in available space
        map_area_width = available_width - (2 * margin_x)
        map_area_height = available_height - (2 * margin_y)

        # Territory size is the smaller of width/cols or height/rows
        territory_size_from_width = map_area_width // MAP_COLS
        territory_size_from_height = map_area_height // MAP_ROWS
        self.territory_size = min(territory_size_from_width, territory_size_from_height)

        # Minimum territory size to keep the game playable
        self.territory_size = max(self.territory_size, 30)

        # Actual map dimensions
        actual_map_width = self.territory_size * MAP_COLS
        actual_map_height = self.territory_size * MAP_ROWS

        # Center the map in the available space
        self.map_offset_x = (available_width - actual_map_width) // 2
        self.map_offset_y = (available_height - actual_map_height) // 2

        # Calculate font sizes to fit all teams in stats panel
        # Use minimal spacing to maximize font size
        # Layout per team: gap + name (medium) + 4 stats (small each)
        # Total: header + (team_content * NUM_TEAMS)

        # Use ratios: large:medium:small = 1.4:1.15:1.0
        # Per team: gap + 1.15*base + 4*base = gap + 5.15*base
        # Header: gap + 1.4*base + gap = 2*gap + 1.4*base
        # Total: (2 + NUM_TEAMS)*gap + base*(1.4 + NUM_TEAMS*5.15)

        gap = 2  # Minimal gap between elements
        available = self.window_height
        fixed_space = (2 + NUM_TEAMS) * gap
        font_multiplier = 1.4 + NUM_TEAMS * 5.15  # 1.4 for header + 5.15 per team

        # Solve: available = fixed_space + base * font_multiplier
        base_font = (available - fixed_space) / font_multiplier

        # Apply the ratios with min/max constraints
        self.font_small_size = max(14, min(22, int(base_font)))
        self.font_medium_size = max(16, min(28, int(base_font * 1.15)))
        self.font_large_size = max(20, min(36, int(base_font * 1.4)))

    def update(self, window_width: int, window_height: int) -> None:
        """Update layout for new window dimensions.

        Args:
            window_width: New window width in pixels
            window_height: New window height in pixels
        """
        self.window_width = max(window_width, MIN_WINDOW_WIDTH)
        self.window_height = max(window_height, MIN_WINDOW_HEIGHT)
        self._calculate()

    def get_grid_position(self, mouse_x: int, mouse_y: int) -> tuple[int, int]:
        """Convert mouse position to grid coordinates.

        Args:
            mouse_x: Mouse X position in pixels
            mouse_y: Mouse Y position in pixels

        Returns:
            Tuple of (grid_x, grid_y) coordinates
        """
        grid_x = (mouse_x - self.map_offset_x) // self.territory_size
        grid_y = (mouse_y - self.map_offset_y) // self.territory_size
        return grid_x, grid_y
