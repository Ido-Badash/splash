import sys
from pathlib import Path

from game.utils.systems_utils import fullscreen_toggle

import glob
import os
from datetime import datetime

from typing import Any, Dict, List, Optional

import luneth_engine as le
import pygame
from winmode import PygameWindowController, WindowStates

from .logger import logger


class BaseGame:
    def __init__(
        self,
        states: Optional[List[le.State]] = None,
    ):
        # le systems
        self.data_folder = Path("data")
        self.settings_path = self.data_folder / "settings.json"
        self.ss = le.SharedSettings(json_path=self.settings_path)
        self.ss.load()
        self.sm = le.StateManager()
        self.tm = le.TimeManager()
        self.gi = le.GlobalInputs()

        # init pygame
        pygame.init()
        self.clock = pygame.time.Clock()

        # winmode controller
        self.wc = PygameWindowController(
            (self.ss.get("screen_w", 640), self.ss.get("screen_h", 480)),
            WindowStates.WINDOWED,
        )

        # create global inputs
        self.gi.add_action("fullscreen", self.trigger_f11, self.toggle_fullscreen)
        self.gi.add_action("screenshot", self.trigger_f2, self.take_screenshot)

        # screenshots
        self.screenshots_folder = Path("screenshots")

        # add game to every state if states were provided
        if states:
            for s in self.sm.states:
                self.add_state(s)

        # start the first state
        if self.states:
            self.state.startup()

    # --- helper functions ---
    def add_state(self, state: le.State):
        state.game = self
        self.sm.add(state)

    # --- actions ---
    def quit_game(self):
        self.running = False
        logger.debug("Quit triggered")

    def toggle_fullscreen(self):
        fullscreen_toggle(self.wc)
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

    # --- triggers ---
    def trigger_f11(self, events):
        return any(e.type == pygame.KEYDOWN and e.key == pygame.K_F11 for e in events)

    def trigger_f2(self, events):
        return any(e.type == pygame.KEYDOWN and e.key == pygame.K_F2 for e in events)

    # --- properties ---
    @property
    def screen(self):
        return self.wc.get_screen()

    @property
    def state(self):
        return self.sm.state

    @property
    def states(self):
        return self.sm.states

    # --- run ---
    def run(self):
        self.running = True
        try:
            while self.running and self.state:
                self.dt = self.clock.tick(self.ss.get("fps", 60)) / 1000.0  # seconds
                self.tm.update(self.dt)

                # get events
                events = pygame.event.get()

                # update inputs
                self.gi.update(events, self.dt)

                # event handle
                for event in events:
                    if event.type == pygame.QUIT:
                        self.running = False
                    else:
                        self.state.get_event(event)

                # update + draw
                self.state.update(self.screen, self.dt)
                self.state.draw(self.screen)

                # find and switch to the named state
                if self.state.done:
                    self.sm.default_switcher()
                    
                # update display
                pygame.display.flip()

        except Exception as e:
            logger.exception(f"An unexpected error occurred in the main loop {e}")

        finally:
            self.ss.save()
            pygame.quit()
            logger.info("Pygame Ended")
