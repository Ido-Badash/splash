import pygame

class Tile:
    def __init__(self, x: int, y: int, walkable: bool = True, interactable: bool = False):
        self.x = x
        self.y = y
        self.walkable = walkable
        self.interactable = interactable
        self.sprite = None
        
    def draw(self, screen: pygame.Surface, tile_size: int):
        if self.sprite:
            screen.blit(self.sprite, (self.x * tile_size, self.y * tile_size))
            
    def update(self, screen: pygame.Surface, dt: float):
        pass
    
    def on_step(self, player):
        pass