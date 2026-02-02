"""Tests for win conditions and game state."""

from unittest.mock import MagicMock

import pytest

from vibegame.game import Game, GamePhase


@pytest.fixture
def game(monkeypatch):
    """Create a game instance with mocked pygame."""
    mock_surface = MagicMock()
    mock_font = MagicMock()

    monkeypatch.setattr("pygame.init", lambda: None)
    monkeypatch.setattr("pygame.display.set_mode", lambda size, flags=0: mock_surface)
    monkeypatch.setattr("pygame.display.set_caption", lambda title: None)
    monkeypatch.setattr("pygame.time.Clock", lambda: MagicMock())
    monkeypatch.setattr("pygame.font.Font", lambda name, size: mock_font)

    return Game()


class TestWinCondition:
    """Tests for win condition detection."""

    def test_no_winner_at_start(self, game):
        """Game starts with no winner."""
        assert game.winner is None
        assert game.phase != GamePhase.GAME_OVER

    def test_team_wins_by_controlling_all_territories(self, game):
        """A team wins when they control all territories."""
        winner_team = game.teams[0]
        total_territories = game.game_map.total_territories

        # Give all territories to the winner team
        for territory in game.game_map.territories.values():
            if territory.owner is not winner_team:
                if territory.owner:
                    territory.owner.remove_territory(territory)
                winner_team.add_territory(territory)

        assert len(winner_team.territories) == total_territories

        # Run update to trigger win check
        game._check_win_condition()

        assert game.winner is winner_team
        assert game.phase == GamePhase.GAME_OVER

    def test_no_winner_with_partial_control(self, game):
        """No winner when a team doesn't control all territories."""
        game._check_win_condition()

        assert game.winner is None
        assert game.phase != GamePhase.GAME_OVER

    def test_game_stops_updating_after_win(self, game):
        """Game state stops updating after a winner is determined."""
        winner_team = game.teams[0]

        # Give all territories to the winner team
        for territory in game.game_map.territories.values():
            if territory.owner is not winner_team:
                if territory.owner:
                    territory.owner.remove_territory(territory)
                winner_team.add_territory(territory)

        # Trigger win condition
        game.update()

        assert game.phase == GamePhase.GAME_OVER

        # Further updates should not change the phase
        original_turn = game.current_turn
        game.update()
        game.update()

        assert game.phase == GamePhase.GAME_OVER
        assert game.current_turn == original_turn
