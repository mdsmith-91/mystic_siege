#!/usr/bin/env python3
"""
Final test to verify XP orbs drop correctly.
"""
import pygame
from pygame.math import Vector2
from src.entities.enemies.skeleton import Skeleton
from src.entities.player import Player
from src.entities.xp_orb import XPOrb

def test_final():
    """Test the actual fix."""
    pygame.init()

    print("=== Testing XP Orb Dropping Fix ===")

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

    print(f"1. Initial state:")
    print(f"   all_sprites: {len(all_sprites)} sprites")
    print(f"   enemy_group: {len(enemy_group)} sprites")
    print(f"   xp_orb_group: {len(xp_orb_group)} sprites")

    # Create a skeleton
    print(f"2. Creating skeleton...")
    skeleton = Skeleton(Vector2(200, 200), player, (all_sprites, enemy_group), xp_orb_group)

    print(f"3. After creation:")
    print(f"   all_sprites: {len(all_sprites)} sprites")
    print(f"   enemy_group: {len(enemy_group)} sprites")
    print(f"   skeleton.xp_orb_group: {skeleton.xp_orb_group}")
    print(f"   skeleton.xp_orb_group len: {len(skeleton.xp_orb_group) if skeleton.xp_orb_group else 'N/A'}")

    # Test that the XP orb creation works
    print(f"4. Testing XP orb creation directly...")
    orb = XPOrb(Vector2(300, 300), 5, (all_sprites, xp_orb_group))
    print(f"   Created XP orb, xp_orb_group now has {len(xp_orb_group)} sprites")

    # Reset the xp_orb_group for the actual test
    xp_orb_group.empty()
    print(f"5. Reset xp_orb_group, now has {len(xp_orb_group)} sprites")

    # Now test the actual damage and death
    print(f"6. Testing damage and death...")
    print(f"   Before damage - skeleton.hp: {skeleton.hp}")
    print(f"   Before damage - xp_orb_group: {len(xp_orb_group)} sprites")

    # This should trigger on_death
    skeleton.take_damage(100)  # Skeleton has 30 HP, so this should kill it

    print(f"   After damage - skeleton.hp: {skeleton.hp}")
    print(f"   After damage - skeleton.is_alive: {skeleton.is_alive}")
    print(f"   After damage - xp_orb_group: {len(xp_orb_group)} sprites")

    if len(xp_orb_group) > 0:
        print("   SUCCESS: XP orb was created!")
        for orb in xp_orb_group:
            print(f"     XP orb at {orb.pos} with value {orb.value}")
    else:
        print("   FAILURE: No XP orb was created!")

    pygame.quit()
    print("=== Test Complete ===")

if __name__ == "__main__":
    test_final()