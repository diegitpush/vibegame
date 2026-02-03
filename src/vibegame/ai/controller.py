"""AI Controller for non-player teams."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from vibegame.actions.attack import AttackAction
from vibegame.actions.negotiate import (
    AcceptAllianceAction,
    DeclineAllianceAction,
    NegotiateAction,
)
from vibegame.settings import ALLIANCE_MIN_SHARED_BORDERS

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

    def _count_shared_borders_with(self, other_team: Team) -> int:
        """Count the number of shared border edges with another team."""
        shared_count = 0
        for territory in self.team.territories:
            for neighbor in self.game_map.get_neighbors(territory.id):
                if neighbor.owner is other_team:
                    shared_count += 1
        return shared_count

    def _should_accept_alliance(
        self, offering_team: Team, all_teams: list[Team]
    ) -> bool:
        """Decide whether to accept an alliance offer.

        Factors considered:
        - Number of existing alliances (avoid too many)
        - Military power comparison (ally with stronger or similar power)
        - Number of threats (more threats = more likely to accept)
        - Current happiness (lower happiness = less willing due to cost)
        """
        # Don't accept if we have too many alliances already (max 2)
        if len(self.team.alliances) >= 2:
            return False

        # Don't accept if happiness is critically low (cost is 1/3 of happiness)
        # Threshold lowered to 10 since happiness decays over time
        if self.team.happiness < 10:
            return False

        # Count non-allied enemies we border
        enemy_count = 0
        for team in all_teams:
            if team is self.team:
                continue
            if team.is_eliminated():
                continue
            if self.team.is_allied_with(team):
                continue
            if self._shares_border_with(team):
                enemy_count += 1

        # More enemies = more willing to accept alliances
        # Base acceptance rate starts higher (50%) and increases with threats
        base_acceptance = 0.5 + (enemy_count * 0.1)

        # Stronger offering team = more attractive
        military_ratio = offering_team.military_power / max(self.team.military_power, 1)
        if military_ratio > 1.2:
            base_acceptance += 0.15  # They're stronger, good ally
        elif military_ratio < 0.3:
            base_acceptance -= 0.15  # They're much weaker, less useful

        # More shared borders = more valuable alliance (reduces front)
        shared_borders = self._count_shared_borders_with(offering_team)
        base_acceptance += shared_borders * 0.05

        return random.random() < min(base_acceptance, 0.9)

    def _should_offer_alliance(self, target: Team, all_teams: list[Team]) -> bool:
        """Decide whether to offer an alliance to a target team.

        Factors considered:
        - Number of existing alliances
        - Number of shared borders with target
        - Number of threats
        - Happiness level (cost consideration)
        """
        # Don't offer if we have too many alliances already
        if len(self.team.alliances) >= 2:
            return False

        # Don't offer if already allied or if target has pending offer from us
        if self.team.is_allied_with(target):
            return False

        # Don't offer if happiness is too low
        if self.team.happiness < 30:
            return False

        # Check minimum shared borders
        shared_borders = self._count_shared_borders_with(target)
        if shared_borders < ALLIANCE_MIN_SHARED_BORDERS:
            return False

        # Count non-allied threats (enemies we border)
        threat_count = 0
        for team in all_teams:
            if team is self.team or team is target:
                continue
            if team.is_eliminated():
                continue
            if self.team.is_allied_with(team):
                continue
            if self._shares_border_with(team):
                threat_count += 1

        # More threats = more likely to seek alliance
        # Also consider territory count - smaller teams more desperate for allies
        territory_ratio = self.team.territory_count / max(
            sum(t.territory_count for t in all_teams if not t.is_eliminated()), 1
        )

        base_offer_chance = 0.1  # Low base chance
        base_offer_chance += threat_count * 0.15
        base_offer_chance += (1 - territory_ratio) * 0.2  # Smaller = more desperate

        # More shared borders = more valuable to secure that front
        base_offer_chance += shared_borders * 0.03

        return random.random() < min(base_offer_chance, 0.5)

    def _handle_pending_alliance_offers(self, all_teams: list[Team]) -> Action | None:
        """Handle any pending alliance offers to this team."""
        for offering_team_name in list(self.team.pending_alliance_offers.keys()):
            # Find the actual team object by name
            offering_team = None
            for team in all_teams:
                if team.name == offering_team_name:
                    offering_team = team
                    break

            if offering_team is None:
                # Team no longer exists, clear the offer
                del self.team.pending_alliance_offers[offering_team_name]
                continue

            if self._should_accept_alliance(offering_team, all_teams):
                return AcceptAllianceAction(self.team, offering_team)
            else:
                return DeclineAllianceAction(self.team, offering_team)
        return None

    def _consider_offering_alliance(self, all_teams: list[Team]) -> Action | None:
        """Consider offering an alliance to another team."""
        potential_allies = []

        for team in all_teams:
            if team is self.team:
                continue
            if team.is_eliminated():
                continue
            if self.team.is_allied_with(team):
                continue

            shared_borders = self._count_shared_borders_with(team)
            if shared_borders >= ALLIANCE_MIN_SHARED_BORDERS:
                potential_allies.append((team, shared_borders))

        if not potential_allies:
            return None

        # Sort by shared borders (more borders = higher priority to secure)
        potential_allies.sort(key=lambda x: x[1], reverse=True)

        for target, _ in potential_allies:
            if self._should_offer_alliance(target, all_teams):
                return NegotiateAction(self.team, target, self.game_map)

        return None

    def decide_action(self, all_teams: list[Team]) -> Action | None:
        """Decide what action to take this turn.

        Args:
            all_teams: List of all teams in the game

        Returns:
            An action to execute, or None to pass the turn
        """
        self._decide_spending()

        # Priority 0: Handle pending alliance offers first
        alliance_response = self._handle_pending_alliance_offers(all_teams)
        if alliance_response:
            return alliance_response

        # Priority 1: Capture adjacent empty territories (free expansion)
        empty_targets = self._get_empty_adjacent_territories()
        if empty_targets:
            from_territory, to_territory = random.choice(empty_targets)
            return AttackAction(self.team, None, from_territory, to_territory)

        # Priority 2: Consider offering alliances
        alliance_offer = self._consider_offering_alliance(all_teams)
        if alliance_offer:
            return alliance_offer

        # Priority 3: Attack enemies if military-focused
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
            List of teams sorted by priority as targets (excludes allies)
        """
        targets = []

        for team in all_teams:
            if team is self.team:
                continue
            if team.is_eliminated():
                continue
            # Don't target allied teams
            if self.team.is_allied_with(team):
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
        Excludes allied teams.
        """
        # Don't attack allies
        if self.team.is_allied_with(target):
            return []

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
