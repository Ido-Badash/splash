import importlib.metadata

_real_version = importlib.metadata.version


def safe_version(package_name):
    try:
        return _real_version(package_name)
    except Exception:
        return "2.5.2"  # valid version


importlib.metadata.version = safe_version
from game.ui import Colors
from game.core import BaseGame, logger
from game.states import (
    States,
    Menu,
    SplashScreen,
    # Credits,
    LaunchTower,
    AstroLink,
    LifeCapsule,
    SoftLanding,
)
import logging
from winmode import WindowStates


def main():
    # logger config
    logger.setLevel(logging.INFO)

    logger.info("=== Game - Starting ===")

    # create game
    game = BaseGame(
        win_state=WindowStates.FULLSCREEN, open_in_fullscreen=True, admin=True
    )

    # defines states
    states = [
        SplashScreen(
            game, next_state=States.MENU, text="Ort Kramim", bg_color=Colors.KHAKI_PLAT
        ),
        Menu(game),
        # Credits(game),
        LaunchTower(game),
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
