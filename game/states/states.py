from enum import Enum


class States(str, Enum):
    SPLASH_SCREEN = "Splash Screen"
    MENU = "Menu"
    PAUSE_MENU = "Pause Menu"
    CREDITS = "Credits"
    LAUNCH_TOWER = "Launch Tower"
    ORBIT_CONTROL = "Orbit Control"
    LIFE_CAPSULE = "Life Capsule"
    ASTRO_LINK = "Astro Link"
    SOFT_LANDING = "Soft Landing"
