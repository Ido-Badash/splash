# THIS FILE IS AN EXAMPLE ON HOW TO USE `BaseGame` CLASS

import pygame
from enum import Enum

# src
from game import BaseGame, BaseState, logger



class States(str, Enum):
    MENU = "Menu"
    LEVEL = "Level"


class Menu(BaseState):
    def __init__(self, game = None):
        super().__init__(States.MENU, game)

    def get_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_2:
            logger.info("-> Switching to Level")
            self.done = True
            self.next = States.LEVEL

    def draw(self, screen: pygame.Surface):
        screen.fill((95, 85, 85))
        pygame.display.set_caption("Menu")

    def update(self, screen: pygame.Surface, dt):
        super().update(screen, dt)


class Level(BaseState):
    def __init__(self, game = None):
        super().__init__(States.LEVEL, game)

    def get_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_1:
            logger.info("-> Switching to Menu")
            self.done = True
            self.next = States.MENU

    def draw(self, screen: pygame.Surface):
        screen.fill((5, 32, 74))
        pygame.display.set_caption("Level")

    def update(self, screen: pygame.Surface, dt):
        super().update(screen, dt)

def main():
    game = BaseGame()
    menu = Menu()
    level = Level()
    states = [menu, level]
    for s in states:
        game.add_state(s)
    game.run()

if __name__ == "__main__":
    main()