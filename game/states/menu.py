import pygame
import gif_pygame
import random
from game.core import BaseState, logger
from game.ui import FadeTransition, Colors
from game.widgets import Button, TextLine
from .states import States
from game.utils import *


class Menu(BaseState):
    def __init__(self, game=None):
        super().__init__(States.MENU, game)
        self.fade_transition = FadeTransition(
            size=(self.game.width, self.game.height),
            starting_alpha=255,
            ending_alpha=0,
            speed=120,
        )

        # Load background GIF
        gif_path = resource_path("assets/gifs/menu_bg_gif.gif")
        with open(gif_path, "rb") as f:
            gif_bytes = f.read()
        self.bg_gif = load_gif_from_bytes(gif_bytes)
        self.bg_frame_index = 0
        self.bg_frame_delay = 60  # ms per frame
        self.bg_frame_timer = 0
        self.bg_gif_surf = None

        # Load astronaut image
        self.astronaut_img = pygame.image.load(
            resource_path("assets/images/astronaut.png")
        ).convert_alpha()

        # Astronaut state
        self.astronaut_x = -200
        self.astronaut_y = 0
        self.astronaut_speed = 50
        self.astronaut_rotation = 0.0
        self.astronaut_rotation_speed = 30.0
        self._spawn_astronaut()

        # Title text
        self.title = TextLine(
            text="SPACE OLYMPICS",
            font=self.game.font,
            base_ratio=8,
            color=(*Colors.DISK_ORANGE, 255),
            game_size=self.game.size,
            y_ratio=0.25,
        )

        # Subtitle text
        self.subtitle = TextLine(
            text="Test Your Space Skills",
            font=self.game.font,
            base_ratio=20,
            color=(*Colors.HOLO_YELLOW, 200),
            game_size=self.game.size,
            y_ratio=0.35,
        )

        # Buttons list (dynamic vertical layout)
        self.buttons = []

        # Start button
        self.start_button = Button(
            color=Colors.DARK_CRIMSON,
            function=self._start_game,
            text="START",
            font=self.game.font,
            font_size=50,
            font_color=Colors.CREAM,
            hover_color=Colors.DISK_RED,
            hover_font_color=Colors.WHITE,
            clicked_color=Colors.DARK_CRIMSON,
            clicked_font_color=Colors.WHITE,
            click_sound=pygame.Sound(
                resource_path("assets/sound/sfx/button_click.mp3")
            ),
            size_ratio=(0.25, 0.08),
            pos_ratio=(0.5, 0.0),
            screen_size=self.game.size,
            dynamic=True,
            border_color=Colors.CREAM,
            hover_border_color=Colors.DISK_ORANGE,
            clicked_border_color=Colors.DARK_CRIMSON,
            border_thickness=4,
            press_depth=6,
            border_radius=15,
        )
        self.buttons.append(self.start_button)

        self.credits_button = Button(
            color=Colors.DARK_CRIMSON,
            function=self._show_credits,
            text="CREDITS",
            font=self.game.font,
            font_size=50,
            font_color=Colors.WHITE,
            hover_color=Colors.DISK_RED,
            hover_font_color=Colors.WHITE,
            clicked_color=Colors.DISK_RED,
            clicked_font_color=Colors.WHITE,
            size_ratio=(0.25, 0.08),
            pos_ratio=(0.5, 0.0),
            screen_size=self.game.size,
            dynamic=True,
            border_color=Colors.DARK_ORANGE_RED,
            hover_border_color=Colors.DISK_ORANGE,
            clicked_border_color=Colors.DISK_RED,
            border_thickness=4,
            press_depth=6,
            border_radius=15,
        )
        self.buttons.append(self.credits_button)

        # Exit button
        self.exit_button = Button(
            color=Colors.VOID_RED,
            function=self._exit_game,
            text="EXIT",
            font=self.game.font,
            font_size=50,
            font_color=Colors.HOLO_YELLOW,
            hover_color=Colors.DISK_RED,
            hover_font_color=Colors.WHITE,
            clicked_color=Colors.DARK_CRIMSON,
            clicked_font_color=Colors.WHITE,
            click_sound=pygame.Sound(
                resource_path("assets/sound/sfx/button_click.mp3")
            ),
            size_ratio=(0.25, 0.08),
            pos_ratio=(0.5, 0.0),
            screen_size=self.game.size,
            dynamic=True,
            border_color=Colors.DARK_ORANGE_RED,
            hover_border_color=Colors.DISK_ORANGE,
            clicked_border_color=Colors.DISK_RED,
            border_thickness=4,
            press_depth=6,
            border_radius=15,
        )
        self.buttons.append(self.exit_button)

        # Pulsing effect for title
        self.pulse_timer = 0.0
        self.pulse_speed = 1.5

    def startup(self):
        pygame.display.set_caption("Space Olympics - Menu")
        self.fade_transition.startup()
        for btn in self.buttons:
            btn.startup()
        self.pulse_timer = 0.0
        self._spawn_astronaut()

        # Play background music
        pygame.mixer.music.load(resource_path("assets/sound/music/interstellar.mp3"))
        pygame.mixer.music.play(-1, fade_ms=2000)

        # Update button positions dynamically
        self._update_button_positions()

    def _update_button_positions(self):
        """Evenly distribute buttons vertically under subtitle."""
        w, h = self.game.size
        top_ratio = 0.5  # start below subtitle
        bottom_ratio = 0.75  # end before bottom
        n = len(self.buttons)
        if n > 1:
            step = (bottom_ratio - top_ratio) / (n - 1)
        else:
            step = 0
        for i, btn in enumerate(self.buttons):
            btn.pos_ratio = (0.5, top_ratio + i * step)
            btn.update(self.game.size)

    def _start_game(self):
        logger.info("Menu: Starting game")
        self.game.sm.set_state(States.SPACE_QUIZ)

    def _show_credits(self):
        logger.info("Menu: Showing Credits")
        self.game.sm.set_state(States.CREDITS)

    def _exit_game(self):
        logger.info("Menu: Exiting game")
        self.game.quit_game()

    def _spawn_astronaut(self):
        astronaut_width = int(self.game.width * 0.12)
        astronaut_aspect = (
            self.astronaut_img.get_height() / self.astronaut_img.get_width()
        )
        astronaut_height = int(astronaut_width * astronaut_aspect)
        self.astronaut_original = pygame.transform.scale(
            self.astronaut_img, (astronaut_width, astronaut_height)
        )
        self.astronaut_y = random.randint(
            int(self.game.height * 0.1), int(self.game.height * 0.9)
        )
        self.astronaut_x = -astronaut_width
        self.astronaut_rotation = 0.0
        self.astronaut_rotation_speed = random.uniform(20.0, 50.0)
        if random.random() > 0.5:
            self.astronaut_rotation_speed *= -1

    def get_event(self, event: pygame.event.Event):
        for btn in self.buttons:
            btn.get_event(event)

    def draw(self, screen: pygame.Surface):
        # Draw background GIF
        if self.bg_gif_surf:
            screen.blit(self.bg_gif_surf, (0, 0))

        # Overlay
        overlay = pygame.Surface(self.game.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        # Title pulsing
        pulse_scale = 1.0 + 0.05 * abs(
            pygame.math.Vector2(1, 0).rotate(self.pulse_timer * 360).x
        )
        title_size = int(self.game.size_depended(8) * pulse_scale)
        title_surf, title_rect = self.game.font.render(
            "SPACE OLYMPICS", Colors.WHITE, size=title_size
        )
        title_rect.centerx = self.game.width // 2
        title_rect.centery = int(self.game.height * 0.25)
        screen.blit(title_surf, title_rect)

        # Subtitle
        self.subtitle.draw(screen)

        # Buttons
        for btn in self.buttons:
            btn.draw(screen)

        # Astronaut
        self._draw_astronaut(screen)

        # Stars
        self._draw_decorative_stars(screen)

        # Fade
        self.fade_transition.draw(screen)

    def _draw_astronaut(self, screen: pygame.Surface):
        rotated = pygame.transform.rotate(
            self.astronaut_original, self.astronaut_rotation
        )
        rect = rotated.get_rect(center=(int(self.astronaut_x), int(self.astronaut_y)))
        screen.blit(rotated, rect)

    def _draw_decorative_stars(self, screen: pygame.Surface):
        w, h = self.game.size
        star_positions = [
            (w * 0.15, h * 0.15),
            (w * 0.85, h * 0.15),
            (w * 0.15, h * 0.85),
            (w * 0.85, h * 0.85),
            (w * 0.1, h * 0.5),
            (w * 0.9, h * 0.5),
        ]
        for i, (x, y) in enumerate(star_positions):
            star_phase = (self.pulse_timer + i * 0.2) % 1.0
            alpha = int(
                150 + 105 * abs(pygame.math.Vector2(1, 0).rotate(star_phase * 360).x)
            )
            size = int(3 + 2 * star_phase)
            star_color = (*Colors.WHITE, alpha)
            surf = pygame.Surface((size * 6, size * 6), pygame.SRCALPHA)
            pygame.draw.line(
                surf, star_color, (0, size * 3), (size * 6, size * 3), size
            )
            pygame.draw.line(
                surf, star_color, (size * 3, 0), (size * 3, size * 6), size
            )
            screen.blit(
                surf,
                (int(x - size * 3), int(y - size * 3)),
                special_flags=pygame.BLEND_ALPHA_SDL2,
            )

    def update(self, screen, dt):
        # GIF update
        self.bg_frame_timer += dt
        if self.bg_frame_timer >= self.bg_frame_delay:
            self.bg_frame_timer = 0
            self.bg_frame_index = (self.bg_frame_index + 1) % len(self.bg_gif)
        self.bg_gif_surf = pygame.transform.scale(
            self.bg_gif[self.bg_frame_index], self.game.size
        )

        # Text
        self.title.update(self.game.size)
        self.subtitle.update(self.game.size)

        # Buttons
        for btn in self.buttons:
            btn.update(self.game.size)

        # Fade
        self.fade_transition.set_size(self.game.size)
        self.fade_transition.update(dt)

        # Pulse
        self.pulse_timer += dt * self.pulse_speed
        if self.pulse_timer >= 1.0:
            self.pulse_timer -= 1.0
