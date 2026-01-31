"""AI Controller for non-player teams."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from vibegame.actions.attack import AttackAction

if TYPE_CHECKING:
    from vibegame.actions.base import Action
    from vibegame.team import Team
    from vibegame.world.map import GameMap
    from vibegame.world.territory import Territory


class AIController:
    """Controls decision-making for an AI team."""

    def __init__(self, team: Team, game_map: GameMap) -> None:
        """Initialize the AI controller.

        Args:
            team: The team this controller manages
            game_map: Reference to the game map for strategic decisions
        """
        self.team = team
        self.game_map = game_map

    @property
    def stat_priorities(self) -> dict[str, float]:
        """Get the team's stat priorities for decision making."""
        return self.team.stat_priorities

    def _decide_spending(self) -> None:
        """Spend all available resources on happiness and military."""
        from vibegame.settings import RESOURCE_SPEND_INCREMENT

        # Randomly decide what percentage goes to happiness vs military (30-70% range)
        happiness_ratio = random.uniform(0.3, 0.7)

        # Spend all resources
        while self.team.resources >= RESOURCE_SPEND_INCREMENT:
            # Use random roll each purchase to achieve approximate ratio
            if random.random() < happiness_ratio:
                self.team.spend_on_happiness(RESOURCE_SPEND_INCREMENT)
            else:
                self.team.spend_on_military(RESOURCE_SPEND_INCREMENT)

    def decide_action(self, all_teams: list[Team]) -> Action | None:
        """Decide what action to take this turn.

        Args:
            all_teams: List of all teams in the game

        Returns:
            An action to execute, or None to pass the turn
        """
        self._decide_spending()

        # Priority 1: Capture adjacent empty territories (free expansion)
        empty_targets = self._get_empty_adjacent_territories()
        if empty_targets:
            from_territory, to_territory = random.choice(empty_targets)
            return AttackAction(self.team, None, from_territory, to_territory)

        # Priority 2: Attack enemies if military-focused
        if self.stat_priorities.get("military", 0) >= 0.3:
            targets = self.evaluate_targets(all_teams)
            if targets:
                # Pick a random target team and attack
                target_team = random.choice(targets)
                attackable = self.get_attackable_territories(target_team)
                if attackable:
                    from_id, to_id = random.choice(attackable)
                    attack_from = self.game_map.get_territory(from_id)
                    attack_to = self.game_map.get_territory(to_id)
                    if attack_from and attack_to:
                        return AttackAction(
                            self.team, target_team, attack_from, attack_to
                        )

        return None

    def evaluate_targets(self, all_teams: list[Team]) -> list[Team]:
        """Evaluate and rank potential target teams.

        Args:
            all_teams: List of all teams in the game

        Returns:
            List of teams sorted by priority as targets
        """
        targets = []

        for team in all_teams:
            if team is self.team:
                continue
            if team.is_eliminated():
                continue

            # Check if we share a border with this team
            has_border = self._shares_border_with(team)
            if has_border:
                targets.append(team)

        # TODO: Sort by threat level, opportunity, etc.
        return targets

    def _shares_border_with(self, other_team: Team) -> bool:
        """Check if we share a border with another team."""
        for territory in self.team.territories:
            for neighbor in self.game_map.get_neighbors(territory.id):
                if neighbor.owner is other_team:
                    return True
        return False

    def get_attackable_territories(self, target: Team) -> list[tuple[int, int]]:
        """Get territories we can attack from.

        Returns list of tuples: (our_territory_id, their_territory_id)
        """
        attackable = []
        for our_territory in self.team.territories:
            for neighbor in self.game_map.get_neighbors(our_territory.id):
                if neighbor.owner is target:
                    attackable.append((our_territory.id, neighbor.id))
        return attackable

    def _get_empty_adjacent_territories(self) -> list[tuple[Territory, Territory]]:
        """Get pairs of (owned_territory, adjacent_empty_territory).

        Returns list of tuples that can be used for expansion actions.
        """
        empty_targets = []
        for our_territory in self.team.territories:
            for neighbor in self.game_map.get_neighbors(our_territory.id):
                if neighbor.owner is None:
                    empty_targets.append((our_territory, neighbor))
        return empty_targets
