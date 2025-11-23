from winmode import WindowController, WindowStates


def fullscreen_toggle(window_controller: WindowController):
    if window_controller.is_current_fullscreen_mode():
        window_controller.set_mode(WindowStates.WINDOWED)
    else:
        window_controller.set_mode(WindowStates.FULLSCREEN)


import sys
import os


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and PyInstaller.
    If relative_path is None, returns None safely.
    """
    if relative_path is None:
        return None
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)
