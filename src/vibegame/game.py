"""Main game class with the pygame loop."""

from enum import Enum, auto

import pygame

from vibegame.actions.attack import AttackAction
from vibegame.actions.negotiate import (
    AcceptAllianceAction,
    DeclineAllianceAction,
    NegotiateAction,
)
from vibegame.ai.controller import AIController
from vibegame.settings import (
    ALLIANCE_MIN_SHARED_BORDERS,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    FPS,
    GRAY,
    HAPPINESS_DECAY_RATE,
    MAP_COLS,
    MAP_ROWS,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    NUM_TEAMS,
    STARTING_HAPPINESS,
    STARTING_MILITARY,
    STARTING_RESOURCES,
    STAT_NORMALIZATION_DIVISOR,
    STAT_NORMALIZATION_THRESHOLD,
    STAT_SCALE_SUFFIXES,
    TEAM_COLORS,
    TEAM_NAMES,
    WINDOW_TITLE,
)
from vibegame.team import Team
from vibegame.ui.layout import Layout
from vibegame.ui.renderer import Renderer
from vibegame.world.map import GameMap
from vibegame.world.territory import Territory


class GamePhase(Enum):
    """Phases of the game turn."""

    PLAYER_TURN = auto()
    AI_TURN = auto()
    BETWEEN_TURNS = auto()
    GAME_OVER = auto()


