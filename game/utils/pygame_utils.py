import pygame
from pathlib import Path

def load_sprite(path: str):
    p = Path(path)
    if p.exists():
        return pygame.image.load(path).convert_alpha()
    else:
        print(f"Warning: Sprite not found: {path}")
        return None
