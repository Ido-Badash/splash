from game.core import BaseGame, logger
from game.states import (
    States,
    Menu,
    SplashScreen,
    # Credits,
    LaunchTower,
    OrbitControl,
    AstroLink,
    LifeCapsule,
    SoftLanding,
)
import logging


def main():
    # logger config
    logger.setLevel(logging.INFO)

    logger.info("=== Game - Starting ===")

    # create game
    game = BaseGame()

    # defines states
    states = [
        SplashScreen(game),
        Menu(game),
        # Credits(game),
        LaunchTower(game),
        OrbitControl(game),
        AstroLink(game),
        LifeCapsule(game),
        SoftLanding(game),
    ]

    # add to game all states
    for state in states:
        game.add_state(state)

    # set starting state
    game.sm.set_state(States.SPLASH_SCREEN)

    # run the game loop
    try:
        game.run()
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
    finally:
        logger.info("=== Game - Ended ===")


if __name__ == "__main__":
    main()
