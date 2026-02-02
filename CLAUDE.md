# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vibegame is a turn-based sandbox simulation game built with Pygame Community Edition (pygame-ce). Six teams compete strategically on a 2D grid map—one player-controlled, five AI-controlled. Teams manage resources, happiness, and military power while expanding territory.

## Development Commands

```bash
# Install in editable mode with dev dependencies
pip install -e '.[dev]'

# Run the game
vibegame
python -m vibegame

# Run all tests
pytest

# Run a single test file
pytest tests/test_team.py

# Run a specific test
pytest tests/test_map.py::TestMapNeighbors::test_corner_neighbors -v

# Linting and formatting
ruff check .            # Check for issues
ruff check --fix .      # Auto-fix issues
ruff format .           # Format code

# Type checking
mypy src/vibegame
```

## Architecture

```
src/vibegame/
├── main.py              # Entry point - creates Game instance and runs it
├── game.py              # Core Game class with turn-based loop and GamePhase enum
├── settings.py          # Configuration: window, teams, map, starting stats
├── team.py              # Team class with stats and territory management
├── ai/
│   ├── __init__.py
│   └── controller.py    # AIController - decision-making for AI teams
├── world/
│   ├── __init__.py
│   ├── map.py           # GameMap - 2D grid with neighbor relationships
│   └── territory.py     # Territory - individual map tiles with ownership
├── actions/
│   ├── __init__.py
│   ├── base.py          # Abstract Action class interface
│   ├── attack.py        # AttackAction - military-based territory capture
│   └── negotiate.py     # NegotiateAction (stub)
└── ui/
    ├── __init__.py
    └── renderer.py      # Renders map territories and stats panel
```

### Core Concepts

- **Teams**: 6 teams with `resources`, `happiness`, `military_power` stats
- **Map**: 10x8 grid (80 territories) with 4-directional adjacency
- **Turns**: Player acts → AI teams act in sequence → next turn
- **Phases**: `GamePhase.PLAYER_TURN`, `GamePhase.AI_TURN`, `GamePhase.BETWEEN_TURNS`

### Key Classes

**Team** (`team.py`):
- Stats: `resources`, `happiness`, `military_power`
- `territories` list and `stat_priorities` dict for AI weighting
- Territory methods: `add_territory()`, `remove_territory()`, `is_eliminated()`
- Stat methods: `apply_resource_growth()`, `apply_happiness_decay()`, `spend_on_happiness()`, `spend_on_military()`

**Territory** (`world/territory.py`):
- Grid position (`grid_x`, `grid_y`), `owner`, `neighbor_ids`
- Methods: `is_adjacent_to()`, `is_owned_by()`

**GameMap** (`world/map.py`):
- Creates grid with automatic neighbor relationships
- `assign_clustered_start()` gives each team adjacent starting territories
- Methods: `get_neighbors()`, `get_team_territories()`, `get_border_territories()`

**AIController** (`ai/controller.py`):
- `decide_action()` returns an Action or None (pass turn)
- `_decide_spending()` handles resource spending on happiness/military based on stat deficits
- `evaluate_targets()` finds teams sharing borders
- Uses `stat_priorities` for decision weighting

**Action** (`actions/base.py`):
- Abstract base with `execute()` → `ActionResult` and `is_valid()`
- `AttackAction` (`actions/attack.py`): Military-based territory capture with randomized combat
- `NegotiateAction` (`actions/negotiate.py`): Stub for future diplomacy implementation

### Game Loop (`game.py`)

```python
class Game:
    def handle_events()            # Process input (H, M, SPACE, mouse clicks)
    def update()                   # Process AI turns, advance phases
    def _apply_turn_stat_changes() # Resource growth + happiness decay at turn start
    def draw()                     # Render via Renderer
```

The loop runs at 60 FPS. Player controls:
- **Click** owned territory → click adjacent enemy to attack
- **H** - Spend 10 resources on happiness
- **M** - Spend 10 resources on military
- **SPACE** - End turn

### Settings (`settings.py`)

- Window: 800x600, 60 FPS
- Teams: 6 teams with colors and names (Azure, Crimson, Verdant, Solar, Mystic, Ember)
- Starting stats: 100 resources, 50 happiness, 25 military
- Map: 10 cols × 8 rows, 60px territory size
- Stat interactions: `HAPPINESS_DECAY_PER_TURN = 5.0`, `RESOURCE_SPEND_INCREMENT = 10.0`

## Testing Strategy

Tests live in `tests/` and use pytest:
- `test_team.py` - Team stats and territory management
- `test_territory.py` - Territory properties and adjacency
- `test_map.py` - Map creation, neighbors, clustered starts
- `test_ai.py` - AIController target evaluation
- `test_attack.py` - Attack action validation and combat outcomes
- `test_stat_interactions.py` - Resource growth, happiness decay, spending

When adding new game features:
1. Write tests for game logic (stat changes, territory transfers, win conditions)
2. Run `pytest` frequently during development
3. Mock pygame display/events when testing game components in isolation

## Code Style

- Python 3.10+ required
- Line length: 88 characters
- Ruff handles linting (E, F, I, UP, B, SIM rules) and formatting
- MyPy for type checking - add type hints to new code

## Future Extension Points
1. **Diplomacy**: Implement in `actions/negotiate.py`
2. **AI Personalities**: Subclass `AIController` with different `stat_priorities`
3. **Events**: Add random occurrences module
