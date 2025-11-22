import pygame


class TextLine:
    def __init__(
        self,
        text: str,
        font: pygame.font.Font,
        base_ratio: float,
        color: tuple,
        game_size: tuple,
        padding=(0, 0, 0, 0),  # (left, top, right, bottom)
        x_ratio=0.5,
        y_ratio=None,
        center_x=True,
    ):
        self.text = text
        self.font = font
        self.base_ratio = base_ratio
        self.color = color
        self.padding = padding
        self.game_size = game_size
        self.x_ratio = x_ratio
        self.y_ratio = y_ratio
        self.center_x = center_x

        self.surf = None
        self.rect = None
        self.pos = (0, 0)

        self.update(game_size)

    # update size & position
    def update(self, game_size: tuple, y_override=None):
        self.game_size = game_size

        # dynamic font size
        font_size = int(self.game_size[1] / self.base_ratio)
        self.font.size = font_size
        self.surf, _ = self.font.render(self.text, self.color)
        self.rect = self.surf.get_rect()

        # --- padding ---
        left, top, right, bottom = self.padding
        self.rect.width += left + right
        self.rect.height += top + bottom

        # --- y ---
        y = (
            y_override
            if y_override is not None
            else int(self.game_size[1] * self.y_ratio if self.y_ratio else 0)
        )

        # --- x ---
        if self.center_x:
            x = self.game_size[0] // 2 - self.rect.width // 2
        else:
            x = int(self.game_size[0] * self.x_ratio)

        self.pos = (x, y)

    def draw(self, screen: pygame.Surface):
        screen.blit(self.surf, self.pos)
