import pygame
import gif_pygame
from game.core import BaseState
from game.ui import FadeTransition, Colors
from .states import States
from game.entities import Rocket


class LaunchTower(BaseState):
    def __init__(self, game=None):
        super().__init__(States.LAUNCH_TOWER, game)

        self.fade_transition = FadeTransition(
            size=(self.game.width, self.game.height),
            starting_alpha=255,
            ending_alpha=0,
        )

        self.bg_gif = gif_pygame.load(self.game.ss.get("launch_tower_bg_gif_path"))
        self.bg_gif_surf = None

        # --- rockets ---
        r_size_ratio = (0.08, 0.20)  # width=8% of screen, height=20%

        self.rocket_weak = Rocket(
            size_ratio=r_size_ratio,
            x_ratio=0.20,
            speed=200,
            image_path="assets/images/rocket.png",
        )

        self.rocket_medium = Rocket(
            size_ratio=r_size_ratio,
            x_ratio=0.50,
            speed=350,
            image_path="assets/images/rocket.png",
        )

        self.rocket_strong = Rocket(
            size_ratio=r_size_ratio,
            x_ratio=0.80,
            speed=500,
            image_path="assets/images/rocket.png",
        )

    def startup(self):
        pygame.display.set_caption(self.name.value)
        self.fade_transition.startup()
        self.rocket_weak.startup()
        self.rocket_medium.startup()
        self.rocket_strong.startup()

    def cleanup(self):
        pass

    def get_event(self, event):
        self.rocket_weak.get_event(event)
        self.rocket_medium.get_event(event)
        self.rocket_strong.get_event(event)

    def draw(self, screen):
        screen.blit(self.bg_gif_surf, (0, 0))
        self.bg_gif._animate()

        self.rocket_weak.draw(screen)
        self.rocket_medium.draw(screen)
        self.rocket_strong.draw(screen)

        self.fade_transition.draw(screen)

    def update(self, screen, dt):
        # bg gif
        bg_frame, _ = self.bg_gif.get_current_frame_data()
        self.bg_gif_surf = pygame.transform.scale(bg_frame, self.game.size)

        self.fade_transition.set_size(self.game.size)
        self.fade_transition.update(dt)

        # update rockets with current screen size
        w, h = self.game.size
        self.rocket_weak.update(screen, dt)
        self.rocket_medium.update(screen, dt)
        self.rocket_strong.update(screen, dt)
