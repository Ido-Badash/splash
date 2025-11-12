from winmode import WindowController, WindowStates


def fullscreen_toggle(window_controller: WindowController):
    if window_controller.is_current_fullscreen_mode():
        window_controller.set_mode(WindowStates.WINDOWED)
    else:
        window_controller.set_mode(WindowStates.FULLSCREEN)