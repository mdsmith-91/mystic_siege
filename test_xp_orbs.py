#!/usr/bin/env python3
import pygame
from pygame.math import Vector2
from src.entities.enemies.skeleton import Skeleton
from src.entities.player import Player
from src.entities.xp_orb import XPOrb

def test_xp_orb_dropping():
    """Test that XP orbs are dropped when enemies die."""
    pygame.init()

    # Create a player
    player = Player(Vector2(100, 100), {
        'name': 'Knight of the Burning Crown',
        'hp': 150,
        'speed': 180,
        'armor': 15,
        'color': (255, 0, 0)
    }, ())

    # Create sprite groups
    all_sprites = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()
    xp_orb_group = pygame.sprite.Group()

    # Create a skeleton
    skeleton = Skeleton(Vector2(200, 200), player, (all_sprites, enemy_group), xp_orb_group)

    print(f"Before damage:")
    print(f"  Skeleton HP: {skeleton.hp}")
    print(f"  XP orb group size: {len(xp_orb_group)}")
    print(f"  Skeleton in groups: {len(all_sprites)} all_sprites, {len(enemy_group)} enemy_group")

    # Take enough damage to kill the skeleton
    skeleton.take_damage(100)  # Skeleton has 30 HP, so this should kill it

    print(f"After damage:")
    print(f"  Skeleton HP: {skeleton.hp}")
    print(f"  Skeleton alive: {skeleton.is_alive}")
    print(f"  XP orb group size: {len(xp_orb_group)}")

    # Check if XP orb was created
    if len(xp_orb_group) > 0:
        print("SUCCESS: XP orb was created!")
        for orb in xp_orb_group:
            print(f"  XP orb at {orb.pos} with value {orb.value}")
    else:
        print("FAILURE: No XP orb was created!")

    pygame.quit()

if __name__ == "__main__":
    test_xp_orb_dropping()