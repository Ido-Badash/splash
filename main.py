from game.core import BaseGame, logger
from game.states import (
    States,
    Menu,
    SplashScreen,
    # PauseMenu,
    # Credits,
)


def main():
    logger.info("=== Game - Starting ===")

    # create game
    game = BaseGame()

    # defines states
    states = [
        SplashScreen(game),
        Menu(game),
        # PauseMenu(game),
        # Credits(game),
    ]

    # add to game all states
    for state in states:
        game.add_state(state)

    # set starting state
    game.set_state_by_name(States.SPLASH_SCREEN)

    # run the game loop
    try:
        game.run()
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
    finally:
        logger.info("=== Game - Ended ===")


if __name__ == "__main__":
    main()
