import pygame
import gif_pygame
from game.core import BaseState
from game.ui import FadeTransition, Colors
from game.utils import *
from .states import States
from game.entities import Rocket
from game.widgets import TextLine, MultiLine, Button


class LaunchTower(BaseState):
    def __init__(self, game=None):
        super().__init__(States.LAUNCH_TOWER, game)
        self.current_rocket = None  # track the current active rocket

        self.fade_transition = FadeTransition(
            size=(self.game.width, self.game.height),
            starting_alpha=255,
            ending_alpha=0,
        )

        bg_gif_path = resource_path("assets/gifs/launch_tower_bg.gif")
        with open(bg_gif_path, "rb") as f:
            gif_bytes = f.read()

        self.bg_gif = load_gif_from_bytes(gif_bytes)
        self.bg_frame_index = 0
        self.bg_frame_delay = 0.5  # ms per frame
        self.bg_frame_timer = 0

        self.bg_gif_surf = None

        # --- MULTILINE TEXT BLOCK (Localized) ---
        line_sizes = (25, 27, 30)
        self.text_block = MultiLine(
            lines=[
                TextLine(
                    text=heb("ארטמיס רוצה לבדוק כמה רקטות"),
                    font=self.game.font,
                    base_ratio=line_sizes[0],
                    color=(*Colors.WHITE, 240),
                    game_size=self.game.size,
                ),
                TextLine(
                    text=heb(
                        "עזרו להם למצוא את הרקטה החזקה ביותר כדי שיוכלו לטוס לירח."
                    ),
                    font=self.game.font,
                    base_ratio=line_sizes[1],
                    color=(*Colors.PLATINUM, 220),
                    game_size=self.game.size,
                ),
                TextLine(
                    text="(" + heb("לחץ על רקטה כדי לשגר") + ")",
                    font=self.game.font,
                    base_ratio=line_sizes[2],
                    color=(*Colors.CRIMSON, 200),
                    game_size=self.game.size,
                ),
            ],
            start_y_ratio=0.025,
            line_spacing_ratio=0.015,
            game_size=self.game.size,
        )

        # --- rockets ---
        r_size_ratio = (0.08, 0.18)

        self.rockets_list = [
            Rocket(
                size_ratio=r_size_ratio,
                x_ratio=0.25,
                y_offset_ratio=0.03,
                speed=200.0,
                fall=True,
            ),
            Rocket(
                size_ratio=r_size_ratio,
                x_ratio=0.5,
                y_offset_ratio=0.03,
                speed=200.0,
                fall=True,
            ),
            Rocket(
                size_ratio=r_size_ratio,
                x_ratio=0.75,
                y_offset_ratio=0.03,
                speed=200.0,
                fall=True,
            ),
        ]

        for r in self.rockets:
            r.dying_sound = pygame.Sound(
                resource_path("assets/sound/sfx/rocket_dying.mp3")
            )
            r.flying_sound = pygame.Sound(
                resource_path("assets/sound/sfx/rocket_flying.mp3")
            )

        # win sound
        self.game.sound_manager.load_sound(
            "win", resource_path("assets/sound/sfx/win.mp3")
        )

        # track clicks
        self.clicks_count = 0

        self.strong_rocket = None
        self.start_finish = False
        self._played_win_sound = False

        # --- next button (Localized) ---
        self.next_button = Button(
            color=Colors.DARK_GREEN,
            function=self.game.sm.next_state,
            text=heb("לשלב הבא"),
            font=self.game.font,
            font_color=Colors.PLATINUM,
            call_on_release=True,
            hover_color=Colors.KHAKI_PLAT,
            hover_font_color=Colors.DARK_GREEN,
            clicked_color=Colors.DARK_GREEN,
            clicked_font_color=Colors.PLATINUM,
            click_sound=pygame.Sound(
                resource_path("assets/sound/sfx/button_click.mp3")
            ),
            size_ratio=(0.15, 0.06),  # 15% width, 6% height of screen
            screen_size=self.game.screen.get_size(),
            border_radius=12,
        )

    def startup(self):
        # Localized window caption
        pygame.display.set_caption(heb("מגדל שיגור"))
        self.fade_transition.startup()
        self.next_button.startup()

        # reset all rockets
        for rocket in self.rockets_list:
            rocket.startup()

        self.current_rocket = None
        self.clicks_count = 0
        self.start_finish = False
        self._played_win_sound = False

        # play main music
        pygame.mixer.music.load(resource_path("assets/sound/music/interstellar.mp3"))
        pygame.mixer.music.play(-1, fade_ms=2000)

    def cleanup(self):
        pass

    def get_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # only allow clicking if no rocket is currently active
            if self.current_rocket is None or self.current_rocket.done:
                for rocket in self.rockets_list:
                    if rocket.rocket_rect.collidepoint(event.pos) and not rocket.done:
                        rocket.get_event(event)
                        self.rocket_stack_logic(rocket)
                        break

        if event.type == pygame.KEYDOWN and self.game.admin:
            if event.key == pygame.K_d and (event.mod & pygame.KMOD_CTRL):
                for r in self.rockets:
                    r.done = True

        if self.start_finish:
            self.next_button.get_event(event)

    def draw(self, screen: pygame.Surface):
        # rocket shake based on current rocket
        shake_x, shake_y = self.get_screen_shake_offset()

        # background
        if self.bg_gif_surf:
            screen.blit(self.bg_gif_surf, (shake_x, shake_y))

        # text block
        self.text_block.draw(screen)

        # draw all rockets
        for rocket in self.rockets_list:
            rocket.draw(screen)

        if self.start_finish:
            self.finish_animation(screen)

        # fade
        self.fade_transition.draw(screen)

    def update(self, screen, dt):
        # If GIF delay accidentally left large, reduce to reasonable frame interval:
        if hasattr(self, "bg_frame_delay") and self.bg_frame_delay > 1.0:
            # likely value from earlier bug — use ~120ms per frame
            self.bg_frame_delay = 0.12

        # Background GIF (dt is seconds)
        self.bg_frame_timer += dt
        if self.bg_frame_timer >= self.bg_frame_delay:
            self.bg_frame_timer = 0.0
            # protect against empty gif frames
            if self.bg_gif:
                self.bg_frame_index = (self.bg_frame_index + 1) % len(self.bg_gif)
        if self.bg_gif:
            bg_frame = self.bg_gif[self.bg_frame_index]
            # scale each frame to screen size
            try:
                self.bg_gif_surf = pygame.transform.scale(bg_frame, self.game.size)
            except Exception:
                # fallback: if frame isn't a surface, ignore
                self.bg_gif_surf = None

        # update text layout on resize
        self.text_block.update(self.game.size)

        # update all rockets
        for rocket in self.rockets_list:
            rocket.update(screen, dt)

        # if current rocket is done, clear it
        if self.current_rocket and self.current_rocket.done:
            self.current_rocket = None

        # if all rockets are done, start finish animation
        if all(rocket.done for rocket in self.rockets_list):
            self.start_finish = True

        # fade
        self.fade_transition.set_size(self.game.size)
        self.fade_transition.update(dt)

    def finish_animation(self, screen: pygame.Surface):
        w, h = screen.get_size()

        overlay = pygame.Surface(self.game.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        if not self._played_win_sound:
            self.game.sound_manager.play_sound("win")
            self._played_win_sound = True

        # render text (Localized)
        text_surf, text_rect = self.game.font.render(
            heb("עבודה טובה!"), Colors.WHITE, size=self.game.size_depended(10)
        )

        # calculate text actual pos on screen
        text_pos = mid_pos((w, h), text_rect)
        screen.blit(text_surf, text_pos)

        # get actual rect in screen
        text_rect_on_screen = text_rect.copy()
        text_rect_on_screen.topleft = text_pos  # update to screen

        # set button pos below text
        self.next_button.pos_ratio = (
            text_rect_on_screen.centerx / w,
            (text_rect_on_screen.bottom + text_rect_on_screen.h) / h,
        )

        self.next_button.update((w, h))
        self.next_button.draw(screen)

    def rocket_stack_logic(self, rocket: Rocket):
        # set the rocket height based on click order
        self.clicks_count += 1
        screen_h = self.game.height

        if self.clicks_count == 1:
            # first click: weak rocket (25% height)
            rocket.height_reach = int(screen_h * 0.5)
            rocket.shake = 1
            rocket.fall = True
        elif self.clicks_count == 2:
            # second click: medium rocket (50% height)
            rocket.height_reach = int(screen_h * 0.25)
            rocket.shake = 2
            rocket.fall = True
        else:
            # third click: strong rocket (flies off screen)
            rocket.height_reach = int(-screen_h)
            rocket.base_speed *= 2
            rocket.shake = 3
            rocket.slow_down = False
            rocket.fall = False
            self.strong_rocket = rocket

        self.current_rocket = rocket

    def get_screen_shake_offset(self):
        if isinstance(self.current_rocket, Rocket):
            return self.current_rocket.get_shake()
        return (0, 0)

    @property
    def rockets(self):
        return self.rockets_list
