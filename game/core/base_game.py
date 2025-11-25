from pathlib import Path
import glob
import os
from datetime import datetime
from typing import Tuple

import luneth_engine as le
from winmode import PygameWindowController, WindowStates

import pygame
import pygame.freetype


from .logger import logger
from .trigger_handler import TriggerHandler
from .sound_manager import SoundManager
from game.utils import resource_path


class BaseGame:

    def __init__(
        self,
        win_state: WindowStates = WindowStates.WINDOWED_STATELESS,
        open_in_fullscreen: bool = False,
        admin: bool = False,
    ):
        self.win_state = win_state
        self.admin = admin

        # le systems
        self.data_folder = Path("data")
        self.settings_path = self.data_folder / "settings.json"
        self.ss = le.SharedSettings(json_path=self.settings_path)
        self.ss.load()
        self.sm = le.StateManager(on_state_change=self.on_state_change)
        self.tm = le.TimeManager()
        self.gi = le.GlobalInputs()

        # Sound manager
        self.sound_manager = SoundManager()

        # init pygame
        pygame.init()
        pygame.mixer.init()
        self.clock = pygame.time.Clock()

        # time since last state
        self.last_state_tm = le.TimeManager()

        # winmode controller
        self.wc = PygameWindowController(
            (self.ss.get("screen_w", 640), self.ss.get("screen_h", 480)),
            WindowStates.FULLSCREEN if open_in_fullscreen else self.win_state,
        )

        # fps
        self.fps = self.ss.get("fps", 60)

        # --- Global Inputs with flags from settings.json ---

        # Fullscreen toggle (F11)
        if self.ss.get("can_fullscreen", True):
            self.gi.add_action(
                "fullscreen",
                lambda events: TriggerHandler.trigger_single_key(events, pygame.K_F11),
                self.toggle_fullscreen,
            )

        # Screenshot (F2)
        if self.ss.get("can_take_screenshots", True):
            self.gi.add_action(
                "screenshot",
                lambda events: TriggerHandler.trigger_single_key(events, pygame.K_F2),
                self.take_screenshot,
            )

        # Exit via Escape
        if self.ss.get("can_exit_via_escape", True):
            self.gi.add_action(
                "escape_quit",
                lambda events: TriggerHandler.trigger_single_key(
                    events, pygame.K_ESCAPE
                ),
                self.quit_game,
            )

        # Admin state switching (only if admin flag is True)
        if self.admin:
            self.gi.add_action(
                "refresh_state",
                lambda events: TriggerHandler.trigger_single_key(events, pygame.K_F3),
                lambda: self.state.startup() if self.state else None,
            )
            self.gi.add_action(
                "admin_switch_right",
                lambda events: TriggerHandler.trigger_single_key(
                    events, pygame.K_RIGHT
                ),
                self.sm.next_state,
            )
            self.gi.add_action(
                "admin_switch_left",
                lambda events: TriggerHandler.trigger_single_key(events, pygame.K_LEFT),
                self.sm.previous_state,
            )
            logger.info("Admin mode enabled: Use LEFT/RIGHT arrows to switch states")

        # screenshots
        self.screenshots_folder = Path("screenshots")

        # font
        self.font = pygame.freetype.Font(
            resource_path("assets/fonts/game_font_hebrew.ttf")
        )

        # add game to every state
        for s in self.sm.states:
            self.add_state(s)

    # --- states helper functions ---
    def add_state(self, state: le.State):
        state.game = self
        self.sm.add(state)

    # --- actions ---
    def on_state_change(self, old: le.State, new: le.State):
        logger.debug(f"Switching from [{old.name}] to [{new.name}]")

        # CRITICAL: Stop all sounds when changing states
        self.sound_manager.cleanup()

        self.last_state_tm.reset()

    def quit_game(self):
        self.running = False
        logger.debug("Quit triggered")

    def toggle_fullscreen(self):
        if self.wc.is_current_fullscreen_mode():
            self.wc.set_mode(self.win_state)
        else:
            self.wc.set_mode(WindowStates.FULLSCREEN)
        logger.debug("Fullscreen toggled")

    def take_screenshot(self):
        # make sure screenshots folder exists
        self.screenshots_folder.mkdir(exist_ok=True)

        # get datetime for filename
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")

        # pattern to count existing screenshots for this state
        pattern = str(self.screenshots_folder / "screenshot_*.png")
        screenshots = glob.glob(pattern)
        count = len(screenshots)

        # if folder has too many screenshots, delete the oldest
        if count >= 100:
            oldest = min(screenshots, key=os.path.getctime)
            os.remove(oldest)  # remove the full path

        # create the file path
        path = (
            self.screenshots_folder
            / f"screenshot_{self.state.name.value.lower()}_{formatted_datetime}.png"
        )

        # save screenshot
        pygame.image.save(self.screen, path)
        logger.info(f"Screenshot {formatted_datetime} saved in {path}")

    def clear_screenshots_folder(self):
        pattern = str(self.screenshots_folder / "screenshot_*.png")
        screenshots = glob.glob(pattern)
        for f in screenshots:
            os.remove(f)

    # --- properties ---
    @property
    def screen(self) -> pygame.Surface:
        return self.wc.get_screen()

    @property
    def size(self) -> Tuple[int, int]:
        return self.screen.get_size()

    @property
    def width(self) -> int:
        return self.screen.get_width()

    @property
    def height(self) -> int:
        return self.screen.get_height()

    @property
    def state(self):
        return self.sm.state

    @property
    def states(self):
        return self.sm.states

    @property
    def time_since_last_state(self):
        return self.last_state_tm.elapsed_time

    # --- util methods ---
    def size_depended(self, base_ratio: float):
        return min(self.width, self.height) / base_ratio

    # --- run ---
    def run(self):
        self.running = True
        try:
            if self.state:
                self.state.startup()
            while self.running and self.state:
                self.dt = self.clock.tick(self.fps) / 1000.0  # seconds

                # time managers
                self.tm.update(self.dt)
                self.last_state_tm.update(self.dt)

                # get events
                events = pygame.event.get()

                # update inputs
                self.gi.update(events, self.tm.dt)

                # event handle
                for event in events:
                    if event.type == pygame.QUIT:
                        self.running = False
                    else:
                        self.state.get_event(event)

                # update + draw
                self.state.update(self.screen, self.tm.dt)
                self.state.draw(self.screen)

                # TODO: sound

                # update display
                pygame.display.flip()

        except Exception as e:
            logger.exception(f"An unexpected error occurred in the main loop, {e}")

        finally:
            # Cleanup sounds before quitting
            self.sound_manager.cleanup()

            self.ss.save()
            pygame.quit()
            logger.info("Pygame Ended")
