#!/usr/bin/env python3
"""Generate placeholder assets for Mystic Siege."""

import os
import wave
import numpy as np
import pygame
from pygame.math import Vector2

def create_asset_directories():
    """Create all required asset directories."""
    directories = [
        "assets/sprites/heroes/",
        "assets/sprites/enemies/",
        "assets/sprites/projectiles/",
        "assets/sprites/effects/",
        "assets/sprites/ui/",
        "assets/audio/sfx/",
        "assets/audio/music/",
        "assets/fonts/"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def generate_hero_assets():
    """Generate hero placeholder assets."""
    # Initialize pygame headlessly
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    # Hero colors and labels
    heroes = [
        ("knight.png", (180, 140, 60), "K"),
        ("wizard.png", (160, 60, 220), "W"),
        ("friar.png", (200, 180, 120), "F")
    ]

    for filename, color, label in heroes:
        # Create 32x32 surface
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)

        # Draw filled rectangle
        pygame.draw.rect(surface, color, (0, 0, 32, 32))

        # Draw label
        font = pygame.font.SysFont(None, 24)
        text = font.render(label, True, (255, 255, 255))
        text_rect = text.get_rect(center=(16, 16))
        surface.blit(text, text_rect)

        # Only write if no real asset exists
        filepath = f"assets/sprites/heroes/{filename}"
        if not os.path.exists(filepath):
            pygame.image.save(surface, filepath)

def generate_enemy_assets():
    """Generate enemy placeholder assets."""
    # Initialize pygame headlessly
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    # Enemy assets
    enemies = [
        ("skeleton.png", (200, 200, 200), "S"),
        ("goblin.png", (60, 160, 60), "G"),
        ("wraith.png", (100, 100, 180), "W"),
        ("bat.png", (80, 40, 80), "B"),
        ("golem.png", (120, 100, 80), "G"),
        ("knight_enemy.png", (100, 100, 140), "K"),
        ("lich.png", (140, 60, 160), "L")
    ]

    for filename, color, label in enemies:
        # Create surface
        if filename == "golem.png":
            # Larger 48x48 surface for golem
            surface = pygame.Surface((48, 48), pygame.SRCALPHA)
            pygame.draw.rect(surface, color, (0, 0, 48, 48))
        else:
            surface = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.rect(surface, color, (0, 0, 32, 32))

        # Special handling for wraith (with alpha)
        if filename == "wraith.png":
            # Set alpha to 180 for wraith
            for x in range(surface.get_width()):
                for y in range(surface.get_height()):
                    r, g, b, a = surface.get_at((x, y))
                    surface.set_at((x, y), (r, g, b, 180))

        # Draw label
        font = pygame.font.SysFont(None, 24)
        text = font.render(label, True, (255, 255, 255))
        text_rect = text.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
        surface.blit(text, text_rect)

        # Only write if no real asset exists
        filepath = f"assets/sprites/enemies/{filename}"
        if not os.path.exists(filepath):
            pygame.image.save(surface, filepath)

def generate_projectile_assets():
    """Generate projectile placeholder assets."""
    # Initialize pygame headlessly
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    # Projectile assets
    projectiles = [
        ("arcane.png", (160, 80, 255)),
        ("nova.png", (212, 175, 55)),
        ("fire.png", (255, 100, 20)),
        ("frost.png", (80, 200, 255)),
        ("lightning.png", (255, 240, 60))
    ]

    for filename, color in projectiles:
        # Create 16x16 surface
        surface = pygame.Surface((16, 16), pygame.SRCALPHA)

        # Draw circle
        pygame.draw.circle(surface, color, (8, 8), 8)

        # Only write if no real asset exists
        filepath = f"assets/sprites/projectiles/{filename}"
        if not os.path.exists(filepath):
            pygame.image.save(surface, filepath)

def generate_xp_orb_asset():
    """Generate XP orb placeholder asset."""
    # Initialize pygame headlessly
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    # Create 12x12 surface
    surface = pygame.Surface((12, 12), pygame.SRCALPHA)

    # Draw gold circle
    pygame.draw.circle(surface, (212, 175, 55), (6, 6), 6)

    # Only write if no real asset exists
    filepath = "assets/sprites/effects/xp_orb.png"
    if not os.path.exists(filepath):
        pygame.image.save(surface, filepath)

