from game.core import BaseState, logger, Colors
import pygame
from .states import States
from game.utils import clamp_alpha, mid_pos
from game.ui import FadeTransition


class SplashScreen(BaseState):
    def __init__(
        self,
        game=None,
        text: str = "Luneth Studio",
        font=None,
        base_font_ratio: float = 4,
        sizing_speed: float = 1,
        font_color=Colors.DARK_GREEN,
        bg_color=Colors.PLATINUM,
        fade_color=(0, 0, 0),
        next_state=States.MENU,
        text_fade: FadeTransition | None = None,
        screen_fade: FadeTransition | None = None,
    ):
        super().__init__(States.SPLASH_SCREEN, game)

        # params
        self.text = text
        self.font = font or self.game.font
        self.base_font_ratio = base_font_ratio
        self.sizing_speed = sizing_speed
        self.font_color = font_color
        self.bg_color = bg_color
        self.fade_color = fade_color
        self.next_state = next_state

        # original params
        self.orig_base_font_ratio = base_font_ratio

        # fade transitions
        self.text_transition = text_fade or FadeTransition(color=self.fade_color)
        self.fade_transition = screen_fade or FadeTransition(
            size=(self.game.width, self.game.height),
            color=self.fade_color,
        )

    def startup(self):
        pygame.display.set_caption(self.text)

        # reset for each run
        self.text_transition.startup()
        self.fade_transition.startup()
        self.base_font_ratio = self.orig_base_font_ratio

    def cleanup(self):
        pass

    def get_event(self, event: pygame.event.Event):
        pass

    def draw(self, screen: pygame.Surface):
        # background
        screen.fill(self.bg_color)

        # text size & rendering
        text_size = min(self.game.width, self.game.height) // self.base_font_ratio

        text_surf, text_rect = self.font.render(
            self.text, self.font_color, size=text_size
        )
        text_surf.set_alpha(self.text_transition.alpha)

        screen.blit(text_surf, mid_pos(self.game.size, text_rect))

        # black overlay fade
        self.fade_transition.draw(screen)

    def update(self, screen: pygame.Surface, dt: float):
        # update text fade animation
        self.text_transition.update(dt)
        self.base_font_ratio += self.sizing_speed * dt

        # update black fade
        self.fade_transition.set_size(self.game.size)
        self.fade_transition.update(dt)

        # switch state when animation ends
        if self.fade_transition.is_done():
            logger.debug("Splash screen fade animation ended.")
            self.game.sm.set_state(self.next_state)
