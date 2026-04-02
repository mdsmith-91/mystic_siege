import pygame
from src.weapons.base_weapon import BaseWeapon
from pygame.math import Vector2
import math
from src.utils.audio_manager import AudioManager

class HolyNova(BaseWeapon):
    name = "Holy Nova"
    description = "Emits an expanding ring of holy light, damaging all enemies it touches."
    base_damage = 25.0
    base_cooldown = 2.0
    base_radius = 80
    expand_speed = 200  # px per second
    ring_width = 8

    def __init__(self, owner, projectile_group, enemy_group):
        super().__init__(owner, projectile_group, enemy_group)

        # Define upgrade levels
        self.upgrade_levels = [
            {},  # Level 1 (no upgrade)
            {"base_damage": 15},  # L2: +15 damage
            {"base_radius": 40},  # L3: +40 radius
            {"base_cooldown": -0.4},  # L4: -0.4 cooldown
            {"base_damage": 20, "ring_width": -4}  # L5: more damage, narrower ring
        ]

        # Keep a list of active rings
        self.rings = []

    def fire(self):
        """Emit a new ring of holy light."""
        AudioManager.instance().play_sfx(AudioManager.WEAPON_NOVA)
        # Append new ring dict
        ring = {
            "radius": 0,
            "max_radius": self.base_radius,
            "damage": self.base_damage * self.owner.damage_multiplier,
            "enemies_hit": set()
        }
        self.rings.append(ring)

    def update(self, dt):
        """Update all active rings."""
        # Update cooldown timer
        super().update(dt)

        # Expand all active rings and check for collisions
        i = 0
        while i < len(self.rings):
            ring = self.rings[i]

            # Expand the ring
            ring["radius"] += self.expand_speed * dt

            # Check circle-vs-rect overlap against each enemy
            for enemy in self.enemy_group:
                # Calculate distance from ring center to enemy center
                distance = (enemy.pos - self.owner.pos).length()

                # Check if enemy is within the ring
                if (distance >= ring["radius"] - self.ring_width and
                    distance <= ring["radius"] + self.ring_width):

                    # Check if this enemy has already been damaged by this ring
                    if enemy.sprite_id not in ring["enemies_hit"]:
                        # Deal damage once per enemy per ring
                        enemy.take_damage(ring["damage"])
                        ring["enemies_hit"].add(enemy.sprite_id)

            # Remove rings that exceed max_radius
            if ring["radius"] > ring["max_radius"]:
                self.rings.pop(i)
            else:
                i += 1

    def draw(self, surface, camera_offset):
        """Draw the expanding holy rings."""
        for ring in self.rings:
            center = (
                int(self.owner.pos.x - camera_offset.x),
                int(self.owner.pos.y - camera_offset.y),
            )
            radius = int(ring["radius"])
            if radius > 0:
                pygame.draw.circle(surface, (255, 230, 100), center, radius, self.ring_width)