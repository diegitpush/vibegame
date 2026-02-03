"""Attack action for military conflicts."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from vibegame.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from vibegame.team import Team
    from vibegame.world.territory import Territory


class AttackAction(Action):
    """Action for attacking an enemy or empty territory."""

    def __init__(
        self,
        actor: Team,
        target: Team | None,
        from_territory: Territory,
        to_territory: Territory,
    ) -> None:
        """Initialize attack action.

        Args:
            actor: The attacking team
            target: The defending team, or None for empty territories
            from_territory: Territory the attack originates from
            to_territory: Territory being attacked
        """
        super().__init__(actor, target)
        self.from_territory = from_territory
        self.to_territory = to_territory

    @property
    def name(self) -> str:
        """Return the name of this action type."""
        return "Attack"

    def is_valid(self) -> bool:
        """Check if the attack is valid.

        An attack is valid if:
        - Actor owns the source territory
        - Target territory is not owned by the actor
        - For enemy territories: target matches the territory owner
        - For empty territories: target is None and territory is unowned
        - Territories are adjacent
        - Actor and target are not allied
        """
        # Actor must own the source territory
        if self.from_territory.owner is not self.actor:
            return False

        # Cannot attack own territory
        if self.to_territory.owner is self.actor:
            return False

        # Target must match the territory owner
        if self.to_territory.owner is not self.target:
            return False

        # Cannot attack allied teams
        if self.target is not None and self.actor.is_allied_with(self.target):
            return False

        # Territories must be adjacent
        return self.from_territory.is_adjacent_to(self.to_territory)

    def execute(self) -> ActionResult:
        """Execute the attack.

        Combat rules:
        - Empty territory: Free capture, no combat
        - Enemy territory: Both teams roll military_power * random(0, 5)
          - Higher result wins
          - Attacker loses: loses 5 military power
          - Defender loses: loses the territory
        """
        if not self.is_valid():
            return ActionResult(success=False, message="Invalid attack")

        # Empty territory - free capture
        if self.target is None:
            self.actor.add_territory(self.to_territory)
            return ActionResult(
                success=True,
                message=f"{self.actor.name} captured empty territory",
                territory_changed=self.to_territory,
            )

        # Combat resolution
        attacker_roll = self.actor.military_power * random.uniform(0, 5)
        defender_roll = self.target.military_power * random.uniform(0, 5)

        if attacker_roll > defender_roll:
            # Attacker wins - capture the territory but lose 10% military power
            self.target.remove_territory(self.to_territory)
            self.actor.add_territory(self.to_territory)
            self.actor.military_power = self.actor.military_power * 0.9
            msg = f"{self.actor.name} defeated {self.target.name}"
            return ActionResult(
                success=True,
                message=msg,
                territory_changed=self.to_territory,
            )
        else:
            # Defender wins - attacker loses 20% of military power
            self.actor.military_power = self.actor.military_power * 0.8
            msg = f"{self.actor.name}'s attack on {self.target.name} failed"
            return ActionResult(
                success=False,
                message=msg,
                territory_changed=None,
            )
