import pygame


from game.core import BaseState, logger
from game.ui import FadeTransition, Colors
from .states import States


class AstroLink(BaseState):
    def __init__(self, game=None):
        super().__init__(States.ASTRO_LINK, game)
        self.fade_transition = FadeTransition(
            size=(self.game.width, self.game.height),
            starting_alpha=255,
            ending_alpha=0,
        )

    def startup(self):
        pygame.display.set_caption(self.name.value)
        self.fade_transition.startup()

    def cleanup(self):
        pass

    def get_event(self, event: pygame.event.Event):
        pass

    def draw(self, screen: pygame.Surface):
        screen.fill(Colors.KHAKI)
        self.fade_transition.draw(screen)

    def update(self, screen, dt):
        self.fade_transition.set_size(self.game.size)
        self.fade_transition.update(dt)
