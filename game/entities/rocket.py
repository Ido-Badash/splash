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
        height_reach: int = 0,
        fall: bool = True,
        slow_down: bool = True,
        slow_down_factor: float = 300.0,
        min_speed=0.2,
        max_speed=1.0,
        launch_sound=None,
        flying_sound=None,
        dying_sound=None,
        falling_sound=None,
    ):
        self.size_ratio = size_ratio
        self.x_ratio = x_ratio
        self.y_offset_ratio = y_offset_ratio

        self.base_speed = speed
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.slow_down = slow_down
        self.slow_down_factor = slow_down_factor
        self.height_reach = height_reach
        self.fall = fall

        # sounds
        self.launch_sound = launch_sound
        self.flying_sound = flying_sound
        self.dying_sound = dying_sound
        self.falling_sound = falling_sound

        # image
        self.image_path = image_path or "assets/images/rocket.png"
        self.image_original = pygame.image.load(self.image_path).convert_alpha()
        self.base_image = self.image_original
        self.rocket = self.base_image
        self.rocket_rect = self.rocket.get_rect()

        # rotation & physics
        self.angle = 0.0
        self.rotation_speed = 90.0
        self.velocity = -self.base_speed
        self.gravity = 350.0

        # state flags
        self.clicked = False
        self.hover = False
        self.going_up = True
        self.done = False

        # sound flags
        self._flying_sound_played = False
        self._dying_sound_played = False
        self._falling_sound_played = False

        # shake
        self.shake_strength = shake_strength
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
        self.rocket = self.base_image

        # reset sounds
        self._flying_sound_played = False
        self._dying_sound_played = False
        self._falling_sound_played = False

    def get_event(self, event: pygame.event.Event):
        if self.done:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and self.hover:
            if self.launch_sound:
                self.launch_sound.play()
            self.start_flying()

    def start_flying(self):
        self.clicked = True
        self.going_up = True
        self.done = False
        self.velocity = -self.base_speed

        # reset sound flags
        self._flying_sound_played = False
        self._dying_sound_played = False
        self._falling_sound_played = False

    def is_flying(self):
        return self.clicked and not self.done

    def update(self, screen: pygame.Surface, dt: float):
        if self.done:
            return

        screen_w, screen_h = screen.get_size()
        self.resize_and_repos(screen_w, screen_h)

        # hover detection
        mouse_pos = pygame.mouse.get_pos()
        self.hover = self.rocket_rect.collidepoint(mouse_pos)

        if self.is_flying():
            self.launch_physics(dt, screen_h)

    def speed_factor(self, dist_to_limit: float):
        raw_factor = (
            dist_to_limit / self.slow_down_factor
            if self.slow_down
            else 0.5 * (dist_to_limit / self.slow_down_factor + 1)
        )
        return max(self.min_speed, min(self.max_speed, raw_factor))

    def launch_physics(self, dt: float, screen_h: int):
        if self.done:
            return  # do nothing if rocket is done

        # start flying sound once
        if not self._flying_sound_played and self.flying_sound:
            self.flying_sound.play(-1)
            self._flying_sound_played = True

        if self.going_up:
            dist_to_limit = max(0.0, abs(self.rocket_rect.y - self.height_reach))
            self.velocity = -self.base_speed * self.speed_factor(dist_to_limit)
            self.rocket_rect.y += self.velocity * dt

            if self.rocket_rect.y <= self.height_reach:
                self.going_up = False
                self.velocity = 0.0

                # stop flying sound at peak
                if self.flying_sound:
                    self.flying_sound.stop()

                # play dying sound
                if self.dying_sound and not self._dying_sound_played:
                    self.dying_sound.play()
                    self._dying_sound_played = True

                # strong rocket (fall=False) is done immediately
                if not self.fall:
                    self.done = True
                    self._stop_all_sounds()
        else:
            if self.fall:
                # falling sound once
                if not self._falling_sound_played and self.falling_sound:
                    self.falling_sound.play()
                    self._falling_sound_played = True
                self.apply_fall(dt, screen_h)
            else:
                self.done = True
                self._stop_all_sounds()

    def apply_fall(self, dt: float, screen_h: int):
        self.angle += self.rotation_speed * dt
        self.velocity += self.gravity * dt
        self.rocket_rect.y += self.velocity * dt

        if self.rocket_rect.bottom < 0 or self.rocket_rect.top >= screen_h - 1:
            self.done = True
            self._stop_all_sounds()

    def _stop_all_sounds(self):
        if self.flying_sound:
            self.flying_sound.stop()
        if self.dying_sound:
            self.dying_sound.stop()
        if self.falling_sound:
            self.falling_sound.stop()

    def resize_and_repos(self, screen_w: int, screen_h: int):
        if self.is_flying() or self.done:
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

        if self.going_up and self.is_flying():
            self.draw_launch_particals(screen)

    def draw_overlay(self, screen: pygame.Surface):
        overlay = pygame.Surface(self.rocket_rect.size, pygame.SRCALPHA)
        overlay.fill((*Colors.BLACK, self.overlay_alpha))
        screen.blit(overlay, self.rocket_rect.topleft)

    def draw_launch_particals(self, screen: pygame.Surface):
        for _ in range(3):
            x, y = self.rocket_rect.bottomleft
            w, h = self.rocket_rect.size

            x = random.randint(int(x), int(x + w))
            y = random.randint(int(y), int(y + h))
            w = random.randint(int(w * 0.1), int(w * 0.25))
            h = random.randint(int(h * 0.1), int(h * 0.25))

            pygame.draw.rect(screen, random.choice(Colors.hots), (x, y, w, h))

    def get_shake(self, min_px: int = 1):
        if self.clicked and self.going_up and not self.done:
            dist_to_peak = max(1.0, abs(self.rocket_rect.y - self.height_reach))
            factor = min(dist_to_peak / self.slow_down_factor, 1.0)
            shake_amount = max(min_px, int(self.shake_strength * factor))
            return (
                random.randint(-shake_amount, shake_amount),
                random.randint(-shake_amount, shake_amount),
            )
        return (0, 0)

    @property
    def hover_sqs_size(self):
        return int(
            min(self.rocket_rect.width, self.rocket_rect.height) * self.sq_hover_size_p
        )

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
