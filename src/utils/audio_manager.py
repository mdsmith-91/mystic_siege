import pygame
import os
from src.utils.resource_loader import ResourceLoader, _get_base_path

class AudioManager:
    _instance = None

    # Class-level constants for SFX names
    PLAYER_HIT = "player_hit"
    PLAYER_DEATH = "player_death"
    ENEMY_DEATH = "enemy_death"
    XP_PICKUP = "xp_pickup"
    LEVEL_UP = "level_up"
    WEAPON_ARCANE = "arcane_bolt"
    WEAPON_NOVA = "holy_nova"
    WEAPON_WHIP = "flame_whip"
    WEAPON_BLADE = "spectral_blade"
    WEAPON_CHAIN = "lightning_chain"
    WEAPON_FROST = "frost_ring"
    WEAPON_LONGBOW = "longbow"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._sfx_cache = {}
            self._sfx_volume = 1.0
            self._music_volume = 1.0
            self._music_playing = False

    @classmethod
    def instance(cls):
        """Return the AudioManager singleton."""
        return cls()

    def load_sfx(self, name: str, path: str):
        """Load SFX into _sfx_cache dict."""
        try:
            if pygame.mixer.get_init() is None:
                return

            sound = ResourceLoader.instance().load_sound(path)
            if sound is not None:
                self._sfx_cache[name] = sound
        except Exception:
            # Fail silently as requested
            pass

    def load_music(self, path: str):
        """Load music file."""
        try:
            if pygame.mixer.get_init() is None:
                return

            full_path = os.path.join(_get_base_path(), path)
            if not os.path.exists(full_path):
                return

            pygame.mixer.music.load(full_path)
        except Exception:
            # Fail silently as requested
            pass

    def play_sfx(self, name: str, volume: float = 1.0):
        """Play SFX from cache if exists."""
        try:
            if pygame.mixer.get_init() is None:
                return

            if name in self._sfx_cache:
                sound = self._sfx_cache[name]
                # Apply volume settings
                sound.set_volume(volume * self._sfx_volume)
                sound.play()
        except Exception:
            # Fail silently as requested
            pass

    def play_music(self, path: str, loop: bool = True, fade_ms: int = 500):
        """Play music with optional looping and fading."""
        try:
            if pygame.mixer.get_init() is None:
                return

            full_path = os.path.join(_get_base_path(), path)
            if not os.path.exists(full_path):
                return

            # Stop any currently playing music
            pygame.mixer.music.stop()

            # Load and play the music
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.set_volume(self._music_volume)
            pygame.mixer.music.play(-1 if loop else 0, fade_ms=fade_ms)
            self._music_playing = True
        except Exception:
            # Fail silently as requested
            pass

    def stop_music(self):
        """Stop currently playing music."""
        try:
            if pygame.mixer.get_init() is None:
                return

            pygame.mixer.music.stop()
            self._music_playing = False
        except Exception:
            # Fail silently as requested
            pass

    def pause_music(self):
        """Pause currently playing music."""
        try:
            if pygame.mixer.get_init() is None:
                return

            pygame.mixer.music.pause()
            self._music_playing = False
        except Exception:
            # Fail silently as requested
            pass

    def resume_music(self):
        """Resume paused music."""
        try:
            if pygame.mixer.get_init() is None:
                return

            pygame.mixer.music.unpause()
            self._music_playing = True
        except Exception:
            # Fail silently as requested
            pass

    def set_master_volume(self, v: float):
        """Set both SFX and music volume."""
        try:
            self.set_sfx_volume(v)
            self.set_music_volume(v)
        except Exception:
            # Fail silently as requested
            pass

    def set_sfx_volume(self, v: float):
        """Set SFX volume (stored, applied to all cached sounds)."""
        try:
            self._sfx_volume = max(0.0, min(1.0, v))
        except Exception:
            # Fail silently as requested
            pass

    def set_music_volume(self, v: float):
        """Set music volume."""
        try:
            self._music_volume = max(0.0, min(1.0, v))
            pygame.mixer.music.set_volume(self._music_volume)
        except Exception:
            # Fail silently as requested
            pass
