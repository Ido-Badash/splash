import pygame
import gif_pygame
from game.core import BaseState
from game.ui import FadeTransition, Colors
from game.utils import mid_pos
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

        self.bg_gif = gif_pygame.load(self.game.ss.get("launch_tower_bg_gif_path"))
        self.bg_gif_surf = None

        # --- MULTILINE TEXT BLOCK ---
        line_sizes = (25, 27, 30)
        self.text_block = MultiLine(
            lines=[
                TextLine(
                    text="Artemis wants to test out some rockets",
                    font=self.game.font,
                    base_ratio=line_sizes[0],
                    color=(*Colors.WHITE, 240),
                    game_size=self.game.size,
                ),
                TextLine(
                    text="Help them find the strongest rocket so they can fly to the moon.",
                    font=self.game.font,
                    base_ratio=line_sizes[1],
                    color=(*Colors.PLATINUM, 220),
                    game_size=self.game.size,
                ),
                TextLine(
                    text="(Click a rocket to launch)",
                    font=self.game.font,
                    base_ratio=line_sizes[2],
                    color=(*Colors.CRIMSON, 200),
                    game_size=self.game.size,
                ),
            ],
            start_y_ratio=0.05,
            line_spacing_ratio=0.015,
            game_size=self.game.size,
        )

        # --- rockets ---
        r_size_ratio = (0.08, 0.20)

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
            r.dying_sound = pygame.Sound(self.game.ss.lget("rocket_dying"))
            r.flying_sound = pygame.Sound(self.game.ss.lget("rocket_flying"))

        # track clicks
        self.clicks_count = 0

        self.strong_rocket = None
        self.start_finish = False

        # --- next button ---
        self.next_button = Button(
            color=Colors.DARK_GREEN,
            function=self.game.sm.next_state,
            text="Next Level →",
            font=self.game.font,
            font_color=Colors.PLATINUM,
            call_on_release=True,
            hover_color=Colors.KHAKI_PLAT,
            hover_font_color=Colors.DARK_GREEN,
            clicked_color=Colors.DARK_GREEN,
            clicked_font_color=Colors.PLATINUM,
            click_sound=pygame.Sound(self.game.ss.lget("button_click_path")),
            size_ratio=(0.15, 0.06),  # 15% width, 6% height of screen
            screen_size=self.game.screen.get_size(),
            border_radius=12,
        )

    def startup(self):
        pygame.display.set_caption(self.name.value)
        self.fade_transition.startup()
        self.next_button.startup()

        # reset all rockets
        for rocket in self.rockets_list:
            rocket.startup()

        self.current_rocket = None
        self.clicks_count = 0
        self.start_finish = False

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

        if event.type == pygame.KEYDOWN and self.game.run_as_admin:
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
            self.bg_gif._animate()

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
        # background GIF scaled to screen
        bg_frame, _ = self.bg_gif.get_current_frame_data()
        self.bg_gif_surf = pygame.transform.scale(bg_frame, self.game.size)

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

        # render text
        text_surf, text_rect = self.game.font.render(
            "Good Job!", Colors.WHITE, size=self.game.size_depended(10)
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
