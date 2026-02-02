"""Game constants and configuration."""

# Window settings
DEFAULT_WINDOW_WIDTH = 840
DEFAULT_WINDOW_HEIGHT = 600
MIN_WINDOW_WIDTH = 640
MIN_WINDOW_HEIGHT = 480
WINDOW_TITLE = "Vibegame"
FPS = 60

# Colors (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

# Teams
NUM_TEAMS = 6
TEAM_COLORS = [
    (0, 120, 255),  # Blue (Player)
    (255, 60, 60),  # Red
    (60, 255, 60),  # Green
    (255, 200, 0),  # Yellow
    (180, 0, 255),  # Purple
    (255, 140, 0),  # Orange
]
TEAM_NAMES = ["Azure", "Crimson", "Verdant", "Solar", "Mystic", "Ember"]

# Starting stats
STARTING_RESOURCES = 100.0
STARTING_HAPPINESS = 50.0
STARTING_MILITARY = 25.0

# Stat interactions
HAPPINESS_DECAY_RATE = 0.10  # 10% decay per turn
RESOURCE_SPEND_INCREMENT = 10.0

# Stat normalization (prevents overflow from large numbers)
STAT_NORMALIZATION_THRESHOLD = 100_000.0  # When any stat exceeds this, normalize
STAT_NORMALIZATION_DIVISOR = 1000.0  # Divide all stats by this amount
STAT_SCALE_SUFFIXES = ["", "K", "M", "B", "T", "C", "Q"]  # Scale level suffixes

# Map
MAP_COLS = 10
MAP_ROWS = 8
TERRITORY_BORDER = 2  # pixels

# UI layout ratios (for proportional scaling)
STATS_PANEL_RATIO = 0.24  # Stats panel takes 24% of window width
MAP_MARGIN_RATIO = 0.025  # Margin around map as percentage of available space
