import pygame as pg
import pygame.freetype as ft


class Button:
    """A button with text, sounds, dynamic sizing/position, and optional border/press effect."""

    def __init__(
        self,
        color,
        function,
        text=None,
        font=None,
        font_color=pg.Color("white"),
        call_on_release=True,
        hover_color=None,
        clicked_color=None,
        hover_font_color=None,
        clicked_font_color=None,
        click_sound=None,
        hover_sound=None,
        size_ratio=(0.2, 0.1),
        pos_ratio=(0.5, 0.5),
        screen_size=(800, 600),
        dynamic: bool = True,
        border_color=None,
        hover_border_color=None,
        clicked_border_color=None,
        border_thickness: int = 2,
        press_depth: int = 4,
        border_radius: int = 0,
    ):
        self.color = color
        self.function = function
        self.clicked = False
        self.hovered = False
        self.dynamic = dynamic

        # ratios for dynamic sizing/position
        self.size_ratio = size_ratio
        self.pos_ratio = pos_ratio
        self.screen_size = screen_size

        # text
        self.text = text
        self.font = font or pg.font.Font(None, 16)
        self.font_color = font_color
        self.hover_font_color = hover_font_color
        self.clicked_font_color = clicked_font_color

        # behavior
        self.call_on_release = call_on_release
        self.hover_color = hover_color
        self.clicked_color = clicked_color

        # sounds
        self.click_sound = click_sound
        self.hover_sound = hover_sound

        # border settings
        self.border_color = border_color or pg.Color("black")
        self.hover_border_color = hover_border_color or self.border_color
        self.clicked_border_color = clicked_border_color or self.border_color
        self.border_thickness = border_thickness
        self.press_depth = press_depth
        self.border_radius = border_radius

        # set initial rect
        self.update_rect()

        # pre-render text surfaces
        self.render_text()

    def startup(self):
        pass

    def get_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            self.on_click(event)
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.on_release(event)

    def update(self, screen_size=None):
        if self.dynamic and screen_size:
            self.update_rect(screen_size)
        self.check_hover()

    def draw(self, surface):
        """Draw button with border, optional press effect, and rounded corners."""
        bg_color = self.color
        border_color = self.border_color
        text_surface = self.text_surface
        offset = 0

        if self.clicked:
            if self.clicked_color:
                bg_color = self.clicked_color
            border_color = self.clicked_border_color
            text_surface = self.clicked_text
            offset = self.press_depth
        elif self.hovered:
            if self.hover_color:
                bg_color = self.hover_color
            border_color = self.hover_border_color
            text_surface = self.hover_text

        # draw border rect (behind button)
        border_rect = self.rect.copy()
        border_rect.y += offset
        pg.draw.rect(
            surface, border_color, border_rect, border_radius=self.border_radius
        )

        # draw main button slightly smaller inside border
        inner_rect = self.rect.inflate(
            -self.border_thickness * 2, -self.border_thickness * 2
        )
        inner_rect.y += offset
        pg.draw.rect(surface, bg_color, inner_rect, border_radius=self.border_radius)

        # draw text
        if self.text:
            text_rect = text_surface.get_rect(center=inner_rect.center)
            surface.blit(text_surface, text_rect)

    def update_rect(self, screen_size=None):
        """Update button rect based on screen size and ratios."""
        if not self.dynamic:
            return
        if screen_size:
            self.screen_size = screen_size

        sw, sh = self.screen_size
        bw = int(sw * self.size_ratio[0])
        bh = int(sh * self.size_ratio[1])
        cx = int(sw * self.pos_ratio[0])
        cy = int(sh * self.pos_ratio[1])
        self.rect = pg.Rect(0, 0, bw, bh)
        self.rect.center = (cx, cy)

    def render_text(self):
        """Pre-render text surfaces (supports freetype and pygame font)."""
        if not self.text:
            return

        if isinstance(self.font, ft.Font):
            surf = self.font.render(self.text, self.font_color)
            self.text_surface = surf[0] if isinstance(surf, tuple) else surf
            self.hover_text = (
                self.font.render(self.text, self.hover_font_color)[0]
                if self.hover_font_color
                else self.text_surface
            )
            self.clicked_text = (
                self.font.render(self.text, self.clicked_font_color)[0]
                if self.clicked_font_color
                else self.text_surface
            )
        else:
            self.text_surface = self.font.render(self.text, True, self.font_color)
            self.hover_text = (
                self.font.render(self.text, True, self.hover_font_color)
                if self.hover_font_color
                else self.text_surface
            )
            self.clicked_text = (
                self.font.render(self.text, True, self.clicked_font_color)
                if self.clicked_font_color
                else self.text_surface
            )

    def on_click(self, event):
        if self.rect.collidepoint(event.pos):
            self.clicked = True
            if self.click_sound:
                self.click_sound.play()
            if not self.call_on_release:
                self.function()

    def on_release(self, event):
        if self.clicked and self.call_on_release:
            self.function()
            if self.click_sound:
                self.click_sound.play()
        self.clicked = False

    def check_hover(self):
        hovered_now = self.rect.collidepoint(pg.mouse.get_pos())
        if hovered_now and not self.hovered and self.hover_sound:
            self.hover_sound.play()
        self.hovered = hovered_now
