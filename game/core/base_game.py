from pathlib import Path
import glob
import os
from datetime import datetime
from typing import Tuple, Dict

import luneth_engine as le
from winmode import PygameWindowController, WindowStates

import pygame
import pygame.freetype


from .logger import logger
from .trigger_handler import TriggerHandler
from game.utils.systems_utils import fullscreen_toggle


class BaseGame:

    def __init__(
        self,
        win_state: WindowStates = WindowStates.FULLSCREEN,
        open_in_fullscreen: bool = True,
        run_as_admin: bool = False,
    ):
        self.win_state = win_state
        self.run_as_admin = run_as_admin

        # le systems
        self.data_folder = Path("data")
        self.settings_path = self.data_folder / "settings.json"
        self.ss = le.SharedSettings(json_path=self.settings_path)
        self.ss.load()
        self.sm = le.StateManager(on_state_change=self.on_state_change)
        self.tm = le.TimeManager()
        self.gi = le.GlobalInputs()

        # init pygame
        pygame.init()
        self.clock = pygame.time.Clock()

        # time since last state
        self.last_state_tm = le.TimeManager()

        # winmode controller
        self.wc = PygameWindowController(
            (self.ss.get("screen_w", 640), self.ss.get("screen_h", 480)),
            WindowStates.FULLSCREEN if open_in_fullscreen else self.win_state,
        )

        # create global inputs
        self.create_global_inputs()

        # screenshots
        self.screenshots_folder = Path("screenshots")

        # font

        self.font = pygame.freetype.Font(self.ss.get("game_font_path"))

        # add game to every state
        for s in self.sm.states:
            self.add_state(s)

    # --- create global inputs ---
    def create_global_inputs(self):
        if self.ss.get("can_fullscreen"):
            self.gi.add_action(
                "fullscreen",
                lambda events: TriggerHandler.trigger_single_key(events, pygame.K_F11),
                self.toggle_fullscreen,
            )
        if self.ss.get("can_take_screenshots"):
            self.gi.add_action(
                "screenshot",
                lambda events: TriggerHandler.trigger_single_key(events, pygame.K_F2),
                self.take_screenshot,
            )
        if self.ss.get("can_exit_via_escape"):
            self.gi.add_action(
                "exit",
                lambda events: TriggerHandler.trigger_single_key(
                    events, pygame.K_ESCAPE
                ),
                self.quit_game,
            )
        if self.run_as_admin:

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

    # --- states helper functions ---
    def add_state(self, state: le.State):
        state.game = self
        self.sm.add(state)

    # --- actions ---
    def on_state_change(self, old: le.State, new: le.State):
        logger.debug(f"Switching from [{old.name}] to [{new.name}]")
        self.last_state_tm.reset()

    def quit_game(self):
        self.running = False
        logger.debug("Quit triggered")

    def toggle_fullscreen(self):
        if self.win_state == WindowStates.FULLSCREEN:
            return
        if self.wc.is_current_fullscreen_mode():
            self.wc.set_mode(self.win_state)
            logger.debug("Fullscreen toggled off")
        else:
            self.wc.set_mode(WindowStates.FULLSCREEN)
            logger.debug("Fullscreen toggled on")

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
        "Returns screen."
        return self.wc.get_screen()

    @property
    def size(self) -> Tuple[int, int]:
        "Returns screen size."
        return self.screen.get_size()

    @property
    def width(self) -> int:
        "Returns screen width."
        return self.screen.get_width()

    @property
    def height(self) -> int:
        "Returns screen height."
        return self.screen.get_height()

    @property
    def state(self):
        """Returns current state."""
        return self.sm.state

    @property
    def states(self):
        "Returns all states."
        return self.sm.states

    @property
    def time_since_last_state(self):
        "Returns time (in seconds) since last state change."
        return self.last_state_tm.elapsed_time

    # --- util methods ---
    def size_depended(self, base_ratio: float):
        return min(self.width, self.height) / base_ratio

    # --- get event ---
    def get_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self.running = False
        else:
            self.state.get_event(event)

    # --- run ---
    def run(self):
        self.running = True
        try:
            if self.state:
                self.state.startup()
            while self.running and self.state:
                self.dt = self.clock.tick(self.ss.get("fps", 60)) / 1000.0  # seconds

                # time managers
                self.tm.update(self.dt)
                self.last_state_tm.update(self.dt)

                # get events
                events = pygame.event.get()

                # update inputs
                self.gi.update(events, self.tm.dt)

                # event handle
                for event in events:
                    self.get_event(event)

                # update + draw
                self.state.update(self.screen, self.tm.dt)
                self.state.draw(self.screen)

                # update display
                pygame.display.flip()

        except Exception as e:
            logger.exception(f"An unexpected error occurred in the main loop, {e}")

        finally:
            self.ss.save()
            pygame.quit()
            logger.info("Pygame Ended")
