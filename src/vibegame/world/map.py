"""GameMap class managing the 2D grid of territories."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from vibegame.world.territory import Territory

if TYPE_CHECKING:
    from vibegame.team import Team


class GameMap:
    """A 2D grid map composed of territories."""

    def __init__(self, cols: int, rows: int) -> None:
        """Create a new map with the given dimensions."""
        self.cols = cols
        self.rows = rows
        self.territories: dict[int, Territory] = {}
        self._create_grid()

    def _create_grid(self) -> None:
        """Create territories in a grid pattern with neighbor relationships."""
        # Create all territories
        for y in range(self.rows):
            for x in range(self.cols):
                territory_id = y * self.cols + x
                self.territories[territory_id] = Territory(
                    id=territory_id,
                    grid_x=x,
                    grid_y=y,
                )

        # Set up neighbor relationships (4-directional: up, down, left, right)
        for territory in self.territories.values():
            x, y = territory.grid_x, territory.grid_y
            neighbors = []

            # Up
            if y > 0:
                neighbors.append((y - 1) * self.cols + x)
            # Down
            if y < self.rows - 1:
                neighbors.append((y + 1) * self.cols + x)
            # Left
            if x > 0:
                neighbors.append(y * self.cols + (x - 1))
            # Right
            if x < self.cols - 1:
                neighbors.append(y * self.cols + (x + 1))

            territory.neighbor_ids = neighbors

    def get_territory(self, territory_id: int) -> Territory | None:
        """Get a territory by ID."""
        return self.territories.get(territory_id)

    def get_territory_at(self, x: int, y: int) -> Territory | None:
        """Get a territory at grid coordinates."""
        if 0 <= x < self.cols and 0 <= y < self.rows:
            return self.territories[y * self.cols + x]
        return None

    def get_neighbors(self, territory_id: int) -> list[Territory]:
        """Get all neighboring territories for a given territory."""
        territory = self.territories.get(territory_id)
        if not territory:
            return []
        return [
            self.territories[nid]
            for nid in territory.neighbor_ids
            if nid in self.territories
        ]

    def get_team_territories(self, team: Team) -> list[Territory]:
        """Get all territories owned by a team."""
        return [t for t in self.territories.values() if t.owner is team]

    def get_border_territories(self, team: Team) -> list[Territory]:
        """Get territories owned by team that border enemy or unowned territories."""
        result = []
        for territory in self.get_team_territories(team):
            for neighbor in self.get_neighbors(territory.id):
                if neighbor.owner is not team:
                    result.append(territory)
                    break
        return result

    def assign_clustered_start(
        self, teams: list[Team], territories_per_team: int = 5
    ) -> None:
        """Assign clustered starting territories to each team.

        Each team gets a cluster of adjacent territories starting from
        different corners/edges of the map.
        """
        # Starting positions spread across the map
        # For 6 teams on a 10x8 grid, use corners and mid-edges
        start_positions = [
            (1, 1),  # Top-left
            (self.cols - 2, 1),  # Top-right
            (1, self.rows - 2),  # Bottom-left
            (self.cols - 2, self.rows - 2),  # Bottom-right
            (self.cols // 2, 1),  # Top-center
            (self.cols // 2, self.rows - 2),  # Bottom-center
        ]

        for i, team in enumerate(teams):
            if i >= len(start_positions):
                break

            start_x, start_y = start_positions[i]
            self._assign_cluster(team, start_x, start_y, territories_per_team)

    def _assign_cluster(
        self, team: Team, start_x: int, start_y: int, count: int
    ) -> None:
        """Assign a cluster of territories starting from a position."""
        assigned = 0
        to_check = [(start_x, start_y)]
        checked = set()

        while to_check and assigned < count:
            x, y = to_check.pop(0)
            if (x, y) in checked:
                continue
            checked.add((x, y))

            territory = self.get_territory_at(x, y)
            if territory and territory.owner is None:
                team.add_territory(territory)
                assigned += 1

                # Add neighbors to check (shuffled for variety)
                neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
                random.shuffle(neighbors)
                to_check.extend(neighbors)

    @property
    def total_territories(self) -> int:
        """Return the total number of territories."""
        return len(self.territories)
