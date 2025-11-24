import pygame
from typing import Dict, Optional
from pathlib import Path


class SoundManager:
    """Centralized sound system with proper cleanup and state management."""

    def __init__(self):
        # Initialize the mixer only once
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # Loaded sounds
        self.sounds: Dict[str, pygame.mixer.Sound] = {}

        # Channels playing sounds
        self.channels: Dict[str, pygame.mixer.Channel] = {}

        # Music track info
        self.current_music: Optional[str] = None
        self.music_volume: float = 0.7
        self.sound_volume: float = 0.8

    def load_sound(self, name: str, path: str) -> pygame.mixer.Sound:
        """Load a sound effect."""
        if name not in self.sounds:
            sound_path = Path(path)
            if sound_path.exists():
                self.sounds[name] = pygame.mixer.Sound(str(sound_path))
                self.sounds[name].set_volume(self.sound_volume)
            else:
                print(f"Warning: Sound file not found: {path}")
                # fallback silent sound
                self.sounds[name] = pygame.mixer.Sound(buffer=bytes(100))
        return self.sounds[name]

    def play_sound(
        self,
        name: str,
        loops: int = 0,
        fade_ms: int = 0,
        volume: Optional[float] = None,
    ) -> Optional[pygame.mixer.Channel]:
        """Play a sound effect, stopping previous instance if needed."""
        if name in self.sounds:
            # stop previous instance if playing
            if name in self.channels and self.channels[name]:
                self.channels[name].stop()

            sound = self.sounds[name]
            # apply per-play volume if specified
            if volume is not None:
                sound.set_volume(max(0.0, min(1.0, volume)))
            else:
                sound.set_volume(self.sound_volume)

            channel = sound.play(loops=loops, fade_ms=fade_ms)
            self.channels[name] = channel
            return channel
        return None

    def stop_sound(self, name: str, fade_ms: int = 0):
        """Stop a specific sound."""
        if name in self.channels and self.channels[name]:
            if fade_ms > 0:
                self.channels[name].fadeout(fade_ms)
            else:
                self.channels[name].stop()
            self.channels[name] = None

    def stop_all_sounds(self, fade_ms: int = 0):
        """Stop all sounds currently playing."""
        if fade_ms > 0:
            pygame.mixer.fadeout(fade_ms)
        else:
            pygame.mixer.stop()
        self.channels.clear()

    def is_sound_playing(self, name: str) -> bool:
        """Return True if a specific sound is currently playing."""
        if name in self.channels and self.channels[name]:
            return self.channels[name].get_busy()
        return False

    # --- Music methods ---
    def load_music(self, path: str):
        music_path = Path(path)
        if music_path.exists():
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(self.music_volume)
            self.current_music = str(music_path)
        else:
            print(f"Warning: Music file not found: {path}")

    def play_music(self, loops: int = -1, fade_ms: int = 0):
        if self.current_music:
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)

    def stop_music(self, fade_ms: int = 0):
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()

    def pause_music(self):
        pygame.mixer.music.pause()

    def unpause_music(self):
        pygame.mixer.music.unpause()

    # --- Volume control ---
    def set_sound_volume(self, volume: float):
        self.sound_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sound_volume)

    def set_music_volume(self, volume: float):
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

    # --- Cleanup ---
    def cleanup(self):
        """Stop all sounds/music and clear channels."""
        self.stop_all_sounds()
        self.stop_music()
        self.channels.clear()
