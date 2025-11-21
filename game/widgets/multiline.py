import pygame
from .text_line import TextLine


class MultiLine:
    def __init__(
        self,
        lines: list[TextLine],
        start_y_ratio: float,
        line_spacing_ratio: float,
        game_size: tuple,
    ):
        self.lines = lines
        self.start_y_ratio = start_y_ratio
        self.line_spacing_ratio = line_spacing_ratio
        self.game_size = game_size

        self.update(game_size)

    def update(self, game_size: tuple):
        self.game_size = game_size

        start_y = int(self.game_size[1] * self.start_y_ratio)
        spacing = int(self.game_size[1] * self.line_spacing_ratio)

        current_y = start_y

        # update each line with new pos
        for line in self.lines:
            line.update(self.game_size, y_override=current_y)
            current_y += line.rect.height + spacing

    def draw(self, screen: pygame.Surface):
        for line in self.lines:
            line.draw(screen)
