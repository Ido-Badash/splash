"""
Sound Manager - Centralized sound system with proper cleanup
"""

import pygame
from typing import Dict, Optional
from pathlib import Path


class SoundManager:
    """Manages all game sounds with proper cleanup and state management"""

    def __init__(self):
        pygame.mixer.init()

        # Store loaded sounds
        self.sounds: Dict[str, pygame.mixer.Sound] = {}

        # Track playing channels
        self.channels: Dict[str, pygame.mixer.Channel] = {}

        # Music track
        self.current_music: Optional[str] = None
        self.music_volume: float = 0.7
        self.sound_volume: float = 0.8

    def load_sound(self, name: str, path: str) -> pygame.mixer.Sound:
        """Load a sound effect and store it"""
        if name not in self.sounds:
            sound_path = Path(path)
            if sound_path.exists():
                self.sounds[name] = pygame.mixer.Sound(path)
                self.sounds[name].set_volume(self.sound_volume)
            else:
                print(f"Warning: Sound file not found: {path}")
                # Create a dummy silent sound
                self.sounds[name] = pygame.mixer.Sound(buffer=bytes(100))
        return self.sounds[name]

    def play_sound(
        self, name: str, loops: int = 0, fade_ms: int = 0
    ) -> Optional[pygame.mixer.Channel]:
        """Play a sound effect. Returns the channel it's playing on."""
        if name in self.sounds:
            # Stop previous instance of this sound if it exists
            if name in self.channels and self.channels[name]:
                self.channels[name].stop()

            # Play the sound
            channel = self.sounds[name].play(loops=loops, fade_ms=fade_ms)
            self.channels[name] = channel
            return channel
        return None

    def stop_sound(self, name: str, fade_ms: int = 0):
        """Stop a specific sound"""
        if name in self.channels and self.channels[name]:
            if fade_ms > 0:
                self.channels[name].fadeout(fade_ms)
            else:
                self.channels[name].stop()
            self.channels[name] = None

    def stop_all_sounds(self, fade_ms: int = 0):
        """Stop all currently playing sounds"""
        if fade_ms > 0:
            pygame.mixer.fadeout(fade_ms)
        else:
            pygame.mixer.stop()
        self.channels.clear()

    def is_sound_playing(self, name: str) -> bool:
        """Check if a specific sound is currently playing"""
        if name in self.channels and self.channels[name]:
            return self.channels[name].get_busy()
        return False

    def load_music(self, path: str):
        """Load background music"""
        music_path = Path(path)
        if music_path.exists():
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music_volume)
            self.current_music = path
        else:
            print(f"Warning: Music file not found: {path}")

    def play_music(self, loops: int = -1, fade_ms: int = 0):
        """Play the loaded music. loops=-1 means loop forever"""
        if self.current_music:
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)

    def stop_music(self, fade_ms: int = 0):
        """Stop the currently playing music"""
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()

    def pause_music(self):
        """Pause the music"""
        pygame.mixer.music.pause()

    def unpause_music(self):
        """Resume paused music"""
        pygame.mixer.music.unpause()

    def set_sound_volume(self, volume: float):
        """Set volume for all sound effects (0.0 to 1.0)"""
        self.sound_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sound_volume)

    def set_music_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

    def cleanup(self):
        """Clean up all sounds - call this on state change or game exit"""
        self.stop_all_sounds()
        self.stop_music()
        self.channels.clear()
