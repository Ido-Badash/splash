from game.core import BaseState, logger, Colors
import pygame
from .states import States


class SplashScreen(BaseState):
    def __init__(self, game=None):
        super().__init__(States.SPLASH_SCREEN, game)
        self.base_font_ratio = 7
        self.text_alpha = 255
        self.fade_speed = self.game.ss.get("splash_screen_text_fade_speed", 75)

    def startup(self):
        pygame.display.set_caption("Splash Screen")

    def cleanup(self):
        pass

    def get_event(self, event: pygame.event.Event):
        pass

    def draw(self, screen: pygame.Surface):
        # fill screen with color
        screen.fill(Colors.PLATINUM)

        # text
        text_size = min(self.game.width, self.game.height) // self.base_font_ratio
        text_surf, text_rect = self.game.font.render(
            "Splash", (*Colors.DARK_GREEN, self.text_alpha), size=text_size
        )
        screen.blit(text_surf, self._text_pos(text_rect))

    def update(self, screen: pygame.Surface, dt: float):
        # decrease alpha relative to dt
        self.text_alpha -= self.fade_speed * dt

        # clamp text alpha
        self.text_alpha = max(0, min(255, int(self.text_alpha)))

        # if animation ended go to menu
        if self.text_alpha <= 0:
            self.next = States.MENU
            self.done = True

    def _text_pos(self, rect: pygame.Rect):
        return (
            self.game.width // 2 - rect.w // 2,
            self.game.height // 2 - rect.h // 2,
        )
