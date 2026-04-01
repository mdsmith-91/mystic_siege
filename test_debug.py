#!/usr/bin/env python3
import pygame
from pygame.math import Vector2
from src.entities.enemies.skeleton import Skeleton
from src.entities.player import Player

def test_detailed():
    """Detailed debugging test."""
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

    print(f"Initial state:")
    print(f"  all_sprites: {len(all_sprites)} sprites")
    print(f"  enemy_group: {len(enemy_group)} sprites")
    print(f"  xp_orb_group: {len(xp_orb_group)} sprites")

    # Create a skeleton
    print(f"Creating skeleton...")
    skeleton = Skeleton(Vector2(200, 200), player, (all_sprites, enemy_group), xp_orb_group)

    print(f"After creation:")
    print(f"  all_sprites: {len(all_sprites)} sprites")
    print(f"  enemy_group: {len(enemy_group)} sprites")
    print(f"  xp_orb_group: {len(xp_orb_group)} sprites")
    print(f"  skeleton.xp_orb_group: {skeleton.xp_orb_group}")
    print(f"  skeleton.xp_orb_group len: {len(skeleton.xp_orb_group) if skeleton.xp_orb_group else 'N/A'}")

    # Add some debug to the skeleton's take_damage method
    original_take_damage = skeleton.take_damage

    def debug_take_damage(amount):
        print(f"DEBUG take_damage called with {amount}")
        print(f"  Before: skeleton.hp = {skeleton.hp}")
        print(f"  Before: skeleton.xp_orb_group = {skeleton.xp_orb_group}")
        print(f"  Before: len(skeleton.xp_orb_group) = {len(skeleton.xp_orb_group) if skeleton.xp_orb_group else 'N/A'}")
        print(f"  Before: condition check (hp <= 0 and xp_orb_group) = {skeleton.hp <= 0 and bool(skeleton.xp_orb_group)}")
        result = original_take_damage(amount)
        print(f"  After: skeleton.hp = {skeleton.hp}")
        print(f"  After: skeleton.xp_orb_group = {skeleton.xp_orb_group}")
        print(f"  After: len(skeleton.xp_orb_group) = {len(skeleton.xp_orb_group) if skeleton.xp_orb_group else 'N/A'}")
        return result

    skeleton.take_damage = debug_take_damage

    # Take enough damage to kill the skeleton
    print(f"Taking damage...")
    skeleton.take_damage(100)  # Skeleton has 30 HP, so this should kill it

    print(f"Final state:")
    print(f"  all_sprites: {len(all_sprites)} sprites")
    print(f"  enemy_group: {len(enemy_group)} sprites")
    print(f"  xp_orb_group: {len(xp_orb_group)} sprites")

    pygame.quit()

if __name__ == "__main__":
    test_detailed()