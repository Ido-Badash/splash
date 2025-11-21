from typing import Tuple
import pygame
import random
from game.ui import Colors


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
        height_reach: int = -1,
        fall: bool = True,  # <── NEW FLAG
    ):
        self.size_ratio = size_ratio
        self.x_ratio = x_ratio
        self.y_offset_ratio = y_offset_ratio

        self.base_speed = speed
        self.height_reach = height_reach

        self.fall = fall  # <── NEW FLAG

        self.image_path = image_path or "assets/images/rocket.png"
        self.image_original = pygame.image.load(self.image_path).convert_alpha()

        # scaled image
        self.base_image = self.image_original
        self.rocket = self.base_image
        self.rocket_rect = self.rocket.get_rect()

        # rotation
        self.angle = 0.0
        self.rotation_speed = 90.0  # degrees per second

        # movement physics
        self.velocity = -self.base_speed  # up is negative y
        self.gravity = 350.0

        # flags
        self.clicked = False
        self.hover = False
        self.going_up = True
        self.done = False

        # shaking
        self.shake_strength = shake_strength
        self.shake_time = shake_time
        self._shake_time = 0.0

        self.overlay_alpha = 120
        self.sq_hover_size_p = 0.10

        # original position
        self.original_pos = self.rocket_rect.topleft

    def startup(self):
        self.rocket_rect.topleft = self.original_pos
        self.clicked = False
        self.hover = False
        self.going_up = True
        self.done = False
        self.angle = 0.0
        self.velocity = -self.base_speed
        self._shake_time = 0.0
        self.rocket = self.base_image

    def get_event(self, event: pygame.event.Event):
        if self.done:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and self.hover:
            self.clicked = True
            self._shake_time = self.shake_time

    def update(self, screen: pygame.Surface, dt: float):
        if self.done:
            return

        screen_w, screen_h = screen.get_size()

        # reposition & scale if not launched
        if not self.clicked:
            self.resize_and_repos(screen_w, screen_h)

        # hover detection
        mouse_pos = pygame.mouse.get_pos()
        self.hover = self.rocket_rect.collidepoint(mouse_pos)

        # launch physics
        if self.clicked and not self.done:
            self.launch_physics(dt, screen_h)

        # shake effect timer
        if self._shake_time > 0:
            self._shake_time -= dt

    def apply_fall(self, dt: float, screen_h: int):

        # rotate while falling
        self.angle += self.rotation_speed * dt
        if self.angle > 180.0:
            self.angle = 180.0

        # gravity
        self.velocity += self.gravity * dt
        self.rocket_rect.y += self.velocity * dt

        # went too high off top
        if self.rocket_rect.bottom < 0:
            self.done = True
            return

        # hit ground
        if self.rocket_rect.top >= screen_h - 1:
            self.done = True
            return

    def launch_physics(self, dt: float, screen_h: int):

        if self.going_up:
            dist_to_limit = max(0.0, abs(self.rocket_rect.y - self.height_reach))
            slow_factor = max(0.2, min(1.0, dist_to_limit / 300.0))

            self.velocity = -self.base_speed * slow_factor
            self.rocket_rect.y += self.velocity * dt

            # reached peak height
            if self.rocket_rect.y <= self.height_reach:
                self.going_up = False
                self.velocity = 0.0

        else:
            if self.fall:
                # regular gravity drop
                self.apply_fall(dt, screen_h)
            else:
                # fall disabled → rocket never comes back down
                self.velocity = -self.base_speed
                self.rocket_rect.y += self.velocity * dt

                if self.rocket_rect.bottom < 0:  # fully gone
                    self.done = True
                    return

        # Update rotation & rect
        rotated = pygame.transform.rotate(self.base_image, self.angle)
        center = self.rocket_rect.center
        self.rocket = rotated
        self.rocket_rect = self.rocket.get_rect(center=center)

    def resize_and_repos(self, screen_w: int, screen_h: int):
        if self.clicked:
            return

        w = int(screen_w * self.size_ratio[0])
        h = int(screen_h * self.size_ratio[1])
        self.base_image = pygame.transform.smoothscale(self.image_original, (w, h))

        x = int(screen_w * self.x_ratio - w / 2)
        y = int(screen_h - h - (screen_h * self.y_offset_ratio))

        self.rocket = self.base_image
        self.rocket_rect = self.rocket.get_rect(topleft=(x, y))
        self.original_pos = (x, y)

    def draw(self, screen: pygame.Surface):
        if self.hover and not self.clicked:
            self.draw_overlay(screen)

        screen.blit(self.rocket, self.rocket_rect)

        if self.hover and not self.clicked:
            self.draw_hover_squares(screen)

        if self.going_up and self.clicked and not self.done:
            self.draw_launch_particals(screen)

    def draw_overlay(self, screen: pygame.Surface):
        overlay = pygame.Surface(self.rocket_rect.size, pygame.SRCALPHA)
        overlay.fill((*Colors.BLACK, self.overlay_alpha))
        screen.blit(overlay, self.rocket_rect.topleft)

    def draw_launch_particals(self, screen: pygame.Surface):
        for _ in range(3):
            x, y = self.rocket_rect.bottomleft
            w, h = self.rocket_rect.size

            x = random.choice(list(range(int(x), int(x + w))))
            y = random.choice(list(range(int(y), int(y + h))))
            w = random.choice(list(range(int(w * 0.1), int(w * 0.25))))
            h = random.choice(list(range(int(h * 0.1), int(h * 0.25))))

            rect = (x, y, w, h)
            pygame.draw.rect(screen, random.choice(Colors.hots), rect)

    def shake(self):
        if self._shake_time > 0:
            return (
                random.randint(-self.shake_strength, self.shake_strength),
                random.randint(-self.shake_strength, self.shake_strength),
            )
        return (0, 0)

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
                screen, Colors.CRIMSON, (pos[0], pos[1], sq, sq), border_radius=4
            )
