"""Territory class representing a single map tile."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vibegame.team import Team


@dataclass
class Territory:
    """A single territory on the game map."""

    id: int
    grid_x: int
    grid_y: int
    owner: Team | None = None
    neighbor_ids: list[int] = field(default_factory=list)

    @property
    def position(self) -> tuple[int, int]:
        """Return grid position as tuple."""
        return (self.grid_x, self.grid_y)

    def is_adjacent_to(self, other: Territory) -> bool:
        """Check if this territory is adjacent to another."""
        return other.id in self.neighbor_ids

    def is_owned(self) -> bool:
        """Check if this territory has an owner."""
        return self.owner is not None

    def is_owned_by(self, team: Team) -> bool:
        """Check if this territory is owned by a specific team."""
        return self.owner is team
