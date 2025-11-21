import pygame
import gif_pygame
from game.core import BaseState
from game.ui import FadeTransition, Colors
from .states import States
from game.entities import Rocket
from game.widgets import TextLine, MultiLine
import random


class LaunchTower(BaseState):
    def __init__(self, game=None):
        super().__init__(States.LAUNCH_TOWER, game)

        self.current_rocket = None  # track the current active rocket

        self.fade_transition = FadeTransition(
            size=(self.game.width, self.game.height),
            starting_alpha=255,
            ending_alpha=0,
        )

        self.bg_gif = gif_pygame.load(self.game.ss.get("launch_tower_bg_gif_path"))
        self.bg_gif_surf = None

        # --- MULTILINE TEXT BLOCK ---
        self.text_block = MultiLine(
            lines=[
                TextLine(
                    text="Artemis wants to test out some rockets",
                    base_ratio=20,
                    color=(*Colors.WHITE, 240),
                    game_size=self.game.size,
                ),
                TextLine(
                    text="Help them find the strongest rocket so they can fly to the moon.",
                    base_ratio=25,
                    color=(*Colors.PLATINUM, 220),
                    game_size=self.game.size,
                ),
                TextLine(
                    text="(Click a rocket to launch)",
                    base_ratio=30,
                    color=(*Colors.CRIMSON, 200),
                    game_size=self.game.size,
                ),
            ],
            start_y_ratio=0.05,
            line_spacing_ratio=0.015,
            game_size=self.game.size,
        )

        # --- rockets ---
        r_size_ratio = (0.08, 0.20)

        # TODO: CREATE ROCKETS

    def startup(self):
        pygame.display.set_caption(self.name.value)
        self.fade_transition.startup()

    def cleanup(self):
        pass

    def get_event(self, event):
        # TODO: get event for each rocket

        if event.type == pygame.MOUSEBUTTONDOWN:
            pass
            # TODO:  for r in self.rockets:
            # TODO:      if r.rocket_rect.collidepoint(event.pos):
            # TODO:          # launch only if there no current active rocket

    def draw(self, screen: pygame.Surface):
        # rocket shake based on current rocket
        shake_x, shake_y = self.get_screen_shake_offset()

        # background
        if self.bg_gif_surf:
            screen.blit(self.bg_gif_surf, (shake_x, shake_y))
            self.bg_gif._animate()

        # text block
        self.text_block.draw(screen)

        # TODO: draw rockets

        # fade
        self.fade_transition.draw(screen)

    def update(self, screen, dt):
        # background GIF scaled to screen
        bg_frame, _ = self.bg_gif.get_current_frame_data()
        self.bg_gif_surf = pygame.transform.scale(bg_frame, self.game.size)

        # update text layout on resize
        self.text_block.update(self.game.size)

        # TODO: update rockets

        # TODO: if current rocket finished, clear current

        # TODO: if all rocket are done, start finish animation

        # fade
        self.fade_transition.set_size(self.game.size)
        self.fade_transition.update(dt)

    def finish_animation(self):
        pass

    def get_screen_shake_offset(self):
        # TODO: if current rocket shake timer > 0:
        # TODO:    s = int(self.current_rocket.shake_strength)
        # TODO:    return (random.randint(-s, s), random.randint(-s, s))
        return (0, 0)

    @property
    def rockets(self):
        return []  # returns all rockets
