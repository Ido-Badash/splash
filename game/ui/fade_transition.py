from typing import Tuple
import pygame
from game.utils import clamp_alpha


class FadeTransition:
    def __init__(
        self,
        size: Tuple[int, int] = (0, 0),
        color: Tuple[int, int, int] = (0, 0, 0),
        starting_alpha: int = 0,
        ending_alpha: int = 255,
        pos: Tuple[int, int] = (0, 0),
        speed: int = 100,
    ):
        self.size = size
        self.color = color
        self.starting_alpha = clamp_alpha(starting_alpha)
        self.ending_alpha = clamp_alpha(ending_alpha)
        self.alpha = self.starting_alpha  # changing alpha
        self.pos = pos
        self.speed = speed
        self.done = False

    def startup(self):
        self.alpha = self.starting_alpha
        self.done = False

    def draw(self, screen: pygame.Surface):
        fade_surf = pygame.Surface(self.size, pygame.SRCALPHA)
        fade_surf.fill((*self.color, self.alpha))
        screen.blit(fade_surf, self.pos)

    def update(self, dt):
        if self.starting_alpha > self.ending_alpha:
            self.alpha -= max(1, self.speed * dt)
        elif self.starting_alpha < self.ending_alpha:
            self.alpha += max(1, self.speed * dt)

        # clamp alpha
        self.alpha = clamp_alpha(self.alpha)

        # animation ended, return True
        if self.alpha == self.ending_alpha:
            self.done = True

    def is_done(self):
        return self.done

    def set_size(self, new_size: Tuple[int, int]):
        self.size = new_size