class Game:
    """Main game class handling initialization, events, updates, and rendering."""

    def __init__(self) -> None:
        """Initialize pygame and create the game window."""
        pygame.init()
        self.screen = pygame.display.set_mode(
            (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT), pygame.RESIZABLE
        )
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize game state
        self.teams: list[Team] = []
        self.ai_controllers: list[AIController] = []
        self.game_map = GameMap(MAP_COLS, MAP_ROWS)
        self.current_turn = 1
        self.current_team_index = 0
        self.phase = GamePhase.PLAYER_TURN

        # UI with dynamic layout
        self.layout = Layout(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.renderer = Renderer(self.screen, self.layout)

        # Player interaction state
        self.selected_territory: Territory | None = None
        self.last_action_message: str | None = None
        # Attack state tracking:
        # - Capturing empty territory ends all attacks for the turn
        # - Attacking enemies allows more enemy attacks but not empty captures
        # - Each territory can only be attacked once per turn
        self.has_captured_empty_this_turn: bool = False
        self.has_attacked_enemy_this_turn: bool = False
        self.attacked_territories_this_turn: set[int] = set()
        self.waiting_for_advance: bool = False  # True when waiting for SPACE to advance

        # Key hold state for accelerating repeat
        self._key_hold_start: dict[int, float] = {}  # key -> time when hold started
        self._key_last_trigger: dict[int, float] = {}  # key -> last trigger time
        self._space_hold_start: float | None = None  # For fast-forward when eliminated

        # Stat scale level (0 = normal, 1 = K, 2 = M, 3 = B, 4 = T, 5 = C, 6 = Q)
        self.stat_scale_level: int = 0

        # Win condition
        self.winner: Team | None = None

        # Alliance negotiation state
        self.negotiation_target: Team | None = None  # Target for alliance offer
        self.pending_player_offer: Team | None = None  # Team offering player alliance

        # Set up the game
        self._create_teams()
        self._assign_starting_territories()
        self._create_ai_controllers()

    def _create_teams(self) -> None:
        """Create all teams with initial stats."""
        for i in range(NUM_TEAMS):
            team = Team(
                name=TEAM_NAMES[i],
                color=TEAM_COLORS[i],
                is_player=(i == 0),  # First team is player-controlled
                resources=STARTING_RESOURCES,
                happiness=STARTING_HAPPINESS,
                military_power=STARTING_MILITARY,
            )
            self.teams.append(team)

    def _assign_starting_territories(self) -> None:
        """Assign clustered starting territories to each team."""
        self.game_map.assign_clustered_start(self.teams, territories_per_team=5)

    def _create_ai_controllers(self) -> None:
        """Create AI controllers for non-player teams."""
        for team in self.teams:
            if not team.is_player:
                controller = AIController(team, self.game_map)
                self.ai_controllers.append(controller)

    def handle_events(self) -> None:
        """Process input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                self.running = False

            # Handle window resize
            if event.type == pygame.VIDEORESIZE:
                self._handle_resize(event.w, event.h)

            # Handle player turn
            if self.phase == GamePhase.PLAYER_TURN:
                self._handle_player_input(event)
            elif self.phase == GamePhase.AI_TURN:
                self._handle_ai_phase_input(event)

    def _handle_resize(self, width: int, height: int) -> None:
        """Handle window resize event.

        Args:
            width: New window width
            height: New window height
        """
        # Enforce minimum size
        width = max(width, MIN_WINDOW_WIDTH)
        height = max(height, MIN_WINDOW_HEIGHT)

        # Update display
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)

        # Update layout
        self.layout.update(width, height)
        self.renderer.screen = self.screen
        self.renderer.update_layout(self.layout)

    def _handle_player_input(self, event: pygame.event.Event) -> None:
        """Handle input during player's turn."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.selected_territory = None
                self.negotiation_target = None
                self._end_player_turn()
            elif event.key in (pygame.K_h, pygame.K_m):
                # Record hold start time and trigger immediately
                now = pygame.time.get_ticks() / 1000.0
                self._key_hold_start[event.key] = now
                self._key_last_trigger[event.key] = now
                if event.key == pygame.K_h:
                    self._player_spend_on_happiness()
                else:
                    self._player_spend_on_military()
            elif event.key == pygame.K_n:
                # N key - select target or offer alliance to current target
                self._handle_negotiate_key()
            elif event.key == pygame.K_TAB:
                # Tab key - cycle through alliance targets
                self._cycle_negotiate_target()
            elif event.key == pygame.K_y:
                # Y key - accept pending alliance offer
                if self.pending_player_offer:
                    self._accept_pending_alliance()
            elif event.key == pygame.K_x:
                # X key - decline pending alliance offer
                if self.pending_player_offer:
                    self._decline_pending_alliance()
            elif event.key == pygame.K_ESCAPE:
                # Cancel negotiation mode
                if self.negotiation_target:
                    self.negotiation_target = None
                    self.last_action_message = "Negotiation cancelled"
        elif event.type == pygame.KEYUP:
            # Clear hold state when key is released
            if event.key in self._key_hold_start:
                del self._key_hold_start[event.key]
            if event.key in self._key_last_trigger:
                del self._key_last_trigger[event.key]
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_territory_click(event.pos)

    def _handle_ai_phase_input(self, event: pygame.event.Event) -> None:
        """Handle input during AI phase (advancing turns with SPACE)."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self.waiting_for_advance:
                self.waiting_for_advance = False
            # Track when SPACE was pressed for hold detection
            self._space_hold_start = pygame.time.get_ticks() / 1000.0
        elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            # Clear hold tracking when released
            self._space_hold_start = None

    def _check_space_hold_for_eliminated_player(self) -> None:
        """Auto-advance turns if player is eliminated and holding SPACE."""
        player = self.teams[0]
        if not player.is_eliminated():
            return

        # Check if SPACE is being held long enough (0.3s threshold)
        keys = pygame.key.get_pressed()
        if not keys[pygame.K_SPACE]:
            return

        hold_start = getattr(self, "_space_hold_start", None)
        if hold_start is None:
            return

        hold_duration = pygame.time.get_ticks() / 1000.0 - hold_start
        if hold_duration >= 0.3 and self.waiting_for_advance:
            self.waiting_for_advance = False

    def _handle_territory_click(self, mouse_pos: tuple[int, int]) -> None:
        """Handle clicking on a territory."""
        # Convert mouse position to grid coordinates using layout
        grid_x, grid_y = self.layout.get_grid_position(mouse_pos[0], mouse_pos[1])

        # Check if click is within map bounds
        territory = self.game_map.get_territory_at(grid_x, grid_y)
        if territory is None:
            return

        player = self.teams[0]

        # If no territory selected, select if owned by player
        if self.selected_territory is None:
            if territory.owner is player:
                self.selected_territory = territory
                self.last_action_message = None
            return

        # If clicking the same territory, deselect
        if territory is self.selected_territory:
            self.selected_territory = None
            return

        # If clicking another owned territory, change selection
        if territory.owner is player:
            self.selected_territory = territory
            self.last_action_message = None
            return

        # Try to attack the clicked territory
        if self.selected_territory.is_adjacent_to(territory):
            is_empty_territory = territory.owner is None

            # Check attack restrictions based on what player has already done this turn
            if self.has_captured_empty_this_turn:
                # Capturing empty territory ends all attacks for the turn
                self.last_action_message = "Turn ended after capturing empty territory!"
                return

            if is_empty_territory and self.has_attacked_enemy_this_turn:
                # Can't capture empty after attacking enemies
                self.last_action_message = "Cannot capture empty after attacking!"
                return

            if territory.id in self.attacked_territories_this_turn:
                self.last_action_message = "Already attacked this territory!"
                return

            # Check if trying to attack an ally
            if territory.owner and player.is_allied_with(territory.owner):
                turns_left = player.get_alliance_turns_remaining(territory.owner)
                ally_name = territory.owner.name
                self.last_action_message = (
                    f"Cannot attack ally {ally_name}! ({turns_left} turns left)"
                )
                return

            action = AttackAction(
                player, territory.owner, self.selected_territory, territory
            )
            if action.is_valid():
                # Capture original color before attack changes ownership
                original_color = territory.owner.color if territory.owner else GRAY
                result = action.execute()
                self.last_action_message = result.message

                # Update attack state based on target type
                if is_empty_territory:
                    self.has_captured_empty_this_turn = True
                else:
                    self.has_attacked_enemy_this_turn = True
                self.attacked_territories_this_turn.add(territory.id)

                # Start animation for the attacked territory
                self.renderer.animations.start_attack_animation(
                    territory=territory,
                    original_color=original_color,
                    attacker_color=player.color,
                    success=result.success,
                )
                # Deselect after action
                self.selected_territory = None

    def _calculate_spend_amount(self, resources: float) -> float:
        """Calculate spend amount based on current resources (10%, min 10)."""
        if resources < 10:
            return 0.0
        return max(10.0, resources * 0.1)

    def _player_spend_on_happiness(self) -> None:
        """Handle player spending resources on happiness."""
        player = self.teams[0]
        amount = self._calculate_spend_amount(player.resources)
        if amount > 0 and player.spend_on_happiness(amount):
            self.last_action_message = f"Spent {int(amount)} on Happiness!"
        else:
            self.last_action_message = "Not enough resources!"

    def _player_spend_on_military(self) -> None:
        """Handle player spending resources on military."""
        player = self.teams[0]
        amount = self._calculate_spend_amount(player.resources)
        if amount > 0 and player.spend_on_military(amount):
            self.last_action_message = f"Spent {int(amount)} on Military!"
        else:
            self.last_action_message = "Not enough resources!"

    def _count_shared_borders_with(self, team1: Team, team2: Team) -> int:
        """Count shared border edges between two teams."""
        shared = 0
        for territory in team1.territories:
            for neighbor in self.game_map.get_neighbors(territory.id):
                if neighbor.owner is team2:
                    shared += 1
        return shared

    def _get_valid_alliance_targets(self) -> list[Team]:
        """Get list of teams that player can offer alliance to."""
        player = self.teams[0]
        valid_targets = []

        for team in self.teams:
            if team is player:
                continue
            if team.is_eliminated():
                continue
            if player.is_allied_with(team):
                continue

            shared = self._count_shared_borders_with(player, team)
            if shared >= ALLIANCE_MIN_SHARED_BORDERS:
                valid_targets.append(team)

        return valid_targets

    def _handle_negotiate_key(self) -> None:
        """Handle N key press for negotiation."""
        player = self.teams[0]

        # If there's a pending offer, remind player about Y/X
        if self.pending_player_offer:
            offer_name = self.pending_player_offer.name
            self.last_action_message = (
                f"{offer_name} offers alliance! Y: Accept, X: Decline"
            )
            return

        valid_targets = self._get_valid_alliance_targets()

        if not valid_targets:
            self.last_action_message = (
                f"No valid targets (need {ALLIANCE_MIN_SHARED_BORDERS}+ shared borders)"
            )
            return

        # If no target selected, select the first one
        if self.negotiation_target is None:
            self.negotiation_target = valid_targets[0]
            shared = self._count_shared_borders_with(player, self.negotiation_target)
            self.last_action_message = (
                f"Target: {self.negotiation_target.name} ({shared} borders) - "
                f"N: offer, TAB: cycle, ESC: cancel"
            )
        else:
            # Target already selected - offer alliance
            self._offer_alliance_to_target()

    def _cycle_negotiate_target(self) -> None:
        """Cycle to the next valid alliance target."""
        player = self.teams[0]

        valid_targets = self._get_valid_alliance_targets()

        if not valid_targets:
            self.last_action_message = (
                f"No valid targets (need {ALLIANCE_MIN_SHARED_BORDERS}+ shared borders)"
            )
            return

        if self.negotiation_target is None:
            # No target yet, select the first one
            self.negotiation_target = valid_targets[0]
        else:
            # Cycle to next target
            try:
                current_idx = valid_targets.index(self.negotiation_target)
                next_idx = (current_idx + 1) % len(valid_targets)
                self.negotiation_target = valid_targets[next_idx]
            except ValueError:
                self.negotiation_target = valid_targets[0]

        shared = self._count_shared_borders_with(player, self.negotiation_target)
        self.last_action_message = (
            f"Target: {self.negotiation_target.name} ({shared} borders) - "
            f"N: offer, TAB: cycle, ESC: cancel"
        )

    def _offer_alliance_to_target(self) -> None:
        """Offer alliance to the current negotiation target."""
        player = self.teams[0]

        if self.negotiation_target is None:
            return

        action = NegotiateAction(player, self.negotiation_target, self.game_map)
        if action.is_valid():
            result = action.execute()
            self.last_action_message = result.message
        else:
            shared = self._count_shared_borders_with(player, self.negotiation_target)
            self.last_action_message = (
                f"Cannot ally with {self.negotiation_target.name} "
                f"({shared}/{ALLIANCE_MIN_SHARED_BORDERS} borders)"
            )

        self.negotiation_target = None

    def _accept_pending_alliance(self) -> None:
        """Accept a pending alliance offer."""
        player = self.teams[0]

        if self.pending_player_offer is None:
            return

        action = AcceptAllianceAction(player, self.pending_player_offer)
        if action.is_valid():
            result = action.execute()
            self.last_action_message = result.message
        else:
            self.last_action_message = "Cannot accept alliance"

        self.pending_player_offer = None

    def _decline_pending_alliance(self) -> None:
        """Decline a pending alliance offer."""
        player = self.teams[0]

        if self.pending_player_offer is None:
            return

        action = DeclineAllianceAction(player, self.pending_player_offer)
        if action.is_valid():
            result = action.execute()
            self.last_action_message = result.message
        else:
            self.last_action_message = "Cannot decline alliance"

        self.pending_player_offer = None

    def _check_pending_player_offers(self) -> None:
        """Check if any team has sent an alliance offer to the player."""
        player = self.teams[0]

        for offering_team_name in list(player.pending_alliance_offers.keys()):
            # Find the actual team object by name
            for team in self.teams:
                if team.name == offering_team_name:
                    self.pending_player_offer = team
                    self.last_action_message = (
                        f"{team.name} offers alliance! Y: Accept, X: Decline"
                    )
                    return  # Only show one offer at a time

    def _end_player_turn(self) -> None:
        """End the player's turn and start AI turns."""
        # Clear any key hold state
        self._key_hold_start.clear()
        self._key_last_trigger.clear()

        # Find the first active AI team
        next_team = self._find_next_active_team(1)
        if next_team is not None:
            self.current_team_index = next_team
            self.phase = GamePhase.AI_TURN
            self.waiting_for_advance = True  # Wait before first AI acts
        else:
            # No AI teams left, start new turn
            self._start_new_turn()

    def _check_win_condition(self) -> None:
        """Check if any team controls all territories."""
        total = self.game_map.total_territories
        for team in self.teams:
            if len(team.territories) == total:
                self.winner = team
                self.phase = GamePhase.GAME_OVER
                return

    def update(self) -> None:
        """Update game state."""
        # Update animations (always, even during game over for visual polish)
        dt = self.clock.get_time() / 1000.0  # Convert ms to seconds
        self.renderer.update_animations(dt)

        if self.phase == GamePhase.GAME_OVER:
            return

        # Check for winner after any potential territory changes
        self._check_win_condition()
        if self.phase == GamePhase.GAME_OVER:
            return

        if self.phase == GamePhase.PLAYER_TURN:
            self._update_key_holds()
        elif self.phase == GamePhase.AI_TURN:
            self._check_space_hold_for_eliminated_player()
            self._process_ai_turn()
        elif self.phase == GamePhase.BETWEEN_TURNS:
            self._start_new_turn()

    def _get_repeat_interval(self, hold_duration: float) -> float:
        """Get the repeat interval based on how long key has been held.

        Starts at 0.4 seconds and decreases to 0.05 seconds as hold continues.
        """
        # Base interval starts at 0.4s, decreases to 0.05s over ~2 seconds of holding
        base_interval = 0.4
        min_interval = 0.05
        acceleration_time = 2.0  # Time to reach max speed

        # Calculate acceleration factor (0 to 1)
        factor = min(hold_duration / acceleration_time, 1.0)
        # Exponential curve for smoother acceleration
        factor = factor * factor

        return base_interval - (base_interval - min_interval) * factor

    def _update_key_holds(self) -> None:
        """Check for held keys and trigger repeated spending."""
        now = pygame.time.get_ticks() / 1000.0
        keys = pygame.key.get_pressed()

        for key in (pygame.K_h, pygame.K_m):
            if keys[key] and key in self._key_hold_start:
                hold_duration = now - self._key_hold_start[key]
                last_trigger = self._key_last_trigger.get(key, now)
                interval = self._get_repeat_interval(hold_duration)

                if now - last_trigger >= interval:
                    self._key_last_trigger[key] = now
                    if key == pygame.K_h:
                        self._player_spend_on_happiness()
                    else:
                        self._player_spend_on_military()

    def _process_ai_turn(self) -> None:
        """Process the current AI team's turn."""
        # Wait for player to press SPACE before processing next turn
        if self.waiting_for_advance:
            return

        if self.current_team_index >= len(self.teams):
            # All teams have acted, start new turn directly
            self._start_new_turn()
            return

        current_team = self.teams[self.current_team_index]

        # Skip eliminated teams (don't wait for input)
        if current_team.is_eliminated():
            next_team = self._find_next_active_team(self.current_team_index + 1)
            if next_team is not None:
                self.current_team_index = next_team
            else:
                self._start_new_turn()
            return

        # Skip player (should not happen but just in case)
        if current_team.is_player:
            next_team = self._find_next_active_team(self.current_team_index + 1)
            if next_team is not None:
                self.current_team_index = next_team
            else:
                self._start_new_turn()
            return

        # Find the AI controller for this team
        for controller in self.ai_controllers:
            if controller.team is current_team:
                action = controller.decide_action(self.teams)
                if action and action.is_valid():
                    # For attack actions, trigger animation
                    if isinstance(action, AttackAction):
                        target_territory = action.to_territory
                        original_color = (
                            target_territory.owner.color
                            if target_territory.owner
                            else GRAY
                        )
                        result = action.execute()
                        self.renderer.animations.start_attack_animation(
                            territory=target_territory,
                            original_color=original_color,
                            attacker_color=current_team.color,
                            success=result.success,
                        )
                    else:
                        action.execute()
                break

        # Move to next active team
        next_team = self._find_next_active_team(self.current_team_index + 1)
        if next_team is not None:
            self.current_team_index = next_team
            self.waiting_for_advance = True
        else:
            # All teams have acted, start new turn
            self._start_new_turn()

    def _apply_turn_stat_changes(self) -> None:
        """Apply per-turn stat changes to all teams."""
        total_territories = self.game_map.total_territories
        for team in self.teams:
            if not team.is_eliminated():
                team.apply_resource_growth(total_territories)
                team.apply_happiness_decay(HAPPINESS_DECAY_RATE)

    def _normalize_stats_if_needed(self) -> None:
        """Scale down all team stats proportionally if any exceed threshold.

        This prevents integer overflow and keeps numbers manageable while
        preserving relative proportions between teams.
        """
        # Check if any stat exceeds threshold
        needs_normalization = False
        for team in self.teams:
            if (
                team.resources > STAT_NORMALIZATION_THRESHOLD
                or team.happiness > STAT_NORMALIZATION_THRESHOLD
                or team.military_power > STAT_NORMALIZATION_THRESHOLD
            ):
                needs_normalization = True
                break

        if not needs_normalization:
            return

        # Normalize all teams' stats by the same divisor
        for team in self.teams:
            team.resources /= STAT_NORMALIZATION_DIVISOR
            team.happiness /= STAT_NORMALIZATION_DIVISOR
            team.military_power /= STAT_NORMALIZATION_DIVISOR

        # Increment scale level (cap at max suffix)
        if self.stat_scale_level < len(STAT_SCALE_SUFFIXES) - 1:
            self.stat_scale_level += 1

    @property
    def stat_scale_suffix(self) -> str:
        """Get the current scale suffix for display."""
        return STAT_SCALE_SUFFIXES[self.stat_scale_level]

    def _find_next_active_team(self, start_index: int) -> int | None:
        """Find the next non-eliminated team starting from start_index.

        Args:
            start_index: Index to start searching from

        Returns:
            Index of next active team, or None if all remaining teams are eliminated
        """
        for i in range(start_index, len(self.teams)):
            if not self.teams[i].is_eliminated():
                return i
        return None

    def _tick_alliances(self) -> None:
        """Decrement alliance turns for all teams and remove expired alliances."""
        for team in self.teams:
            if team.is_eliminated():
                continue
            expired = team.tick_alliances()
            # Show message if player's alliance expired
            if team.is_player and expired and self.last_action_message is None:
                expired_names = ", ".join(expired)
                self.last_action_message = f"Alliance with {expired_names} expired!"

    def _start_new_turn(self) -> None:
        """Start a new turn."""
        self._apply_turn_stat_changes()
        self._tick_alliances()
        self._normalize_stats_if_needed()
        self.current_turn += 1
        self.has_captured_empty_this_turn = False
        self.has_attacked_enemy_this_turn = False
        self.attacked_territories_this_turn.clear()
        self.waiting_for_advance = False
        self.negotiation_target = None

        # Check if player (index 0) is still active
        player = self.teams[0]
        if not player.is_eliminated():
            self.current_team_index = 0
            self.phase = GamePhase.PLAYER_TURN
            # Check for pending alliance offers to player
            self._check_pending_player_offers()
        else:
            self.last_action_message = None
            # Player is eliminated, skip to first active AI team
            next_team = self._find_next_active_team(1)
            if next_team is not None:
                self.current_team_index = next_team
                self.phase = GamePhase.AI_TURN
                self.waiting_for_advance = True
            else:
                # No active teams left (shouldn't happen if win condition works)
                self.current_team_index = len(self.teams)

    def draw(self) -> None:
        """Render the game."""
        self.renderer.render(
            self.game_map,
            self.teams,
            self.current_turn,
            self.current_team_index,
            self.selected_territory,
            self.stat_scale_suffix,
        )

        # Show phase-specific messages
        if self.phase == GamePhase.GAME_OVER and self.winner:
            self.renderer.render_message(
                f"{self.winner.name} wins! Total domination achieved. ESC to quit."
            )
        elif self.phase == GamePhase.AI_TURN and self.waiting_for_advance:
            if self.current_team_index < len(self.teams):
                current_team = self.teams[self.current_team_index]
                player = self.teams[0]
                if player.is_eliminated():
                    self.renderer.render_message(
                        f"{current_team.name}'s turn - Hold SPACE to fast-forward"
                    )
                else:
                    self.renderer.render_message(
                        f"{current_team.name}'s turn - SPACE to proceed"
                    )
        elif self.phase == GamePhase.PLAYER_TURN:
            if self.last_action_message:
                self.renderer.render_message(self.last_action_message)
            elif self.negotiation_target:
                shared = self._count_shared_borders_with(
                    self.teams[0], self.negotiation_target
                )
                self.renderer.render_message(
                    f"Target: {self.negotiation_target.name} ({shared} borders) - "
                    f"N: offer, TAB: cycle, ESC: cancel"
                )
            elif self.selected_territory:
                self.renderer.render_message(
                    "Click adjacent territory to attack, or SPACE to end turn"
                )
            else:
                player = self.teams[0]
                msg = f"{player.name}'s Turn - H/M: spend, N: negotiate, SPACE: End"
                self.renderer.render_message(msg)

        pygame.display.flip()

    def run(self) -> None:
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
