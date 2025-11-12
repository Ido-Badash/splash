import pygame
from game.core import Tile

class Floor(Tile):
    def __init__(self, x, y):
        super().__init__(x, y)