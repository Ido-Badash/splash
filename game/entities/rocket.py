from typing import Tuple
import pygame
from game.ui import Colors


class Rocket:
    def __init__(
        self,
        size_ratio: Tuple[float, float],
        x_ratio: float,
        y_offset_ratio: float = 0.03,
        speed: float = 300.0,
        image_path: str = None,
    ):
        self.size_ratio = size_ratio
        self.x_ratio = x_ratio
        self.y_offset_ratio = y_offset_ratio

        self.speed = speed
        self.image_path = image_path or "assets/images/rocket.png"
        self.image_original = pygame.image.load(self.image_path).convert_alpha()

        self.hover = False
        self.clicked = False

        self.size = (0, 0)
        self.dest = (0, 0)
        self.rocket = self.image_original

        self.overlay_alpha = 120
        self.sq_hover_size_p = 0.10  # 10%

    def startup(self):
        pass

    def get_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.hover:
            self.clicked = True
            print("Rocket clicked!")

    def draw(self, screen: pygame.Surface):
        if self.hover:
            self.draw_overlay(screen)

        screen.blit(self.rocket, self.dest)

        if self.hover:
            self.draw_hover_squares(screen)

    def update(self, screen: pygame.Surface, dt: float):
        screen_w, screen_h = screen.get_size()
        self.resize_and_repos(screen_w, screen_h)

        mouse_pos = pygame.mouse.get_pos()
        self.hover = self.rocket_rect.collidepoint(mouse_pos)

    def resize_and_repos(self, screen_w, screen_h):
        # dynamic size
        w = int(screen_w * self.size_ratio[0])
        h = int(screen_h * self.size_ratio[1])
        self.size = (w, h)

        # scale sprite
        self.rocket = pygame.transform.smoothscale(self.image_original, self.size)

        # dynamic position
        x = int(screen_w * self.x_ratio - w / 2)
        y = int(screen_h - h - (screen_h * self.y_offset_ratio))
        self.dest = (x, y)

    @property
    def rocket_rect(self):
        rect = self.rocket.get_rect()
        rect.topleft = self.dest
        return rect

    @property
    def hover_sqs_size(self):
        return int(
            min(self.rocket_rect.width, self.rocket_rect.height) * self.sq_hover_size_p
        )

    def draw_overlay(self, screen: pygame.Surface):
        rect = self.rocket_rect
        overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
        overlay.fill((*Colors.BLACK, self.overlay_alpha))  # black with transparency
        screen.blit(overlay, rect.topleft)

    def draw_hover_squares(self, screen: pygame.Surface):
        rect = self.rocket_rect
        sq = self.hover_sqs_size

        # sq's positions
        positions = {
            "up_left": (rect.left - sq * 1.0, rect.top - sq * 1.0),
            "up_right": (rect.right, rect.top - sq * 1.0),
            "down_left": (rect.left - sq * 1.0, rect.bottom),
            "down_right": (rect.right, rect.bottom),
        }

        for i, pos in enumerate(positions.values()):
            pygame.draw.rect(
                screen, Colors.CRIMSON, (pos[0], pos[1], sq, sq), border_radius=4
            )
