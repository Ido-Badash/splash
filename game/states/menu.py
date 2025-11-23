import pygame
import gif_pygame
import random
from game.core import BaseState, logger
from game.ui import FadeTransition, Colors
from game.widgets import Button, TextLine
from .states import States
from game.utils import resource_path


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
        self.bg_gif = gif_pygame.load(
            resource_path(self.game.ss.get("menu_bg_gif_path"))
        )
        self.bg_gif_surf = None

        # Load astronaut image
        self.astronaut_img = pygame.image.load(
            resource_path(self.game.ss.get("menu_astronaut_path"))
        ).convert_alpha()

        # Astronaut state
        self.astronaut = None
        self.astronaut_rect = None
        self.astronaut_x = -200  # Start off-screen left
        self.astronaut_y = 0
        self.astronaut_speed = 50  # pixels per second
        self.astronaut_rotation = 0.0
        self.astronaut_rotation_speed = 30.0  # degrees per second
        self._spawn_astronaut()

        # Title text
        self.title = TextLine(
            text="SPACE OLYMPICS",
            font=self.game.font,
            base_ratio=8,
            color=(*Colors.DISK_ORANGE, 255),  # hot black hole theme
            game_size=self.game.size,
            y_ratio=0.25,
        )

        # Subtitle text
        self.subtitle = TextLine(
            text="Test Your Space Skills",
            font=self.game.font,
            base_ratio=20,
            color=(*Colors.HOLO_YELLOW, 200),  # subtle warm glow
            game_size=self.game.size,
            y_ratio=0.35,
        )

        # Start button
        self.start_button = Button(
            color=Colors.DARK_CRIMSON,
            function=self._start_game,
            text="START",
            font=self.game.font,
            font_color=Colors.WHITE,
            hover_color=Colors.DISK_ORANGE,
            hover_font_color=Colors.WHITE,
            clicked_color=Colors.DISK_RED,
            clicked_font_color=Colors.WHITE,
            click_sound=pygame.Sound(
                resource_path(self.game.ss.get("button_click_path"))
            ),
            size_ratio=(0.25, 0.08),
            pos_ratio=(0.5, 0.55),
            screen_size=self.game.size,
            dynamic=True,
            border_color=Colors.DARK_ORANGE_RED,
            hover_border_color=Colors.DISK_ORANGE,
            clicked_border_color=Colors.DISK_RED,
            border_thickness=4,
            press_depth=6,
            border_radius=15,
        )

        # Exit button
        self.exit_button = Button(
            color=Colors.VOID_RED,
            function=self._exit_game,
            text="EXIT",
            font=self.game.font,
            font_color=Colors.HOLO_YELLOW,
            hover_color=Colors.DISK_RED,
            hover_font_color=Colors.WHITE,
            clicked_color=Colors.DARK_CRIMSON,
            clicked_font_color=Colors.WHITE,
            click_sound=pygame.Sound(
                resource_path(self.game.ss.get("button_click_path"))
            ),
            size_ratio=(0.25, 0.08),
            pos_ratio=(0.5, 0.68),
            screen_size=self.game.size,
            dynamic=True,
            border_color=Colors.DARK_ORANGE_RED,
            hover_border_color=Colors.DISK_ORANGE,
            clicked_border_color=Colors.DISK_RED,
            border_thickness=4,
            press_depth=6,
            border_radius=15,
        )

        # Pulsing effect for title
        self.pulse_timer = 0.0
        self.pulse_speed = 1.5

    def startup(self):
        pygame.display.set_caption("Space Olympics - Menu")
        self.fade_transition.startup()
        self.start_button.startup()
        self.exit_button.startup()
        self.pulse_timer = 0.0
        self._spawn_astronaut()

        # Play background music
        pygame.mixer.music.load(resource_path(self.game.ss.get("main_music_path")))
        pygame.mixer.music.play(-1, fade_ms=2000)

    def cleanup(self):
        pass

    def _start_game(self):
        """Start the game - go to first level."""
        logger.info("Menu: Starting game")
        self.game.sm.set_state(States.LAUNCH_TOWER)

    def _exit_game(self):
        """Exit the game."""
        logger.info("Menu: Exiting game")
        self.game.quit_game()

    def _spawn_astronaut(self):
        """Spawn a new astronaut at random Y position."""
        # Scale astronaut to reasonable size
        astronaut_width = int(self.game.width * 0.12)
        astronaut_aspect = (
            self.astronaut_img.get_height() / self.astronaut_img.get_width()
        )
        astronaut_height = int(astronaut_width * astronaut_aspect)

        self.astronaut_original = pygame.transform.scale(
            self.astronaut_img, (astronaut_width, astronaut_height)
        )

        # Random Y position
        self.astronaut_y = random.randint(
            int(self.game.height * 0.1), int(self.game.height * 0.9)
        )

        # Start off-screen left
        self.astronaut_x = -astronaut_width
        self.astronaut_rotation = 0.0

        # Random rotation speed
        self.astronaut_rotation_speed = random.uniform(20.0, 50.0)
        if random.random() > 0.5:
            self.astronaut_rotation_speed *= -1  # Sometimes rotate backwards

    def get_event(self, event: pygame.event.Event):
        self.start_button.get_event(event)
        self.exit_button.get_event(event)

    def draw(self, screen: pygame.Surface):
        # Draw animated GIF background
        if self.bg_gif_surf:
            screen.blit(self.bg_gif_surf, (0, 0))
            self.bg_gif._animate()

        # Draw semi-transparent overlay for better text visibility
        overlay = pygame.Surface(self.game.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        # Draw title with pulsing effect
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

        # Draw subtitle
        self.subtitle.draw(screen)

        # Draw buttons
        self.start_button.draw(screen)
        self.exit_button.draw(screen)

        # Draw floating astronaut
        self._draw_astronaut(screen)

        # Draw decorative stars
        self._draw_decorative_stars(screen)

        # Draw fade transition
        self.fade_transition.draw(screen)

    def _draw_astronaut(self, screen: pygame.Surface):
        """Draw the rotating floating astronaut."""
        if not hasattr(self, "astronaut_original"):
            return

        # Rotate astronaut
        rotated_astronaut = pygame.transform.rotate(
            self.astronaut_original, self.astronaut_rotation
        )
        astronaut_rect = rotated_astronaut.get_rect(
            center=(int(self.astronaut_x), int(self.astronaut_y))
        )

        screen.blit(rotated_astronaut, astronaut_rect)

    def _draw_decorative_stars(self, screen: pygame.Surface):
        """Draw some animated stars around the menu."""
        w, h = self.game.size

        # Calculate star positions based on timer for animation
        star_positions = [
            (w * 0.15, h * 0.15),
            (w * 0.85, h * 0.15),
            (w * 0.15, h * 0.85),
            (w * 0.85, h * 0.85),
            (w * 0.1, h * 0.5),
            (w * 0.9, h * 0.5),
        ]

        for i, (x, y) in enumerate(star_positions):
            # Each star has slightly different timing
            star_phase = (self.pulse_timer + i * 0.2) % 1.0
            alpha = int(
                150 + 105 * abs(pygame.math.Vector2(1, 0).rotate(star_phase * 360).x)
            )
            size = int(3 + 2 * star_phase)

            # Draw star (simple 4-pointed star)
            star_color = (*Colors.WHITE, alpha)
            star_surf = pygame.Surface((size * 6, size * 6), pygame.SRCALPHA)

            # Horizontal line
            pygame.draw.line(
                star_surf,
                star_color,
                (0, size * 3),
                (size * 6, size * 3),
                size,
            )
            # Vertical line
            pygame.draw.line(
                star_surf,
                star_color,
                (size * 3, 0),
                (size * 3, size * 6),
                size,
            )

            screen.blit(
                star_surf,
                (int(x - size * 3), int(y - size * 3)),
                special_flags=pygame.BLEND_ALPHA_SDL2,
            )

    def update(self, screen, dt):
        # Background GIF scaled to screen
        bg_frame, _ = self.bg_gif.get_current_frame_data()
        self.bg_gif_surf = pygame.transform.scale(bg_frame, self.game.size)

        # Update text layout on resize
        self.title.update(self.game.size)
        self.subtitle.update(self.game.size)

        # Update buttons
        self.start_button.update(self.game.size)
        self.exit_button.update(self.game.size)

        # Update fade transition
        self.fade_transition.set_size(self.game.size)
        self.fade_transition.update(dt)

        # Update pulse timer
        self.pulse_timer += dt * self.pulse_speed
        if self.pulse_timer >= 1.0:
            self.pulse_timer -= 1.0
