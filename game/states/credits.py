import pygame
import pygame.freetype
from game.core import BaseState
from game.utils import resource_path
from game.ui import Colors
from .states import States


class Credits(BaseState):
    def __init__(self, game=None):
        super().__init__(States.CREDITS, game)

        self.scroll_speed = 50  # pixels/sec
        self.text_items = []
        self.total_content_height = 0
        self.scroll_y = 0.0

        # --- FADE OUT LOGIC ---
        self.is_exiting = False
        self.exit_start_time = 0
        self.fade_duration = 2000  # 2 seconds to fade out music
        self.fade_surface = pygame.Surface(self.game.size, pygame.SRCALPHA)
        # ----------------------

        w, h = self.game.size
        self.section_spacing = int(h * 0.07)
        self.line_spacing = int(h * 0.02)
        self.base_font_size = self.game.size_depended(22)

        self._create_credits_text()

    def _create_credits_text(self):
        lines = []
        # --- Content Definition ---
        lines.append(("DEVELOPER", Colors.ICE_BLUE, True))
        lines.append(("Ido Badash, idoba12012011@gmail.com", Colors.CREAM, False))
        lines.append(("", Colors.CREAM, False))

        lines.append(("SCHOOL", Colors.ICE_BLUE, True))
        lines.append(("Ort Kramim Karmiel", Colors.CREAM, False))
        lines.append(("", Colors.CREAM, False))

        lines.append(("YEAR", Colors.ICE_BLUE, True))
        lines.append(("2025", Colors.CREAM, False))
        lines.append(("", Colors.CREAM, False))

        lines.append(("PROGRAM", Colors.ICE_BLUE, True))
        lines.append(("Space Olympics", Colors.CREAM, False))
        lines.append(("", Colors.CREAM, False))

        lines.append(("LEADING PROGRAM TEACHERS", Colors.ICE_BLUE, True))
        lines.append(("Tanyae Atikin, tanyae@kramim.ort.org.il", Colors.CREAM, False))
        lines.append(("Keren Raz, kerengeron@gmail.com", Colors.CREAM, False))
        lines.append(("", Colors.CREAM, False))

        lines.append(("STUDENTS TEAM", Colors.ICE_BLUE, True))
        lines.append(("Ido, Linor, Dan, Dafni, Maya", Colors.CREAM, False))
        lines.append(("", Colors.CREAM, False))

        lines.append(("RESEARCHERS / CONTRIBUTORS", Colors.ICE_BLUE, True))
        lines.append(("Linor, Dan, Dafni, Maya", Colors.CREAM, False))
        lines.append(("", Colors.CREAM, False))

        lines.append(("GITHUB", Colors.ICE_BLUE, True))
        lines.append(
            (
                "https://github.com/Ido-Badash/space_olympics_ort_kramim",
                Colors.CREAM,
                False,
            )
        )

        # --- Generation Logic ---
        self.text_items.clear()
        current_rel_y = 0

        for text, color, bold in lines:
            if text == "":
                current_rel_y += self.section_spacing
                continue

            style = (
                pygame.freetype.STYLE_STRONG if bold else pygame.freetype.STYLE_DEFAULT
            )
            surf, rect = self.game.font.render(
                text, color, size=self.base_font_size, style=style
            )
            self.text_items.append((surf, current_rel_y))
            current_rel_y += rect.height + self.line_spacing

        self.total_content_height = current_rel_y

    def startup(self):
        pygame.display.set_caption("Credits")
        self.scroll_y = float(self.game.height)

        # Reset exit state
        self.is_exiting = False
        self.fade_surface.fill((0, 0, 0, 0))  # Transparent

        try:
            self.game.sound_manager.load_sound(
                "credits", resource_path("assets/sound/music/moog_city_2_c418.mp3")
            )
            # Fade in slightly for smoothness
            self.game.sound_manager.play_sound("credits", fade_ms=1000)
        except Exception:
            pass

    def trigger_exit(self):
        """Helper to start the exit sequence (music fade + visual fade)."""
        if self.is_exiting:
            return  # Already exiting, don't trigger twice

        self.is_exiting = True
        self.exit_start_time = pygame.time.get_ticks()

        # Stop sound with fade out
        self.game.sound_manager.stop_sound("credits", fade_ms=self.fade_duration)

    def get_event(self, event):
        # If user clicks/escapes, trigger the exit sequence instead of jumping immediately
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.trigger_exit()

    def update(self, screen, dt):
        # 1. Handle Exiting Sequence
        if self.is_exiting:
            current_time = pygame.time.get_ticks()
            time_passed = current_time - self.exit_start_time

            # Calculate alpha for visual fade out (0 to 255)
            # This makes the screen go black smoothly while music fades
            alpha = min(255, int((time_passed / self.fade_duration) * 255))
            self.fade_surface.fill((0, 0, 0, alpha))

            # If time is up, FINALLY switch state
            if time_passed >= self.fade_duration:
                self.game.sm.set_state(States.MENU)
            return  # Skip scrolling logic if we are fading out

        # 2. Normal Scrolling Logic
        self.scroll_y -= self.scroll_speed * dt
        credits_bottom = self.scroll_y + self.total_content_height

        # 3. Auto-trigger exit when text is done
        if credits_bottom < 0:
            self.trigger_exit()

    def draw(self, screen):
        screen.fill(Colors.DEEP_SPACE_BLUE)

        screen_w = self.game.width
        screen_h = self.game.height

        for surf, rel_y in self.text_items:
            draw_y = self.scroll_y + rel_y
            if -50 < draw_y < screen_h + 50:
                draw_x = (screen_w - surf.get_width()) // 2
                screen.blit(surf, (draw_x, int(draw_y)))

        # Draw the black fade overlay (invisible unless is_exiting is True)
        if self.is_exiting:
            screen.blit(self.fade_surface, (0, 0))