def generate_weapon_icon_assets():
    """Generate weapon icon placeholder assets."""
    # Initialize pygame headlessly
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    # Weapon colors matching projectiles
    weapons = [
        ("arcane.png", (160, 80, 255)),
        ("nova.png", (212, 175, 55)),
        ("fire.png", (255, 100, 20)),
        ("frost.png", (80, 200, 255)),
        ("lightning.png", (255, 240, 60)),
        ("blade.png", (100, 150, 255))  # Spectral blade color
    ]

    for filename, color in weapons:
        # Create 32x32 surface
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)

        # Draw filled rectangle with color
        pygame.draw.rect(surface, color, (0, 0, 32, 32))

        # Draw weapon symbol
        font = pygame.font.SysFont(None, 24)
        symbol = filename.split('.')[0]  # Get weapon name without extension
        symbol = symbol[0].upper()  # Get first letter
        text = font.render(symbol, True, (255, 255, 255))
        text_rect = text.get_rect(center=(16, 16))
        surface.blit(text, text_rect)

        # Only write if no real asset exists
        filepath = f"assets/sprites/ui/{filename}"
        if not os.path.exists(filepath):
            pygame.image.save(surface, filepath)

def _write_sine_wav(path: str, freq_hz: float, duration_s: float, volume: float = 0.25, sample_rate: int = 44100):
    """Write a mono sine-wave WAV file."""
    n = int(sample_rate * duration_s)
    t = np.linspace(0, duration_s, n, endpoint=False)
    # Apply a short fade-out envelope to avoid clicks
    envelope = np.minimum(1.0, np.linspace(1.0, 0.0, n) * (n / max(1, int(sample_rate * 0.01))))
    samples = (np.sin(2 * np.pi * freq_hz * t) * envelope * volume * 32767).astype(np.int16)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())


def _write_sweep_wav(path: str, freq_start: float, freq_end: float, duration_s: float, volume: float = 0.25, sample_rate: int = 44100):
    """Write a mono frequency-sweep (chirp) WAV file."""
    n = int(sample_rate * duration_s)
    freq = np.linspace(freq_start, freq_end, n)
    phase = np.cumsum(2 * np.pi * freq / sample_rate)
    envelope = np.linspace(1.0, 0.0, n)
    samples = (np.sin(phase) * envelope * volume * 32767).astype(np.int16)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())


def _write_chord_wav(path: str, freqs: list, duration_s: float, volume: float = 0.2, sample_rate: int = 44100):
    """Write a mono chord WAV file by mixing multiple sine frequencies."""
    n = int(sample_rate * duration_s)
    t = np.linspace(0, duration_s, n, endpoint=False)
    envelope = np.linspace(1.0, 0.0, n)
    mixed = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
    samples = (mixed * envelope * volume * 32767).astype(np.int16)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())


def generate_audio_placeholders():
    """Generate placeholder SFX WAV files using simple sine waves."""
    sfx_dir = "assets/audio/sfx/"

    # Only write each file if no real asset exists
    def maybe_write_sine(name, **kw):
        p = f"{sfx_dir}{name}"
        if not os.path.exists(p):
            _write_sine_wav(p, **kw)

    def maybe_write_sweep(name, **kw):
        p = f"{sfx_dir}{name}"
        if not os.path.exists(p):
            _write_sweep_wav(p, **kw)

    def maybe_write_chord(name, **kw):
        p = f"{sfx_dir}{name}"
        if not os.path.exists(p):
            _write_chord_wav(p, **kw)

    maybe_write_sine("player_hit.wav",      freq_hz=220,  duration_s=0.10)
    maybe_write_sweep("player_death.wav",   freq_start=440, freq_end=110, duration_s=0.40)
    maybe_write_sine("enemy_death.wav",     freq_hz=660,  duration_s=0.06)
    maybe_write_sine("xp_pickup.wav",       freq_hz=1320, duration_s=0.05)
    maybe_write_chord("level_up.wav",       freqs=[330, 440, 550], duration_s=0.35)
    maybe_write_sine("arcane_bolt.wav",     freq_hz=880,  duration_s=0.07)
    maybe_write_sine("holy_nova.wav",       freq_hz=110,  duration_s=0.25)
    maybe_write_sine("flame_whip.wav",      freq_hz=330,  duration_s=0.10)
    maybe_write_sine("spectral_blade.wav",  freq_hz=550,  duration_s=0.06)
    maybe_write_sine("lightning_chain.wav", freq_hz=1760, duration_s=0.08)
    maybe_write_sine("frost_ring.wav",      freq_hz=220,  duration_s=0.20)


def main():
    """Generate all placeholder assets."""
    print("Generating placeholder assets...")

    # Create directories
    create_asset_directories()

    # Generate assets
    generate_hero_assets()
    generate_enemy_assets()
    generate_projectile_assets()
    generate_xp_orb_asset()
    generate_weapon_icon_assets()
    generate_audio_placeholders()

    print("Generated 28 placeholder assets to assets/")
    print("Run 'python main.py' to start the game")

if __name__ == "__main__":
    main()