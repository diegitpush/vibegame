"""Team class representing a faction in the game."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vibegame.world.territory import Territory


@dataclass
class Team:
    """A team/faction with stats and territories."""

    name: str
    color: tuple[int, int, int]
    is_player: bool = False

    # Core stats
    resources: float = 100.0
    happiness: float = 50.0
    military_power: float = 25.0

    # Territories owned by this team
    territories: list[Territory] = field(default_factory=list)

    # AI decision-making weights (higher = more priority)
    stat_priorities: dict[str, float] = field(default_factory=dict)

    # Active alliances: maps allied team name to turns remaining
    alliances: dict[str, int] = field(default_factory=dict)

    # Pending alliance offers received: maps offering team name to True
    pending_alliance_offers: dict[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Set default stat priorities if not provided."""
        if not self.stat_priorities:
            self.stat_priorities = {
                "military": 0.4,
                "resources": 0.4,
                "happiness": 0.2,
            }

    @property
    def territory_count(self) -> int:
        """Return the number of territories owned."""
        return len(self.territories)

    def add_territory(self, territory: Territory) -> None:
        """Add a territory to this team's control."""
        if territory not in self.territories:
            self.territories.append(territory)
            territory.owner = self

    def remove_territory(self, territory: Territory) -> None:
        """Remove a territory from this team's control."""
        if territory in self.territories:
            self.territories.remove(territory)
            territory.owner = None

    def is_eliminated(self) -> bool:
        """Check if the team has been eliminated (no territories)."""
        return len(self.territories) == 0

    def apply_resource_growth(self, total_territories: int) -> float:
        """Calculate and apply resource growth. Returns total gained.

        Formula: happiness * (territory_count / total_territories)
        """
        if total_territories <= 0:
            return 0.0
        territory_ratio = self.territory_count / total_territories
        gained = self.happiness * territory_ratio
        self.resources += gained
        return gained

    def apply_happiness_decay(self, rate: float = 0.10) -> None:
        """Apply percentage-based happiness decay (e.g., 0.10 = 10%)."""
        self.happiness = max(0.0, self.happiness * (1.0 - rate))

    def spend_on_happiness(self, amount: float) -> bool:
        """Spend resources on happiness (1:1). Returns True if successful."""
        if self.resources >= amount:
            self.resources -= amount
            self.happiness += amount
            return True
        return False

    def spend_on_military(self, amount: float) -> bool:
        """Spend resources on military (1:1). Returns True if successful."""
        if self.resources >= amount:
            self.resources -= amount
            self.military_power += amount
            return True
        return False

    def is_allied_with(self, other: Team) -> bool:
        """Check if this team has an active alliance with another team."""
        return other.name in self.alliances and self.alliances[other.name] > 0

    def get_alliance_turns_remaining(self, other: Team) -> int:
        """Get the number of turns remaining in an alliance with another team."""
        return self.alliances.get(other.name, 0)

    def form_alliance(self, other: Team, duration: int = 15) -> bool:
        """Form an alliance with another team.

        Both teams pay 1/3 of their happiness as the cost.
        Returns True if alliance was formed successfully.
        """
        happiness_cost_self = self.happiness / 3
        happiness_cost_other = other.happiness / 3

        # Apply happiness costs
        self.happiness -= happiness_cost_self
        other.happiness -= happiness_cost_other

        # Set up alliance on both sides (using team names as keys)
        self.alliances[other.name] = duration
        other.alliances[self.name] = duration

        return True

    def tick_alliances(self) -> list[str]:
        """Decrement alliance turns and remove expired alliances.

        Returns list of team names whose alliances just expired.
        """
        expired: list[str] = []
        names_to_remove: list[str] = []

        for team_name, turns in self.alliances.items():
            if turns <= 1:
                expired.append(team_name)
                names_to_remove.append(team_name)
            else:
                self.alliances[team_name] = turns - 1

        for team_name in names_to_remove:
            del self.alliances[team_name]

        return expired

    def clear_pending_offer_from(self, team: Team) -> None:
        """Clear a pending alliance offer from a specific team."""
        if team.name in self.pending_alliance_offers:
            del self.pending_alliance_offers[team.name]

    def has_pending_offer_from(self, team: Team) -> bool:
        """Check if there's a pending alliance offer from a team."""
        return team.name in self.pending_alliance_offers

    def add_pending_offer_from(self, team: Team) -> None:
        """Add a pending alliance offer from a team."""
        self.pending_alliance_offers[team.name] = True
