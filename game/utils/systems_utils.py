from winmode import WindowController, WindowStates


def fullscreen_toggle(window_controller: WindowController):
    if window_controller.is_current_fullscreen_mode():
        window_controller.set_mode(WindowStates.WINDOWED)
    else:
        window_controller.set_mode(WindowStates.FULLSCREEN)


# In game/utils/systems_utils.py (or wherever resource_path is)
import sys, os
from pathlib import Path


def resource_path(relative_path: str) -> str:
    if not relative_path:
        raise ValueError("resource_path received None!")

    # Use _MEIPASS if packaged by PyInstaller
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        # Use project root (2 levels up from utils/)
        base = Path(__file__).resolve().parent.parent.parent

    return str(base / relative_path)
