import pygame

from game.core import BaseState, Colors, logger

from .states import States


class Menu(BaseState):
    def __init__(self, game=None):
        super().__init__(States.MENU, game)

    def get_event(self, event: pygame.event.Event):
        pass

    def draw(self, screen: pygame.Surface):
        screen.fill(Colors.PLATINUM)
        pygame.display.set_caption("Menu")

    def update(self, screen, dt):
        pass
