#!/usr/bin/env python3
"""Generate placeholder assets for Mystic Siege."""

import os
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
        ("witch.png", (160, 60, 220), "W"),
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

        # Save file
        filepath = f"assets/sprites/heroes/{filename}"
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
        ("knight_e.png", (100, 100, 140), "K"),
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

        # Save file
        filepath = f"assets/sprites/enemies/{filename}"
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

        # Save file
        filepath = f"assets/sprites/projectiles/{filename}"
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

    # Save file
    filepath = "assets/sprites/effects/xp_orb.png"
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

        # Save file
        filepath = f"assets/sprites/ui/{filename}"
        pygame.image.save(surface, filepath)

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

    print("Generated 17 placeholder assets to assets/")
    print("Run 'python main.py' to start the game")

if __name__ == "__main__":
    main()