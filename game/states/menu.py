import pygame

from game.core import BaseState, Colors, logger

from .states import States


class Menu(BaseState):
    def __init__(self, game=None):
        super().__init__(States.MENU, game)

    def startup(self):
        pygame.display.set_caption("Menu")

    def cleanup(self):
        pass

    def get_event(self, event: pygame.event.Event):
        pass

    def draw(self, screen: pygame.Surface):
        screen.fill(Colors.KHAKI)

    def update(self, screen, dt):
        pass
