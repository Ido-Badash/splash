import pygame

from game.core import BaseState, Colors, logger
from game.states import States

class Night1(BaseState):
    def __init__(self, game=None):
        super().__init__(States.NIGHT_1, game)
        
    def startup(self):
        pygame.display.set_caption("Night 1")
        
    def get_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.done = True
            self.next = States.MENU

    def draw(self, screen: pygame.Surface):
        screen.fill(Colors.KHAKI)

    def update(self, screen, dt):
        pass
