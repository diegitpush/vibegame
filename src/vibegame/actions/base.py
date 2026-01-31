"""Base action class for all game actions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vibegame.team import Team
    from vibegame.world.territory import Territory


@dataclass
class ActionResult:
    """Result of executing an action."""

    success: bool
    message: str
    territory_changed: Territory | None = None


class Action(ABC):
    """Abstract base class for all game actions."""

    def __init__(self, actor: Team, target: Team | None) -> None:
        """Initialize action with actor and target teams."""
        self.actor = actor
        self.target = target

    @abstractmethod
    def execute(self) -> ActionResult:
        """Execute the action and return the result."""
        pass

    @abstractmethod
    def is_valid(self) -> bool:
        """Check if the action can be executed."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this action type."""
        pass
