import pygame

from game.core import BaseState, Colors, logger

from .states import States


class Menu(BaseState):
    def __init__(self, game=None):
        super().__init__(States.MENU, game)

    def startup(self):
        pygame.display.set_caption("Menu")
    
    def get_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN  and event.key == pygame.K_RETURN:
            self.done = True
            self.next = States.NIGHT_1

    def draw(self, screen: pygame.Surface):
        screen.fill(Colors.PLATINUM)

    def update(self, screen, dt):
        pass
