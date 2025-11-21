from typing import Tuple
import pygame
from game.ui import Colors
import random


class Rocket:
    def __init__(
        self,
        size_ratio: Tuple[float, float],
        x_ratio: float,
        y_offset_ratio: float = 0.03,
        speed: float = 200.0,
        image_path: str = None,
        shake_strength: int = 1,
        shake_time: float = 3,
        height_reach: int = 1000,
    ):
        self.size_ratio = size_ratio
        self.x_ratio = x_ratio
        self.y_offset_ratio = y_offset_ratio

        self.speed = speed
        self.image_path = image_path or "assets/images/rocket.png"
        self.image_original = pygame.image.load(self.image_path).convert_alpha()

        self.shake_strength = shake_strength
        self.shake_time = shake_time
        self._shake_time = 0

        self.height_reach = height_reach
        self.rocket_go_down = False

        self.hover = False
        self.clicked = False

        self.size = (0, 0)
        self.rocket = self.image_original
        self.rocket_rect = self.rocket.get_rect()
        self.original_pos = self.rocket_rect.topleft

        self.overlay_alpha = 120
        self.sq_hover_size_p = 0.10  # 10%

    def startup(self):
        # reset pos
        self.rocket_rect.topleft = self.original_pos

        # reset flags
        self.clicked = False
        self.hover = False
        self.rocket_go_down = False

    def get_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.hover:
            self.clicked = True
            self._shake_time = self.shake_time

    def update(self, screen: pygame.Surface, dt: float):
        screen_w, screen_h = screen.get_size()

        if not self.clicked:
            self.resize_and_repos(screen_w, screen_h)

        # hover detection
        mouse_pos = pygame.mouse.get_pos()
        self.hover = self.rocket_rect.collidepoint(mouse_pos)

        # launch animation
        if self.clicked:
            self.launch_animation(screen, dt, self.height_reach)

        # decrease shake timer
        if self._shake_time > 0:
            self._shake_time -= dt

    def launch_animation(self, screen: pygame.Surface, dt: float, height: int):
        # -1 = up, +1 = down
        direction = 1 if self.rocket_go_down else -1

        self.rocket_rect.y += direction * self.speed * dt

        # flip direction
        if self.rocket_rect.y <= height:
            self.rocket_go_down = True

        if self.rocket_rect.top <= 0:
            self.rocket_go_down = False

    def resize_and_repos(self, screen_w, screen_h):
        if self.clicked:
            return

        w = int(screen_w * self.size_ratio[0])
        h = int(screen_h * self.size_ratio[1])
        self.size = (w, h)

        self.rocket = pygame.transform.smoothscale(self.image_original, self.size)

        x = int(screen_w * self.x_ratio - w / 2)
        y = int(screen_h - h - (screen_h * self.y_offset_ratio))

        # set rect
        self.rocket_rect = self.rocket.get_rect(topleft=(x, y))

        # save original pos
        if not hasattr(self, "original_pos"):
            self.original_pos = (x, y)

    def draw(self, screen: pygame.Surface):
        if self.hover:
            self.draw_overlay(screen)

        screen.blit(self.rocket, self.rocket_rect)

        if self.hover:
            self.draw_hover_squares(screen)

    def draw_overlay(self, screen: pygame.Surface):
        overlay = pygame.Surface(self.rocket_rect.size, pygame.SRCALPHA)
        overlay.fill((*Colors.BLACK, self.overlay_alpha))
        screen.blit(overlay, self.rocket_rect.topleft)

    def shake(self):
        shake_x = 0
        shake_y = 0

        if self._shake_time > 0:
            shake_x = random.randint(-self.shake_strength, self.shake_strength)
            shake_y = random.randint(-self.shake_strength, self.shake_strength)

        return (shake_x, shake_y)

    @property
    def hover_sqs_size(self):
        return int(
            min(self.rocket_rect.width, self.rocket_rect.height) * self.sq_hover_size_p
        )

    @property
    def shake_timer(self):
        return self._shake_time

    def draw_hover_squares(self, screen: pygame.Surface):
        rect = self.rocket_rect
        sq = self.hover_sqs_size

        positions = {
            "up_left": (rect.left - sq, rect.top - sq),
            "up_right": (rect.right, rect.top - sq),
            "down_left": (rect.left - sq, rect.bottom),
            "down_right": (rect.right, rect.bottom),
        }

        for pos in positions.values():
            pygame.draw.rect(
                screen,
                Colors.CRIMSON,
                (pos[0], pos[1], sq, sq),
                border_radius=4,
            )
