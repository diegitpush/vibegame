"""Entry point for the game."""

from vibegame.game import Game


def main() -> None:
    """Create and run the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
