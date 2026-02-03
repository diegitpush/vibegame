"""Negotiate action for diplomacy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vibegame.actions.base import Action, ActionResult
from vibegame.settings import ALLIANCE_DURATION, ALLIANCE_MIN_SHARED_BORDERS

if TYPE_CHECKING:
    from vibegame.team import Team
    from vibegame.world.map import GameMap


class NegotiateAction(Action):
    """Action for offering an alliance to another team."""

    def __init__(
        self, actor: Team, target: Team, game_map: GameMap, offer_type: str = "alliance"
    ) -> None:
        """Initialize negotiation action.

        Args:
            actor: The team initiating negotiation
            target: The team being negotiated with
            game_map: Reference to the game map for border calculations
            offer_type: Type of offer (currently only "alliance" is supported)
        """
        super().__init__(actor, target)
        self.game_map = game_map
        self.offer_type = offer_type

    @property
    def name(self) -> str:
        """Return the name of this action type."""
        return "Negotiate"

    def count_shared_borders(self) -> int:
        """Count the number of shared border edges between actor and target.

        Returns the number of adjacent square pairs (edges) shared.
        """
        if self.target is None:
            return 0

        shared_count = 0
        for territory in self.actor.territories:
            for neighbor in self.game_map.get_neighbors(territory.id):
                if neighbor.owner is self.target:
                    shared_count += 1
        return shared_count

    def is_valid(self) -> bool:
        """Check if the negotiation is valid.

        An alliance offer is valid if:
        - Both teams exist and are different
        - Teams share at least ALLIANCE_MIN_SHARED_BORDERS adjacent squares
        - Teams are not already allied
        - No pending offer exists from actor to target
        """
        if self.target is None:
            return False

        if self.actor is self.target:
            return False

        # Check if already allied
        if self.actor.is_allied_with(self.target):
            return False

        # Check minimum shared borders
        shared = self.count_shared_borders()
        return shared >= ALLIANCE_MIN_SHARED_BORDERS

    def execute(self) -> ActionResult:
        """Execute the negotiation - send an alliance offer.

        The offer is placed in the target's pending_alliance_offers.
        The target must accept for the alliance to form.
        """
        if not self.is_valid():
            shared = self.count_shared_borders()
            if shared < ALLIANCE_MIN_SHARED_BORDERS:
                return ActionResult(
                    success=False,
                    message=f"Need {ALLIANCE_MIN_SHARED_BORDERS}+ shared borders "
                    f"(have {shared})",
                )
            return ActionResult(success=False, message="Invalid negotiation")

        if self.target is None:
            return ActionResult(success=False, message="No target specified")

        # Place the offer in target's pending offers
        self.target.add_pending_offer_from(self.actor)

        return ActionResult(
            success=True,
            message=f"{self.actor.name} offers alliance to {self.target.name}",
        )


class AcceptAllianceAction(Action):
    """Action for accepting a pending alliance offer."""

    def __init__(self, actor: Team, target: Team) -> None:
        """Initialize accept alliance action.

        Args:
            actor: The team accepting the offer
            target: The team that sent the offer
        """
        super().__init__(actor, target)

    @property
    def name(self) -> str:
        """Return the name of this action type."""
        return "Accept Alliance"

    def is_valid(self) -> bool:
        """Check if acceptance is valid."""
        if self.target is None:
            return False

        # Must have a pending offer from target
        return self.actor.has_pending_offer_from(self.target)

    def execute(self) -> ActionResult:
        """Execute the alliance acceptance."""
        if not self.is_valid():
            return ActionResult(success=False, message="No pending offer to accept")

        if self.target is None:
            return ActionResult(success=False, message="No target specified")

        # Clear the pending offer
        self.actor.clear_pending_offer_from(self.target)

        # Form the alliance
        self.actor.form_alliance(self.target, ALLIANCE_DURATION)

        return ActionResult(
            success=True,
            message=f"{self.actor.name} allied with {self.target.name} "
            f"for {ALLIANCE_DURATION} turns!",
        )


class DeclineAllianceAction(Action):
    """Action for declining a pending alliance offer."""

    def __init__(self, actor: Team, target: Team) -> None:
        """Initialize decline alliance action.

        Args:
            actor: The team declining the offer
            target: The team that sent the offer
        """
        super().__init__(actor, target)

    @property
    def name(self) -> str:
        """Return the name of this action type."""
        return "Decline Alliance"

    def is_valid(self) -> bool:
        """Check if decline is valid."""
        if self.target is None:
            return False
        return self.actor.has_pending_offer_from(self.target)

    def execute(self) -> ActionResult:
        """Execute the alliance decline."""
        if not self.is_valid():
            return ActionResult(success=False, message="No pending offer to decline")

        if self.target is None:
            return ActionResult(success=False, message="No target specified")

        # Clear the pending offer
        self.actor.clear_pending_offer_from(self.target)

        return ActionResult(
            success=True,
            message=f"{self.actor.name} declined alliance with {self.target.name}",
        )
